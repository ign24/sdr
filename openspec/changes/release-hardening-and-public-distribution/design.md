## Context

SDR validates its source tree thoroughly, but it has no complete public-release chain. CI tests Python 3.12 and 3.13, while artifact smoke tests run only on 3.12 and stop after import, help, creation, and status. Publishing is disabled, artifacts are temporary, public coordinates and private vulnerability reporting are not operational, and optional dependency closures are not independently audited.

Snapshot retrieval exposes the final response URL and HTTP status in memory but persists the declared URL as if it were the retrieval identity, marks any non-empty extraction as `ok`, and does not verify the persisted `content_hash` before matching. Integrations depend on a framework checkout and use `SDR_ROOT` for both framework source and research storage.

The design must close these gaps without changing lifecycle order, approval semantics, deterministic claim matching, or `src/sdr/__init__.py` as the sole version source.

## Goals / Non-Goals

**Goals:**

- Build release artifacts once and promote only their digest-verified bytes.
- Publish through least-privilege PyPI Trusted Publishing with an approved release identity.
- Test the installed console script across every claimed runtime, artifact, optional profile, lifecycle mode, and representative failure path.
- Make support and dependency claims correspond to release-blocking evidence.
- Persist and verify snapshot retrieval provenance without claiming publisher identity or truth.
- Complete public governance, security reporting, versioned acquisition for Claude Code, Codex, and OpenCode, and bilingual documentation.

**Non-Goals:**

- Claiming Windows, macOS, future Python, or agent-host support without evidence.
- Adding agent SDKs, a plugin manager, long-lived package-index credentials, or placeholder public coordinates.
- Maintaining or claiming public support for Hermes Agent, OpenClaw, or other agent hosts in this release.
- Turning SDR into a network or process sandbox.
- Authenticating publishers or judging semantic truth.
- Redesigning lifecycle stages, gates, approval, or Git behavior.

## Decisions

### Build once and promote by digest

A tag-triggered release workflow will validate release identity, build wheel and sdist once, and create a manifest containing version, tag, source commit, artifact filenames, sizes, SHA-256 digests, and workflow identity. Every audit, E2E, and publication job will consume that handoff and verify the manifest. Publication will never rebuild artifacts.

Rebuilding in the publication job was rejected because source equivalence does not guarantee byte equivalence. Selecting artifacts from an unrelated CI run was rejected because it makes revision, retention, and authorization ambiguous.

### Bind publication to a protected identity

The version tag, `sdr.__version__`, changelog release, wheel metadata, and sdist metadata must agree. Publication will run only in a protected environment after approval, with `contents: read` and job-scoped `id-token: write`, no PyPI token, and the official PyPA action pinned to a reviewed full commit SHA. Pull-request and branch workflows remain read-only and unable to publish.

Real repository, environment, package-index, and reporting coordinates are deployment preconditions and will not be invented in source.

### Separate pre-publication and post-publication verification

All reversible checks run before upload. After publication, a finalization job installs the exact public version and compares package-index artifacts with the manifest. A post-publication failure triggers an incident path that preserves evidence and uses yank plus a new version; published versions are never overwritten.

### Use an installed-artifact release matrix

Release validation covers every claimed Python minor, wheel and sdist, core and snapshot profiles, on each Linux environment represented in support claims. Each cell records its actual OS, architecture, Python runtime, and runner or container identity without requiring a fixed runner vendor or image, and runs outside the checkout with a fresh environment, cleared source import paths, synthetic fixtures, no publication credentials, and the installed `sdr` command.

The harness covers complete light and full lifecycles, explicit claim/probe verification and approval, expected stage failures, stale hashes, offline core operation, optional snapshot extraction against a controlled fixture, packaged resources, and JSON output. PR checks may keep a smaller smoke matrix; the exhaustive matrix blocks releases.

### Make compatibility evidence-backed

The first public release will claim only Python minors and Linux environments covered by the full installed matrix. Direct lower bounds receive explicit minimum-version installation tests; current locked resolutions are tested separately. Core and every optional extra have independent vulnerability audits. Unsupported or untested combinations are excluded from metadata and documentation rather than assumed compatible.

### Persist exact snapshot provenance

Versioned snapshot metadata will distinguish declared URL, final URL, redirect chain, terminal status, capture time, extraction status, and SHA-256 of the exact bytes written to `content.md`. Only eligible 2xx textual responses with non-empty extraction and a matching persisted-byte hash may be used for textual anchoring. Non-2xx, incomplete, empty, or hash-mismatched captures remain visible but unverifiable.

Verification identity will include provenance fields that affect evidence identity. Redirects remain visible and do not authenticate the publisher. Legacy snapshots will not have missing final URLs inferred; they require conservative migration, recapture, or existing scoped human review.

### Distribute canonical integration resources without forks

Released skills and adapter descriptors will be obtainable from a version-identifiable public artifact. If included as package resources, their build output must be byte-equivalent to top-level canonical sources. Installation remains explicit, refuses conflicts, and does not modify credentials, hooks, permissions, or unrelated agent configuration.

The supported adapter set is exactly Claude Code, Codex, and OpenCode. Hermes Agent and OpenClaw descriptors, guides, package resources, and support claims are removed rather than retained as experimental adapters.

`SDR_ROOT` remains exclusively the research root. Framework checkout or acquisition locations use explicit source-root terminology. Static contract and installation checks are required for all three supported adapters. A host E2E may run in an isolated sandbox, but an adapter may claim `verified` only when version-matched installed-CLI evidence records the host, SDR version, acquisition identity, environment, discovery, and lifecycle result. Otherwise it remains `documented`.

### Make governance and documentation release gates

Publication requires real public project coordinates, a monitored private vulnerability-reporting route, release and immutable-version policy, supported-version policy, contribution guidance, and Apache-2.0 licensing. Tree, history, artifact, and secret audits remain fail closed and redact values.

English and Spanish entry points must agree semantically on installation, support, release verification, security reporting, source provenance, root terminology, integration acquisition, statuses, and limitations. Parity stays concept-based rather than line-by-line.

## Risks / Trade-offs

- [Public-index verification happens after irreversible upload] -> Maximize pre-publication checks; never overwrite a version; use yank and a corrected version on failure.
- [The release matrix increases duration and cost] -> Keep focused PR smoke checks and reserve exhaustive cells for release candidates.
- [A bounded Python range may exclude versions that happen to work] -> Prefer an honest tested contract and expand it through evidence.
- [Lower-bound tests expose combinations absent from the lock] -> Raise inaccurate floors or restore compatibility rather than weakening tests.
- [Packaged integration resources duplicate files in artifacts] -> Generate them mechanically and enforce byte equivalence to canonical sources.
- [Legacy snapshots lack final-URL provenance] -> Preserve them without invented facts and require recapture or scoped review.
- [CI cannot prove a reporting channel or protected environment is operated] -> Require protected-environment human attestation in addition to structural checks.
- [Hashes prove identity, not truth] -> Keep confidence boundaries explicit in structured and human-facing output.

## Migration Plan

1. Establish real repository, package-index, protected-environment, approver, and private reporting coordinates outside the codebase.
2. Add failing policy and E2E tests for release identity, build-once digest handoff, permissions, matrix coverage, dependency profiles, and fail-closed aggregation.
3. Implement the installed-artifact lifecycle harness and align Python/dependency metadata with passing evidence.
4. Introduce versioned snapshot provenance and conservative legacy handling.
5. Make canonical skills and the Claude Code, Codex, and OpenCode adapters publicly version-identifiable, remove Hermes Agent and OpenClaw from public artifacts and documentation, and remove `SDR_ROOT` ambiguity.
6. Update English and Spanish public contracts and validators.
7. Exercise the workflow with publication disabled, then configure Trusted Publishing against the final reviewed workflow identity.
8. Rehearse digest-bound publication with upload disabled, then publish to the declared public index only after approval. TestPyPI remains an optional operator-selected rehearsal target rather than a release-readiness requirement.

Rollback before publication disables the release workflow and restores the prior metadata contract. After publication, rollback means yanking the affected version and issuing a new corrected version, never replacing artifacts.

## Open Questions

- What are the canonical public repository and package-index coordinates?
- Which protected environment and maintainers will authorize publication?
- Which operational private vulnerability-reporting mechanism will be used?
- Where will manifests and provenance remain durable after CI artifact expiry?
- Is `0.1.0` the intended first public release, or should the first release use a later version?
