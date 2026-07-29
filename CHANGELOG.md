# Changelog

All notable user-visible changes are documented here. The format follows Keep a
Changelog, and releases use semantic versioning.

This file records releases; it is not the package version source of truth. The
single source of truth is `src/sdr/__init__.py`.

## [Unreleased]

### Added

- Public English documentation, security guidance, contribution governance, and
  maintenance validation instructions.
- Public Spanish README and deterministic semantic parity validation for both
  language guides.
- Read-only Linux CI for Python 3.12 and 3.13, strict specification checks,
  dependency and secret scanning, and isolated wheel/sdist release audits.
- Sanitized machine-readable discovery-canary evidence for Claude Code, Codex,
  and OpenCode, with fail-closed validation against public integration claims.
- An installed `sdr integrations install --destination PATH` command for copying
  all seven packaged canonical skills from isolated tool environments.

### Changed

- Current and future distributions are licensed under MIT; historical Apache-2.0 grants are not revoked.
- Narrowed the documented Agent Skills adapter set to Claude Code, Codex, and
  OpenCode; removed Hermes Agent and OpenClaw adapters and support claims.

## [0.1.0] - 2026-07-27

### Added

- Five-stage full and light Spec-Driven Research lifecycle.
- Deterministic structural, evidential, textual, executable, consistency, and
  human-approval controls.
- Source snapshots, scoped claim resolution, reproducible probe execution,
  backtracking, archiving, status reporting, and optional Context Graph views.
- Documented adapters for supported Agent Skills hosts.
