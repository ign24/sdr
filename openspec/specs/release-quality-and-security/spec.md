## Purpose

Define the automated quality, security, and release checks required for a trustworthy SDR public
artifact, including filesystem, network, execution, and Git trust boundaries.

## Requirements

### Requirement: Complete automated test gate
Required unit, integration, lifecycle, CLI, packaging, documentation, and end-to-end tests MUST pass
without ignored failures before release.

#### Scenario: A required test is not green
- **WHEN** a test fails, errors, or is unexpectedly skipped
- **THEN** release readiness fails

### Requirement: Static quality gate
The supported Python tree MUST pass configured Ruff lint and formatting checks.

#### Scenario: Lint or formatting differs
- **WHEN** Ruff reports a violation or formatting change
- **THEN** the quality gate fails with the affected path

### Requirement: Dependency and artifact review
Release checks MUST inspect declared dependencies and independently audit wheel and source
distribution contents for required resources, vulnerabilities, secrets, and prohibited material.

#### Scenario: An artifact contains prohibited content
- **WHEN** artifact inspection detects a credential, cache, repository metadata, or private path
- **THEN** the artifact is rejected with a redacted finding

### Requirement: Confined filesystem access
User-controlled roots, slugs, destinations, filenames, and artifact references MUST be resolved
within their declared roots before access, including protection against traversal and symlink escape.

#### Scenario: A path escapes its root
- **WHEN** an absolute path, parent traversal, unsafe separator, or symlink resolves outside the root
- **THEN** the operation fails before reading, writing, staging, or executing the target

### Requirement: Bounded network retrieval
Source retrieval MUST accept only HTTP and HTTPS, reject prohibited and metadata destinations before
connection and after redirects, and bound redirects, timeouts, and response sizes.

#### Scenario: A public URL redirects to a prohibited address
- **WHEN** resolution or a redirect targets loopback, private, link-local, reserved, or metadata space
- **THEN** retrieval stops with a safe network-policy error

### Requirement: Explicit bounded probe execution
Probe verification MUST require `verify.action: run`, prefer a list-valued `verify.argv`, execute
without an implicit shell, confine the working directory, bound time and output, and document its
environment. Passive checks and advancement MUST NOT launch probes.

#### Scenario: Run passive lifecycle validation
- **WHEN** a user runs `sdr check` or `sdr advance`
- **THEN** no probe process is started

#### Scenario: An explicit probe times out
- **WHEN** `sdr verify-probe` exceeds its timeout
- **THEN** the process tree is terminated
- **THEN** a failed verification result is persisted

### Requirement: Scoped lifecycle commits
Automatic lifecycle commits MUST stage only intended paths for the current investigation and MUST
preserve unrelated tracked and untracked work.

#### Scenario: Transition inside a dirty repository
- **WHEN** unrelated changes exist during a lifecycle transition
- **THEN** only explicit transition paths are staged and committed
- **THEN** unrelated changes remain untouched

### Requirement: Non-destructive Git failure handling
Git failures MUST be reported without reset, clean, amend, force, hook bypass, or false success, and
`--no-commit` MUST suppress commit creation.

#### Scenario: Commit creation fails
- **WHEN** a lifecycle commit cannot be created
- **THEN** user work and existing history remain unchanged
- **THEN** the CLI reports the failure

#### Scenario: Commit suppression is requested
- **WHEN** a transition receives `--no-commit`
- **THEN** it creates no Git commit

### Requirement: Fail-closed release result
Release readiness MUST aggregate current test, lint, package, documentation, integration, dependency,
public-audit, path, network, probe, and Git-safety evidence.

#### Scenario: A mandatory result is absent or stale
- **WHEN** any required result is missing, skipped, stale, or failing
- **THEN** the repository is reported as not release-ready with actionable unmet criteria
