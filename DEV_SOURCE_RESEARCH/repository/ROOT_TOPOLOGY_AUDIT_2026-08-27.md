# Root topology audit — 2026-08-27 Trigger 3

## Evidence identity

- repository: `gschaidergabriel/clay-global-research-entity`
- audited base `main`: `854f6bc87780f4a5242489a6c807d186b16a8c3d`
- audited root tree: `e7cee5640aa2f05edc695adadc50d6e20ccb8755`
- classification: `CURRENT_SOURCE` at the named commit only
- migration execution: `PREPARED_NOT_RUN`

This is an evidence-producing topology audit, not a claim that the root has already been migrated.

## Target public root

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

The Trigger-3 branch creates the three new entry directories while leaving the root README unchanged. Existing root technical material remains on the audited base and must be migrated only after reference/path impact is proven.

## Observed root examples that are outside the target public surface

The exact root-tree read at the audited commit visibly includes, among others:

### Repository / host instructions and configuration

- `.claude/`
- `.env.example`
- `.github/`
- `.gitignore`
- `AGENTS.md`
- `CLAUDE.md`
- `CLAUDE_CODE_INTRODUCTION.md`
- `JOIN_RAE_CLAUDE_CODE.txt`

### Current / historical authority and bootstrap surfaces

- `000_CLAY_CURRENT.md`
- `000_FRANK_GLOBAL_RESEARCH_ENTITY_AUTOBOOT.txt`
- `AUTHORITATIVE_STATE_RESOLUTION.md`
- `CLAY_EXECUTION_AUTHORITY.md`
- `PROJECT_AUTO_BOOT_KERNEL_FINAL.txt`
- `PROJECT_SOURCE_SINGLE_BOOTSTRAP.txt`
- `PROJECT_SOURCE_SINGLE_BOOTSTRAP_V2.txt`
- `RAE_VNEXT_RUNTIME.md`

### Metrics / results / manifests

- `000_FREE_SWARM_LIVE_DASHBOARD.md`
- `ZZZ_FREE_SWARM_RESULTS.md`
- `CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json`

### Source / research trees

- `agentZero/`
- `agentzeroforschung/`
- `benchmarks/`
- `dump archive/`
- `dump/`
- `frank_reference/`
- `free swarm/`
- `governance/`
- `rae_core/`
- `receipts/`
- `research_entity/`
- `research_sources/`
- `runtime_checks/`
- `schemas/`
- `tests/`
- `the artefact/`

### Anomalous root filenames requiring explicit classification

- `gemeinsamer State)` — zero-byte blob in the audited tree
- `libc.malloc_trim(0)` — blob, not a normal public-root entry name
- `madvise(ptr, length, MADV_FREE);` — blob, not a normal public-root entry name
- `rae.py`

These names are not deleted or renamed here. Their references and historical purpose have not yet been proven sufficiently for a safe move.

## Why no bulk move is executed in this audit

The target root is clear, but the dependency graph is not yet complete. A root move can alter:

- CI/workflow paths;
- repository instruction discovery;
- import/runtime assumptions;
- scripts with fixed relative paths;
- historical evidence links;
- external references not visible from current source search.

A cosmetic mass move would therefore violate the Trigger-3 evidence discipline if performed before reference classification and regression checks.

## Migration decisions

| Class | Current decision |
|---|---|
| `README.md` | `PUBLIC_ENTRY` — keep, do not rewrite in this trigger turn |
| new `HUMAN_READ_THIS/` | `PUBLIC_ENTRY` — created on synthesis branch |
| new `DEV_SOURCE_RESEARCH/` | `PUBLIC_ENTRY` — created on synthesis branch |
| new `AI_START_HERE_DO_NOT_SCAN_REPO/` | `PUBLIC_ENTRY` — created on synthesis branch |
| `.github/`, `.claude/`, host instruction files | `UNKNOWN/RUNTIME_PINNED` until host discovery and workflow references are audited |
| current authority pointers | `RUNTIME_PINNED` until no-scan entry and all consumers can resolve relocated paths |
| historical bootstrap/directive files | candidate `HISTORICAL_EVIDENCE`, index before move |
| dashboards/generated metrics | candidate `GENERATED_METRIC`, writer/reader discovery required |
| source/research trees | `RUNTIME_PINNED` or `RESEARCH_SOURCE` pending reference graph |
| anomalous root blobs | `UNKNOWN`, inspect provenance/references before move/delete |

## Acceptance gate for the first physical move batch

The first move batch is allowed only after all of these are evidenced at an exact base commit:

1. a complete top-level inventory;
2. reference search across source, workflows and current docs;
3. classification of every old-path reference;
4. byte digest for every source file to move;
5. destination plan under `DEV_SOURCE_RESEARCH/repository/`;
6. path/link/import regression command set;
7. explicit compatibility handling where host discovery depends on a root filename;
8. post-move digest equality for files intended to be byte-identical;
9. no duplicate authority copy left behind.

Until then the correct status is:

`PARTIAL_TARGET_LAYER_CREATED_ROOT_MIGRATION_PREPARED_NOT_RUN`

See [`ROOT_TOPOLOGY_MIGRATION.md`](ROOT_TOPOLOGY_MIGRATION.md) for the move protocol and [`FRANKENSTEIN_EVIDENCE_INDEX_2026-08-27.json`](FRANKENSTEIN_EVIDENCE_INDEX_2026-08-27.json) for evidence classification.
