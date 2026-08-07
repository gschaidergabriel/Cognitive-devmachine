# Goodman Anti-Echo Protocol — FRANK ↔ ClayCode

## Purpose

The FRANK and ClayCode branches are deliberately coupled, but they must not manufacture confidence by citing each other recursively. This protocol treats circular agreement as lineage, not replication.

## Core rule

A claim does **not** gain evidential strength merely because it travels through:

`FRANK -> ClayCode -> FRANK`, `Clay -> FRANK -> ClayCode`, or any longer descendant chain sharing the same originating source/experiment.

Shared ancestry is collapsed into one evidence family. Re-expression, reformulation, implementation in ClayCode, or repetition by another RAE worker is not independent confirmation.

## Mandatory ClayCode review of FRANK

Every `claycode` trigger must inspect the newest FRANK research material, including the latest available `FRANK_ARCHITECTURE.claycode.json` and `CLAYCODE_ARCHITECTURE_MAPPING.md` when they exist, plus newer FRANK reports, Topic Packets and micro-packets.

For every FRANK-derived architecture assumption that materially affects ClayCode, create an entry in:

`research_entity/trigger_runs/claycode/<run_id>/FRANK_CLAYCODE_GOODMAN_REVIEW.json`

Each entry must receive exactly one verdict:

- `SUPPORTED` — independently supported and retained;
- `REFINED` — core survives but scope/semantics change;
- `REFUTED` — contradicted strongly enough to reject in ClayCode;
- `UNRESOLVED` — insufficient independent evidence; keep open, do not silently absorb.

## Goodman filter

Before `SUPPORTED` or `REFINED` is allowed, the worker must perform all of the following:

1. **Ancestry collapse** — identify the source/experiment ancestry and collapse descendants of the same evidence into one family.
2. **Independent check** — seek at least one source, executable experiment, target-runtime observation, or counterexample search whose evidential ancestry is independent of the FRANK↔ClayCode loop. If unavailable, verdict cannot exceed `UNRESOLVED` unless a genuinely new discriminating experiment is executed in the current run.
3. **Counterhypothesis** — state a plausible competing explanation/design.
4. **Falsifier** — state what result would overturn the favored interpretation.
5. **Adversarial test** — actively search for a failure case, boundary condition, hidden dependency, stale assumption or cost reversal.
6. **Evidence-class preservation** — synthetic/proxy FRANK evidence remains synthetic/proxy when used by ClayCode; it cannot become live evidence through reuse.
7. **No popularity vote** — agreement of multiple workers/models sharing the same sources is not independent replication.

## Integration rule

- `SUPPORTED`: may be incorporated into ClayCode with original evidence status and ancestry.
- `REFINED`: incorporate only the refined form; record what FRANK assumption changed and why.
- `REFUTED`: create/preserve a negative result or supersession link and do not implement the rejected assumption as canonical ClayCode semantics.
- `UNRESOLVED`: may remain an explicit hypothesis/optional branch, but cannot be silently baked into the semantic IR as established truth.

## Reverse write-back

ClayCode must write its verdicts back into the research mesh so the next FRANK run can see which parts of its architecture were supported, narrowed, rejected or remain unresolved. FRANK must not count ClayCode's review as independent evidence when ClayCode only reused FRANK's ancestry; only the independent evidence/test recorded by the review may add support.

## Required review fields

Each review item must contain at least:

- `claim_id`
- `frank_statement`
- `frank_source_refs`
- `ancestry_families`
- `shared_ancestry_collapsed: true`
- `counterhypothesis`
- `falsifier`
- `independent_checks[]`
- `adversarial_checks[]`
- `verdict`
- `reason`
- `claycode_action`
- `affected_claycode_artifacts[]`

The review file also records `latest_frank_run`, the latest available FRANK ClayCode architecture artifact (or explicit `null` if none yet), and the ClayCode run id.

## Scientific boundary

This filter is an anti-circularity rule, not a guarantee that the surviving claim is true. Independent support may still be weak, confounded or wrong; evidence quality and falsifiability remain decisive.
