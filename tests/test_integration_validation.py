import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from sdr.integration_validation import (
    ADAPTERS,
    install_canonical_skills,
    validate_integrations,
)
from sdr.skill_validation import SKILLS

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _metadata(agent: str) -> dict[str, object]:
    path = PROJECT_ROOT / "integrations" / agent / "adapter.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_five_documented_adapters_pass_the_contract() -> None:
    assert ADAPTERS == (
        "claude-code",
        "opencode",
        "codex",
        "openclaw",
        "hermes",
    )
    assert validate_integrations(PROJECT_ROOT) == []
    assert {
        path.name for path in (PROJECT_ROOT / "integrations").iterdir() if path.is_dir()
    } == set(ADAPTERS)

    for agent in ADAPTERS:
        adapter_dir = PROJECT_ROOT / "integrations" / agent
        assert (adapter_dir / "README.md").is_file()
        assert (adapter_dir / "adapter.yaml").is_file()
        assert _metadata(agent)["status"] == "documented"


def test_adapters_reference_the_canonical_skills_without_runtime_dependencies() -> None:
    for agent in ADAPTERS:
        metadata = _metadata(agent)
        assert metadata["canonical_skills"] == "../../skills"
        assert metadata["skills"] == list(SKILLS)
        assert metadata["runtime_dependencies"] == []

        adapter_dir = PROJECT_ROOT / "integrations" / agent
        assert not any(path.name == "SKILL.md" for path in adapter_dir.rglob("SKILL.md"))


def test_agent_specific_discovery_and_safety_contracts() -> None:
    assert _metadata("claude-code")["discovery"]["project"] == ".claude/skills"

    opencode = _metadata("opencode")
    assert opencode["adapter"] == "sdr"
    assert opencode["discovery"]["project"] == ".opencode/skills"

    codex = _metadata("codex")
    assert codex["discovery"]["project"] == ".agents/skills"
    assert codex["installation"] == "canonical-symlink"

    openclaw = _metadata("openclaw")
    assert openclaw["format"] == "agent-skills"
    assert openclaw["required_bins"] == ["sdr"]
    assert openclaw["runtime_plugin"] is False

    hermes = _metadata("hermes")
    assert hermes["product"] == "NousResearch/hermes-agent"
    assert hermes["format"] == "agent-skills"
    assert hermes["supports_external_dirs"] is True
    assert hermes["runtime_plugin"] is False


def test_openclaw_readme_documents_all_public_skill_roots() -> None:
    readme = (PROJECT_ROOT / "integrations" / "openclaw" / "README.md").read_text(encoding="utf-8")

    for root in (
        "<workspace>/skills",
        "<workspace>/.agents/skills",
        "~/.agents/skills",
        "~/.openclaw/skills",
    ):
        assert f"`{root}`" in readme


def test_install_links_all_canonical_skills_without_overwriting(tmp_path: Path) -> None:
    destination = tmp_path / ".agents" / "skills"

    installed = install_canonical_skills(PROJECT_ROOT, destination)

    assert [path.name for path in installed] == list(SKILLS)
    for name in SKILLS:
        link = destination / name
        assert link.is_symlink()
        assert link.resolve() == (PROJECT_ROOT / "skills" / name).resolve()

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        install_canonical_skills(PROJECT_ROOT, destination)


def test_install_refuses_to_replace_a_broken_existing_symlink(tmp_path: Path) -> None:
    destination = tmp_path / ".agents" / "skills"
    destination.mkdir(parents=True)
    (destination / "sdr-new").symlink_to(tmp_path / "missing-skill")

    with pytest.raises(FileExistsError, match="refusing to overwrite existing skills: sdr-new"):
        install_canonical_skills(PROJECT_ROOT, destination)


def test_validator_rejects_divergent_or_unsafe_adapter_content(tmp_path: Path) -> None:
    integrations = tmp_path / "integrations"
    source = PROJECT_ROOT / "integrations"
    shutil.copytree(source, integrations)
    readme = integrations / "opencode" / "README.md"
    private_path = "/" + "home/example/private"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        + f"\nUse SpecLab from {private_path} with model gpt-5.\n"
        + "Run sdr deploy and follow intake -> transfer.\n",
        encoding="utf-8",
    )

    findings = validate_integrations(tmp_path)

    assert {finding.code for finding in findings} >= {
        "fixed-model",
        "legacy-concept",
        "private-path",
        "unknown-command",
        "divergent-lifecycle",
    }


def test_module_cli_validates_and_installs_to_an_explicit_scope(tmp_path: Path) -> None:
    validation = subprocess.run(
        [sys.executable, "-m", "sdr.integration_validation", "validate", str(PROJECT_ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )
    destination = tmp_path / ".claude" / "skills"
    installation = subprocess.run(
        [
            sys.executable,
            "-m",
            "sdr.integration_validation",
            "install",
            str(PROJECT_ROOT),
            "--destination",
            str(destination),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert validation.returncode == 0
    assert validation.stdout == "integrations: OK\n"
    assert installation.returncode == 0
    assert installation.stdout == "installed 7 canonical skills\n"
    assert (destination / "sdr-new").is_symlink()
