# Root topology migration — Trigger 3

## Target

The intended human-facing repository root is:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

This branch creates the three layered entry directories. It deliberately does **not** rewrite `README.md` and does not bulk-move existing root files yet.

## Why the root is not bulk-cleaned in one blind pass

The current root contains technical files that may be referenced by:

- source code;
- CI/workflows;
- repository instructions;
- historical evidence links;
- scripts that use fixed relative paths;
- external tooling or users whose references are not visible from filename inspection alone.

Moving those files without dependency classification could make the repository prettier while making the system less reproducible. Trigger 3 requires the opposite: better navigation **and** preserved causal/evidence lineage.

## Migration invariant

A move is acceptable only when all of the following are true:

1. source bytes are preserved unless an intentional edit is separately evidenced;
2. old path references are found and either updated or explicitly retained through a compatibility mechanism;
3. runtime-critical path assumptions are tested;
4. historical evidence keeps the old path/commit identity it originally cited;
5. no second authority copy is created;
6. current authority files remain discoverable from the no-scan AI entry path;
7. root README remains untouched unless explicitly requested in that user turn.

## Classification buckets

Each current root path should be classified into exactly one migration bucket:

| Bucket | Action |
|---|---|
| `PUBLIC_ENTRY` | Remain in the public root target. |
| `RUNTIME_PINNED` | Keep current path until a verified compatibility migration exists. |
| `REPOSITORY_TECHNICAL` | Move under `DEV_SOURCE_RESEARCH/repository/`. |
| `RESEARCH_SOURCE` | Move/link into the relevant technical research subtree only if lineage remains exact. |
| `HISTORICAL_EVIDENCE` | Preserve original identity; index it rather than rewriting history. |
| `GENERATED_METRIC` | Move only after writers/readers are updated and a regeneration test passes. |
| `UNKNOWN` | Do not move. Find references first. |

## Safe move protocol

For each batch:

```text
1. capture base main SHA
2. capture exact file SHA / bytes
3. search code + workflows + docs for the old path
4. classify every reference
5. create destination with byte-identical content
6. update current-facing references that are allowed to move
7. run source/link/path regressions
8. delete old path only after step 7 passes
9. verify destination bytes == original bytes
10. record commit + scope + exceptions in the evidence index
```

Do not use “Git says renamed” as sufficient evidence. Verify the bytes and references.

## Priority order

1. obvious standalone documentation/metrics that have no runtime readers;
2. generated dashboards only after their writers are identified;
3. repository instructions only after host-specific discovery behavior is verified;
4. source/config paths last, with exact regression coverage.

## Current status of this branch

`PARTIAL_TARGET_LAYER_CREATED_ROOT_MIGRATION_NOT_COMPLETE`

Completed:

- `HUMAN_READ_THIS/README.md`
- `DEV_SOURCE_RESEARCH/README.md`
- `AI_START_HERE_DO_NOT_SCAN_REPO/README.md`
- machine-readable Trigger-3 evidence index
- this migration protocol

Not completed:

- root technical-file inventory;
- reference graph for every root path;
- byte-identical batch moves;
- full link/path regression;
- final four-entry public root.

The next correct step is an evidence-producing root inventory, not mass deletion.
