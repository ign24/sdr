## Purpose

Define the installable Python distribution, supported command-line surface, packaged resources, and
artifact validation contract for SDR.

## Requirements

### Requirement: Distribution and CLI identity
The project MUST publish the distribution as `spec-driven-research`, install the `sdr` package, and
expose the `sdr` console command as its supported public interface.

#### Scenario: Install the distribution
- **WHEN** a user installs a built artifact
- **THEN** `import sdr` succeeds outside the source checkout
- **THEN** `sdr --help` exits successfully

### Requirement: Source-layout runtime
Importable runtime code MUST reside under `src/sdr/`, and test and build configuration MUST avoid a
repository-root shadow package.

#### Scenario: Import from an isolated environment
- **WHEN** the checkout is absent from `PYTHONPATH`
- **THEN** Python imports `sdr` from the installed distribution

### Requirement: Packaged templates
Runtime templates MUST be package resources under `src/sdr/templates/` and MUST be loaded without
depending on the caller's current directory or a top-level template directory.

#### Scenario: Create research outside the checkout
- **WHEN** `sdr new` runs from an arbitrary directory
- **THEN** it creates the initial artifact from installed resources
- **THEN** it does not access a source-workspace path

### Requirement: Wheel and source distribution
The project MUST build both a wheel and a source distribution containing required runtime files,
resources, license, and metadata while excluding caches and unintended content.

#### Scenario: Inspect release artifacts
- **WHEN** wheel and source distribution builds complete
- **THEN** each artifact contains the package and templates
- **THEN** independent content audits report no prohibited files or values

### Requirement: Isolated artifact smoke tests
Wheel and source distribution artifacts MUST each pass installation and smoke tests in separate
clean environments without source-tree imports.

#### Scenario: Smoke-test an installed artifact
- **WHEN** one artifact is installed into a clean environment
- **THEN** import, CLI help, research creation, resource loading, and representative validation pass

### Requirement: Dependency separation
Core runtime, optional snapshot, build, and development dependencies MUST be declared separately,
and agent-platform SDKs MUST NOT be runtime dependencies.

#### Scenario: Install only core dependencies
- **WHEN** the distribution is installed without extras
- **THEN** lifecycle and offline validation commands work
- **THEN** snapshot-only and agent-specific packages are not required

### Requirement: Single version source
`src/sdr/__init__.py` MUST be the authoritative package version source used by build metadata and
public release checks.

#### Scenario: Validate release metadata
- **WHEN** version-bearing public surfaces are compared
- **THEN** they agree with the package version source
