import subprocess

import pytest
from click.testing import CliRunner

from sdr.cli import main


@pytest.fixture
def run(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    monkeypatch.setenv("SDR_ROOT", str(tmp_path / "research"))
    monkeypatch.setenv("SDR_KNOWLEDGE", str(tmp_path / "knowledge"))
    runner = CliRunner()

    def _run(*args):
        return runner.invoke(main, list(args), catch_exceptions=False)

    _run.base = tmp_path
    return _run


def _log(repo):
    out = subprocess.run(
        ["git", "log", "--format=%s"], cwd=repo, capture_output=True, text=True, check=False
    )
    return out.stdout.strip().splitlines() if out.returncode == 0 else []


def _new(run, slug="eval-foo"):
    return run("new", slug, "--title", "Eval Foo", "--question", "¿Q?")


def test_new_commits_creation(run):
    _new(run)
    assert _log(run.base)[0] == "research(eval-foo): new"


def test_new_no_commit_flag(run):
    result = run("new", "eval-foo", "--title", "t", "--question", "q", "--no-commit")
    assert result.exit_code == 0
    assert _log(run.base) == []
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=run.base,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert status == "?? research/\n"


def test_advance_commits_stage_transition(run):
    _new(run)
    result = run("advance", "eval-foo", "--offline")
    assert result.exit_code == 0
    assert _log(run.base)[0] == "research(eval-foo): intake -> explore"


def test_advance_does_not_commit_other_dirty_research_files(run):
    _new(run)
    brief = run.base / "research" / "eval-foo" / "brief.md"
    brief.write_text(brief.read_text(encoding="utf-8") + "\ncambio ajeno\n", encoding="utf-8")

    result = run("advance", "eval-foo", "--offline")

    assert result.exit_code == 0
    committed = subprocess.run(
        ["git", "show", "--name-only", "--format="],
        cwd=run.base,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "research/eval-foo/sdr.yaml" in committed
    assert "research/eval-foo/brief.md" not in committed
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=run.base,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert " M research/eval-foo/brief.md" in status


def test_drop_commits_transition(run):
    _new(run)
    run("drop", "eval-foo", "--reason", "no aplica")
    assert _log(run.base)[0] == "research(eval-foo): drop"


def test_reopen_command_goes_back_with_reason(run):
    _new(run)
    run("advance", "eval-foo", "--offline")
    result = run("reopen", "eval-foo", "--to", "intake", "--reason", "criterios mal definidos")
    assert result.exit_code == 0
    assert _log(run.base)[0] == "research(eval-foo): reopen explore -> intake"
    status = run("status", "eval-foo")
    assert "intake" in status.output


def test_reopen_forward_fails(run):
    _new(run)
    result = run("reopen", "eval-foo", "--to", "probe", "--reason", "x")
    assert result.exit_code != 0


def test_archive_requires_done_or_dropped(run):
    _new(run)
    result = run("archive", "eval-foo")
    assert result.exit_code != 0


def test_archive_dropped_writes_knowledge_and_commits(run):
    _new(run)
    run("drop", "eval-foo", "--reason", "tecnologia inmadura")
    result = run("archive", "eval-foo")
    assert result.exit_code == 0
    knowledge = run.base / "knowledge" / "eval-foo.md"
    assert knowledge.exists()
    assert "tecnologia inmadura" in knowledge.read_text(encoding="utf-8")
    assert _log(run.base)[0] == "research(eval-foo): archive"
