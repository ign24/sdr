import subprocess
import sys
from pathlib import Path

import pytest

from sdr.public_tree_audit import audit_tree, render_findings


@pytest.mark.parametrize(
    "relative_path",
    [
        "research/example/brief.md",
        "knowledge/example.md",
        "analysis.ipynb",
        ".env",
        ".env.production",
        "src/__pycache__/module.pyc",
        ".pytest_cache/state",
        ".ruff_cache/state",
        "vendor/.git/config",
    ],
)
def test_audit_rejects_prohibited_paths(tmp_path, relative_path):
    target = tmp_path / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("public content", encoding="utf-8")

    findings = audit_tree(tmp_path)

    assert any(finding.code == "prohibited-path" for finding in findings)


def test_root_git_can_be_excluded_without_hiding_nested_git(tmp_path):
    root_git = tmp_path / ".git" / "config"
    nested_git = tmp_path / "artifact" / ".git" / "config"
    root_git.parent.mkdir()
    nested_git.parent.mkdir(parents=True)
    root_git.write_text("private root metadata", encoding="utf-8")
    nested_git.write_text("embedded repository", encoding="utf-8")

    findings = audit_tree(tmp_path, excluded=(Path(".git"),))

    assert [finding.path for finding in findings] == ["artifact/.git"]


def test_sensitive_text_is_reported_without_echoing_values(tmp_path):
    private_path = "/" + "home/example-user/private/source/file.py"
    aws_key = "AKIA" + "IOSFODNN7EXAMPLE"
    github_token = "ghp_" + "abcdefghijklmnopqrstuvwxyzABCDEFGHIJ"
    target = tmp_path / "config.txt"
    target.write_text(
        f"origin={private_path}\naws={aws_key}\ngithub={github_token}\n",
        encoding="utf-8",
    )

    findings = audit_tree(tmp_path)
    output = render_findings(findings)

    assert {finding.code for finding in findings} == {
        "private-absolute-path",
        "secret",
    }
    assert private_path not in output
    assert aws_key not in output
    assert github_token not in output
    assert "config.txt:1" in output


def test_sensitive_filename_is_redacted(tmp_path):
    github_token = "ghp_" + "abcdefghijklmnopqrstuvwxyzABCDEFGHIJ"
    (tmp_path / github_token).write_text(github_token, encoding="utf-8")

    output = render_findings(audit_tree(tmp_path))

    assert github_token not in output
    assert "<redacted>" in output


def test_findings_have_deterministic_order(tmp_path):
    private_path = "/" + "Users/person/private/file"
    aws_key = "AKIA" + "IOSFODNN7EXAMPLE"
    (tmp_path / "z.txt").write_text(f"path={private_path}\n", encoding="utf-8")
    (tmp_path / "a.txt").write_text(f"token={aws_key}\n", encoding="utf-8")

    first = audit_tree(tmp_path)
    second = audit_tree(tmp_path)

    assert first == second
    assert [(item.path, item.line) for item in first] == sorted(
        (item.path, item.line) for item in first
    )


def test_module_cli_audits_arbitrary_artifact_root(tmp_path):
    artifact = tmp_path / "dist"
    artifact.mkdir()
    (artifact / "bundle.env").write_text("safe=true\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "sdr.public_tree_audit", str(artifact)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "prohibited-path" in result.stdout
    assert str(tmp_path) not in result.stdout


def test_safe_tree_passes(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "module.py").write_text("VALUE = 1\n", encoding="utf-8")

    assert audit_tree(tmp_path) == []
