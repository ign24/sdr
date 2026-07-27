# Hermes Agent

Adapter id: `hermes`. Product: `NousResearch/hermes-agent`.

Status: `documented`. Official `NousResearch/hermes-agent` documentation
confirms Agent Skills and `skills.external_dirs`; no local Hermes E2E is
claimed.

Hermes stores local skills under `~/.hermes/skills` and can scan canonical
skills in place through an external directory. Merge this key into the active
profile's `config.yaml` without replacing any existing settings:

```yaml
skills:
  external_dirs:
    - ${SDR_ROOT}/skills
```

Export `SDR_ROOT` to the checked-out SDR repository before starting Hermes.
Preserve any existing `skills` keys and `external_dirs` entries. This adapter
does not write credentials, add `.hermes.md`, install a runtime plugin, or pin a
model. If the shared canonical directory must be immutable to Hermes, enforce
that with filesystem permissions because external directories are not a write
protection boundary.

Start a new session, use `/skills` to confirm discovery, and invoke the relevant
`sdr-*` skill. The lifecycle remains solely in the canonical `SKILL.md` files.

Official source:
<https://hermes-agent.nousresearch.com/docs/user-guide/features/skills>
