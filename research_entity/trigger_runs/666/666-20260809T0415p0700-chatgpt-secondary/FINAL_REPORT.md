# 666 Level-0 Archive Assimilation — Worker Report

Run: `666-20260809T0415p0700-chatgpt-secondary`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `L0_ARCHIVE_ASSIMILATION`  
Gate at run time: `NOT_PASS`

## Execution

This invocation followed Mode A of the 666 protocol. It joined the repo-native `center`, cross-read concurrent workers, avoided overlapping primary credit, analyzed non-overlapping Project-Frankenstein history, routed branch/Q12 deltas, wrote archive receipts and produced deduplicated earned-work mappings.

### Source access

- Drive folder `clay` was enumerated and contains `all frank data 1.tar.xz` (`663,552,000` bytes).
- Raw streamed fetch with `include_base64=false` still failed HTTP 413 at the connector's `104,857,600` byte response limit.
- No Drive-internal content or exact coverage credit is claimed.
- Project-Frankenstein frozen working head remains `abba90a5767d85abc8a1ac340bae92842dab35c1`.
- Exact recursive tree/history enumeration is still unavailable on the current connector surface; history-aware semantic shards are therefore valid evidence but not an exact denominator.

## New unique evidence from this worker

### 1. Persistent state race / semantic-authority failure

Historical E-PQ code explicitly refreshed persisted state before each event because separate process-local EPQ instances could otherwise overwrite a homeostasis reset written by another process. This is a concrete lost-update/stale-truth failure and directly motivates versioned/CAS state transitions, replay identity and single logical authority in current FRANK/ClayCode/UnifiedDB.

### 2. Persistent goals/body/proprioception lineage

Historical consciousness/spatial code implemented persistent goals, attention, rumination controls, multi-timescale rhythms, self-vs-environment resource attribution, service-health awareness, body/physics state and persistent world/location transitions. The reusable content is the typed state and causal transition logic, not the literal daemon/service/room topology.

### 3. Historical failure atlas for Harness

SOMA and related fixes expose reusable test oracles: TOCTOU, unsafe thread lifecycle, non-atomic config writes, stale runtime config, duplicate restart scoring, adapter-key loss, zero-baseline drift falsely judged safe, threshold off-by-one, model/resource leaks and training-order bias. These should become executable H1/H2/H3 regression fixtures.

### 4. Historical benchmark preserved but causal claim downgraded

The March 2026 70-turn bare-Llama-vs-Frank comparison reported `11 vs 2` deflections and unique-word ratios `0.843 vs 0.929`, among other longitudinal differences. It is retained as benchmark scaffolding only. System prompt, output constraint, memory path and 30+ subsystems changed simultaneously, so the original full-architecture causal interpretation is confounded and must be replaced by factorized matched ablations.

### 5. Storage != cognitive availability

A historical fix records `2106` Titan nodes while FRANK still had no active way to query its own long-term memory. Another fix shows entity-session data persisted in isolated DBs/transcripts but remained unavailable for cross-session recall until explicit Titan/chat-memory ingestion was added. Durable bytes are therefore not functional memory unless retrieval becomes causally available to cognition.

### 6. Federated logical memory precedent

Historical MemoryHub provided a single query path across chat, Titan, consciousness, world and preferences while retaining multiple underlying stores, with RRF fusion, budget packing, source attribution, retrieval metrics and consistency maintenance. This is direct historical support for UnifiedDB's current logical/semantic unification model without assuming a mandatory physical single-store merge.

### 7. Integrity/recovery negative result

Titan repair found `6675` orphaned edges with `0` nodes, followed by foreign-key enforcement, cascading deletion, re-ingestion, crash-resumable embedding backfill and consistency maintenance. ClayGraph/UnifiedDB acceptance should therefore include referential-integrity, orphan-repair, interrupted-job resume, idempotence and recovery receipts.

### 8. Migration-stable identities

Titan -> LCME was renamed across many source files while durable DB filenames and tool names were preserved deliberately for data safety and LoRA compatibility, with a backwards-compatible redirect. Current ClayCode/UnifiedDB migrations should preserve stable semantic resource identity or use explicit reversible versioned migrations.

## Crossread / dedup

This worker cross-read the existing GWT/runtime shard and the LCME/SOMA/autonomy shard.

- GWT/Thalamus/AURA primary findings remain owned by the GWT/runtime shard.
- LCME P@5, 7,213-vector cleanup, neural maturity gating and generic source-class semantics remain owned by the LCME shard.
- No duplicate earned-work hours were added for those findings.
- Shared ancestry is recorded as correlated evidence, not independent replication.

## Earned-work mapping

The first state/body/failure/benchmark shard was successfully aggregated into the shared mapping earlier in the run. Concurrent workers subsequently advanced the shared file, and CAS correctly rejected a stale replacement attempt.

The memory/persistence remainder was therefore written as a separate deduplicated aggregation delta:

`research_entity/forecast/earned_work_deltas/666_20260809T0424p0700_pf_memory_persistence_recovery_unique.json`

Unique pending estimate from this delta only:

- low: `9 h`
- center: `21 h`
- high: `42 h`

This is a low-confidence avoided/reused-current-work estimate, not completion percentage. It must be re-crossread against newer receipts before central aggregation.

## Branch feedback

Complete branch feedback including explicit `NO_CHANGE` where appropriate and Q12 routing is stored in:

`research_entity/trigger_runs/666/666-20260809T0415p0700-chatgpt-secondary/BRANCH_FEEDBACK_MANIFEST.json`

## Concurrency behavior

Two attempted central-file updates were rejected by GitHub CAS because other workers wrote newer state between read and write. The worker did not overwrite those changes. Instead it published immutable receipts/deltas and a workspace registration delta for later merge. This is the intended repo-native multiworker behavior.

## Level-0 status after this worker

- Gate: `NOT_PASS`.
- Exact combined coverage: `0.00%` by protocol because the denominator is not frozen.
- Project-Frankenstein has multiple valid deep semantic/history shards and a partial manifest, but not an exact full tree/history denominator.
- Drive archive internals remain inaccessible through the current connector due the 663.6 MB vs 100 MiB limit.
- Therefore a truthful Level-0 PASS is impossible on this execution surface.

## Highest-value next actions

1. obtain a Drive access path that can mount/stream or split the 663.6 MB tar.xz and freeze its internal manifest;
2. finish exact Project-Frankenstein tree/history obligation enumeration;
3. merge immutable workspace/earned-work deltas with CAS crossread rather than overwriting concurrent state;
4. turn the recovered historical failure families into Harness regression tests;
5. after both source denominators are frozen, perform cross-source duplicate/supersession reconciliation and release audit.

No paid training or paid model execution was started.
