## Purpose

Define SDR's deterministic research lifecycle, artifact contract, evidence layers, explicit
backtracking, and human decision boundary.

## Requirements

### Requirement: Ordered lifecycle modes
SDR MUST use `intake -> explore -> probe -> transfer -> reuse -> done` in full mode and MUST omit
only `probe` in light mode. Reuse remains required in both modes.

#### Scenario: Advance a full investigation
- **WHEN** every current-stage control passes
- **THEN** stages advance in full-mode order until status becomes `done`

#### Scenario: Advance a light investigation
- **WHEN** intake and explore pass in light mode
- **THEN** the next stages are transfer and reuse rather than probe
- **THEN** recommendations are capped at `assess`

### Requirement: Stage-specific artifact contract
Each stage MUST validate its declared artifact shape: `brief.md`, traceable `notes/*.md`, executable
`probe/results.md`, `decision-memo.md`, and reusable `assets/*.md` as applicable to the mode.

#### Scenario: A required artifact field is missing
- **WHEN** a stage artifact lacks required frontmatter, sections, or enumerated metadata
- **THEN** `sdr check` identifies the failing deterministic check
- **THEN** advancement remains blocked

### Requirement: Structural and evidential gates
Intake MUST contain at least two identifiable criteria; explore MUST declare dated tiered sources with
required maturity, cost, risk, counter-evidence, and triangulation; probe MUST map every criterion to
a result and reproducible evidence; transfer MUST provide a complete Y-statement and evidence-backed
ring; reuse MUST declare a supported type and audience.

#### Scenario: Evidence is incomplete
- **WHEN** a stage lacks a required criterion mapping, source property, recommendation element, or asset property
- **THEN** its gate fails with an actionable detail

### Requirement: Offline semantics
Offline mode MUST skip network link checks without reporting them as passed and MUST retain all local
structural, evidential, textual, executable-evidence, consistency, and approval requirements.

#### Scenario: Check explore offline
- **WHEN** `sdr check <slug> --offline` runs with valid local artifacts
- **THEN** link resolution is marked skipped
- **THEN** skipped network checks do not conceal any local gate failure

### Requirement: Deterministic textual anchoring
Factual explore claims marked `[S<n>]` MUST match the corresponding current local snapshot or carry a
current scoped human resolution. Contextual `[cf. S<n>]` references MUST validate source identity but
MUST NOT create factual claims.

#### Scenario: A factual claim is not locally anchored
- **WHEN** deterministic matching cannot verify the current claim against its declared snapshot
- **THEN** the claim is `not_anchored` or `unverifiable`
- **THEN** explore advancement remains blocked until evidence changes or `resolve-claim` records a scoped review

#### Scenario: A contextual citation is present
- **WHEN** a note uses `[cf. S<n>]` for attribution
- **THEN** source declaration rules apply
- **THEN** no textual-match claim is created

### Requirement: Explicit executable evidence
Probe execution MUST occur only through `sdr verify-probe` after an explicit run declaration, and
probe advancement MUST consume a persisted passing result whose hash matches the current probe tree.

#### Scenario: Probe has not been explicitly verified
- **WHEN** `sdr advance` runs at probe without a current green verification
- **THEN** it does not execute the probe
- **THEN** advancement is blocked with a `verify-probe` instruction

#### Scenario: Probe content changes after verification
- **WHEN** any hashed probe content changes
- **THEN** the persisted verification becomes stale
- **THEN** adopt and trial recommendations remain unavailable until re-verification passes

### Requirement: Hash consistency
Successful advancement MUST persist a hash of the validated stage artifacts, and later operations
MUST block if previously validated content no longer matches its stored hash.

#### Scenario: Validated evidence is edited
- **WHEN** a validated stage artifact changes without explicit reopening and revalidation
- **THEN** consistency checking identifies the stage
- **THEN** further advancement is blocked

### Requirement: Human approval boundary
Transfer advancement MUST require explicit approval of the current decision memo. A scoped claim
resolution MUST NOT substitute for decision approval.

#### Scenario: Transfer gates pass without approval
- **WHEN** a valid decision memo has no recorded approver and date
- **THEN** advancement to reuse is blocked

#### Scenario: One claim was human-reviewed
- **WHEN** `resolve-claim` records a scoped explore resolution
- **THEN** transfer still requires a separate `sdr approve`

### Requirement: Explicit backtracking and terminal states
`sdr reopen` MUST move only backward with a reason, invalidate validation hashes from the destination
stage onward, and reactivate done research. Dropping MUST record a reason rather than deleting evidence.

#### Scenario: Reopen to an earlier stage
- **WHEN** a valid earlier stage and non-empty reason are supplied
- **THEN** the transition is recorded and later validation hashes are removed
- **THEN** the investigation becomes active at the requested stage

### Requirement: Structured automation interface
Operational commands used by agents MUST support structured JSON where documented, and lifecycle
transitions MUST preserve stage guards rather than relying on agent-specific behavior.

#### Scenario: An automation checks current state
- **WHEN** it invokes a supported command with `--json`
- **THEN** it receives machine-readable status or gate details suitable for deterministic decisions
