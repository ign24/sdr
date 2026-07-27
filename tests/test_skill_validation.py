import shutil
import subprocess
import sys
from pathlib import Path

from sdr.skill_validation import validate_skill_tree

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _copy_skills(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(PROJECT_ROOT / "skills", root / "skills")
    return root


def test_canonical_skill_tree_passes_contract() -> None:
    assert validate_skill_tree(PROJECT_ROOT) == []


def test_validator_requires_exactly_seven_canonical_skills(tmp_path: Path) -> None:
    root = _copy_skills(tmp_path)
    shutil.rmtree(root / "skills" / "sdr-probe")
    extra = root / "skills" / "sdr-extra"
    extra.mkdir()
    (extra / "SKILL.md").write_text(
        "---\nname: sdr-extra\ndescription: Extra workflow.\n---\n",
        encoding="utf-8",
    )

    findings = validate_skill_tree(root)

    assert {item.code for item in findings} >= {"missing-skill", "unexpected-skill"}


def test_validator_rejects_nonportable_metadata_and_vendor_tool_names(tmp_path: Path) -> None:
    root = _copy_skills(tmp_path)
    path = root / "skills" / "sdr-intake" / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("---\n\n#", "allowed-tools: [Bash, Read]\n---\n\n#", 1)
    text += "\nUse Claude Code and the OpenCode Read tool.\n"
    path.write_text(text, encoding="utf-8")

    findings = validate_skill_tree(root)

    assert {item.code for item in findings} >= {"frontmatter-keys", "vendor-specific-name"}


def test_validator_rejects_private_paths_unknown_commands_and_broken_skill_links(
    tmp_path: Path,
) -> None:
    root = _copy_skills(tmp_path)
    path = root / "skills" / "sdr-status" / "SKILL.md"
    private_path = "/" + "home/person/private.md"
    path.write_text(
        path.read_text(encoding="utf-8")
        + f"\nRead `{private_path}`, run `sdr deploy`, then use `sdr-missing`.\n",
        encoding="utf-8",
    )

    findings = validate_skill_tree(root)

    assert {item.code for item in findings} >= {
        "private-path",
        "unknown-command",
        "broken-skill-reference",
    }


def test_validator_detects_missing_stage_workflow_step(tmp_path: Path) -> None:
    root = _copy_skills(tmp_path)
    path = root / "skills" / "sdr-probe" / "SKILL.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("sdr verify-probe <slug> --json", "probe check"),
        encoding="utf-8",
    )

    findings = validate_skill_tree(root)

    assert any(item.code == "workflow-coverage" and item.skill == "sdr-probe" for item in findings)


def test_validator_rejects_broken_relative_links(tmp_path: Path) -> None:
    root = _copy_skills(tmp_path)
    path = root / "skills" / "sdr-new" / "SKILL.md"
    path.write_text(
        path.read_text(encoding="utf-8") + "\nSee [missing guidance](references/missing.md).\n",
        encoding="utf-8",
    )

    findings = validate_skill_tree(root)

    assert any(item.code == "broken-link" and item.skill == "sdr-new" for item in findings)


def test_module_check_is_machine_usable(tmp_path: Path) -> None:
    root = _copy_skills(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "sdr.skill_validation", str(root)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == "skills: OK\n"
