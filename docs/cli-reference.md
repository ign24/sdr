# CLI Reference

The research root defaults to `research/` and can be changed with `SDR_ROOT`.
The knowledge directory defaults to `knowledge/` and can be changed with
`SDR_KNOWLEDGE`. Prefer `--json` for automation when the command offers it.

## Lifecycle commands

| Command | Guard and result | Side effects |
| --- | --- | --- |
| `sdr new SLUG --title TEXT --question TEXT [--mode full|light]` | Requires a new safe slug; starts at intake. | Creates metadata and brief; commits unless `--no-commit`. |
| `sdr check SLUG [--stage STAGE] [--offline] [--json]` | Evaluates structural/evidential rules and consistency. | May capture missing explore snapshots; never advances or commits. |
| `sdr check --all [--offline] [--json]` | Checks active investigations. | Same network behavior as single check. |
| `sdr advance SLUG [--offline]` | Current-stage gates, required verification, hashes, and approval must pass. | Changes metadata; commits unless `--no-commit`. Never runs the probe command. |
| `sdr reopen SLUG --to STAGE --reason TEXT` | Destination must be an earlier stage in the selected mode. | Records reason, invalidates later hashes, reactivates done work, commits unless `--no-commit`. |
| `sdr drop SLUG --reason TEXT` | Active work can be discarded explicitly. | Preserves evidence and commits unless `--no-commit`. |
| `sdr archive SLUG` | Requires `done` or `dropped`. | Writes a knowledge summary, marks archived, commits unless `--no-commit`. |
| `sdr migrate SLUG [--json]` | Migrates legacy schema metadata without changing stage. | Assigns source IDs, may fetch snapshots, and writes metadata. |

## Evidence commands

| Command | Purpose | Important behavior |
| --- | --- | --- |
| `sdr snapshot SLUG [--json]` | Capture declared explore sources. | Performs bounded outbound HTTP requests and writes local snapshots. |
| `sdr verify-claims SLUG [--json]` | Match current factual claims against local snapshots. | Deterministic and model-free; writes verification evidence. |
| `sdr resolve-claim SLUG CLAIM_ID --reason TEXT [--by NAME]` | Record human review of one current unresolved claim. | Scoped to claim identity; does not approve transfer. |
| `sdr verify-probe SLUG [--timeout SECONDS] [--json]` | Execute the declared probe runner and persist its result. | Requires `verify.action: run`; runs argv without a shell in `probe/`. |
| `sdr approve SLUG [--by NAME] [--offline]` | Approve the current transfer memo. | Transfer-only stage guard; writes approval metadata. |

## Reporting commands

| Command | Result |
| --- | --- |
| `sdr status [SLUG] [--json]` | Current stage, status, gate summary, timebox, and audit markers. Status uses an offline gate view, so network checks are skipped. |
| `sdr index` | Regenerates `research/INDEX.md`. |
| `sdr doctor [--json]` | Reports local readiness and deprecated environment variables. |

## Context commands

`sdr context build`, `inspect`, `trace`, `check`, `export`, and `query` operate
on a derived Context Graph. `check --strict` can return a failure for graph
warnings when explicitly invoked. Context commands remain auxiliary and
non-blocking: lifecycle `advance` does not call them, and the graph is not
complete lineage.

## Retired command

`sdr judge` is a tombstone that exits with guidance. Use `verify-claims` for
deterministic anchoring and `resolve-claim` for scoped human review.

## Git behavior

`new`, `advance`, `reopen`, `drop`, and `archive` attempt focused transition
commits. They preserve pre-existing staging state, but operators should still
inspect the worktree. Use `--no-commit` when running in CI, an agent-managed
repository, or any workflow where another tool owns history.
