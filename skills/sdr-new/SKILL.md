---
name: sdr-new
description: >
  Create a new Spec-Driven Research investigation and route it to the intake
  workflow. Use when a research question, technology evaluation, or spike does
  not yet have an SDR investigation.
---

# Create an SDR investigation

Use this workflow only when `research/<slug>/` does not already exist. Existing
investigations must continue with the skill for their current stage.

## Gather inputs

Confirm a falsifiable question, a short English kebab-case slug, title, owner,
timebox in days, and mode:

- `full`: `intake -> explore -> probe -> transfer -> reuse -> done`; required when
  a POC, benchmark, or demo is planned.
- `light`: `intake -> explore -> transfer -> reuse -> done`; there is no probe and
  the strongest permitted recommendation is `assess`.

Ask for missing required inputs rather than inventing them.

## Create and verify

Run the CLI with all agreed metadata so the CLI remains its owner:

```bash
sdr new <slug> --title "<title>" --question "<question>" --mode <full|light> --owner "<owner>" --timebox <days>
sdr status <slug> --json
```

The result must report `stage: intake` and `status: active`. Do not edit
`sdr.yaml` manually; use current CLI options and lifecycle commands for
CLI-managed metadata. Do not complete `brief.md` in this workflow.

Hand the investigation to `sdr-intake`. Reuse is required in both modes.

## Lifecycle exceptions

If the investigation cannot proceed, record the reason with
`sdr drop <slug> --reason "<reason>"`. A `done` or `dropped` investigation can be
consolidated with `sdr archive <slug>`; offer that command instead of copying its
evidence manually.
