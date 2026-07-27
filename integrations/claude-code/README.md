# Claude Code

Status: `documented`. Official documentation confirms Agent Skills discovery,
but this repository does not claim an end-to-end check with a local Claude Code
binary.

Claude Code discovers project skills under `.claude/skills` and personal skills
under `~/.claude/skills`. It follows symlinked skill directories, so install the
canonical SDR skills into one explicit scope without copying their content:

```bash
python -m sdr.integration_validation install "$SDR_ROOT" --destination .claude/skills
```

Run the command from the consuming project. It creates only missing skill links
and refuses to overwrite an existing name. Use an absolute destination under
your home directory instead for personal scope. It does not edit settings,
permissions, credentials, or hooks.

Confirm discovery with Claude Code's skill list, then invoke `sdr-new` for a new
investigation or `sdr-status` for an existing one. The instructions and current
CLI commands remain defined only in `$SDR_ROOT/skills/sdr-*/SKILL.md`.

Official source: <https://code.claude.com/docs/en/skills>
