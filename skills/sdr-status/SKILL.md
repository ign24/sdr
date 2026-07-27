---
name: sdr-status
description: >
  Inspect one or all SDR investigations, explain current gates and next
  workflows, and regenerate the reporting index. Use for status and consistency
  checks without producing stage artifacts.
---

# Inspect SDR status

This workflow must not create or modify stage artifacts. It may regenerate the
CLI-managed global index only when requested.

## Inspect one investigation

Run:

```bash
sdr status <slug> --json
sdr check <slug> --json
```

Report stage, mode, status, missing evidence, consistency failures, approval, and
the next matching skill: `sdr-intake`, `sdr-explore`, `sdr-probe`,
`sdr-transfer`, or `sdr-reuse`. Do not patch `sdr.yaml` to bypass a failed gate.

## Inspect all investigations

Run `sdr status --json`. Highlight active work, expired timeboxes, and terminal
`done` or `dropped` investigations. A stopped investigation should use
`sdr drop <slug> --reason "<reason>"`, not an unrecorded metadata edit.

When requested, run `sdr index`; never edit `research/INDEX.md` manually.

## Explain lifecycle actions

When evidence invalidates an earlier stage, direct the user to
`sdr reopen <slug> --to <stage> --reason "<reason>"`. Reopen must move backward
and preserves the audit trail. For any `done` or `dropped` investigation, offer
`sdr archive <slug>` to consolidate the evidence.
