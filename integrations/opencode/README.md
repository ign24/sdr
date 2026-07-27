# OpenCode

Status: `documented`. OpenCode's official documentation confirms native Agent
Skills discovery; no local-agent E2E is asserted here.

This is the public SDR adapter. It uses the native `skill` tool and does not
depend on a selected model, private configuration, MCP server, or plugin.
OpenCode discovers project skills at `.opencode/skills` and user skills at
`~/.config/opencode/skills`.

Install into the current project with links to the canonical source:

```bash
python -m sdr.integration_validation install "$SDR_ROOT" --destination .opencode/skills
```

The installer is scoped to the destination passed by the operator, creates no
agent configuration, and refuses to overwrite existing skills. OpenCode exposes
the seven skill descriptions and loads a `SKILL.md` through its native tool only
when selected. Use `sdr-new` to start or `sdr-status` to inspect work. Workflow
details remain solely in `$SDR_ROOT/skills/sdr-*/SKILL.md`.

Official source: <https://opencode.ai/docs/skills/>
