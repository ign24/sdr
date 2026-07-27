# Evidence Model

SDR separates declared research content from deterministic validation records.
This separation makes gaps visible without claiming that automation can judge
the truth of a recommendation.

## Artifacts

- `brief.md` defines the question and criterion IDs.
- `notes/*.md` declare sources and contain cited exploration.
- local snapshots preserve text used for deterministic matching.
- `probe/results.md` maps every criterion to a result and reproducible evidence.
- probe files provide executable or inspectable evidence.
- `decision-memo.md` connects results, alternatives, limitations, and a ring.
- `assets/*.md` package a reusable output.
- `sdr.yaml` stores CLI-managed lifecycle and validation metadata.

## Validation controls

The public controls are **Structural**, **Evidential**, **Textual anchoring**,
**Executable**, **Hash consistency**, and **HITL**.

Structural validation checks schemas, required files, frontmatter, and sections.
Evidential validation checks source declarations, dates, tiers, triangulation,
criterion references, artifact paths, and reproducibility declarations.

Textual anchoring extracts factual claims ending in `[S<n>]` and matches them
against local source snapshots. `[cf. S<n>]` validates the source reference but
does not create a claim and does not enter textual matching. The matcher does
not use models. A human-reviewed exception is explicit and scoped to the current
claim identity.

Executable validation runs an explicitly declared probe action and persists its
output, result, and current probe hash. Hash consistency detects changes after a
stage or probe was validated. HITL approval records who approved the current
decision memo and when.

## Offline semantics

Offline mode skips outbound link checks and automatic snapshot capture. A
skipped check is reported as skipped, not passed. Previously captured local
snapshots can still be matched. Offline mode does not relax structure,
criterion coverage, executable evidence, consistency, or approval requirements.

## Context Graph

The Context Graph is a deterministic, derived view over selected criteria,
sources, results, decisions, and optional external references. It is useful for
coverage warnings, traces, exports, and queries. It is non-blocking and not
complete lineage: absence from the graph is not proof that a relationship does
not exist, and graph success is not an `advance` gate.

## Confidence boundaries

A passing gate means the declared contract passed. It does not mean a source is
accurate, a benchmark is representative, an executable is benign, or a human
decision is correct. Those judgments require review outside deterministic checks.
