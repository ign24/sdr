# Codex

Status: `documented`. Official Codex documentation confirms repository and user
Agent Skills discovery; no installed Codex binary is required by this adapter's
automated checks.

Codex scans `.agents/skills` from the current directory through the repository
root and also scans `~/.agents/skills`. Install the canonical SDR skills into a
repository scope with the generated, test-covered mechanism:

```bash
python -m sdr.integration_validation install "$SDR_ROOT" --destination .agents/skills
python -m sdr.integration_validation validate "$SDR_ROOT"
```

The installer creates symlinks to `$SDR_ROOT/skills/sdr-*`, refuses to overwrite
existing names, and does not create hooks, project configuration, credentials,
or trust-dependent files. The later root `AGENTS.md` may explain repository-wide
policy, but it is not needed for skill discovery and is intentionally absent
from this adapter.

After discovery, select a skill with Codex's skills interface. Lifecycle and CLI
instructions remain exclusively in each canonical `SKILL.md`.

Official source: <https://developers.openai.com/codex/build-skills/>
