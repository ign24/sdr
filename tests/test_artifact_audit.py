import subprocess
import sys
import tarfile
import zipfile
from io import BytesIO
from pathlib import Path

from sdr.artifact_audit import audit_artifact, render_findings

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _write_wheel(
    path: Path, extra_name: str, content: str = "safe", *, include_py_typed: bool = True
) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("sdr/__init__.py", "__version__ = '1.0.0'\n")
        archive.writestr("sdr/cli.py", "def main(): pass\n")
        if include_py_typed:
            archive.writestr("sdr/py.typed", "")
        archive.writestr("sdr/templates/brief.md", "# Brief\n")
        archive.writestr("example-1.0.dist-info/METADATA", "Name: example\n")
        archive.writestr("example-1.0.dist-info/WHEEL", "Wheel-Version: 1.0\n")
        archive.writestr("example-1.0.dist-info/RECORD", "")
        archive.writestr(extra_name, content)


def test_wheel_allowlist_rejects_unknown_top_level_member(tmp_path: Path) -> None:
    wheel = tmp_path / "example-1.0-py3-none-any.whl"
    _write_wheel(wheel, "private-notes.txt")

    findings = audit_artifact(wheel)

    assert any(
        item.code == "unexpected-member" and item.path == "private-notes.txt" for item in findings
    )


def test_artifact_audit_rejects_traversal_without_extracting_it(tmp_path: Path) -> None:
    wheel = tmp_path / "example-1.0-py3-none-any.whl"
    _write_wheel(wheel, "../escaped.txt")

    findings = audit_artifact(wheel)

    assert any(item.code == "unsafe-member" and item.path == "../escaped.txt" for item in findings)
    assert not (tmp_path / "escaped.txt").exists()


def test_artifact_audit_redacts_sensitive_member_names(tmp_path: Path) -> None:
    wheel = tmp_path / "example-1.0-py3-none-any.whl"
    github_token = "ghp_" + "abcdefghijklmnopqrstuvwxyzABCDEFGHIJ"
    _write_wheel(wheel, github_token)

    output = render_findings(audit_artifact(wheel))

    assert github_token not in output
    assert "<redacted>" in output


def test_sdist_rejects_prohibited_material_and_redacts_private_paths(tmp_path: Path) -> None:
    sdist = tmp_path / "example-1.0.tar.gz"
    private_path = "/" + "home/person/private/source.py"
    with tarfile.open(sdist, "w:gz") as archive:
        content = f"source={private_path}\n".encode()
        info = tarfile.TarInfo("example-1.0/research/private.md")
        info.size = len(content)
        archive.addfile(info, BytesIO(content))

    findings = audit_artifact(sdist)
    output = render_findings(findings)

    assert {item.code for item in findings} >= {"prohibited-path", "private-absolute-path"}
    assert private_path not in output


def test_built_wheel_and_sdist_pass_the_artifact_contract(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(dist), str(PROJECT_ROOT)],
        check=True,
    )

    artifacts = sorted(dist.iterdir())
    assert {path.suffix for path in artifacts} == {".gz", ".whl"}
    assert all(audit_artifact(path) == [] for path in artifacts)


def test_artifact_audit_requires_typed_package_marker(tmp_path: Path) -> None:
    markerless = tmp_path / "markerless-1.0-py3-none-any.whl"
    _write_wheel(markerless, "sdr/extra.py", include_py_typed=False)

    assert any(
        finding.code == "missing-member" and finding.path == "sdr/py.typed"
        for finding in audit_artifact(markerless)
    )


def test_module_cli_audits_all_artifacts_without_sensitive_output(tmp_path: Path) -> None:
    wheel = tmp_path / "example-1.0-py3-none-any.whl"
    private_path = "/" + "Users/person/private/file"
    _write_wheel(wheel, "sdr/private.txt", private_path)

    result = subprocess.run(
        [sys.executable, "-m", "sdr.artifact_audit", str(wheel)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "private-absolute-path" in result.stdout
    assert private_path not in result.stdout
