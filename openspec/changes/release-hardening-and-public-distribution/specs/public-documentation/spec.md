## MODIFIED Requirements

### Requirement: English human guide
`README.md` MUST explain SDR's purpose, evidence model, approval boundaries, lifecycle, modes, commands, safety limitations, integrations, and contribution paths. It MUST provide or link to current English guidance for public installation, supported environments, release verification, security reporting, release and source provenance, and integration acquisition and compatibility.

#### Scenario: Onboard an English-speaking user
- **WHEN** a user opens `README.md`
- **THEN** they can install a released distribution and execute a minimal supported lifecycle
- **THEN** they can locate compatibility, verification, security, provenance, and integration guidance
- **THEN** supported behavior is distinguished from limitations

### Requirement: Spanish human guide
`README.es.md` MUST provide Spanish guidance equivalent in commands, lifecycle behavior, installation, compatibility, release verification, security reporting, provenance, integrations, limitations, and safety boundaries. Both entry points MUST link to each other.

#### Scenario: Onboard a Spanish-speaking user
- **WHEN** a user opens `README.es.md`
- **THEN** its public contract has equivalent scope to the English guide
- **THEN** no supported prerequisite or safety limitation exists in only one language

### Requirement: Deterministic bilingual parity
Documentation checks MUST compare commands, stages, modes, installation sources, compatibility claims, release-verification steps, security routes, provenance statements, integration acquisition and status, links, limitations, and warnings across English and Spanish without requiring line-by-line translation.

#### Scenario: One language changes a supported contract alone
- **WHEN** a covered public concept changes in only one language
- **THEN** parity validation fails with the subject and language identified

#### Scenario: Equivalent prose uses different wording
- **WHEN** both languages express equivalent behavior and limitations differently
- **THEN** parity validation succeeds

### Requirement: Evidence-backed claims
Public documentation MUST describe only behavior supported by current identifiable evidence. Installation, compatibility, release, provenance, and integration claims MUST map to the corresponding public artifact, environment, source revision, digest, or validation record. Documentation MUST NOT present hashes, retrieval, textual matching, or integration metadata as proof beyond their stated confidence boundary.

#### Scenario: A public claim lacks validation
- **WHEN** a claim cannot be mapped to current applicable evidence
- **THEN** it is removed, narrowed, or identified as unverified before release

#### Scenario: Evidence becomes stale
- **WHEN** supporting evidence is missing, stale, or applies to another artifact or environment
- **THEN** documentation readiness fails and identifies the affected claim

## ADDED Requirements

### Requirement: Public release verification guidance
English and Spanish public documentation MUST explain how to identify a release, obtain its artifacts and digests, associate it with an immutable source revision, inspect available provenance, and understand the limits of those records.

#### Scenario: Verify a public release
- **WHEN** a user follows either language's verification guidance
- **THEN** they can identify the release and source revision
- **THEN** they can compare artifacts with published digests
- **THEN** they can distinguish integrity and traceability from correctness or truth

### Requirement: Source provenance guidance
English and Spanish guidance MUST distinguish the declared source URL, final retrieval location, redirect and HTTP outcome, capture metadata, persisted content hash, textual anchoring, publisher identity, and factual truth.

#### Scenario: Interpret captured-source evidence
- **WHEN** a user reads source-provenance guidance
- **THEN** they understand what was requested, retrieved, persisted, and matched
- **THEN** they are warned that these records do not authenticate the publisher or prove truth

### Requirement: Operational security and integration guidance
English and Spanish documentation MUST identify the same private security-reporting route and describe only the supported Claude Code, Codex, and OpenCode integrations, including version-identifiable acquisition, compatible CLI contract, distinct research and framework locations, and evidence represented by integration status.

#### Scenario: Follow public operational guidance
- **WHEN** a user follows either language's security or integration instructions
- **THEN** the route or acquisition is real, public where appropriate, version-identifiable, and equivalent between languages
- **THEN** no instruction conflates framework source with the research root
