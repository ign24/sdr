"""Audit wheel and source-distribution contents against the public package contract."""

from __future__ import annotations

import argparse
import re
import tarfile
import tempfile
import zipfile
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .public_tree_audit import Finding as TreeFinding
from .public_tree_audit import audit_bytes, audit_tree, redact_sensitive

MAX_MEMBER_SIZE = 25 * 1024 * 1024
MAX_TOTAL_SIZE = 100 * 1024 * 1024
WHEEL_METADATA_RE = re.compile(r"^[A-Za-z0-9_.]+-[^/]+\.dist-info$")
SDIST_ROOT_RE = re.compile(r"^spec_driven_research-[^/]+$")
SDIST_FILES = {
    ".gitignore",
    ".gitleaks.toml",
    "AGENTS.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "PKG-INFO",
    "README.es.md",
    "README.md",
    "SECURITY.md",
    "pyproject.toml",
    "uv.lock",
}
SDIST_DIRECTORIES = {
    ".github",
    "docs",
    "examples",
    "integrations",
    "openspec/specs",
    "skills",
    "src/sdr",
    "tests",
}


@dataclass(frozen=True)
class ArtifactFinding:
    artifact: str
    code: str
    path: str
    line: int | None = None


@dataclass(frozen=True)
class _Member:
    name: str
    size: int
    is_file: bool
    is_safe_type: bool
    source: zipfile.ZipInfo | tarfile.TarInfo


def audit_artifact(path: Path) -> list[ArtifactFinding]:
    """Audit one wheel or gzipped source distribution without unsafe extraction."""
    path = path.resolve()
    try:
        if path.suffix == ".whl":
            with zipfile.ZipFile(path) as archive:
                members = [_zip_member(item) for item in archive.infolist()]
                return _audit_members(path, members, lambda item: archive.read(item.source))
        if path.name.endswith(".tar.gz"):
            with tarfile.open(path, "r:gz") as archive:
                members = [_tar_member(item) for item in archive.getmembers()]
                return _audit_members(path, members, lambda item: _read_tar(archive, item))
    except (OSError, tarfile.TarError, zipfile.BadZipFile):
        return [ArtifactFinding(path.name, "invalid-archive", path.name)]
    return [ArtifactFinding(path.name, "unsupported-artifact", path.name)]


def audit_artifacts(paths: Iterable[Path]) -> list[ArtifactFinding]:
    """Audit artifacts in deterministic path order."""
    findings = [item for path in sorted(paths) for item in audit_artifact(path)]
    return sorted(findings, key=lambda item: (item.artifact, item.path, item.line or 0, item.code))


def render_findings(findings: Sequence[ArtifactFinding]) -> str:
    """Render locations and categories without rendering matched content."""
    lines = []
    for finding in findings:
        location = redact_sensitive(f"{finding.artifact}:{finding.path}")
        if finding.line is not None:
            location += f":{finding.line}"
        lines.append(f"{location} [{finding.code}] sensitive content redacted")
    return "\n".join(lines)


def _audit_members(
    artifact: Path,
    members: list[_Member],
    read_member: Callable[[_Member], bytes],
) -> list[ArtifactFinding]:
    findings: list[ArtifactFinding] = []
    seen: set[str] = set()
    total_size = 0
    safe_files: list[_Member] = []
    names = {item.name for item in members if item.is_file}

    for member in members:
        if member.name in seen:
            findings.append(ArtifactFinding(artifact.name, "duplicate-member", member.name))
        seen.add(member.name)
        if not _safe_name(member.name) or not member.is_safe_type:
            findings.append(ArtifactFinding(artifact.name, "unsafe-member", member.name))
            continue
        if not _allowed_member(artifact, member.name):
            findings.append(ArtifactFinding(artifact.name, "unexpected-member", member.name))
        if not member.is_file:
            continue
        total_size += member.size
        if member.size > MAX_MEMBER_SIZE or total_size > MAX_TOTAL_SIZE:
            findings.append(ArtifactFinding(artifact.name, "oversized-member", member.name))
            continue
        safe_files.append(member)
        findings.extend(
            _tree_findings(artifact.name, audit_bytes(read_member(member), member.name))
        )

    findings.extend(_required_findings(artifact, names))
    with tempfile.TemporaryDirectory(prefix="sdr-artifact-audit-") as directory:
        root = Path(directory)
        for member in safe_files:
            target = root.joinpath(*PurePosixPath(member.name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(read_member(member))
        findings.extend(_tree_findings(artifact.name, audit_tree(root)))
    return sorted(findings, key=lambda item: (item.path, item.line or 0, item.code))


def _allowed_member(artifact: Path, name: str) -> bool:
    parts = PurePosixPath(name).parts
    if artifact.suffix == ".whl":
        return bool(parts) and (
            parts[0] == "sdr" or WHEEL_METADATA_RE.fullmatch(parts[0]) is not None
        )
    if not parts or SDIST_ROOT_RE.fullmatch(parts[0]) is None:
        return False
    relative = "/".join(parts[1:])
    return relative in SDIST_FILES or any(
        relative == prefix or relative.startswith(f"{prefix}/") for prefix in SDIST_DIRECTORIES
    )


def _required_findings(artifact: Path, names: set[str]) -> list[ArtifactFinding]:
    if artifact.suffix == ".whl":
        required = {"sdr/__init__.py", "sdr/cli.py", "sdr/py.typed", "sdr/templates/brief.md"}
        metadata_required = {"METADATA", "WHEEL", "RECORD"}
        missing = required - names
        for metadata_name in metadata_required:
            if not any(
                WHEEL_METADATA_RE.fullmatch(PurePosixPath(name).parts[0])
                and PurePosixPath(name).name == metadata_name
                for name in names
            ):
                missing.add(f"*.dist-info/{metadata_name}")
    else:
        relative_names = {
            "/".join(PurePosixPath(name).parts[1:])
            for name in names
            if len(PurePosixPath(name).parts) > 1
        }
        missing = {
            "LICENSE",
            "README.md",
            "pyproject.toml",
            "src/sdr/__init__.py",
            "src/sdr/cli.py",
            "src/sdr/py.typed",
            "src/sdr/templates/brief.md",
        } - relative_names
    return [ArtifactFinding(artifact.name, "missing-member", name) for name in sorted(missing)]


def _safe_name(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and ".." not in path.parts and "\\" not in name


def _zip_member(info: zipfile.ZipInfo) -> _Member:
    mode = info.external_attr >> 16
    is_symlink = (mode & 0o170000) == 0o120000
    return _Member(info.filename, info.file_size, not info.is_dir(), not is_symlink, info)


def _tar_member(info: tarfile.TarInfo) -> _Member:
    return _Member(info.name, info.size, info.isfile(), info.isfile() or info.isdir(), info)


def _read_tar(archive: tarfile.TarFile, member: _Member) -> bytes:
    extracted = archive.extractfile(member.source)
    if extracted is None:
        return b""
    with extracted:
        return extracted.read(MAX_MEMBER_SIZE + 1)


def _tree_findings(artifact: str, findings: list[TreeFinding]) -> list[ArtifactFinding]:
    return [ArtifactFinding(artifact, item.code, item.path, item.line) for item in findings]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifacts", nargs="+", type=Path)
    args = parser.parse_args(argv)
    findings = audit_artifacts(args.artifacts)
    if findings:
        print(render_findings(findings))
        return 1
    print(f"artifacts: OK ({len(args.artifacts)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
