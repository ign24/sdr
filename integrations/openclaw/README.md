# OpenClaw

Status: `documented`. The `openclaw/openclaw` documentation confirms Agent
Skills, workspace discovery, managed installs, and binary gating. No local
OpenClaw E2E is claimed.

Prerequisite: install the SDR package so the `sdr` binary is on the host `PATH`.
If OpenClaw runs tools in a sandbox, the same binary must be available there.

OpenClaw discovers skills from `<workspace>/skills`,
`<workspace>/.agents/skills`, `~/.agents/skills`, and `~/.openclaw/skills`. For
a workspace-scoped installation, install each canonical directory with
OpenClaw's local installer:

```bash
openclaw skills install "$SDR_ROOT/skills/sdr-new" --as sdr-new
openclaw skills install "$SDR_ROOT/skills/sdr-intake" --as sdr-intake
openclaw skills install "$SDR_ROOT/skills/sdr-explore" --as sdr-explore
openclaw skills install "$SDR_ROOT/skills/sdr-probe" --as sdr-probe
openclaw skills install "$SDR_ROOT/skills/sdr-transfer" --as sdr-transfer
openclaw skills install "$SDR_ROOT/skills/sdr-reuse" --as sdr-reuse
openclaw skills install "$SDR_ROOT/skills/sdr-status" --as sdr-status
openclaw skills check
```

Review existing workspace skill names first; do not replace a conflicting skill.
This deployment uses only Agent Skills and the SDR executable. It does not ship
or require an OpenClaw runtime plugin, hooks, credentials, or project config.
The canonical workflow remains under `$SDR_ROOT/skills/`; reinstall from that
source to refresh a deployed workspace copy.

Official source: <https://docs.openclaw.ai/tools/skills>
