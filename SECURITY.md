# Security Policy

## Supported versions

Security fixes currently target the latest released 0.1.x version. Pre-release
and unreleased source snapshots receive fixes on a best-effort basis.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Contact the maintainer
privately through the security-reporting channel of the public hosting platform
once that repository is published. Until a public hosting and private reporting
channel exists, do not send sensitive exploit details; retain them and request a
private channel from the package distributor.

Include the affected version, impact, reproduction steps, and any suggested
mitigation. Remove credentials, personal data, private paths, and unrelated
research artifacts. Allow a reasonable remediation window before disclosure.

## Scope

Reports about path traversal, unsafe probe execution, SSRF or redirect handling,
secret exposure, package integrity, Git side effects, and validation bypasses
are in scope. Source misinformation and unsafe commands deliberately chosen by
an operator are normally trust-model limitations, but bypasses of documented
controls remain in scope.

See [docs/security-model.md](docs/security-model.md) for boundaries and limitations.

## Dependency vulnerability exceptions

There are no active exceptions. A dependency advisory fails the security gate by
default; CI does not carry an empty or pre-approved ignore list.

An exception is temporary risk acceptance, not a suppression convenience. Each
active exception must be added in a reviewed change and state the advisory ID,
affected dependency and version, justification, named owner, approval date,
expiration date, and compensating controls. The owner must remove or renew it
before expiration. Renewal requires current evidence and a new review; expired,
ownerless, or unjustified exceptions fail release readiness. Exception records
must not contain credentials, exploit payloads, or private paths.

Machine-readable records, when needed, use the required fields `owner`,
`justification`, `expires`, and `compensating controls`; `expires` is an ISO 8601
calendar date. No record is created until an actual advisory is accepted.
