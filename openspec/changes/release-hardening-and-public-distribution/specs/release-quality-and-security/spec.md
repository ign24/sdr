## MODIFIED Requirements

### Requirement: Dependency and artifact review
Release checks MUST inspect declared dependencies and independently audit wheel and source distribution contents for required resources, vulnerabilities, secrets, and prohibited material. Vulnerability checks MUST cover core runtime and every supported optional dependency set independently, and artifact evidence MUST identify exact content by cryptographic digest.

#### Scenario: An artifact contains prohibited content
- **WHEN** artifact inspection detects a credential, cache, repository metadata, or private path
- **THEN** the artifact is rejected with a redacted finding

#### Scenario: Audit all published dependency sets
- **WHEN** release readiness evaluates dependency vulnerability evidence
- **THEN** core and every supported optional set have current results
- **THEN** an advisory without an active, complete, unexpired, approved exception fails readiness

### Requirement: Fail-closed release result
Release readiness MUST aggregate current test, lint, package, documentation, integration, dependency, public-audit, path, network, probe, Git-safety, supported-environment, installed-E2E, artifact digest, provenance, release identity, and publication-authorization evidence. Publication MUST remain blocked unless every applicable criterion is present, current, and successful.

#### Scenario: A mandatory result is absent or stale
- **WHEN** any required result is missing, skipped, stale, or failing
- **THEN** the repository is reported as not release-ready with actionable unmet criteria

#### Scenario: Publication lacks complete evidence
- **WHEN** a release lacks any applicable identity, compatibility, E2E, dependency, artifact, provenance, or approval result
- **THEN** publication does not start

## ADDED Requirements

### Requirement: Installed console-script end-to-end gate
Release evidence MUST include clean-environment tests that install release artifacts and exercise the installed `sdr` console script outside the source checkout. Evidence MUST cover representative light and full lifecycles, expected failure paths, snapshot support, and every claimed environment.

#### Scenario: Exercise installed lifecycles
- **WHEN** installed-artifact E2E validation runs
- **THEN** representative light and full lifecycles reach `done`
- **THEN** blocked and invalid operations return documented non-success behavior

#### Scenario: A claimed environment lacks installed E2E evidence
- **WHEN** no current installed-console-script result exists for a claimed environment
- **THEN** release readiness fails and identifies the missing environment

### Requirement: Authorized immutable release identity
A public release MUST originate from an authorized version tag resolving to one immutable source revision. The tag, `src/sdr/__init__.py`, changelog, artifacts, and public release identity MUST agree, and publication MUST require protected-environment approval.

#### Scenario: Validate release identity
- **WHEN** a version tag requests publication
- **THEN** all version-bearing surfaces agree with the recorded source revision
- **THEN** the protected environment authorizes publication

#### Scenario: Release identities disagree
- **WHEN** tag, source, changelog, artifact, or intended index versions differ
- **THEN** release readiness fails before publication and reports the conflicts

### Requirement: Build-once artifact provenance
Release automation MUST publish only previously validated artifacts and MUST record each filename, digest, source revision, tag, version, validation run identity, and available provenance. Publication MUST verify this evidence before upload.

#### Scenario: Acquire artifacts for publication
- **WHEN** the publication job obtains release artifacts
- **THEN** it verifies their digests and source identity
- **THEN** it publishes those exact artifacts without rebuilding

#### Scenario: An artifact digest differs
- **WHEN** an acquired artifact differs from its recorded digest
- **THEN** publication stops before upload and reports the mismatch

### Requirement: Least-privilege Trusted Publishing
Public package-index publication MUST use short-lived OIDC Trusted Publishing and MUST NOT use a stored API token. Only the protected publication job may receive job-scoped `id-token: write`; pull-request and branch validation MUST remain read-only and unable to publish.

#### Scenario: Publish an authorized release
- **WHEN** complete approved release evidence reaches publication
- **THEN** the job obtains a short-lived OIDC credential
- **THEN** no stored package-index token is present
- **THEN** the publishing action is pinned to a reviewed full commit SHA

#### Scenario: Run an untrusted workflow
- **WHEN** automation runs for a pull request or ordinary branch
- **THEN** it cannot request publication credentials or publish artifacts
