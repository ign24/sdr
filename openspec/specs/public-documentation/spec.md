## Purpose

Define audience-specific, bilingual, test-backed documentation for people who operate SDR and agents
that contribute to or execute the framework.

## Requirements

### Requirement: English human guide
`README.md` MUST explain purpose, installation, quickstart, lifecycle stages, modes, evidence,
approval, main commands, integrations, safety boundaries, limitations, and contribution paths.

#### Scenario: Onboard an English-speaking user
- **WHEN** a user opens `README.md`
- **THEN** they can install SDR and identify the steps of a minimal supported lifecycle

### Requirement: Spanish human guide
`README.es.md` MUST provide equivalent supported commands, lifecycle behavior, limitations, and
safety guidance in Spanish, and both READMEs MUST link to each other.

#### Scenario: Onboard a Spanish-speaking user
- **WHEN** a user opens `README.es.md`
- **THEN** its installation and lifecycle commands match the English contract
- **THEN** the English guide is directly reachable

### Requirement: Deterministic bilingual parity
Documentation checks MUST compare public commands, stages, modes, integrations, compatibility,
links, and security warnings across both READMEs without requiring line-by-line translation.

#### Scenario: One README changes a command alone
- **WHEN** a supported command changes in only one language
- **THEN** parity validation fails with an actionable difference

### Requirement: Agent repository instructions
`AGENTS.md` MUST concisely identify sources of truth, contribution workflow, tests, canonical skills,
security constraints, Git constraints, and prohibited content for agents.

#### Scenario: An agent starts framework work
- **WHEN** the agent reads the root instructions
- **THEN** it can locate runtime code and required validations
- **THEN** it is instructed not to stage, commit, copy private material, or use destructive Git actions without authorization

### Requirement: Audience separation
Human operation guidance MUST remain usable without agent tooling, while agent-specific repository
constraints MUST not replace the human CLI documentation.

#### Scenario: A person operates SDR directly
- **WHEN** no agent integration is installed
- **THEN** the READMEs and detailed docs are sufficient to use the supported CLI

### Requirement: Evidence-backed claims
Public documentation MUST describe only tested behavior, identify probe verification as explicit
execution of user-controlled code, and avoid claims of semantic truth or stable internal APIs.

#### Scenario: A public claim lacks validation
- **WHEN** documentation review cannot map a behavior claim to implementation or a release check
- **THEN** the claim is removed or validation is added before release

### Requirement: Privacy-safe documentation examples
Documentation examples MUST use synthetic identities, reserved domains, repository-relative paths,
and invented results.

#### Scenario: Scan public prose
- **WHEN** documentation and examples are audited
- **THEN** no credentials, private paths, real investigation data, or unpublished endpoint appears
