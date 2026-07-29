## MODIFIED Requirements

### Requirement: Distribution and CLI identity
The project MUST publish the distribution as `spec-driven-research`, install the `sdr` package, and expose the `sdr` console command as its supported public interface. A public release MUST be installable from the declared public Python package index without access to the source checkout or a repository-local artifact.

#### Scenario: Install the distribution
- **WHEN** a user installs a built artifact
- **THEN** `import sdr` succeeds outside the source checkout
- **THEN** `sdr --help` exits successfully

#### Scenario: Install a published release
- **WHEN** a user installs an identified release from the declared public package index in a clean supported environment
- **THEN** the installed version matches the requested release
- **THEN** imports and the console command work without the source checkout on `PYTHONPATH`

### Requirement: Wheel and source distribution
The project MUST build both a wheel and a source distribution containing required runtime files, resources, license, and metadata while excluding caches and unintended content. Release publication MUST promote the exact wheel and source distribution that passed release validation and MUST NOT rebuild or modify either artifact after validation.

#### Scenario: Inspect release artifacts
- **WHEN** wheel and source distribution builds complete
- **THEN** each artifact contains the package and templates
- **THEN** independent content audits report no prohibited files or values

#### Scenario: Promote validated artifacts
- **WHEN** a release is approved for publication
- **THEN** the selected wheel and source distribution match the validated cryptographic digests
- **THEN** no publication step rebuilds or modifies them

### Requirement: Isolated artifact smoke tests
Wheel and source distribution artifacts MUST each pass installation and smoke tests in separate clean environments without source-tree imports. The installed `sdr` console script MUST pass representative light and full lifecycle tests, expected failure paths, and optional snapshot tests in every environment for which those features are claimed.

#### Scenario: Smoke-test an installed artifact
- **WHEN** one artifact is installed into a clean environment
- **THEN** import, CLI help, research creation, resource loading, and representative validation pass

#### Scenario: Validate installed lifecycle behavior
- **WHEN** a release artifact is tested in a claimed environment
- **THEN** tests invoke the installed console script outside the checkout
- **THEN** representative light and full lifecycles reach `done`
- **THEN** blocked and invalid operations return the documented non-success behavior

### Requirement: Dependency separation
Core runtime, optional snapshot, build, and development dependencies MUST be declared separately, and agent-platform SDKs MUST NOT be runtime dependencies. Declared direct dependency bounds and every supported optional dependency set MUST agree with compatibility and vulnerability evidence enforced for release.

#### Scenario: Install only core dependencies
- **WHEN** the distribution is installed without extras
- **THEN** lifecycle and offline validation commands work
- **THEN** snapshot-only and agent-specific packages are not required

#### Scenario: Validate a declared dependency set
- **WHEN** release automation evaluates core dependencies or a supported extra
- **THEN** it resolves within published constraints
- **THEN** direct dependency bounds and vulnerability status have current evidence

## ADDED Requirements

### Requirement: Complete public package metadata
Published artifacts and package-index metadata MUST identify the project, version, supported Python range, license, authorship, description, classifiers, and resolvable public URLs for source, documentation, issues, changelog, and security policy. Version-bearing metadata MUST agree with `src/sdr/__init__.py`, and metadata MUST NOT contain placeholders or private locations.

#### Scenario: Inspect public release metadata
- **WHEN** release automation inspects artifacts and the public package-index record
- **THEN** required identity, compatibility, license, and project URLs are present and consistent
- **THEN** the version agrees with `src/sdr/__init__.py`
- **THEN** no value contains a placeholder or private location

### Requirement: Evidence-backed compatibility claims
Package metadata and public documentation MUST claim only Python versions, operating environments, direct dependency bounds, and optional dependency combinations covered by current release evidence. Unsupported environments MUST be excluded from support claims.

#### Scenario: Validate a claimed environment
- **WHEN** metadata or documentation claims support for an environment
- **THEN** release automation contains successful installed-artifact evidence for that environment and its claimed features

#### Scenario: Compatibility evidence is absent
- **WHEN** a runtime, platform, dependency bound, or optional combination lacks current evidence
- **THEN** the release MUST NOT claim that combination as supported
