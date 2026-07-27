import re
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_ACTIONS = {
    "actions/checkout": "11bd71901bbe5b1630ceea73d27597364c9af683",
    "actions/setup-python": "a26af69be951a213d495a4c3e4e4022e16d87065",
    "actions/setup-go": "44694675825211faa026b3c33043df3e48a5fa00",
    "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
    "astral-sh/setup-uv": "b75a909f75acd358c2196fb9a5f1299a9a8868a4",
}


def _workflow(name: str) -> tuple[str, dict[str, object]]:
    text = (WORKFLOWS / name).read_text(encoding="utf-8")
    return text, yaml.safe_load(text)


def test_ci_uses_read_only_permissions_linux_python_matrix_and_required_gates() -> None:
    text, workflow = _workflow("ci.yml")

    assert workflow["permissions"] == {"contents": "read"}
    assert "ubuntu-latest" in text
    assert 'python-version: ["3.12", "3.13"]' in text
    assert "pull_request:" in text
    assert "push:" in text and "main" in text
    for command in (
        "ruff check .",
        "ruff format --check .",
        "pytest",
        "sdr.readme_parity",
        "sdr.skill_validation",
        "sdr.integration_validation",
        "openspec validate --specs --strict --no-interactive",
        "twine check dist/*",
        "sdr.artifact_audit dist/*",
    ):
        assert command in text


def test_security_workflow_scans_dependencies_tree_history_staged_and_artifacts() -> None:
    text, workflow = _workflow("security.yml")

    assert workflow["permissions"] == {"contents": "read"}
    assert "pip-audit" in text
    assert "gitleaks/v8@v8.28.0" in text
    assert "gitleaks dir --redact --no-banner ." in text
    assert "gitleaks git --redact --no-banner" in text
    assert "git diff --cached --binary" in text
    assert "gitleaks --redact --no-banner stdin" in text
    assert "--max-archive-depth=1" in text
    assert "sdr.public_tree_audit" in text
    assert "sdr.artifact_audit" in text
    assert "secrets." not in text


def test_gitleaks_excludes_only_local_generated_directories() -> None:
    config = tomllib.loads((ROOT / ".gitleaks.toml").read_text(encoding="utf-8"))

    assert config["extend"] == {"useDefault": True}
    assert len(config["allowlists"]) == 1
    allowlist = config["allowlists"][0]
    assert set(allowlist) == {"description", "paths"}
    assert all(name in "\n".join(allowlist["paths"]) for name in (".git", ".venv", "__pycache__"))
    assert "dist" not in "\n".join(allowlist["paths"])


def test_external_actions_are_pinned_to_documented_full_shas() -> None:
    found: set[str] = set()
    for path in sorted(WORKFLOWS.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        for action, ref in re.findall(r"uses:\s+([^@\s]+)@([^\s#]+)", text):
            assert FULL_SHA.fullmatch(ref), f"{path.name}: {action}@{ref} is not a full SHA"
            assert EXPECTED_ACTIONS[action] == ref
            found.add(action)
    assert found == set(EXPECTED_ACTIONS)


def test_workflows_do_not_publish_or_request_write_permissions() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in WORKFLOWS.glob("*.yml"))

    assert "id-token: write" not in combined
    assert "contents: write" not in combined
    assert "pypa/gh-action-pypi-publish" not in combined
    assert "twine upload" not in combined


def test_dependabot_covers_actions_and_python_lock_updates() -> None:
    config = yaml.safe_load((ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8"))
    updates = config["updates"]

    assert {(item["package-ecosystem"], item["directory"]) for item in updates} == {
        ("github-actions", "/"),
        ("pip", "/"),
    }


def test_linux_only_evidence_and_security_release_policies_are_explicit() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    classifiers = config["project"]["classifiers"]
    docs = (ROOT / "docs" / "validation.md").read_text(encoding="utf-8")
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    releasing = (ROOT / "docs" / "releasing.md").read_text(encoding="utf-8")

    assert "Operating System :: POSIX :: Linux" in classifiers
    assert "Operating System :: OS Independent" not in classifiers
    assert "Python 3.12" in docs and "Python 3.13" in docs and "Ubuntu" in docs
    assert "Windows" in docs and "macOS" in docs and "not" in docs
    for field in ("owner", "justification", "expires", "compensating controls"):
        assert field in security.lower()
    assert "no active exceptions" in security.lower()
    assert "Trusted Publishing" in releasing
    assert "OIDC" in releasing
    assert "not enabled" in releasing
