# Trigger-3 repository topology migration

## Target

The intended public human-readable root is:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

Technical/archive material should progressively converge beneath `DEV_SOURCE_RESEARCH/repository/` or remain deep-linked from the curated layer until a safe history-preserving move is executed.

## Current Trigger-3 state

At snapshot base `0ec6784cf06a47d4a955b1cc38ef0f0e526ec30e`:

- `HUMAN_READ_THIS/README.md` exists;
- `DEV_SOURCE_RESEARCH/` did not yet exist on the base and is added by this tranche;
- `AI_START_HERE_DO_NOT_SCAN_REPO/` did not yet exist on the base and is added by this tranche;
- repository root still contains substantial historical/technical clutter;
- root `README.md` is intentionally **not rewritten** by this Trigger-3 organ because the trigger contract forbids silently changing it unless the user explicitly asks for README work in that turn.

## Why this tranche does not mass-move the root

A giant move looks tidy but can destroy useful information if done casually:

- links break;
- workflows/scripts use old paths;
- historical receipts bind exact paths/hashes;
- external references may point to old GitHub paths;
- compatibility code may import by path;
- concurrent workers may be changing the same files;
- Git can represent a rename heuristically, but application/runtime references still need validation.

So Trigger-3 uses **progressive convergence**:

1. create the three missing navigation/front-door layers;
2. create archive metadata and deep links;
3. inventory root entries and classify each move;
4. identify exact path consumers;
5. move only a bounded batch;
6. validate references/tests;
7. repeat.

## Move classes

Every root item should receive one class before relocation:

| Class | Meaning | Action |
|---|---|---|
| `PUBLIC_ROOT_KEEP` | Required public root surface. | Keep. |
| `MOVE_BYTE_IDENTICAL` | Technical/archive file with no intentional content change. | Move only; preserve bytes. |
| `MOVE_WITH_REFERENCE_REPAIR` | Move is safe only after import/link/workflow consumers are updated. | Atomic bounded move + reference repair + tests. |
| `HISTORICAL_PATH_PINNED` | Exact path is part of evidence/receipt/ABI or external reference. | Keep path or add explicit compatibility strategy; never silently rewrite history. |
| `GENERATED_OR_TRANSIENT` | Should not be a public-root authority. | Relocate/remove only under its owning policy. |
| `AUTHORITY_SURFACE` | Current governance/authority material. | Do not hide/move until all canonical readers are successor-safe. |
| `UNKNOWN` | Not enough evidence. | Leave in place. |

## Required invariant

For a `MOVE_BYTE_IDENTICAL` item:

```text
SHA256(before bytes) == SHA256(after bytes)
```

A path change can be intentional; a content change must be separately reviewed and evidenced.

## Reference-discovery gate

Before moving `old/path`, search at least:

```text
source imports
shell scripts
workflow YAML
Markdown links
JSON/YAML/TOML config
runtime path constants
receipts/manifests that bind exact paths
installer/hook settings
```

A search result is not automatically a blocker: historical prose may intentionally retain the old path. Classify consumers rather than global-replacing strings.

## Suggested bounded batches

### Batch 0 — completed by this curation branch

- create `DEV_SOURCE_RESEARCH/`;
- create `AI_START_HERE_DO_NOT_SCAN_REPO/`;
- add chronology/evidence/research notes;
- add machine-readable archive index;
- leave root README untouched;
- do not move technical source yet.

### Batch 1 — inventory only

Generate a machine-readable root inventory:

```json
{
  "path": "<root item>",
  "class": "UNKNOWN",
  "consumers": [],
  "authority_relevance": "unknown",
  "move_target": null,
  "byte_sha256": null
}
```

No moves in the same commit as the first inventory unless a path is trivially proven independent.

### Batch 2 — low-risk documentation/archive moves

Move only files classified `MOVE_BYTE_IDENTICAL` with no live consumers.

Verify:

- byte hash preserved;
- repository links repaired where current-facing;
- historical receipts unchanged;
- no workflow/runtime imports broken.

### Batch 3 — technical runtime/tooling paths

Do not mass-move active code. For each bounded subtree:

1. exact consumer graph;
2. branch move;
3. import/workflow/path update;
4. deterministic tests;
5. exact diff review;
6. merge only if no competing authority/path is created.

## No duplicate authorities

A curated copy of a technical file is dangerous if both old and new paths look canonical.

Prefer:

- deep link to original source;
- move with verified consumers;
- generated index metadata;

Avoid:

- copy/paste mirrors;
- “cleaned up” duplicates of authority JSON;
- a second database/effect journal just for the new directory structure;
- summaries that silently become newer truth than the source they summarize.

## Current concurrency warning

During this Trigger-3 invocation, `main` changed while inspection was in progress and another organ added `HUMAN_READ_THIS/README.md` directly to main. That is exactly why this tranche re-entered current `main` and avoided creating a duplicate human layer.

Future topology work must repeat that behavior: refresh `main`, inspect overlapping work, and converge rather than preserve authorship through duplicate lanes.

## Acceptance for the final root target

Do not declare topology PASS merely because only four visible root entries remain.

PASS also requires:

- current public links resolve;
- current workflows/tests using moved paths pass;
- byte-preservation receipts for byte-identical moves;
- no duplicate authority introduced;
- authority readers resolve newest surfaces;
- AI installer can start from its front door without root scan;
- historical evidence remains reproducible;
- root README change, if any, is explicit and separately authorized/reviewed.

Until then the correct status is `IN_PROGRESS`.