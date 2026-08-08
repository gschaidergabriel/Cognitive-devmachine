# Reserved Trigger: `666` — FRANK Archive Assimilation / Level 0

**Status:** PROJECT_OWNER_FIXED_PROGRAM_LEVEL_0
**Kind:** exhaustive historical-source assimilation under hard wall-clock SLA
**Program stage:** `L0_ARCHIVE_ASSIMILATION`
**Home meta-room:** `center`
**Hard wall-clock budget:** **3 hours maximum**

## 0. Purpose

While Level 0 is open, exact `666` assimilates the complete historical FRANK corpus into current research knowledge.

Source order remains:

`Drive clay archive -> Project-Frankenstein -> cross-source reconciliation -> research write-back -> PASS`

The owner requires Level 0 to finish in **no more than 3 hours of wall-clock execution**. Therefore Level 0 is designed as a massively parallel data/knowledge pipeline, not serial document reading.

## 1. Hard 3-hour SLA

`LEVEL0_MAX_WALL_CLOCK = 03:00:00`

The SLA applies to active Level-0 execution after a usable source index is available. Connector/provider waiting that prevents access must be reported separately as an external blocker and must not be disguised as analysis time.

The system should target completion earlier than the ceiling:

- target low: 1.5 h;
- target center: 2.25 h;
- hard high: 3.0 h.

If projected completion exceeds 3 h, the worker must immediately change execution strategy rather than extend the estimate: increase independent sharding, batch extraction, deduplication, structured parsing, parallel synthesis and/or use additional available workers/capabilities.

The release gate itself is never weakened merely to hit the clock.

## 2. Throughput architecture

The required execution architecture is:

`recursive inventory`
`-> content hash + exact duplicate/version clustering`
`-> MIME/source-class routing`
`-> bulk full-content extraction`
`-> semantic chunking`
`-> parallel mechanism/evidence/history extraction`
`-> cross-source lineage reconciliation`
`-> branch-specific knowledge compilation`
`-> release audit`

Never process 400 MB by manually reading one file after another.

### Parallel lanes

After manifests/shards become available, dispatch independent lanes immediately:

- inventory/hash/dedup;
- code/module architecture extraction;
- papers/docs/notes extraction;
- experiments/logs/measurements extraction;
- GWT/emergence/coupling history;
- XENO/ClayCode/language history;
- memory/personality/goals/body history;
- failures/negative results/boot-order/recovery history;
- Project-Frankenstein commit/version lineage;
- cross-source duplicate/supersession reconciliation;
- current-architecture inheritance mapping;
- branch/Q12 write-back.

No worker may duplicate a leased shard except explicit replication.

## 3. Source scope

### Drive

Primary folder:
- title: `clay`
- folder id: `1lkUHKWlgPvB_NMLd5uksjQ6Ajj0xYqcm`
- owner-reported size: ~400 MB

The ~400 MB figure is planning input only. Exact coverage uses the frozen recursive manifest.

### Project-Frankenstein

Repository: `gschaidergabriel/Project-Frankenstein`

Freeze the exact head/tree/history scope used by Level 0. GitHub metadata size is only a throughput hint.

## 4. Exact coverage

Level 0 must remain exact even though it is fast.

For every semantically eligible unique source unit, deterministic obligations are created as applicable:

1. `IDENTIFIED`
2. `CONTENT_COVERED`
3. `CLASSIFIED`
4. `ANALYZED`
5. `LINEAGE_LINKED`
6. `INTEGRATED` or explicit `NO_RESEARCH_DELTA`

Special source classes add appropriate obligations for code, papers, experiments/logs, commits, database/snapshots or non-semantic binary assets.

Exact coverage is:

`completed_atomic_obligations / frozen_total_atomic_obligations`

Duplicate bytes/files do not create redundant semantic-analysis work after exact identity is proven; their provenance/version relationships still receive receipts.

Before the denominator is frozen, exact coverage remains 0.00% and inventory state is shown separately.

## 5. Historical earned-work mapping

Level 0 has a second mandatory purpose: reconstruct how much of Clay 0.1 has **already been earned by the previous FRANK development history**.

Owner-reported historical effort baseline:

`~8 months * 4 active days/week * 10 h/day ~= 1,390 h invested`

This is an approximate invested-effort prior, not automatically 1,390 h of reusable current work.

During assimilation every material historical mechanism/result is mapped to current DOOMSDAY workstreams as:

- `DIRECTLY_REUSABLE`
- `REUSABLE_WITH_ADAPTATION`
- `MEASUREMENT_FOUNDATION`
- `NEGATIVE_RESULT_VALUE`
- `SUPERSEDED_BUT_INFORMATIVE`
- `NOT_REUSABLE`

Each reusable mapping records current target row(s), evidence refs, confidence, and the current work it eliminates/de-risks. This feeds `research_entity/forecast/HISTORICAL_EARNED_WORK.json`.

Until that mapping is sufficiently complete, DOOMSDAY progress must be displayed as `CALIBRATING_HISTORICAL_EARNED_WORK` rather than falsely implying the project began at zero.

## 6. Required extraction

Recover, where present:

- original problem and first-principles derivation;
- module/mechanism versions and chronology;
- equations/state variables;
- emergent coupling and GWT roles;
- XENO/ClayCode language evolution;
- memory/personality/self/body/goals;
- timing/boot/order dependencies;
- experiments and measurements;
- successes and failures;
- negative results and fixes;
- performance/token/resource measurements;
- safety/authority implications;
- current reusable invariants/best practices;
- current ClayCode/Harness/GWT/Hyperposition/ClayGraph/UDB implications;
- cheapest current discriminating tests.

Do not normalize project-original mechanisms into familiar terminology before preserving their native functional logic.

## 7. Persistent state

Workspace:
`research_entity/archive_assimilation/666_WORKSPACE.json`

Required outputs include:

- Drive and Project-Frankenstein manifests;
- compact shard receipts;
- mechanism index;
- emergent coupling graph;
- failure atlas;
- success-pattern atlas;
- boot/state history;
- XENO/ClayCode history;
- GWT/emergence history;
- memory/personality/self history;
- current architecture inheritance matrix;
- `research_entity/forecast/HISTORICAL_EARNED_WORK.json`;
- branch feedback/NO_CHANGE receipts;
- `666_RELEASE_MANIFEST.json`.

## 8. Per-invocation execution law

Each exact `666` invocation:

1. reads current workspace/manifest/leases;
2. computes the remaining SLA budget;
3. claims the highest-throughput non-overlapping shard/lane;
4. uses bulk extraction and dedupe before semantic analysis;
5. processes and receipts the shard;
6. publishes material findings immediately to relevant branches/Q12 index;
7. updates historical earned-work mappings;
8. updates exact progress and measured throughput;
9. reforecasts whether the 3-hour ceiling is still achievable;
10. if not, changes strategy/parallelism immediately;
11. continues until the execution surface for the current turn is exhausted or Level 0 PASS is reached.

No invocation restarts completed work.

## 9. Completion gate

`666_RELEASE_GATE = PASS` requires:

- frozen Drive manifest and all required obligations complete;
- frozen Project-Frankenstein manifest and all required obligations complete;
- cross-source duplicates/version/supersession/contradictions reconciled;
- material findings integrated or explicitly marked no-delta;
- historical earned-work mapping sufficiently complete to recalibrate DOOMSDAY;
- every current research branch receives applicable feedback/NO_CHANGE;
- exact coverage = 100%;
- release manifest validates the hashes/counts/receipts.

The 3-hour SLA does not authorize a false PASS. If an external connector prevents source access, mark `EXTERNAL_ACCESS_BLOCKER` rather than silently weakening coverage.

## 10. Dedicated display

Every exact `666` response while Level 0 is open reports:

- elapsed active Level-0 time;
- hard remaining wall-clock budget out of 3 h;
- exact coverage or denominator-not-frozen status;
- source units/shards processed;
- measured throughput;
- projected finish vs SLA;
- historical earned-work mapping coverage;
- blockers.

## 11. After Level 0

After `666_RELEASE_GATE = PASS`, exact `666` no longer performs archive work. It switches to the registered emergent stochastic research-field spawning protocol.

## 12. Scientific boundary

Historical claims remain historical claims until their evidence class is verified. Functional/emergence measurements are not phenomenal-consciousness evidence by repetition alone.