## MODIFIED Requirements

### Requirement: Prohibited material exclusion
The public repository tree and Git history reachable from every ref intended for publication MUST exclude real investigations, knowledge outputs, notebooks, environment files, caches, nested repositories, credentials, private paths, private endpoints, confidential vulnerability reports, and generated build artifacts. Findings MUST identify category and location without disclosing sensitive values.

#### Scenario: Prohibited content is present in the current tree
- **WHEN** excluded content is detected in the candidate publication tree
- **THEN** the audit reports its category and location with redaction
- **THEN** release readiness fails

#### Scenario: Prohibited content exists only in reachable history
- **WHEN** sensitive content is absent from the tree but present in public reachable history
- **THEN** the audit identifies the affected ref and location without echoing the value
- **THEN** readiness fails until history and exposed credentials are remediated

### Requirement: Public identity consistency
Repository, distribution, command, license, governance, documentation, security, and release metadata MUST identify the same public project. Required repository, source, documentation, issue, release, changelog, security, and package-index coordinates MUST be real public locations and MUST NOT be placeholders, private locations, or unrelated projects.

#### Scenario: Compare public metadata
- **WHEN** public metadata is validated
- **THEN** the distribution is `spec-driven-research`
- **THEN** the import package and command are `sdr`
- **THEN** the license is Apache-2.0
- **THEN** all public identities and coordinates are consistent

#### Scenario: A public coordinate is invalid
- **WHEN** a required coordinate is missing, inaccessible, placeholder, private, or inconsistent
- **THEN** release readiness fails and identifies that coordinate

### Requirement: Deterministic boundary audit
The repository MUST provide a repeatable, history-aware boundary audit covering the candidate tree and all Git objects reachable from publication refs. Findings MUST have stable ordering, identify scope, and redact sensitive values.

#### Scenario: Run the public-boundary audit twice
- **WHEN** an unchanged candidate and publication scope are audited twice
- **THEN** both runs return the same ordered findings and result

#### Scenario: Audit scope cannot be established
- **WHEN** the candidate revision or publication refs cannot be identified completely
- **THEN** the audit reports missing scope and does not report the repository safe

## ADDED Requirements

### Requirement: Operational private vulnerability reporting
The public repository MUST provide a real, monitored, private vulnerability-reporting channel. Guidance MUST state scope, submission process, expected report contents, and response behavior without requiring initial public disclosure.

#### Scenario: Report a vulnerability privately
- **WHEN** a researcher follows the security guidance
- **THEN** they can reach an operational private channel associated with SDR
- **THEN** they are not directed to disclose the issue publicly

#### Scenario: Reporting is not operational
- **WHEN** the route is placeholder, inaccessible, public-only, or unowned
- **THEN** release readiness fails

### Requirement: Immutable public source provenance
Every public release MUST be associated with an immutable source revision in the canonical public repository. Package, release, and repository metadata MUST agree on that identity; a mutable branch alone MUST NOT satisfy provenance.

#### Scenario: Trace a release to source
- **WHEN** a user inspects a public SDR release
- **THEN** its identity resolves to an immutable obtainable source revision
- **THEN** public metadata identifies the same project, release, and revision

#### Scenario: Source provenance is inconsistent
- **WHEN** the immutable revision is missing or public surfaces point to different revisions
- **THEN** release readiness fails and identifies the inconsistency
