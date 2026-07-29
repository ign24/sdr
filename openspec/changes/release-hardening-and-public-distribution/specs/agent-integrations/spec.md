## MODIFIED Requirements

### Requirement: Optional supported adapters
The supported public adapter set MUST consist exactly of Claude Code, Codex, and OpenCode. Integration validation MUST derive this exhaustive set from explicit structured surfaces: top-level adapter directories, Hatch wheel `force-include` source-to-target mappings under `sdr/resources/integrations`, adapter descriptors, and public integration status tables. Those surfaces MUST agree on the exact set and each documented status; support MUST NOT be inferred by scanning arbitrary prose or by blacklisting selected unsupported hosts. Agent-platform SDKs MUST NOT become Python runtime dependencies.

#### Scenario: Use SDR without an agent platform
- **WHEN** no supported agent is installed
- **THEN** all core CLI commands remain available

#### Scenario: Install one supported adapter
- **WHEN** a user explicitly follows the Claude Code, Codex, or OpenCode installation instructions
- **THEN** that platform can discover the canonical workflows
- **THEN** the Python package remains independent of that platform

#### Scenario: An unsupported adapter is exposed
- **WHEN** validation finds an adapter directory, Hatch-packaged descriptor target, or public status-table row outside the supported set
- **THEN** validation identifies the unsupported agent and fails

#### Scenario: Structured support surfaces disagree
- **WHEN** a Hatch source or target is missing or changed, or a public status differs from its adapter descriptor
- **THEN** validation identifies the affected adapter and surface and fails

### Requirement: Thin adapter contract
Adapters MUST reference, link, or mechanically mirror canonical skills and MUST NOT independently redefine lifecycle semantics. Released skills and adapters MUST use only the public CLI contract supported by their corresponding installed SDR version, and compatibility validation MUST detect unavailable commands, options, or structured-output behavior without invoking an agent runtime.

#### Scenario: Compare an adapter with canonical skills
- **WHEN** integration consistency is validated
- **THEN** lifecycle semantics and public commands are equivalent
- **THEN** differences are limited to platform discovery, installation, and invocation

#### Scenario: Skill and CLI versions are incompatible
- **WHEN** an adapter invokes behavior absent from its corresponding CLI version
- **THEN** validation identifies the reference and rejects compatibility

### Requirement: Portable and honest integration metadata
Adapters MUST use public commands, portable paths, distinct source and research roots, and version-identifiable public acquisition targets. Each adapter MUST declare `verified`, `documented`, or `experimental` with sufficient evidence. `verified` MUST require recorded host E2E using publicly acquired version-matched skills and the installed CLI; `documented` MUST NOT imply such an E2E run.

#### Scenario: Validate integration metadata
- **WHEN** an adapter references a missing skill, obsolete command, private path, conflated root, unpublished acquisition, or unsupported status evidence
- **THEN** validation identifies the adapter and fails

#### Scenario: Adapter has documentation but no host E2E
- **WHEN** official discovery documentation and deterministic checks pass without host E2E
- **THEN** the adapter may be `documented` but MUST NOT claim `verified`

#### Scenario: Adapter is declared verified
- **WHEN** an adapter declares `verified`
- **THEN** evidence identifies agent version, SDR version, acquisition identity, environment, discovery, and successful installed-CLI lifecycle use

#### Scenario: Host E2E runs in a sandbox
- **WHEN** a supported host requires isolated execution for E2E validation
- **THEN** the sandbox provides the installed SDR CLI and version-matched skills without using real user configuration
- **THEN** evidence records host version, SDR version, acquisition identity, environment, discovery, and lifecycle result
- **THEN** sandbox execution alone does not justify `verified` unless the complete host E2E succeeds

## ADDED Requirements

### Requirement: Version-identifiable public acquisition
The canonical skill set and supported adapters MUST be obtainable from a public target identified by SDR release version and immutable source revision or artifact digest. The installed `sdr integrations install --destination PATH` console command MUST be the primary package-resource installation interface so tool-isolated installations do not depend on ambient Python resolution. The `python -m sdr.integration_validation install` command MUST remain available for compatibility. Guidance MUST NOT require private paths, unpublished artifacts, or only a mutable default branch.

#### Scenario: Acquire integrations for a released CLI
- **WHEN** an operator selects a released SDR version
- **THEN** public acquisition provides all canonical skills and adapter metadata for that version
- **THEN** the operator can verify correspondence with the installed CLI

#### Scenario: Acquisition is not version-identifiable
- **WHEN** guidance references only a mutable, private, or unpublished source
- **THEN** validation reports the contract incomplete and it is not represented as reproducible

#### Scenario: Install integrations from an isolated tool environment
- **WHEN** a user installs SDR with `uv tool install .` and runs the installed `sdr integrations install --destination PATH` command outside the source checkout
- **THEN** all seven canonical skills are installed from package resources without relying on an ambient `python` command
- **THEN** conflicts remain all-or-nothing and installation does not read `SDR_ROOT` or write agent configuration

### Requirement: Distinct framework and research roots
The integration contract MUST reserve `SDR_ROOT` for CLI research storage. Framework checkout, package resource, or acquisition locations MUST be described and passed separately and MUST NOT be called `SDR_ROOT`.

#### Scenario: Install skills with a custom research root
- **WHEN** an operator configures `SDR_ROOT` and installs skills from a separate acquisition
- **THEN** installation reads only from the explicit acquisition source
- **THEN** lifecycle artifacts remain under the configured research root

#### Scenario: Instructions conflate roots
- **WHEN** integration instructions use `SDR_ROOT` as framework source
- **THEN** validation rejects the ambiguous public installation contract
