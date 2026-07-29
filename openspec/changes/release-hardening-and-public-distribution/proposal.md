## Why

SDR's source-tree quality gates are strong, but the project does not yet establish a trustworthy public release from an immutable source revision through installation and full lifecycle use. Before broad distribution, release provenance, installed-artifact evidence, supported-environment claims, security reporting, source attribution, integration acquisition, and public documentation must become complete and fail closed.

## What Changes

- Establish an auditable public release path that promotes already validated wheel and source artifacts through least-privilege Trusted Publishing and records their digests, source revision, release identity, and provenance.
- Require clean-environment, installed-console-script end-to-end validation for representative light and full lifecycles, failure paths, optional snapshot support, and every claimed Python environment.
- Align Python, platform, direct dependency, and optional dependency claims with the compatibility and vulnerability evidence enforced by release automation.
- Complete the public repository identity and governance surface, including real project URLs, immutable release guidance, history-aware public audits, and an operational private vulnerability-reporting channel.
- Strengthen snapshot provenance so declared URLs, final retrieval locations, HTTP outcomes, capture metadata, and persisted content hashes cannot be conflated, while preserving explicit limits on publisher identity and truth claims.
- Make canonical skills and the Claude Code, Codex, and OpenCode adapters obtainable from a version-identifiable public source, remove Hermes Agent and OpenClaw from the supported public surface, separate the research root from framework acquisition, and keep integration status proportional to actual E2E evidence.
- Update English and Spanish installation, compatibility, release verification, security, source-provenance, and integration documentation so every public claim maps to current automated or human-reviewed evidence.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `python-distribution`: Require public-index installation, an evidence-backed support matrix, complete public package metadata, and build-once artifact promotion after isolated installed-CLI validation.
- `release-quality-and-security`: Add authorized release identity, artifact digest/provenance, least-privilege publication, complete dependency-extra auditing, installed E2E evidence, and fail-closed release aggregation.
- `public-repository-boundary`: Extend public identity, governance, secret/private-material, and provenance checks to the actual publication surface and Git history.
- `public-documentation`: Require evidence-backed public installation, compatibility, release, security-reporting, source-verification, and integration guidance with bilingual parity.
- `agent-integrations`: Require version-identifiable public acquisition, unambiguous source and research roots, CLI compatibility, and evidence-based integration statuses.
- `sdr-lifecycle-evidence-contract`: Strengthen snapshot attribution and hash consistency so locally anchored evidence records the content actually retrieved without overstating authenticity or truth.

## Impact

The change affects package metadata and dependency floors, release and security workflows, artifact and public-tree audits, installed CLI E2E tests, snapshot/network metadata and validation, canonical integration packaging or acquisition, README and maintenance/security documentation, and the corresponding OpenSpec contracts. Public integration validation, tests, artifacts, and documentation will expose exactly Claude Code, Codex, and OpenCode; Hermes Agent and OpenClaw support will be removed. It introduces no intentional CLI or lifecycle-stage break; any temporary upper Python bound would narrow an currently overbroad compatibility claim and must be called out in release notes.
