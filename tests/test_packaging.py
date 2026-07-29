import os
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from pathlib import Path

import sdr

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SKILLS = {
    f"sdr/resources/skills/{path.parent.name}/SKILL.md": path
    for path in sorted((PROJECT_ROOT / "skills").glob("sdr-*/SKILL.md"))
}
CANONICAL_ADAPTERS = {
    f"sdr/resources/integrations/{name}/adapter.yaml": (
        PROJECT_ROOT / "integrations" / name / "adapter.yaml"
    )
    for name in ("claude-code", "codex", "opencode")
}


def test_package_metadata_uses_sdr_version_as_single_source(tmp_path):
    config = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "version" not in config["project"]
    assert config["project"]["dynamic"] == ["version"]
    assert config["tool"]["hatch"]["version"]["path"] == "src/sdr/__init__.py"
    assert config["project"]["readme"] == "README.md"
    assert config["project"]["license"] == "Apache-2.0"
    assert config["project"]["authors"] == [{"name": "Ignacio Zúñiga Navarro"}]
    assert "urls" not in config["project"]

    dist = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist), str(PROJECT_ROOT)],
        check=True,
    )
    wheel = next(dist.glob("spec_driven_research-*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        assert "sdr/py.typed" in archive.namelist()
        metadata_name = next(
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        )
        metadata = archive.read(metadata_name).decode("utf-8")

    assert f"Version: {sdr.__version__}\n" in metadata
    assert "License-Expression: Apache-2.0\n" in metadata


def test_sdist_contains_public_package_files_and_excludes_active_changes(tmp_path):
    dist = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--sdist", "--outdir", str(dist), str(PROJECT_ROOT)],
        check=True,
    )
    sdist = next(dist.glob("spec_driven_research-*.tar.gz"))
    with tarfile.open(sdist, "r:gz") as archive:
        names = archive.getnames()

    assert any(name.endswith("/src/sdr/py.typed") for name in names)
    assert not any("/openspec/changes/" in name for name in names)


def test_wheel_contains_only_canonical_integration_resources_byte_for_byte(tmp_path):
    dist = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist), str(PROJECT_ROOT)],
        check=True,
    )
    wheel = next(dist.glob("spec_driven_research-*.whl"))
    expected = CANONICAL_SKILLS | CANONICAL_ADAPTERS

    assert len(CANONICAL_SKILLS) == 7
    assert len(CANONICAL_ADAPTERS) == 3
    with zipfile.ZipFile(wheel) as archive:
        resource_names = {name for name in archive.namelist() if name.startswith("sdr/resources/")}
        assert resource_names == set(expected)
        for packaged_name, canonical_path in expected.items():
            assert archive.read(packaged_name) == canonical_path.read_bytes()


def test_changelog_records_current_version_without_defining_package_version():
    changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert "## [0.1.0]" in changelog
    assert "src/sdr/__init__.py" in changelog
    assert "source of truth" in changelog


def test_wheel_install_sdr_new_creates_brief(tmp_path):
    dist = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist), str(PROJECT_ROOT)],
        check=True,
    )
    wheel = next(dist.glob("spec_driven_research-*.whl"))

    venv = tmp_path / "venv"
    subprocess.run(["uv", "venv", str(venv)], check=True)
    subprocess.run(
        ["uv", "pip", "install", "--python", str(venv / "bin" / "python"), str(wheel)],
        check=True,
    )

    subprocess.run(
        [
            str(venv / "bin" / "python"),
            "-c",
            "from importlib.resources import files; import sdr; "
            "assert files('sdr').joinpath('templates/brief.md').is_file()",
        ],
        cwd=tmp_path,
        check=True,
    )

    research_root = tmp_path / "research"
    env = {**os.environ, "SDR_ROOT": str(research_root)}
    subprocess.run(
        [
            str(venv / "bin" / "sdr"),
            "new",
            "wheel-smoke-test",
            "--title",
            "Wheel smoke test",
            "--question",
            "¿El wheel contiene las plantillas?",
            "--no-commit",
        ],
        cwd=tmp_path,
        env=env,
        check=True,
    )

    brief = research_root / "wheel-smoke-test" / "brief.md"
    assert brief.is_file()
    assert "## Pregunta" in brief.read_text(encoding="utf-8")
