# UnifiedDB — Deeper Delta Run, Extended

Run: `unifieddb-20260811T0441p0700-chatgpt-secondary-deeper-deltas`

Status: **COMPLETE_EXTENDED_DEEP / RESEARCH DELTAS COMMITTED / PROMOTION HOLD**

## Executive result

The earlier UnifiedDB model correctly separated canonical semantic authority from derived ClayGraph state, but it still compressed several different correctness claims into too few certificates. The deeper run now resolves UnifiedDB continuity into independently falsifiable layers:

1. storage/build safety;
2. executable migration-source identity;
3. live materialized `sqlite_schema` identity;
4. authoritative dynamic semantic-root/lineage identity;
5. derived dynamic projection identity/freshness;
6. explicit temporal read/replay identity;
7. selection/query-plan identity;
8. consistent snapshot/recovery-image identity;
9. external rollback-domain-independent recovery floor;
10. execution/effect causal and recovery authority;
11. stable historical closure identity.

The most important correction is architectural: **a single symmetric UnifiedDB↔ClayGraph pair certificate is too strong in one direction and too weak in another.** It is too strong because a rebuildable ClayGraph source/schema evolution can make `open_unified()` fail even when canonical UnifiedDB is unchanged and healthy. It is too weak because a schema-compatible ClayGraph can still be dynamically stale, derived from the wrong semantic root, or expose stale rows through current views. Authority dependencies must therefore be acyclic: Graph/index state may depend on canonical UnifiedDB identity, but canonical UnifiedDB availability must not depend on rebuildable derived state.

A second blocking correction is replay semantics: **`CURRENT_TIMESTAMP` is an undeclared input to canonical reads.** The current semantic and graph views use ambient time. A local negative control showed identical database bytes returning a record before a short expiry and not returning it after wall-clock advancement. The evolving PR #286 independently added a stronger deterministic probe showing that Python-style ISO timestamp text (`T` and offset) and SQLite `CURRENT_TIMESTAMP` text can also disagree under raw lexical comparison even when SQLite's datetime parser identifies the represented instant correctly. Exact replay therefore requires both canonical timestamp representation and an explicit `as_of_valid_time` bound into query/assembly receipts.

A third blocking correction is snapshot identity: **a main `.sqlite` file is not necessarily the database state.** In WAL mode a commit can be durable in the WAL before checkpointing into the main file. A local negative control committed one row, copied only the main file while the WAL remained non-empty, and the copy contained zero rows. Snapshot identity must therefore describe a transactionally consistent logical image and the method by which it was produced, not just file hashes.

## Delta A — pre-action EffectIntent / temporal causal provenance

Relationally coherent causal support can still be post-hoc. The active V17 V3 learning test records the verified outcome and then constructs attention, receiver-use, prediction, prediction outcome, causal credit and exact-outcome support before expecting learning re-entry to succeed.

Introduce immutable pre-action `EffectIntent/DecisionReceipt` with preallocated effect id, exact current execution generation, GWT cycle/episode, prediction commitment, receiver-use/local-effect receipt and action/target/request identity. The reservation consumes that receipt.

Required falsifier: `POST_HOC_SUPPORT_MINT` must reject with zero terminal mutation.

## Delta B — origin execution != reconciler execution

Effect origin identity proves who reserved/attempted an effect; crash recovery asks who is authorized to reconcile it now. These are different identities.

Required split:
- immutable origin execution/epoch;
- current reconciler execution/epoch;
- explicit recovery assignment for successor completion;
- stale origin and unrelated successor fail closed.

## Delta C — historical terminal validity must be monotonic

A historical DONE chain must not become invalid because an admitted semantic record later becomes SUPERSEDED rather than CURRENT. Freeze validity-at-admission in an immutable closure witness. Ordinary semantic evolution changes current belief state; corruption/revocation creates separate quarantine evidence.

## Delta D — live schema attestation != migration-source identity

The U12 source-chain digest binds the expected executable migration program. It does not by itself prove that the physical database still has exactly that schema after certification.

PR #286 now carries a dedicated disposable negative probe that adds a rogue schema object and deletes a required view while preserving certificate metadata. This is the correct falsifier class.

Candidate: `LiveSchemaAttestationV1` over normalized `sqlite_schema` objects, kept separate from source-chain identity. Source identity answers *what code should have built this*. Live-schema identity answers *what is actually here now*.

## Delta E — authority direction must be acyclic

The symmetric pair digest currently includes both UnifiedDB and ClayGraph chains. A Graph-only expected source-chain change can alter the pair digest and reject `open_unified()` even when UnifiedDB is unchanged and healthy.

Correct dependency direction:

`UnifiedDB storage/build -> UnifiedDB source schema -> UnifiedDB live schema -> semantic root/lineage`

then derived:

`semantic root/lineage -> Graph/index source identity -> projection/index admission -> selection`

Never the reverse.

`open_unified()` must not require current ClayGraph identity. `open_pair()` may gate Graph use; Graph failure quarantines/rebuilds the projection while canonical reads remain available unless the exact requested operation semantically requires Graph.

## Delta F — StateProjectionCertificateV1

Schema compatibility is not dynamic projection freshness. The current ClayGraph schema carries `source_semantic_epoch`, but the evolving R1C probe shows two problems:
- global graph materialization status can become STALE while current graph views remain visible;
- epoch-only source identity cannot distinguish different semantic roots/sibling lineages at the same epoch.

Add an authoritative projection admission receipt in UnifiedDB:
- projection receipt id;
- exact semantic epoch + semantic root/selected-lineage identity;
- graph epoch;
- derivation contract hash;
- materializer identity/code hash;
- graph content digest;
- lag class;
- admission state (`CANDIDATE|ADMITTED|STALE|RETRACTED|REBUILD_REQUIRED`).

ClayGraph may mirror the receipt but cannot self-admit.

Truth-critical Graph reads require an exact admitted root unless the query contract explicitly permits a canonical fallback. Exploratory reads may admit bounded lag only when the lag policy is recorded.

## Delta G — ReplayClockV1 and canonical timestamp encoding

Replay-critical predicates must not read a fresh wall clock implicitly.

Contract:
- every query/assembly receives explicit `as_of_valid_time` and semantic epoch/root;
- a live-now cognition cycle resolves now once and persists that value in the query/assembly receipt;
- replay reuses the captured value;
- timestamp storage uses one canonical machine representation (candidate: integer UTC epoch at defined precision, or one canonical UTC text encoding);
- never compare mixed timestamp encodings as raw TEXT.

Required falsifiers:
- `BYTE_STABLE_TIME_SHIFT`: same durable bytes + same receipt -> identical result after real time advances;
- `MIXED_TIMESTAMP_ENCODING`: equal instants in supported input forms canonicalize to one ordering/equality result.

## Delta H — SnapshotManifestV2

Current snapshot rows contain hashes/cursors but do not fully specify how a consistent image was obtained. SQLite WAL is part of persistent state; committed changes may not yet be in the main file.

Candidate manifest fields:
- snapshot id and method;
- SQLite version/source id/compile-options digest;
- journal mode, synchronous, page size;
- materialization pair identity + live schema digests;
- semantic epoch/root + transaction cursor;
- projection receipt identity;
- hashes of consistent UnifiedDB/ClayGraph images;
- WAL bundle hashes if the method intentionally uses a WAL bundle;
- external floor generation/ref;
- restore verification receipt.

Initial allowed methods:
- Online Backup API;
- `VACUUM INTO`;
- explicitly quiescent rollback-journal bundle;
- explicitly complete WAL bundle.

A raw main-file hash is evidence about that file, not sufficient evidence of the logical database state.

## Delta I — CanonicalRootChainV1

`state_epochs.root_hash` exists, but a root field is not yet a root protocol. Define a canonical, domain-separated construction, for example:

`SHA256('FRANK_SEMANTIC_ROOT_V1' || parent_root || epoch || tx_receipt_hash || ordered_typed_op_digests || authority_scope_digest || provenance_digest)`

Properties:
- canonical byte encoding;
- ordered, typed operations;
- no ambient wall clock;
- no Graph activation/rank/unadmitted derived payload;
- same parent + same commitments => identical replay root;
- any semantic mutation => different root;
- admission performs parent epoch/root compare-and-swap.

Required negative: `SAME_EPOCH_SIBLING_ROOT` and transplanted-root replay.

This gives semantic-lineage selection a real dynamic state identity instead of relying on epoch labels plus opaque supplied strings.

## Delta J — SelectionReceiptV2

Authenticated records do not imply authenticated selection. Prior U2 evidence already separated replay integrity from selection integrity: manipulated selection structure changed naive selected membership while source records remained authentic.

Current query receipts should be extended with:
- semantic root and explicit as-of time;
- projection/index identity and content digest;
- candidate-universe hash;
- normalized query digest;
- retrieval operator/ranker identity;
- filter policy digest;
- ordered candidate digest/count;
- selected refs digest;
- score-trace digest;
- admissibility digest;
- final selection receipt hash.

Emergent retrieval, Graph ranking, FTS and vectors all produce candidates; none directly mint semantic authority.

## Delta K — DerivedIndexHealthV1

Derived indexes need the same source-root/rebuild discipline as ClayGraph.

For FTS5, SQLite supplies explicit `integrity-check` and `rebuild` operations; local SQLite exposed the primitive successfully. A product receipt should bind source semantic root, builder/index code digest, content digest, health state and rebuild receipt. Target compile capability must still be verified.

For vector and other indexes use the same abstract contract even when the implementation-specific checker differs.

## Delta L — SQLiteDefensiveOpenV1

SQLite documents `trusted_schema=OFF` as the safer posture when schema content must not gain unintended application-function authority. The local scripting binding supports the pragma.

Candidate normal-open hardening:
- `trusted_schema=OFF`;
- extension loading stays disabled;
- verify `writable_schema` remains off;
- where the deployed binding exposes it, evaluate `SQLITE_DBCONFIG_DEFENSIVE`;
- regression-test every persistent Frank view/trigger/function under the hardened setting.

This does not replace live-schema attestation; it reduces what a modified schema can do.

## Delta M — DELETE+ATTACH is a real architecture, not just a fallback

Official SQLite semantics make multi-database transactions atomic as a set when the main database is file-backed and journal mode is not WAL. Therefore target-safe `DELETE + FULL` opens a genuine candidate:

**SYSTEM_SAFE_DELETE**
- canonical UnifiedDB main;
- ClayGraph attached;
- bounded semantic-head + projection-admission/batch transaction;
- cross-file atomicity supplied by rollback-journal/super-journal semantics;
- expected cost: more writer serialization/fsync/lock scope.

Local proxy measured attached p50 ~1.48x two separate transactions, so this must compete on target rather than be assumed superior.

## Delta N — fixed WAL requires a different recovery protocol

A fixed WAL runtime may win concurrency/latency, but SQLite explicitly does not make multi-ATTACH WAL updates atomic across files.

**PRIVATE_FIXED_WAL** therefore needs:
- canonical UnifiedDB commit;
- durable projection outbox/intent;
- async ClayGraph materialization;
- StateProjectionCertificate admission;
- replay/rebuild until convergence;
- explicit Graph lag policy.

The semantic contract stays identical across DELETE and WAL physical lowerings.

## Delta O — snapshot/replay, projection/replay and selection/replay are separate tests

A restored DB can be byte-valid but semantically stale. A Graph can be perfectly rebuildable yet influence the wrong selected facts. A selection can be correctly recomputed over a stale root. Therefore the final continuity gate is conjunctive:

`storage_safe`
`∧ unified_source_schema_admitted`
`∧ unified_live_schema_admitted`
`∧ selected_semantic_root_admitted`
`∧ external_floor_ok`
`∧ authorized_current_or_recovery_execution`
`∧ explicit_replay_clock`
`∧ snapshot_or_live_state_consistent`
`∧ graph/index_projection_admitted_if_used`
`∧ selection_receipt_valid_if_selection_used`
`∧ effect causal/terminal closure valid`

No existing single receipt proves this conjunction.

## Architecture comparison retained

The run now keeps six physical/logical alternatives rather than prematurely selecting one:
1. specialized baseline;
2. logically unified API over specialized stores;
3. canonical UnifiedDB + durable outbox + async derived stores;
4. DELETE/FULL + bounded ATTACH atomic projection;
5. private fixed WAL + async projection admission;
6. physical monolith benchmark.

Historical U2 mechanism evidence is retained: same-process specialized and monolith mixed reads were close in the tested cache-hot workload; JSON/service boundaries cost more; monolith writes were cheaper than canonical+outbox; unsynchronized two-store recovery tore frequently; outbox replay converged; trusted selection structure mattered independently of authentic records. None of those synthetic measurements establishes the target winner.

## New implementation/research output

- PR #286 continues as the fused runtime-candidate lane and now contains multiple deeper negative probes: live-schema drift, authority-direction coupling, R1C Graph freshness and temporal replay semantics.
- PR #293 is a research-only adversarial layer created on top of #286. It intentionally carries no runtime promotion authority and explores additional replay/snapshot/security/index primitives.
- The shared run now contains protocol-shaped JSON companions for architecture, store roles, query routing and migration, plus `REPLAY_SNAPSHOT_SELECTION_DELTAS.json`.

## Target evidence boundary

The prior target storage component proves the conservative SQLite 3.45.1 DELETE/FULL behavior and forced-WAL rejection on the accepted self-hosted lane. The rapidly advancing #286 head repeatedly superseded/cancelled queued jobs during this run; a cancelled or queued job is not evidence for the newest head.

Therefore do not promote #286, the new temporal/schema/freshness probes, PR #293, the ATTACH profile, trusted-schema hardening, SnapshotManifestV2, CanonicalRootChainV1 or SelectionReceiptV2 from this run alone.

## Highest-information next work

1. stabilize one #286 candidate head long enough to execute all storage-pair + live-schema + authority-direction + R1C-freshness + temporal probes on the accepted target;
2. turn the currently diagnostic negative probes into repair PRs only after each failure scope is confirmed;
3. implement ReplayClockV1 in SHADOW and demand byte-stable replay equivalence;
4. implement CanonicalRootChainV1 shadow roots and run sibling/transplant/replay discriminators;
5. implement SnapshotManifestV2 with Online Backup/VACUUM INTO disposable restores and external-floor rejection;
6. implement StateProjectionCertificateV1 plus exact-root/fallback query routing;
7. implement SelectionReceiptV2 and repeat trusted-vs-manipulated selector tests;
8. A/B exact-target SYSTEM_SAFE_DELETE+ATTACH against PRIVATE_FIXED_WAL+outbox under identical semantic workloads;
9. compose all passing layers into one crash/restart/rollback/rebuild/query-replay receipt before F-V01-04 can close.

## Promotion boundary

**HOLD.** F-V01-04 remains OPEN. No whole Frank v0.1 acceptance, canonical DB migration, external provider effect, Frank/self.root Harness mutation authority or final training authorization follows from this run.
