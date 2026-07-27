"""Validate and install the public SDR Agent Skills integrations."""

from __future__ import annotations

import argparse
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml

from sdr.skill_validation import ACTIVE_COMMANDS, SKILLS

ADAPTERS = (
    "claude-code",
    "opencode",
    "codex",
    "openclaw",
    "hermes",
)
VALID_STATUSES = frozenset({"documented", "verified", "experimental"})

_PRIVATE_PATH = re.compile(r"(?<![\w.])/(?:home|Users|root)/[^\s`)]+")
_COMMAND = re.compile(r"\bsdr[ \t]+([a-z][a-z-]*)\b")
_FIXED_MODEL = re.compile(
    r"\b(?:gpt-[0-9][\w.-]*|claude-(?:opus|sonnet|haiku)[\w.-]*|gemini-[0-9][\w.-]*)\b",
    re.IGNORECASE,
)
_DIVERGENT_LIFECYCLE = re.compile(
    r"\b(?:intake|explore|probe|transfer|reuse)\s*(?:->|→)", re.IGNORECASE
)
_FORBIDDEN_FILES = frozenset(
    {
        ".hermes.md",
        "openclaw.plugin.json",
        "package.json",
        "requirements.txt",
        "pyproject.toml",
    }
)
_REQUIRED_METADATA = frozenset(
    {
        "schema_version",
        "agent",
        "status",
        "adapter",
        "format",
        "canonical_skills",
        "skills",
        "discovery",
        "installation",
        "runtime_dependencies",
        "official_docs",
    }
)


@dataclass(frozen=True, order=True)
class IntegrationFinding:
    """One stable integration contract violation."""

    agent: str
    code: str
    detail: str


def install_canonical_skills(project_root: Path, destination: Path) -> list[Path]:
    """Link every canonical skill into an explicit host discovery directory."""
    root = Path(project_root).resolve()
    skills_root = root / "skills"
    destination = Path(destination)
    conflicts = [
        destination / name
        for name in SKILLS
        if (destination / name).exists() or (destination / name).is_symlink()
    ]
    if conflicts:
        names = ", ".join(path.name for path in conflicts)
        raise FileExistsError(f"refusing to overwrite existing skills: {names}")

    destination.mkdir(parents=True, exist_ok=True)
    installed: list[Path] = []
    for name in SKILLS:
        source = skills_root / name
        if not (source / "SKILL.md").is_file():
            raise FileNotFoundError(f"canonical skill is missing: {name}")
        target = destination / name
        target.symlink_to(source, target_is_directory=True)
        installed.append(target)
    return installed


def validate_integrations(project_root: Path) -> list[IntegrationFinding]:
    """Validate all public integration adapters without invoking agent binaries."""
    root = Path(project_root)
    integrations = root / "integrations"
    findings: list[IntegrationFinding] = []
    present = (
        {path.name for path in integrations.iterdir() if path.is_dir()}
        if integrations.is_dir()
        else set()
    )

    for agent in sorted(set(ADAPTERS) - present):
        findings.append(
            IntegrationFinding(agent, "missing-adapter", "adapter directory is missing")
        )
    for agent in sorted(present - set(ADAPTERS)):
        findings.append(
            IntegrationFinding(agent, "unexpected-adapter", "unknown adapter directory")
        )

    for agent in ADAPTERS:
        adapter_dir = integrations / agent
        readme = adapter_dir / "README.md"
        metadata_path = adapter_dir / "adapter.yaml"
        if not readme.is_file():
            findings.append(IntegrationFinding(agent, "missing-readme", "README.md is missing"))
        if not metadata_path.is_file():
            findings.append(
                IntegrationFinding(agent, "missing-metadata", "adapter.yaml is missing")
            )
            continue

        try:
            metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            metadata = None
        if not isinstance(metadata, dict):
            findings.append(
                IntegrationFinding(agent, "invalid-metadata", "adapter.yaml must be a mapping")
            )
            continue

        missing_keys = sorted(_REQUIRED_METADATA - set(metadata))
        if missing_keys:
            findings.append(
                IntegrationFinding(
                    agent, "metadata-keys", "missing keys: " + ", ".join(missing_keys)
                )
            )
        if metadata.get("agent") != agent:
            findings.append(
                IntegrationFinding(agent, "agent-name", "agent must match directory name")
            )
        if metadata.get("status") not in VALID_STATUSES:
            findings.append(
                IntegrationFinding(agent, "invalid-status", "unsupported integration status")
            )
        if metadata.get("canonical_skills") != "../../skills" or metadata.get("skills") != list(
            SKILLS
        ):
            findings.append(
                IntegrationFinding(agent, "canonical-skills", "must reference all canonical skills")
            )
        if metadata.get("runtime_dependencies") != []:
            findings.append(
                IntegrationFinding(
                    agent, "runtime-dependency", "runtime dependencies are forbidden"
                )
            )
        official_docs = metadata.get("official_docs")
        if not isinstance(official_docs, str) or not official_docs.startswith("https://"):
            findings.append(
                IntegrationFinding(agent, "official-docs", "an HTTPS official source is required")
            )

        files = [path for path in adapter_dir.rglob("*") if path.is_file()]
        for path in files:
            if path.name in _FORBIDDEN_FILES or "hooks" in path.parts or path.name == "SKILL.md":
                findings.append(
                    IntegrationFinding(
                        agent, "forbidden-artifact", f"forbidden adapter file: {path.name}"
                    )
                )
            text = path.read_text(encoding="utf-8")
            findings.extend(_validate_text(agent, text))

    return sorted(set(findings))


def _validate_text(agent: str, text: str) -> list[IntegrationFinding]:
    findings: list[IntegrationFinding] = []
    if re.search(r"\bSpecLab\b", text, re.IGNORECASE):
        findings.append(
            IntegrationFinding(agent, "legacy-concept", "legacy adapter concept is forbidden")
        )
    if _PRIVATE_PATH.search(text):
        findings.append(
            IntegrationFinding(agent, "private-path", "private absolute path is forbidden")
        )
    if _FIXED_MODEL.search(text):
        findings.append(IntegrationFinding(agent, "fixed-model", "fixed model names are forbidden"))
    if _DIVERGENT_LIFECYCLE.search(text):
        findings.append(
            IntegrationFinding(agent, "divergent-lifecycle", "lifecycle copies are forbidden")
        )
    for command in sorted(set(_COMMAND.findall(text)) - ACTIVE_COMMANDS):
        findings.append(
            IntegrationFinding(agent, "unknown-command", f"sdr {command} is not active")
        )
    return findings


def render_findings(findings: Sequence[IntegrationFinding]) -> str:
    """Render deterministic findings without environment-specific paths."""
    return "\n".join(f"{item.agent}: {item.code}: {item.detail}" for item in findings)


def main(argv: Sequence[str] | None = None) -> int:
    """Validate adapters or install canonical skills into an explicit scope."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("project_root", type=Path)
    install_parser = subparsers.add_parser("install")
    install_parser.add_argument("project_root", type=Path)
    install_parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args(argv)

    if args.command == "validate":
        findings = validate_integrations(args.project_root)
        if findings:
            print(render_findings(findings))
            return 1
        print("integrations: OK")
        return 0

    try:
        installed = install_canonical_skills(args.project_root, args.destination)
    except (FileExistsError, FileNotFoundError) as error:
        parser.error(str(error))
    print(f"installed {len(installed)} canonical skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
