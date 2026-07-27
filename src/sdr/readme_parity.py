"""Deterministic semantic parity checks for the English and Spanish READMEs."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ParityFinding:
    code: str
    path: str
    message: str


CRITICAL_COMMANDS = (
    "sdr new",
    "sdr check",
    "sdr advance",
    "sdr status",
    "sdr snapshot",
    "sdr verify-claims",
    "sdr resolve-claim",
    "sdr verify-probe",
    "sdr approve",
    "sdr reopen",
    "sdr drop",
    "sdr archive",
    "sdr index",
    "sdr doctor",
    "sdr migrate",
    "sdr context",
)
STAGES = ("intake", "explore", "probe", "transfer", "reuse")
INTEGRATIONS = ("Claude Code", "Codex", "Hermes Agent", "OpenClaw", "OpenCode")
REQUIRED_LINKS = (
    "docs/workflow.md",
    "docs/cli-reference.md",
    "docs/evidence-model.md",
    "docs/validation.md",
    "docs/integrations.md",
    "docs/security-model.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "AGENTS.md",
    "LICENSE",
)
SHARED_CONTRACTS = {
    "critical-commands": CRITICAL_COMMANDS,
    "five-stages": STAGES,
    "modes": ("full", "light"),
    "integrations": INTEGRATIONS,
    "status": ("sdr status", "--json"),
    "links": REQUIRED_LINKS,
    "compatibility": ("Python 3.12", "uv tool install .", "python -m pip install ."),
    "probe-execution": ("verify.action: run", "argv", "without a shell|sin un shell"),
    "controls": (
        "Structural|Estructural",
        "Evidential",
        "Textual anchoring|Anclaje textual",
        "Executable|Ejecutable",
        "Hash consistency|Consistencia de hashes",
        "HITL",
    ),
    "security": (
        "trust boundaries|límites de confianza",
        "credentials|credenciales",
        "sandbox",
    ),
}
LOCALIZED_CONTRACTS = {
    "README.md": {
        "offline-skipped": ("--offline", "skipped", "not passed"),
        "context-graph": ("Context Graph", "optional", "non-blocking", "not complete lineage"),
    },
    "README.es.md": {
        "offline-skipped": ("--offline", "omitid", "no aprob"),
        "context-graph": ("Context Graph", "opcional", "no bloqueante", "trazabilidad completa"),
    },
}
LANGUAGE_LINKS = {
    "README.md": "README.es.md",
    "README.es.md": "README.md",
}


def validate_readme_parity(root: Path) -> list[ParityFinding]:
    """Validate required concepts without comparing translated prose line by line."""
    findings: list[ParityFinding] = []
    for filename, counterpart in LANGUAGE_LINKS.items():
        path = root / filename
        if not path.is_file():
            findings.append(ParityFinding("missing-readme", filename, f"create {filename}"))
            continue

        text = path.read_text(encoding="utf-8")
        opening = "\n".join(text.splitlines()[:15])
        if f"]({counterpart})" not in opening:
            findings.append(
                ParityFinding(
                    "language-link",
                    filename,
                    f"add a prominent reciprocal link to {counterpart} within the first 15 lines",
                )
            )

        for code, markers in SHARED_CONTRACTS.items():
            _require_markers(findings, filename, text, code, markers)
        for code, markers in LOCALIZED_CONTRACTS[filename].items():
            _require_markers(findings, filename, text, code, markers)

    return sorted(findings, key=lambda item: (item.path, item.code, item.message))


def _require_markers(
    findings: list[ParityFinding],
    filename: str,
    text: str,
    code: str,
    markers: Sequence[str],
) -> None:
    normalized = text.casefold()
    missing = [
        marker
        for marker in markers
        if not any(option.casefold() in normalized for option in marker.split("|"))
    ]
    if missing:
        findings.append(
            ParityFinding(
                code,
                filename,
                f"document the missing contract markers: {', '.join(missing)}",
            )
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    findings = validate_readme_parity(args.root)
    if findings:
        for finding in findings:
            print(f"{finding.path} [{finding.code}] {finding.message}")
        return 1
    print("README parity: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
