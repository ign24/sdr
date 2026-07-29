"""Deterministic semantic parity checks for the English and Spanish READMEs."""

from __future__ import annotations

import argparse
import re
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
INTEGRATIONS = ("Claude Code", "Codex", "OpenCode")
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
    "integration-installation": (
        "sdr integrations install --destination",
        ".claude/skills",
        ".agents/skills",
        ".opencode/skills",
        "SDR_ROOT",
    ),
    "integration-statuses": ("`documented`", "`verified`", "`experimental`"),
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
    "docs/README.md": "README.es.md",
    "docs/README.es.md": "README.md",
    "docs/getting-started.md": "getting-started.es.md",
    "docs/getting-started.es.md": "getting-started.md",
}
PAIR_CONTRACTS = {
    "README.md": {
        "outcome-chain": (
            "question",
            "evidence",
            "optional probe",
            "human-approved decision",
            "reusable asset",
        ),
        "source-only-alpha": (
            "alpha",
            "source checkout|source-only",
            "no GitHub release",
            "no PyPI release|or PyPI release|does not publish to PyPI",
        ),
        "evidence-boundaries": (
            "does not prove source truth|guarantee that cited material is true",
            "People remain responsible",
        ),
        "git-side-effects": (
            "`new`, `advance`, `reopen`, `drop`, and `archive` commit by default",
            "--no-commit",
        ),
    },
    "README.es.md": {
        "outcome-chain": (
            "pregunta",
            "evidencia|pruebas",
            "probe opcional",
            "decisión con aprobación humana|decisión aprobada por una persona",
            "activo reutilizable",
        ),
        "source-only-alpha": (
            "alfa|alpha",
            "checkout del código fuente|solo desde el código fuente",
            "no hay release en GitHub",
            "no hay release en PyPI|ni en PyPI|no publica en PyPI",
        ),
        "evidence-boundaries": (
            "no demuestra la verdad de las fuentes|garantía de veracidad",
            "Las personas responden|Las personas siguen siendo responsables",
        ),
        "git-side-effects": (
            "`new`, `advance`, `reopen`, `drop` y `archive` crean commits por defecto",
            "--no-commit",
        ),
    },
    "docs/README.md": {
        "documentation-routes": (
            "getting-started.md",
            "workflow.md",
            "cli-reference.md",
            "evidence-model.md",
            "security-model.md",
            "integrations.md",
            "validation.md",
            "releasing.md",
        ),
    },
    "docs/README.es.md": {
        "documentation-routes": (
            "getting-started.es.md",
            "workflow.md",
            "cli-reference.md",
            "evidence-model.md",
            "security-model.md",
            "integrations.md",
            "validation.md",
            "releasing.md",
        ),
    },
    "docs/getting-started.md": {
        "light-lifecycle": ("intake -> explore -> transfer -> reuse -> done",),
        "light-boundaries": ("offline", "no probe", "explicit", "approve", "reuse", "mandatory"),
        "git-side-effects": ("commit by default", "--no-commit", "Git"),
        "synthetic-fixture": (
            "../examples/light-complete/README.md",
            "../examples/light-complete/brief.md",
            "../examples/light-complete/notes/landscape.md",
            "../examples/light-complete/decision-memo.md",
            "../examples/light-complete/assets/checklist.md",
        ),
    },
    "docs/getting-started.es.md": {
        "light-lifecycle": ("intake -> explore -> transfer -> reuse -> done",),
        "light-boundaries": (
            "sin red|offline",
            "no ejecuta probes|sin probe",
            "explícit",
            "approve",
            "reuse",
            "obligatori",
        ),
        "git-side-effects": ("commits por defecto|commit por defecto", "--no-commit", "Git"),
        "synthetic-fixture": (
            "../examples/light-complete/README.md",
            "../examples/light-complete/brief.md",
            "../examples/light-complete/notes/landscape.md",
            "../examples/light-complete/decision-memo.md",
            "../examples/light-complete/assets/checklist.md",
        ),
    },
}
ONBOARDING_DOCUMENTS = tuple(LANGUAGE_LINKS)
DOCUMENTED_AGENTS = frozenset(INTEGRATIONS)
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^]]*]\(([^)\s]+)(?:\s+[^)]*)?\)")
PACKAGE_INDEX_CLAIMS = (
    re.compile(r"\bpip install\s+(?![\"']?\.)sdr\b", re.IGNORECASE),
    re.compile(r"\buv tool install\s+(?![\"']?\.)sdr\b", re.IGNORECASE),
    re.compile(r"https?://pypi\.org/project/sdr(?:/|\b)", re.IGNORECASE),
    re.compile(r"\b(?:install(?:ed)? from|available on) PyPI\b", re.IGNORECASE),
)


def validate_readme_parity(root: Path) -> list[ParityFinding]:
    """Validate required concepts without comparing translated prose line by line."""
    findings: list[ParityFinding] = []
    for filename, counterpart in LANGUAGE_LINKS.items():
        path = root / filename
        if not path.is_file():
            code = "missing-readme" if path.parent == root else "missing-document"
            findings.append(ParityFinding(code, filename, f"create {filename}"))
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

        if filename in LOCALIZED_CONTRACTS:
            for code, markers in SHARED_CONTRACTS.items():
                _require_markers(findings, filename, text, code, markers)
            for code, markers in LOCALIZED_CONTRACTS[filename].items():
                _require_markers(findings, filename, text, code, markers)
            _validate_documented_agents(findings, filename, text)
        for code, markers in PAIR_CONTRACTS[filename].items():
            contract_text = "\n".join(text.splitlines()[:30]) if code == "outcome-chain" else text
            _require_markers(findings, filename, contract_text, code, markers)

        _validate_local_links(findings, root, filename, text)

    _reject_package_index_claims_when_disabled(findings, root)

    return sorted(findings, key=lambda item: (item.path, item.code, item.message))


def _validate_documented_agents(findings: list[ParityFinding], filename: str, text: str) -> None:
    documented = {
        match.group(1).strip()
        for match in re.finditer(r"^\|\s*([^|]+?)\s*\|[^\n]*`documented`", text, re.MULTILINE)
    }
    if documented != DOCUMENTED_AGENTS:
        findings.append(
            ParityFinding(
                "documented-agents",
                filename,
                "list exactly Claude Code, Codex, and OpenCode with `documented` status",
            )
        )


def _validate_local_links(
    findings: list[ParityFinding], root: Path, filename: str, text: str
) -> None:
    source = root / filename
    for raw_target in MARKDOWN_LINK.findall(text):
        target = raw_target.strip("<>").split("#", 1)[0]
        if not target or target.startswith(("#", "mailto:")) or "://" in target:
            continue
        resolved = source.parent / target
        if resolved.exists():
            continue
        code = "fixture-reference" if "examples/light-complete" in target else "local-link"
        findings.append(ParityFinding(code, filename, f"fix unresolved local target: {target}"))


def _reject_package_index_claims_when_disabled(findings: list[ParityFinding], root: Path) -> None:
    release_policy = root / "docs" / "releasing.md"
    if not release_policy.is_file():
        return
    policy = release_policy.read_text(encoding="utf-8").casefold()
    if "does not publish to pypi" not in policy or "not enabled" not in policy:
        return
    for filename in ONBOARDING_DOCUMENTS:
        path = root / filename
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in PACKAGE_INDEX_CLAIMS:
            match = pattern.search(text)
            if match:
                message = (
                    f"remove package-index claim {match.group(0)!r} while publication is disabled"
                )
                findings.append(
                    ParityFinding(
                        "package-index-install",
                        filename,
                        message,
                    )
                )
                break


def _require_markers(
    findings: list[ParityFinding],
    filename: str,
    text: str,
    code: str,
    markers: Sequence[str],
) -> None:
    normalized = " ".join(text.casefold().split())
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
