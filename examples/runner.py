"""Materialize and run synthetic examples without modifying their source fixtures."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import frontmatter
import yaml

from sdr import gates, lifecycle, probe_verify, schema
from sdr.gates import GateReport
from sdr.research import Approval, Research


def _load_config(example_dir: Path) -> dict:
    return yaml.safe_load((example_dir / "fixture.yaml").read_text(encoding="utf-8"))


def _create_research(example_dir: Path, destination: Path) -> Research:
    config = _load_config(example_dir)
    return Research.create(
        base=destination,
        slug=config["slug"],
        title=config["title"],
        question=config["question"],
        mode=config.get("mode", "full"),
        owner=config.get("owner", ""),
        timebox=config.get("timebox", 0),
    )


def _copy_stage(example_dir: Path, research: Research, stage: str) -> None:
    sources = {
        "intake": ("brief.md",),
        "explore": ("notes",),
        "probe": ("probe",),
        "transfer": ("decision-memo.md",),
        "reuse": ("assets",),
    }[stage]
    for relative in sources:
        source = example_dir / relative
        target = research.root / relative
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            shutil.copy2(source, target)


def _make_probe_argv_portable(research: Research) -> None:
    path = research.artifact_path("probe/results.md")
    artifact = frontmatter.load(path)
    verify = dict(artifact.metadata["verify"])
    verify["argv"] = [sys.executable, *verify["argv"][1:]]
    artifact.metadata["verify"] = verify
    path.write_text(frontmatter.dumps(artifact) + "\n", encoding="utf-8")


def run_example(example_dir: Path, destination: Path) -> Research:
    """Copy a complete fixture to ``destination`` and execute its lifecycle offline."""
    example_dir = example_dir.resolve()
    research = _create_research(example_dir, destination)
    config = _load_config(example_dir)

    for stage in schema.stage_order(research.meta.mode):
        _copy_stage(example_dir, research, stage)
        if stage == "probe":
            _make_probe_argv_portable(research)
            verification = probe_verify.verify_probe(research, timeout=10)
            if not verification.passed:
                raise RuntimeError(f"probe verification failed: {verification.error_code}")
        if stage == "transfer":
            approval = config["approval"]
            research.meta.approval = Approval(by=approval["by"], date=str(approval["date"]))
            research.save()
        result = lifecycle.advance(research, offline=True)
        if not result.ok:
            raise RuntimeError(f"{stage} failed: {result.blocked_reason}")

    return research


def evaluate_failing_example(example_dir: Path, destination: Path) -> tuple[GateReport, str]:
    """Materialize one focused negative fixture and return its current-stage gate report."""
    example_dir = example_dir.resolve()
    config = _load_config(example_dir)
    research = _create_research(example_dir, destination)
    stage = config["stage"]
    if stage != "intake" and (example_dir / "brief.md").is_file():
        _copy_stage(example_dir, research, "intake")
    _copy_stage(example_dir, research, stage)
    research.meta.stage = stage
    research.save()
    return gates.check_stage(research, stage=stage, offline=True), config["expected_check"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example", choices=("light-complete", "full-complete"))
    parser.add_argument("--root", type=Path, required=True, help="Empty destination research root")
    args = parser.parse_args()
    research = run_example(Path(__file__).parent / args.example, args.root)
    print(f"{research.meta.slug}: {research.meta.status}")


if __name__ == "__main__":
    main()
