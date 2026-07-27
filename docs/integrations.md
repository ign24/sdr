# Integrations

SDR integrations expose the seven canonical Agent Skills to external coding
agents. They do not change the deterministic CLI contract.

## Status

| Adapter | Discovery approach | Status | Local E2E claimed? |
| --- | --- | --- | --- |
| Claude Code | Project or user Agent Skills links | `documented` | No |
| Codex | Repository or user Agent Skills links | `documented` | No |
| Hermes Agent | `skills.external_dirs` | `documented` | No |
| OpenClaw | Workspace skill installation | `documented` | No |
| OpenCode | Project or user Agent Skills links | `documented` | No |

`documented` means official discovery behavior and installation instructions
have been recorded and adapter metadata is validated. It does not mean the
project executed a local end-to-end session with that agent.

## Canonical skills

The source of truth is `skills/sdr-new`, `sdr-intake`, `sdr-explore`,
`sdr-probe`, `sdr-transfer`, `sdr-reuse`, and `sdr-status`. Adapters must link,
install, or reference those directories. Do not copy and modify skill content in
an integration because copies drift from stage guards and CLI behavior.

## Validation and installation

Inspect each `integrations/<agent>/README.md` and `adapter.yaml` before installing.
Where the generated validator is supported:

```bash
python -m sdr.integration_validation validate .
python -m sdr.integration_validation install . --destination PATH_TO_SKILLS
```

The installer creates missing links and refuses to overwrite conflicts. It does
not write credentials, hooks, permissions, or general agent configuration.
Agent platforms and linked skill directories remain separate trust boundaries.

## Runtime contract

An agent should read `sdr status <slug> --json`, select the skill matching the
current stage, run `sdr check <slug> --json`, and obey stage guards. The CLI,
not the adapter or agent model, determines whether evidence can advance.
