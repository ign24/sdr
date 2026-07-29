import shutil
import subprocess
import sys
from pathlib import Path

from sdr.readme_parity import validate_readme_parity

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _copy_readmes(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    for filename in ("README.md", "README.es.md"):
        shutil.copy2(PROJECT_ROOT / filename, root / filename)
    return root


def test_english_and_spanish_readmes_pass_semantic_parity_contract() -> None:
    assert validate_readme_parity(PROJECT_ROOT) == []


def test_validator_reports_missing_contract_with_actionable_message(tmp_path: Path) -> None:
    root = _copy_readmes(tmp_path)
    spanish = root / "README.es.md"
    spanish.write_text(
        spanish.read_text(encoding="utf-8").replace("`sdr verify-probe`", "`probe`"),
        encoding="utf-8",
    )

    findings = validate_readme_parity(root)

    finding = next(item for item in findings if item.code == "critical-commands")
    assert finding.path == "README.es.md"
    assert "sdr verify-probe" in finding.message


def test_validator_requires_package_resource_integration_contract(tmp_path: Path) -> None:
    root = _copy_readmes(tmp_path)
    english = root / "README.md"
    english.write_text(
        english.read_text(encoding="utf-8").replace(
            "sdr integrations install --destination", "python -m installer"
        ),
        encoding="utf-8",
    )

    findings = validate_readme_parity(root)

    finding = next(item for item in findings if item.code == "integration-installation")
    assert finding.path == "README.md"
    assert "sdr integrations install --destination" in finding.message


def test_validator_requires_prominent_reciprocal_language_links(tmp_path: Path) -> None:
    root = _copy_readmes(tmp_path)
    english = root / "README.md"
    english.write_text(
        english.read_text(encoding="utf-8").replace("[Español](README.es.md)", "Español"),
        encoding="utf-8",
    )

    findings = validate_readme_parity(root)

    assert any(
        item.code == "language-link" and item.path == "README.md" and "README.es.md" in item.message
        for item in findings
    )


def test_module_cli_is_deterministic_and_machine_usable() -> None:
    first = subprocess.run(
        [sys.executable, "-m", "sdr.readme_parity", str(PROJECT_ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )
    second = subprocess.run(
        [sys.executable, "-m", "sdr.readme_parity", str(PROJECT_ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert first.returncode == 0
    assert first.stdout == "README parity: OK\n"
    assert second.stdout == first.stdout
