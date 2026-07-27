"""Ejecución reproducible y confinada de la etapa probe."""

from __future__ import annotations

import hashlib
import os
import re
import shlex
import signal
import subprocess
import threading
from dataclasses import dataclass
from datetime import date
from typing import Any, BinaryIO

from sdr.parser import parse_artifact
from sdr.research import Research

OUTPUT_LIMIT_BYTES = 4000


@dataclass(frozen=True)
class ProbeVerifyResult:
    passed: bool
    argv: list[str]
    expect: str
    exit_code: int | None
    output: str
    probe_hash: str
    cwd: str
    environment: str
    output_limit_bytes: int = OUTPUT_LIMIT_BYTES
    output_truncated: bool = False
    timed_out: bool = False
    error_code: str | None = None
    error: str | None = None

    @property
    def result(self) -> str:
        return "pass" if self.passed else "fail"

    @property
    def command(self) -> str:
        """Representación legible; la ejecución usa siempre ``argv``."""
        return shlex.join(self.argv)

    def to_dict(self) -> dict[str, object]:
        return {
            "result": self.result,
            "action": "run",
            "argv": self.argv,
            "command": self.command,
            "expect": self.expect,
            "exit_code": self.exit_code,
            "output": self.output,
            "probe_hash": self.probe_hash,
            "cwd": self.cwd,
            "environment": self.environment,
            "output_limit_bytes": self.output_limit_bytes,
            "output_truncated": self.output_truncated,
            "timed_out": self.timed_out,
            "error_code": self.error_code,
            "error": self.error,
        }


def verify_probe(research: Research, *, timeout: float = 300) -> ProbeVerifyResult:
    """Ejecuta una acción ``run`` sin shell, confinada al directorio probe/."""
    verify = _verify_config(research)
    argv = _argv(verify)
    expect = str(verify["expect"])
    environment = str(verify.get("environment") or "clean")
    cwd = research.artifact_path("probe").resolve()
    if timeout <= 0:
        raise ValueError("verify-probe requiere un timeout mayor que cero")

    process: subprocess.Popen[bytes] | None = None
    output = ""
    output_truncated = False
    exit_code: int | None = None
    timed_out = False
    error_code: str | None = None
    error: str | None = None
    try:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=_execution_environment(environment),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=os.name != "nt",
            creationflags=(
                getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
            ),
        )
        captured = bytearray()
        state = {"truncated": False}
        reader = threading.Thread(
            target=_capture_output,
            args=(process.stdout, captured, state),
            daemon=True,
        )
        reader.start()
        try:
            exit_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            error_code = "timeout"
            error = f"el comando excedió el timeout de {timeout:g}s"
            _terminate_process_tree(process)
            process.wait()
        reader.join()
        output_truncated = state["truncated"]
        output = captured.decode("utf-8", errors="replace")
        if output_truncated:
            output += "...<truncated>"
        if timed_out:
            output += f"\ntimeout {timeout:g}s"
    except FileNotFoundError as exc:
        error_code = "command_not_found"
        error = f"no se encontró el ejecutable: {argv[0]}"
        output = str(exc)
    except PermissionError as exc:
        error_code = "permission_denied"
        error = f"no se puede ejecutar: {argv[0]}"
        output = str(exc)
    except OSError as exc:
        error_code = "spawn_error"
        error = f"no se pudo iniciar el comando: {exc}"
        output = str(exc)

    matches = False
    if error_code is None:
        try:
            matches = expect in output or re.search(expect, output, flags=re.MULTILINE) is not None
        except re.error as exc:
            error_code = "invalid_expect"
            error = f"verify.expect no es una expresión regular válida: {exc}"
    passed = exit_code == 0 and matches and error_code is None
    probe_hash = hash_probe_dir(research)
    result = ProbeVerifyResult(
        passed=passed,
        argv=argv,
        expect=expect,
        exit_code=exit_code,
        output=output,
        probe_hash=probe_hash,
        cwd=str(cwd),
        environment=environment,
        output_truncated=output_truncated,
        timed_out=timed_out,
        error_code=error_code,
        error=error,
    )
    research.meta.verify_probe = {**result.to_dict(), "date": date.today().isoformat()}
    research.save()
    return result


def hash_probe_dir(research: Research) -> str:
    """Hash estable del contenido versionable de probe/."""
    digest = hashlib.sha256()
    probe_dir = research.artifact_path("probe")
    for path in sorted(probe_dir.rglob("*")) if probe_dir.is_dir() else []:
        if path.is_file():
            digest.update(str(path.relative_to(probe_dir)).encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _verify_config(research: Research) -> dict[str, Any]:
    path = research.artifact_path("probe/results.md")
    if not path.exists():
        raise ValueError("falta probe/results.md")
    verify = parse_artifact(path).frontmatter.get("verify") or {}
    if not isinstance(verify, dict):
        raise ValueError("verify debe ser un objeto en probe/results.md")
    if verify.get("action") != "run":
        raise ValueError("verify.action debe declarar explícitamente 'run'")
    if not verify.get("expect"):
        raise ValueError("falta verify.expect en probe/results.md")
    if bool(verify.get("argv")) == bool(verify.get("command")):
        raise ValueError("verify debe declarar exactamente uno de argv o command")
    environment = verify.get("environment") or "clean"
    if environment not in {"clean", "inherit"}:
        raise ValueError("verify.environment debe ser 'clean' o 'inherit'")
    return verify


def _argv(verify: dict[str, Any]) -> list[str]:
    value = verify.get("argv")
    if value is not None:
        if (
            not isinstance(value, list)
            or not value
            or not all(isinstance(arg, str) for arg in value)
        ):
            raise ValueError("verify.argv debe ser una lista no vacía de strings")
        argv = list(value)
    else:
        try:
            argv = shlex.split(str(verify["command"]), posix=os.name != "nt")
        except ValueError as exc:
            raise ValueError(f"verify.command legacy no se puede tokenizar: {exc}") from exc
        if not argv:
            raise ValueError("verify.command legacy no puede estar vacío")
    if any("\0" in arg for arg in argv):
        raise ValueError("verify argv no admite bytes NUL")
    return argv


def _execution_environment(policy: str) -> dict[str, str]:
    if policy == "inherit":
        return os.environ.copy()
    allowed = ("PATH", "PATHEXT", "SYSTEMROOT", "WINDIR")
    return {name: os.environ[name] for name in allowed if name in os.environ}


def _capture_output(stream: BinaryIO | None, captured: bytearray, state: dict[str, bool]) -> None:
    if stream is None:
        return
    while chunk := stream.read(8192):
        remaining = OUTPUT_LIMIT_BYTES - len(captured)
        if remaining > 0:
            captured.extend(chunk[:remaining])
        if len(chunk) > remaining:
            state["truncated"] = True
    stream.close()


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    """Termina el grupo creado para la acción y evita descendientes huérfanos."""
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if process.poll() is None:
            process.kill()
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
