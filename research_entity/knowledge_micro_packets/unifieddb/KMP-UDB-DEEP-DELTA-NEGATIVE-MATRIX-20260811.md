# KMP-UDB-DEEP-DELTA-NEGATIVE-MATRIX-20260811

packet_id: `KMP-UDB-DEEP-DELTA-NEGATIVE-MATRIX-20260811`
domains: `unifieddb, claygraph, recovery, replay, schema_integrity, materialization, authority_direction, effect_reentry`
epistemic_class: `EXACT_PR_MERGE_CONTEXT_TARGET_VPS_NEGATIVE_EVIDENCE_PLUS_PRIMARY_SQLITE_MECHANISM_SYNTHESIS`
status_hint: `OPEN_BLOCKING_PROMOTION_WITH_NEW_SPLIT_GATES`
origin_actor: `chatgpt-secondary`
provider: `OpenAI`
model: `GPT-5.6 Sol`
trigger: `unifieddb`
invoked_alias: `unifiedb`
program: `FRANK_V0_1`
work_package: `F-V01-04-UNIFIEDDB-STATE-CONTINUITY`

## Scope and ancestry

This is a deeper continuation of the completed parent run
`research_entity/trigger_runs/unifieddb/unifieddb-20260811T0417p0700-chatgpt-secondary-state-continuity/`
and the U12 schema-pair scope correction.

The active product candidate remains draft PR #286 on branch
`chatgpt/unifieddb-storage-pair-fused-main-20260811`.

At evidence execution time the PR head was `d615d91b1a6688cef0c69141a945733c4a64fbb9` and the pull-request checkout tested exact merge-context SHA `e5297e8534885799eeff69504c5c8b5f4a1df62e`.

Target run: `31436105499`
Target host: `digital-retina`
Runner: `clay`
Platform: `Linux-6.8.0-117-generic-x86_64-with-glibc2.39`
Python: `3.12.3`
SQLite: `3.45.1`
Artifact: `frank-unifieddb-deep-negative-31436105499`
Artifact digest: `sha256:b8a83d19c38f3d80ac5f58f8cb0a2cfe1a6e90a7c80b63dcbb2ae115418c44e8`

Classification: **NEGATIVE_ARCHITECTURE_EVIDENCE_NOT_PRODUCT_PASS**.
The workflow is green because every expected blind spot was reproduced; it is not a promotion receipt.

## Six target-reproduced deltas

### D1 — Pair source certificate does not attest live SQLite schema

The current U12 certificate remained `CURRENT` and retained the same graph source-chain and pair digests after post-certification DDL changes.

Negative control A added a rogue ClayGraph table:
- physical `integrity_check = ok`;
- schema version moved 51 -> 52;
- live materialized-schema digest changed from `381d26b...41468` to `2794872b...311d7`;
- pair/source certificate remained unchanged;
- normal `open_pair()` accepted.

Negative control B removed required view `v_graph_current_nodes`:
- `integrity_check = ok`;
- schema version reached 54;
- live materialized-schema digest changed to `9ff29bf9...56d55b`;
- certificate remained unchanged;
- normal `open_pair()` again accepted.

Exact re-migration restored the baseline materialized-schema digest and normal open.

Measured ClayGraph materialized-schema digest cost on target, N=200:
- p50 91.170 us;
- p95 126.770 us;
- p99 148.112 us;
- mean 94.678 us;
- max 162.651 us.

Conclusion: source-chain identity and live materialized-schema identity are different proof surfaces. Store both. `PRAGMA schema_version` is useful as a cheap change detector, not as identity; SQLite documents that it increments on schema changes and may also change on VACUUM.

### D2 — Symmetric pair certificate reverses authority direction

Only the expected ClayGraph migration chain was changed in-process. UnifiedDB source-chain digest stayed exactly constant. The shared pair digest changed, and `open_unified()` rejected the unchanged, physically healthy UnifiedDB solely because the derived Graph expectation moved.

Conclusion: a rebuildable projection currently becomes an availability dependency of canonical authority.

Required law:
`derived -> canonical dependency` is permitted;
`canonical -> derived availability dependency` is not.

Successor certificate split:
- UnifiedDB MaterializationIdentity: Unified source-chain + live materialized schema + storage/runtime compatibility + semantic lineage/root;
- ClayGraph ProjectionIdentity: Graph source-chain + live materialized schema + exact source UnifiedDB semantic/materialization identity + derivation/projection identity.

`open_unified()` must not depend on current Graph identity. Graph failure should quarantine/rebuild/bypass the projection.

### D3 — ClayGraph global STALE state does not gate current views; root identity absent

Disposable current graph counts before global materialization STALE:
- nodes 2;
- edges 1;
- couplings 1;
- alternatives 1.

After setting `graph_materialization_state.status='STALE'`, the same four current-view counts remained exactly unchanged.

The current `graph_materialization_state` columns are:
`materialization_key, source_repo_head, source_semantic_epoch, graph_epoch, derivation_hash, materializer_version, projection_receipt_id, status, updated_at`.

There is no source semantic root / selected-lineage identity field. Two divergent semantic roots at the same epoch cannot be distinguished by this identity.

Conclusion: R1C must be a separate gate:
- current Graph readouts require global materialization CURRENT + exact graph epoch + valid derivation/projection receipt;
- source identity includes semantic root/selected lineage, not epoch alone;
- STALE/CONFLICT/DEGRADED Graph cannot surface as authoritative `current` projection and never mints truth.

### D4 — Mixed timestamp text formats create false-current rows; wall clock is unreceipted replay input

Target SQLite `CURRENT_TIMESTAMP` at probe time was `2026-08-10 21:56:37`.
Equivalent runtime-style ISO text was `2026-08-10T21:56:37+00:00`.

SQLite typed datetime parsing said that instant was not future.
Raw TEXT comparison said it was future.

Observed:
- UnifiedDB `v_current_semantic_records`: raw view count 1, typed datetime predicate count 0;
- ClayGraph `v_graph_current_edges`: raw view count 1, typed datetime predicate count 0.

Current `query_receipts` columns contain no explicit `as_of_time`, `read_as_of`, `query_time`, `evaluation_time` or clock-receipt field.

Conclusion:
1. canonical timestamps need one machine comparison representation;
2. mixed ISO/Python and SQLite timestamp texts must not be compared lexicographically;
3. ambient `CURRENT_TIMESTAMP` is an implicit, non-replayed input;
4. replay-critical query receipts must bind explicit read-as-of clock evidence and replay with it.

### D5 — Snapshot receipt hashes mutable live files without a pair barrier

Probe forced rollback-journal DELETE + FULL, matching the current safe target storage direction.

The current checkpoint path captured recorded snapshot:
- unified_epoch 0;
- graph_epoch 2;
- graph hash `4bbb11f0...2d8b5`;
- unified hash `9e2fa301...128f`;
- checkpoint_state `CHECKPOINTED`.

A graph epoch was injected between UnifiedDB hash and ClayGraph hash. Live state after receipt commit:
- graph_epoch 3;
- graph hash still `4bbb11f0...2d8b5` — therefore the recorded hash belongs to the later graph epoch, not recorded epoch 2;
- UnifiedDB hash became `1ecbcf6a...1da28`, different from the recorded Unified hash because the snapshot receipt itself was inserted/committed into the same live DB after hashing.

Both databases still passed integrity checks.

Conclusion:
- current snapshot pair is not a proven point-in-time pair;
- a hash of a mutable live DB before inserting its own receipt is not a self-verifying hash of the post-receipt DB;
- authoritative snapshot should be an immutable backup/copy artifact, verified then hashed, with receipt persisted outside that immutable artifact or using an explicitly defined canonical-content scheme;
- ClayGraph snapshot should normally be optional cache; authoritative recovery can rebuild it from admitted UnifiedDB;
- pair-consistent snapshots require a real barrier/atomic protocol, not serial checkpoints/hashes.

### D6 — Exact repository HEAD is broader than semantic materialization dependencies

Probe held UnifiedDB epoch/root, Graph epoch and both physical databases constant and changed only the `repo_head()` observation from synthetic head A to head B.

At A:
- UnifiedDB verify ACCEPT;
- ClayGraph verify ACCEPT.

At B with state unchanged and both integrity checks `ok`:
- UnifiedDB verify REJECT `CONTINUITY_DEGRADED`;
- ClayGraph verify REJECT `CONTINUITY_DEGRADED`.

Conclusion: exact Git HEAD is useful provenance but is broader than semantic materialization identity. Evidence-only/unrelated commits should not necessarily invalidate canonical state.

Successor authority should bind a content-addressed semantic dependency manifest: relevant migration/runtime/materializer blobs + semantic head/root + required build contract. Repo HEAD remains audit provenance.

## Additional static/compositional deltas

### D7 — current Graph derivation hash is not a content hash

`FrankStateRuntime.project()` computes `derivation_hash = sha256(epoch | graph_epoch | reason)`. It does not hash projected nodes/edges/assemblies. A later Graph payload mutation leaves that derivation hash untouched, while identical projection content under another `reason` gets a different hash.

`projection_receipt_id` in `graph_materialization_state` is plain TEXT and the runtime verifier currently does not validate receipt existence/hash coherence.

Required: content/projection root or deterministic derivation receipt bound to exact source semantic root + materializer identity + projection policy + resulting content identity.

### D8 — normal Frank runtime hard-depends on Graph availability

The runtime constructor opens the pair before verification. Therefore missing/unopenable derived Graph can block normal canonical runtime startup even though an `open_unified()` primitive exists.

Required: canonical boot opens/verifies UnifiedDB independently. Graph may be `CURRENT`, `DEGRADED_REBUILDABLE`, `MISSING_REBUILD`, or quarantined. Only graph-dependent queries fail/fallback; canonical truth access remains available when safe.

### D9 — source-chain digest is provenance-sensitive, not semantic-schema identity

U12 hashes executable migration source bytes after removing only selected PRAGMAs. Comment/whitespace/source-only edits can therefore change source-chain identity even when resulting `sqlite_schema` is equivalent.

Keep source-chain digest for reproducibility/provenance, but use a distinct materialized-schema attestation for physical compatibility. Do not collapse them.

### D10 — `CURRENT_TIMESTAMP` views are nondeterministic even after format repair

Even with canonical timestamp encoding, ambient wall-clock predicates make unchanged DB bytes yield different results at different replay times. Current-state convenience and deterministic replay are separate query modes.

Required: explicit `read_as_of` in query receipt/planner semantics. Current live query captures a clock receipt; replay reuses that exact input.

### D11 — Graph materialization exact repo-head equality is an additional R1C overcoupling

Current high-level Graph verifier requires exact repo head, source semantic epoch and graph epoch, but not source semantic root. Replace exact-head authority with relevant source dependency identity and exact canonical semantic root/head.

### D12 — checkpoint label does not encode selected journal semantics

Current runtime calls `PRAGMA wal_checkpoint(FULL)` on both stores and records `CHECKPOINTED`, but the target-safe candidate for SQLite 3.45.1 intentionally uses rollback-journal DELETE. Recovery receipts should describe the actual durability/capture mechanism, not a generic WAL-oriented label.

## New U13 research hypothesis — eliminate migration tear rather than only detect it

Primary SQLite documentation states that transactions spanning multiple databases attached to one connection are atomic when the main DB is not `:memory:` and journal mode is not WAL. SQLite's multi-file rollback protocol uses per-database rollback journals plus a super-journal to make the files commit or roll back together across crash/power loss.

This matters because the current target-safe storage candidate already chooses rollback-journal DELETE + FULL for SQLite 3.45.1.

Hypothesis:
- during schema migration, open one physical DB as main;
- ATTACH the second DB;
- run one schema-qualified transaction covering Graph + Unified DDL and certificate state;
- commit through SQLite multi-file rollback/super-journal atomicity;
- then, on a future fixed SQLite runtime, runtime journal mode may be chosen separately after migration.

Counterhypotheses:
- current migration SQL is unqualified and not directly attached-schema-addressable;
- trigger/view/index syntax and same-database trigger restrictions may make automatic qualification unsafe;
- migration-time mode switching may introduce lock/recovery complexity;
- target filesystem/VFS durability assumptions still require crash testing.

Therefore this is a research/compiler problem first, not a direct PR #286 runtime change.

## Current evidence law

The new continuation now separates at least these proof surfaces:

`R0 storage substrate`
`R1A live physical-schema attestation`
`R1B migration/source identity`
`R1C derived Graph freshness/source-root closure`
`R2 semantic lineage / rollback authority`
`R3 exact execution ownership`
`R4 causal support closure`
`R5 replay clock/query determinism`
`R6 snapshot artifact consistency`

No ring inherits PASS from another.

## V17 / terminal-state fusion

Fresh target V17 bound-reentry evidence exists, but the current product lane remains candidate-only. The independently completed CCW research killed a separate derived-DONE runtime architecture while retaining one law:

**persisted DONE receipt != current causal closure authority**.

A terminal receipt may remain durable audit/cache evidence. Current causal completion must be revalidatable from exact execution/outcome/GWT/causal/delta-or-typed-no-learning support. Support invalidation must not erase verified provider outcome and must mint zero effect-retry authority.

## Promotion decision

**HOLD.**

Do not merge/promote PR #286 from the six-negative workflow. A green negative matrix means the present candidate's boundaries were successfully falsified.

Required next product work:
1. repair R1A live materialized-schema attestation;
2. break derived->authority symmetric pair dependency;
3. add R1C source-root + global materialization read gating;
4. repair temporal storage/comparison and explicit replay clock receipts;
5. redesign snapshots around immutable artifacts / proven pair barrier;
6. replace exact repo-head authority with semantic dependency-manifest identity;
7. separately evaluate ATTACH/super-journal atomic migration feasibility;
8. rerun the six negatives with expectations flipped where mechanisms are repaired;
9. preserve independently open R2/R3/R4 gates.

No canonical DB migration, product merge, whole Frank v0.1 acceptance, external effect, final training authorization, or self.root/Frank Harness mutation authority follows from this packet.
