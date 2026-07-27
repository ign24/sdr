---
name: sdr-reuse
description: >
  Convert an approved SDR decision into reusable assets. Use only in the
  mandatory reuse stage to create audience-specific material without overstating
  the recommendation or evidence.
---

# Produce reusable assets

## Enforce stage order

Read `research/<slug>/sdr.yaml` first and require `stage: reuse` with an active
status. If the stage differs, stop, route to the matching stage skill, and do not
create or modify stage artifacts. Reuse is required in both full and light mode.

## Read the decision and write one artifact family

Read `research/<slug>/decision-memo.md`, its audience, recommendation ring,
risks, and next steps. Consult earlier evidence when needed for accuracy. Modify
only files under `research/<slug>/assets/`; do not change the memo, prior
artifacts, or `sdr.yaml`.

Every asset under `research/<slug>/assets/` must declare:

- `type`: `playbook` | `template` | `post` | `carousel` | `script` |
  `executive-summary` | `other`.
- `audience`: `internal` | `external`.

Keep each asset within the approved ring and evidence. This workflow creates the
asset but does not publish or distribute it.

## Reach a green gate and close

Run `sdr check <slug> --json`, correct only assets, and repeat until the command
returns exit code 0. Offer `sdr advance <slug>` to move the investigation to
`done`, then offer:

```bash
sdr index
sdr archive <slug>
```

Archive consolidates the completed investigation into the configured knowledge
base. It is also available for a `dropped` investigation.

## Backtracking

If asset production exposes unsupported claims or an invalid decision, use
`sdr reopen <slug> --to <intake|explore|probe|transfer> --reason "<reason>"`
instead of changing a validated earlier artifact.
