# Contributing

Contributions should preserve SDR's deterministic, local, evidence-first contract.

## Before changing behavior

Framework changes require an active OpenSpec change with a proposal, affected
specification, design when needed, and task list. Read those artifacts before
editing. Keep task status under the change owner's control unless task updates
are explicitly part of your assignment.

For a bug, first add the smallest test that reproduces it. For a feature, write
a failing test for the public behavior before implementation. Keep changes small
and avoid compatibility paths without a concrete persisted or external consumer.

## Development setup

```bash
uv sync --all-extras --dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Public Python functions require type hints. Code, tests, logs, documentation,
templates, and skills must not contain emojis. Never include credentials,
private material, personal paths, real research data, or private organization
names. Use `.env` only for local secrets and never commit it.

## Documentation and releases

Update `README.md` or `docs/` when public behavior changes. Update
`CHANGELOG.md` under the intended release, but keep
`src/sdr/__init__.py::__version__` as the single version source of truth. Follow
[docs/validation.md](docs/validation.md) before proposing a release.

Do not add placeholder project URLs to package metadata. Add URLs only after a
real public location exists.

## Git safety

Do not use destructive Git commands. Do not rewrite history, bypass hooks, or
stage unrelated files. SDR lifecycle commands commit by default; pass
`--no-commit` when testing them in a working repository unless the test isolates Git.

## Conduct decision for 0.1

Version 0.1 does not include a copied Code of Conduct. The project has no
published community contact or enforcement address yet, so adopting a covenant
without a real reporting and enforcement process would be misleading. Respectful,
professional participation is required. A future release should adopt and
attribute a standard code of conduct when maintainers can publish and operate
its reporting process.
