# Spec-Driven Research

Spec-Driven Research (SDR) is a local CLI for turning an open research question
into reviewable evidence and an explicit decision. It gives each investigation a
fixed lifecycle, validates required artifacts, and records when evidence changes.
It is designed for people who need repeatable applied research rather than an
unstructured folder of notes.

Read this documentation in [Español](README.es.md). The English and Spanish
guides are maintained against the same semantic parity checks.

## What SDR solves

SDR helps a team:

- frame a falsifiable question and measurable criteria before researching;
- distinguish sourced exploration from executable validation;
- preserve evidence, limitations, human review, and backtracking decisions;
- produce a decision memo and a reusable asset before closing the work;
- expose deterministic JSON results to humans, scripts, and coding agents.

SDR is not a source-of-truth database, a web crawler, an agent runtime, or a
guarantee that cited material is true. It validates declared structure and local
evidence. People remain responsible for source quality, safe execution, and the
final recommendation.

## Requirements and installation

SDR requires Python 3.12 or newer.

Install the checked-out project as an isolated tool with `uv`:

```bash
uv tool install .
sdr --help
```

For project development, create the locked environment instead:

```bash
uv sync --all-extras --dev
uv run sdr --help
```

Install from the checked-out project with `pip`:

```bash
python -m pip install .
sdr --help
```

Snapshot extraction is optional. A source checkout can install it with
`python -m pip install '.[snapshot]'`.

## Quickstart

Run this in a Git repository. By default, lifecycle transitions create focused
Git commits. Add `--no-commit` to state-changing commands when you do not want
that side effect.

```bash
sdr new example-study \
  --title "Evaluate a data export approach" \
  --question "Which approach meets the stated reliability and maintenance criteria?" \
  --mode full \
  --no-commit
```

Edit `research/example-study/brief.md`, preserving its frontmatter and required
sections. Then validate and inspect machine-readable output:

```bash
sdr check example-study --json
sdr advance example-study --no-commit
sdr status example-study --json
```

At each later stage, fill the generated artifact, run the stage-specific
verification where applicable, run `check`, and then run `advance`. See the
[workflow guide](docs/workflow.md) for a complete walkthrough.

## Lifecycle and modes

The five stages are:

| Stage | Purpose | Primary evidence |
| --- | --- | --- |
| `intake` | Define the question, hypothesis, scope, criteria, and adoption risks. | `brief.md` |
| `explore` | Compare alternatives using dated, tiered, traceable sources. | `notes/*.md` and snapshots |
| `probe` | Test the criteria with reproducible code or commands. | `probe/results.md` and `probe/` artifacts |
| `transfer` | Make an evidence-backed recommendation for a named audience. | `decision-memo.md` |
| `reuse` | Package at least one reusable output. | `assets/*.md` |

Full mode follows `intake -> explore -> probe -> transfer -> reuse -> done`.
Light mode follows `intake -> explore -> transfer -> reuse -> done`. Light mode
omits `probe`; it does not make `reuse` optional. Use full mode when an
executable test is needed.

## Validation controls

SDR exposes these controls in conceptual evidence order: **Structural**,
**Evidential**, **Textual anchoring**, **Executable**, **Hash consistency**, and
**HITL** approval. `advance` checks stored hash consistency before running the
controls required by the current stage and mutating lifecycle state.

| Control | Command | Stage | Blocks `advance`? | What it establishes |
| --- | --- | --- | --- | --- |
| Structural | `sdr check` | All | Yes | Required files, frontmatter, sections, and stage rules exist. |
| Evidential | `sdr check` | Primarily explore/probe/transfer | Yes | Sources, criteria references, artifacts, and link policy meet deterministic rules. |
| Textual anchoring | `sdr verify-claims` | Explore | Yes | Factual `[S<n>]` claims match current local source snapshots or have explicit human resolution. |
| Executable | `sdr verify-probe` | Probe | Yes | A declared probe command ran successfully and matched `verify.expect`; the result hash is current. |
| Hash consistency | `sdr advance` and `sdr check` consistency reporting | Previously validated stages | Yes | Validated artifacts have not changed silently. |
| HITL | `sdr approve` | Transfer | Yes | A person approved the current decision memo. |
| Context Graph | `sdr context ...` | Any | No | Auxiliary coverage, relationships, exports, and deterministic queries. It is not complete lineage. |

`check` runs the structural and evidential gate for a selected stage. It may
capture missing explore snapshots unless `--offline` is used, but it never
advances the stage. `advance` orchestrates all blocking controls needed for the
current stage, persists a validation hash, changes stage, and may commit the
transition. `verify-claims` and `verify-probe` are explicit evidence-producing
steps; `advance` does not execute probe commands. `approve` is an explicit human
decision, not an automated quality score.

`[cf. S<n>]` is a contextual reference. It validates the declared source but
does not create a claim and does not enter textual matching. Textual anchoring
does not use models. `resolve-claim` records scoped human review for one current
claim identity; it does not replace or substitute transfer-level `approve`.

Offline mode skips network link checks and automatic snapshot capture. Skipped
checks remain reported as skipped, not passed. Existing local snapshots are
still required for textual matching:

```bash
uv run sdr check example-study --offline
```

The Context Graph is optional and non-blocking. It summarizes selected
relationships but is neither complete lineage nor a prerequisite for
`advance`. See [Evidence model](docs/evidence-model.md) and
[Validation](docs/validation.md).

## Command overview

| Goal | Commands | Mutates files or state | Network | Git by default |
| --- | --- | --- | --- | --- |
| Create work | `sdr new` | Yes | No | Commit unless `--no-commit` |
| Validate a stage | `sdr check` | May capture explore snapshots | Link checks and snapshot capture unless offline | No |
| Capture and anchor sources | `sdr snapshot`, `sdr verify-claims`, `sdr resolve-claim` | Yes | `sdr snapshot` uses the network | No |
| Run a probe | `sdr verify-probe` | Executes a process and stores result metadata | Command-dependent | No |
| Advance or backtrack | `sdr advance`, `sdr reopen`, `sdr drop` | Yes | `sdr advance` may check links | Commit unless `--no-commit` |
| Approve transfer | `sdr approve` | Yes | Optional link checks | No |
| Report | `sdr status`, `sdr index`, `sdr doctor` | `sdr index` writes `research/INDEX.md` | No | No |
| Consolidate | `sdr archive` | Writes `knowledge/<slug>.md` | No | Commit unless `--no-commit` |
| Auxiliary graph | `sdr context build/inspect/trace/check/export/query` | Build/export write derived files | No | No |
| Migrate legacy metadata | `sdr migrate` | Yes | Captures declared sources | No |

Use `--json` where offered for stable structured output. The complete options,
guards, and side effects are listed in the [CLI reference](docs/cli-reference.md).

## Probe execution

Probe verification must explicitly declare `verify.action: run` and
`verify.expect` in `probe/results.md`. Prefer an `argv` list:

```yaml
verify:
  action: run
  argv: ["python", "verify.py"]
  expect: "PASS"
  environment: clean
```

SDR runs `argv` directly, without a shell, with `probe/` as the working
directory. A legacy `command` string is tokenized into arguments and is also
executed without a shell. This prevents shell expansion, but it does not make
the executable safe. Review every probe and prefer `environment: clean`.

## Archive and reopen

`sdr archive <slug>` accepts only `done` or `dropped` work, writes a concise
knowledge artifact, and marks the investigation archived. `sdr reopen <slug>
--to <stage> --reason <text>` moves backward only, records the reason,
invalidates affected validation hashes, and can reactivate `done` work.

Both commands create transition commits by default. Use `--no-commit` when the
operator, CI system, or host agent owns Git history.

## Agent integrations

The installed distribution provides package resources for Claude Code, Codex,
and OpenCode. Install all seven canonical skills into a project's discovery
directory with:

```bash
sdr integrations install --destination PATH_TO_SKILLS
```

| Agent | Project destination | Current status |
| --- | --- | --- |
| Claude Code | `.claude/skills` | `documented` |
| Codex | `.agents/skills` | `documented` |
| OpenCode | `.opencode/skills` | `documented` |

The installer copies byte-equivalent skill resources from the installed SDR
package; it does not depend on checkout paths. `SDR_ROOT` controls only research
storage and is not an integration source or installation destination.

`documented` means discovery guidance and deterministic adapter checks exist,
but no complete host E2E has been recorded. `verified` requires recorded,
version-matched host E2E discovery and installed-CLI lifecycle evidence.
`experimental` identifies an incomplete or provisional contract. All three
current adapters remain `documented`; none claims verified host E2E. See
[Integrations](docs/integrations.md).

## Security and limitations

Treat notes, snapshots, repositories, URLs, probe commands, and generated Git
changes as separate trust boundaries. SDR blocks non-public HTTP targets,
limits redirects and snapshot size, runs probes without a shell, and avoids
proxy environment variables for its own HTTP client. These controls do not
prove source truth, prevent a chosen executable from acting maliciously, scan
all secrets, or sandbox the host.

Keep credentials outside research artifacts. Review commands before execution,
inspect generated files before publication, and use least-privilege environments.
Read [Security model](docs/security-model.md) and [SECURITY.md](SECURITY.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the OpenSpec, TDD, quality, and public
content requirements. Agent contributors must also follow [AGENTS.md](AGENTS.md).
Maintenance checks are documented in [docs/validation.md](docs/validation.md).

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE).
