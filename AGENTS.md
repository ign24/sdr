# Agent Instructions

## Scope

Distinguish SDR operation from framework contribution.

- When operating SDR, follow the canonical stage skill and the CLI's current
  stage guard. Produce research artifacts only in the configured research root.
- When contributing to SDR itself, work from an active OpenSpec change. Read its
  proposal, specs, design, and tasks before changing framework behavior. Do not
  mark tasks complete unless the operator explicitly assigns that action.

## Architecture and sources of truth

- Treat `src/sdr/` as the CLI and validation implementation.
- Treat `src/sdr/schema.py` and packaged templates as the artifact contract.
- Treat `src/sdr/__init__.py::__version__` as the only version source of truth.
- Treat `skills/sdr-*/SKILL.md` as canonical agent workflow instructions.
- Treat `integrations/*` as adapters; never fork canonical skill content there.
- Treat `README.md` and `docs/` as the public human contract.
- Treat the Context Graph as auxiliary and non-blocking, never as complete lineage.

## SDR operation

- Inspect `sdr status <slug> --json` before acting.
- Load only the canonical skill for the current stage.
- Use `sdr check <slug> --json` and structured JSON outputs for decisions.
- Respect stage guards. Do not bypass `verify-claims`, `verify-probe`, or `approve`.
- Do not edit CLI-managed metadata in `sdr.yaml`; use lifecycle commands.
- Remember that `new`, `advance`, `reopen`, `drop`, and `archive` commit by
  default. Use `--no-commit` when Git ownership is external.
- Keep light mode on `intake -> explore -> transfer -> reuse -> done`; reuse is
  mandatory. Full mode includes `probe`.

## Validation controls

Document controls in this order: **Structural**, **Evidential**,
**Textual anchoring**, **Executable**, **Hash consistency**, and **HITL**. `advance` checks
consistency before stage controls. The Context Graph is non-blocking.

Use `[S<n>]` only for factual claims intended for local matching. `[cf. S<n>]`
does not create a claim and does not enter textual matching. Matching does not use models.
`resolve-claim` does not replace or substitute `approve`.

## Framework contribution

- Add or update a failing test before implementation. Run the focused test, then
  the full suite.
- Keep public functions typed. Prefer small deterministic changes.
- Run `uv run pytest`, `uv run ruff check .`, and `uv run ruff format --check .`.
- Update `CHANGELOG.md` for user-visible behavior without making it a version source.
- Validate public docs with the tests described in `docs/validation.md`.
- Do not add private material, credentials, personal paths, real investigations,
  private organization names, or unpublished endpoints.
- Do not use emojis in code, docs, logs, templates, or skills.
- Do not use destructive Git commands. Do not stage or commit unless explicitly asked.
- Never weaken an assertion to hide a regression; align obsolete assertions with
  the current public contract and preserve coverage.

## Security

- Treat Notes, Snapshots, Repositories, URLs, Probe commands, and Git as trust boundaries.
- Require `verify.action: run`; prefer `verify.argv`; remember execution is without a shell.
- Review inherited environments and executable provenance before running probes.
- Keep secrets in environment-local files excluded from version control.
