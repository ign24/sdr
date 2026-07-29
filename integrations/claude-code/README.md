# Claude Code

Status: `documented`. Official documentation confirms Agent Skills discovery.
The [sanitized canary evidence](../canary-evidence.json) records only
filesystem installation for the tested binary because it exposed no offline
skill-introspection command; it does not claim host E2E.

Claude Code discovers project skills under `.claude/skills` and personal skills
under `~/.claude/skills`. Install the canonical SDR skills packaged with the
current SDR version into one explicit scope:

```bash
sdr integrations install --destination .claude/skills
```

Run the command from the consuming project. It creates only missing skill files
and refuses to overwrite an existing name. Use an absolute destination under
your home directory instead for personal scope. It does not edit settings,
permissions, credentials, or hooks.

Confirm discovery with Claude Code's skill list, then invoke `sdr-new` for a new
investigation or `sdr-status` for an existing one. `SDR_ROOT` configures only
research storage and is not read by skill installation.

Official source: <https://code.claude.com/docs/en/skills>
