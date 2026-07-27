"""Deterministic checks for content intended for public distribution."""

from __future__ import annotations

import argparse
import os
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

PROHIBITED_NAMES = {
    ".cache",
    ".git",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    "__pycache__",
    "knowledge",
    "research",
}
PROHIBITED_SUFFIXES = {".ipynb"}
PRIVATE_PATH_PATTERNS = (
    re.compile(r"(?<![\w])/(?:home|root|Users)/[^\s\"'<>]+"),
    re.compile(r"(?i)(?<![\w])[a-z]:\\Users\\[^\s\"'<>]+"),
)
SECRET_PATTERNS = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?:gh[oprsu]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{82,255})"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"sk_live_[A-Za-z0-9]{20,}"),
    re.compile(r"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----"),
)


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    line: int | None = None


def audit_tree(root: Path, excluded: Iterable[Path] = ()) -> list[Finding]:
    """Audit a directory without including matched sensitive values in findings."""
    root = root.resolve()
    exclusions = {PurePosixPath(_relative_posix(path)) for path in excluded}
    findings: list[Finding] = []

    for directory, names, files in os.walk(root):
        relative_directory = Path(directory).relative_to(root)
        names[:] = sorted(
            name for name in names if not _is_excluded(relative_directory / name, exclusions)
        )
        files.sort()

        for name in names:
            relative_path = relative_directory / name
            if _is_prohibited(relative_path):
                findings.append(Finding("prohibited-path", _relative_posix(relative_path)))
        names[:] = [name for name in names if not _is_prohibited(relative_directory / name)]

        for name in files:
            relative_path = relative_directory / name
            if _is_excluded(relative_path, exclusions):
                continue
            display_path = _relative_posix(relative_path)
            if _is_prohibited(relative_path):
                findings.append(Finding("prohibited-path", display_path))
            findings.extend(_audit_text(Path(directory) / name, display_path))

    return sorted(findings, key=lambda item: (item.path, item.line or 0, item.code))


def render_findings(findings: Sequence[Finding]) -> str:
    """Render only locations and categories, never matched content."""
    lines = []
    for finding in findings:
        location = redact_sensitive(finding.path)
        if finding.line is not None:
            location = f"{location}:{finding.line}"
        lines.append(f"{location} [{finding.code}] sensitive content redacted")
    return "\n".join(lines)


def redact_sensitive(value: str) -> str:
    """Redact secret-like and private-path values before writing logs."""
    redacted = value
    for pattern in (*PRIVATE_PATH_PATTERNS, *SECRET_PATTERNS):
        redacted = pattern.sub("<redacted>", redacted)
    return "".join(character if character.isprintable() else "?" for character in redacted)


def audit_bytes(content: bytes, display_path: str) -> list[Finding]:
    """Audit in-memory file content without including matched values in findings."""
    if b"\0" in content:
        return []
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return []

    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if any(pattern.search(line) for pattern in PRIVATE_PATH_PATTERNS):
            findings.append(Finding("private-absolute-path", display_path, line_number))
        if any(pattern.search(line) for pattern in SECRET_PATTERNS):
            findings.append(Finding("secret", display_path, line_number))
    return findings


def _audit_text(path: Path, display_path: str) -> list[Finding]:
    return audit_bytes(path.read_bytes(), display_path)


def _is_prohibited(path: Path) -> bool:
    parts = path.parts
    return (
        any(
            part in PROHIBITED_NAMES or part == ".env" or part.startswith(".env.") for part in parts
        )
        or path.suffix.lower() in PROHIBITED_SUFFIXES
        or path.name.endswith(".env")
    )


def _is_excluded(path: Path, exclusions: set[PurePosixPath]) -> bool:
    relative = PurePosixPath(_relative_posix(path))
    return any(relative == excluded or excluded in relative.parents for excluded in exclusions)


def _relative_posix(path: Path) -> str:
    value = path.as_posix().removeprefix("./")
    return value or "."


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        type=Path,
        help="Relative path to exclude; repeat for multiple technical exclusions",
    )
    args = parser.parse_args(argv)
    findings = audit_tree(args.root, excluded=args.exclude)
    if findings:
        print(render_findings(findings))
        return 1
    print("audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
