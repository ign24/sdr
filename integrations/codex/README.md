# Codex

Status: `documented`. Official Codex documentation confirms repository and user
Agent Skills discovery. The [sanitized canary evidence](../canary-evidence.json)
records a local no-model discovery diagnostic, not a host-driven SDR lifecycle.

Codex scans `.agents/skills` from the current directory through the repository
root and also scans `~/.agents/skills`. Install the canonical SDR skills into a
repository scope with the generated, test-covered mechanism:

```bash
sdr integrations install --destination .agents/skills
```

The installer copies the packaged canonical skill bytes, refuses to overwrite
existing names, and does not create hooks, project configuration, credentials,
or trust-dependent files. `SDR_ROOT` configures only research storage and is not
read by installation. The later root `AGENTS.md` may explain repository-wide
policy, but it is not needed for skill discovery and is intentionally absent.

After discovery, select a skill with Codex's skills interface. Lifecycle and CLI
instructions remain exclusively in each canonical `SKILL.md`.

Official source: <https://developers.openai.com/codex/build-skills/>
