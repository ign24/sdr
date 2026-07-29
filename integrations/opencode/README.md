# OpenCode

Status: `documented`. OpenCode's official documentation confirms native Agent
Skills discovery. The [sanitized canary evidence](../canary-evidence.json)
records pure local discovery without model invocation; no host E2E is asserted.

This is the public SDR adapter. It uses the native `skill` tool and does not
depend on a selected model, private configuration, MCP server, or plugin.
OpenCode discovers project skills at `.opencode/skills` and user skills at
`~/.config/opencode/skills`.

Install the canonical skills packaged with the current SDR version into the
current project:

```bash
sdr integrations install --destination .opencode/skills
```

The installer is scoped to the destination passed by the operator, creates no
agent configuration, and refuses to overwrite existing skills. OpenCode exposes
the seven skill descriptions and loads a `SKILL.md` through its native tool only
when selected. Use `sdr-new` to start or `sdr-status` to inspect work. Workflow
details remain in the installed skill files. `SDR_ROOT` configures only research
storage and is not read by skill installation.

Official source: <https://opencode.ai/docs/skills/>
