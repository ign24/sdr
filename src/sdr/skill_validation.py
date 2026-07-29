"""Deterministic contract checks for the canonical SDR Agent Skills."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

SKILLS = (
    "sdr-new",
    "sdr-intake",
    "sdr-explore",
    "sdr-probe",
    "sdr-transfer",
    "sdr-reuse",
    "sdr-status",
)

ACTIVE_COMMANDS = frozenset(
    {
        "advance",
        "approve",
        "archive",
        "check",
        "drop",
        "index",
        "integrations",
        "new",
        "reopen",
        "resolve-claim",
        "snapshot",
        "status",
        "verify-claims",
        "verify-probe",
    }
)

_WORKFLOW_REQUIREMENTS = {
    "sdr-new": (
        "sdr new <slug>",
        "sdr status <slug> --json",
        "stage: intake",
        "Do not edit `sdr.yaml` manually",
        "`sdr-intake`",
    ),
    "sdr-intake": (
        "stage: intake",
        "research/<slug>/brief.md",
        "Modify only `research/<slug>/brief.md`",
        "sdr check <slug> --json",
        "sdr advance <slug>",
    ),
    "sdr-explore": (
        "stage: explore",
        "research/<slug>/brief.md",
        "research/<slug>/notes/",
        "Modify only files under `research/<slug>/notes/`",
        "sdr snapshot <slug>",
        "sdr verify-claims <slug> --json",
        "sdr check <slug> --json",
        "sdr advance <slug>",
    ),
    "sdr-probe": (
        "stage: probe",
        "research/<slug>/brief.md",
        "research/<slug>/notes/",
        "research/<slug>/probe/results.md",
        "Modify only files under `research/<slug>/probe/`",
        "sdr verify-probe <slug> --json",
        "sdr check <slug> --json",
        "sdr advance <slug>",
    ),
    "sdr-transfer": (
        "stage: transfer",
        "research/<slug>/brief.md",
        "research/<slug>/notes/",
        "research/<slug>/decision-memo.md",
        "Modify only `research/<slug>/decision-memo.md`",
        "sdr check <slug> --json",
        "sdr approve <slug> --by",
        "sdr advance <slug>",
    ),
    "sdr-reuse": (
        "stage: reuse",
        "research/<slug>/decision-memo.md",
        "research/<slug>/assets/",
        "Modify only files under `research/<slug>/assets/`",
        "sdr check <slug> --json",
        "sdr advance <slug>",
        "sdr archive <slug>",
    ),
    "sdr-status": (
        "must not create or modify stage artifacts",
        "sdr status <slug> --json",
        "sdr status --json",
        "sdr check <slug> --json",
        "sdr index",
        "sdr archive <slug>",
    ),
}

_PRIVATE_PATH = re.compile(r"(?<![\w.])/(?:home|Users)/[^\s`]+")
_VENDOR_NAME = re.compile(
    r"\b(?:Claude(?: Code)?|OpenCode|AskUserQuestion|ToolSearch)\b|"
    r"`(?:Bash|Read|Write|Edit|Glob|Grep)`"
)
_COMMAND = re.compile(r"\bsdr\s+([a-z][a-z-]*)\b")
_SKILL_REFERENCE = re.compile(r"\bsdr-[a-z][a-z-]*\b")
_MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


@dataclass(frozen=True, order=True)
class SkillFinding:
    """One stable, machine-readable skill contract violation."""

    skill: str
    code: str
    detail: str


def _parse_skill(path: Path) -> tuple[dict[str, object], str] | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    marker = text.find("\n---\n", 4)
    if marker < 0:
        return None
    metadata = yaml.safe_load(text[4:marker])
    if not isinstance(metadata, dict):
        return None
    return metadata, text[marker + 5 :]


def validate_skill_tree(project_root: Path) -> list[SkillFinding]:
    """Validate canonical skills below ``project_root/skills`` deterministically."""
    root = Path(project_root)
    skills_dir = root / "skills"
    findings: list[SkillFinding] = []
    present = {path.name for path in skills_dir.glob("sdr-*") if path.is_dir()}

    for name in sorted(set(SKILLS) - present):
        findings.append(SkillFinding(name, "missing-skill", "canonical skill directory is missing"))
    for name in sorted(present - set(SKILLS)):
        findings.append(SkillFinding(name, "unexpected-skill", "unexpected sdr-* skill directory"))

    for name in SKILLS:
        path = skills_dir / name / "SKILL.md"
        if not path.is_file():
            if name in present:
                findings.append(SkillFinding(name, "missing-skill-file", "SKILL.md is missing"))
            continue
        parsed = _parse_skill(path)
        if parsed is None:
            findings.append(
                SkillFinding(name, "invalid-frontmatter", "YAML frontmatter is invalid")
            )
            continue
        metadata, body = parsed
        if set(metadata) != {"name", "description"}:
            findings.append(
                SkillFinding(
                    name, "frontmatter-keys", "frontmatter must contain only name and description"
                )
            )
        if metadata.get("name") != name:
            findings.append(SkillFinding(name, "skill-name", "name must match its directory"))
        description = metadata.get("description")
        if not isinstance(description, str) or not description.strip():
            findings.append(
                SkillFinding(name, "skill-description", "description must be non-empty text")
            )

        text = path.read_text(encoding="utf-8")
        if _PRIVATE_PATH.search(text):
            findings.append(
                SkillFinding(name, "private-path", "private absolute path is forbidden")
            )
        if _VENDOR_NAME.search(text):
            findings.append(
                SkillFinding(
                    name, "vendor-specific-name", "vendor or tool-specific name is forbidden"
                )
            )
        for command in sorted(set(_COMMAND.findall(body)) - ACTIVE_COMMANDS):
            findings.append(
                SkillFinding(name, "unknown-command", f"sdr {command} is not an active command")
            )
        for reference in sorted(set(_SKILL_REFERENCE.findall(body)) - set(SKILLS)):
            findings.append(
                SkillFinding(name, "broken-skill-reference", f"{reference} does not exist")
            )
        for target in _MARKDOWN_LINK.findall(body):
            clean_target = target.split("#", 1)[0].split("?", 1)[0]
            if not clean_target or "://" in clean_target or clean_target.startswith("mailto:"):
                continue
            if (
                Path(clean_target).is_absolute()
                or not (path.parent / clean_target).resolve().exists()
            ):
                findings.append(
                    SkillFinding(name, "broken-link", f"linked path does not exist: {target}")
                )
        normalized_body = " ".join(body.split())
        missing = [
            fragment
            for fragment in _WORKFLOW_REQUIREMENTS[name]
            if " ".join(fragment.split()) not in normalized_body
        ]
        if missing:
            findings.append(
                SkillFinding(
                    name,
                    "workflow-coverage",
                    "missing required workflow text: " + ", ".join(missing),
                )
            )

    return sorted(findings)


def render_findings(findings: list[SkillFinding]) -> str:
    """Render findings without environment-dependent paths."""
    return "\n".join(f"{item.skill}: {item.code}: {item.detail}" for item in findings)


def main(argv: list[str] | None = None) -> int:
    """Run the reusable skill consistency check."""
    args = sys.argv[1:] if argv is None else argv
    root = Path(args[0]) if args else Path.cwd()
    findings = validate_skill_tree(root)
    if findings:
        print(render_findings(findings))
        return 1
    print("skills: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
