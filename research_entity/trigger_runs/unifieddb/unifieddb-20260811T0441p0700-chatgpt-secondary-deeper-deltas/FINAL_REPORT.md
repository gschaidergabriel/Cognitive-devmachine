# UnifiedDB — Deeper Delta Run, Target-Executed Extension

Run: `unifieddb-20260811T0441p0700-chatgpt-secondary-deeper-deltas`

Status: **COMPLETE_EXTENDED_DEEP / SIX ARCHITECTURE GAPS REPRODUCED ON ACCEPTED TARGET / PROMOTION HOLD**

## Executive result

The deeper UnifiedDB run no longer rests only on static audit and local proxies. PR #286 candidate head `d615d91b1a6688cef0c69141a945733c4a64fbb9` was tested as merge candidate `e5297e8534885799eeff69504c5c8b5f4a1df62e` on the accepted self-hosted `clay` / `digital-retina` target (Python 3.12.3, SQLite 3.45.1). Workflow `31436105499` executed all six negative discriminators successfully. This is **negative architecture evidence, not product PASS**: the success means each discriminator reproduced the intended current design gap while canonical state and external effects remained untouched.

The six target-reproduced gaps are:

1. `PAIR_SOURCE_CERTIFICATE_DOES_NOT_ATTEST_LIVE_SQLITE_SCHEMA`
2. `SYMMETRIC_PAIR_CERTIFICATE_MAKES_DERIVED_GRAPH_AN_AVAILABILITY_DEPENDENCY_OF_AUTHORITY`
3. `R1C_GAP_GLOBAL_STALE_NOT_READ_GATED_AND_SOURCE_ROOT_NOT_BOUND`
4. `TEMPORAL_TEXT_ORDER_FALSE_CURRENT_PLUS_AMBIENT_CLOCK_REPLAY_INPUT`
5. `SNAPSHOT_RECEIPT_HASHES_LIVE_MUTABLE_FILES_WITHOUT_PAIR_BARRIER`
6. `REPO_HEAD_IS_BROADER_THAN_SEMANTIC_MATERIALIZATION_DEPENDENCY_SET`

The same candidate generation also had successful storage/pair, current-self.root, execution-anchor and effect/provider workflows. That does not erase the six negative findings; it shows the deeper gaps exist underneath otherwise passing component gates.

## The core architecture correction

UnifiedDB continuity must be decomposed into independent proof surfaces rather than represented by one broad pair certificate:

1. physical storage/build safety;
2. executable migration-source identity;
3. live materialized schema identity;
4. dynamic canonical semantic-root/lineage identity;
5. dynamic derived projection identity/freshness;
6. temporal read/replay identity;
7. selection/query-plan identity;
8. snapshot/recovery-image identity;
9. minimal semantic dependency-manifest identity;
10. external rollback-domain-independent floor;
11. execution/effect causal and recovery authority;
12. stable historical closure identity.

The dependency graph must be acyclic. Canonical UnifiedDB authority may feed Graph/index/projection admission. Rebuildable Graph/index state must never become a prerequisite for opening canonical truth unless the exact requested operation semantically requires that derived capability.

## Delta A — LiveSchemaAttestationV1

The current source-chain certificate says which executable migrations are expected. Target probe evidence shows that a rogue table can be added or a required view removed while the pair/source certificate remains unchanged and SQLite integrity remains `ok`; normal open still accepts. The probe measured normalized materialized-schema digest cost over 200 samples at roughly p50 91.17 µs, p95 126.77 µs, p99 148.112 µs on the target.

Repair direction:
- keep migration-source digest and live-schema digest separate;
- attest normalized `sqlite_schema` after migration;
- verify live schema at open or behind a protected cache/schema-version mechanism;
- fail/quarantine on rogue or missing required objects.

## Delta B — Acyclic authority certificates

Target probe changed only the expected ClayGraph source chain while UnifiedDB source chain and physical DB remained unchanged and healthy. `open_unified()` then failed because the symmetric pair digest changed.

Repair direction:
- UnifiedDB certificate binds only UnifiedDB storage/runtime compatibility + UnifiedDB source chain + UnifiedDB live schema;
- Graph certificate depends on canonical UnifiedDB materialization/semantic identity plus Graph source/live schema;
- `open_unified()` does not depend on current Graph identity;
- Graph failure becomes quarantine/rebuild/fallback, not canonical truth outage.

## Delta C — StateProjectionCertificateV1 / R1C

Target probe marked global Graph materialization STALE, yet current Graph views still returned the same two nodes, one edge, one coupling and one alternative. The materialization schema also had no exact source semantic root/lineage identity, only epoch-oriented source identity.

Repair direction:
- authoritative projection admission in UnifiedDB;
- exact source semantic epoch + semantic root/selected lineage;
- graph epoch + derivation contract + materializer code identity + content digest;
- status `CANDIDATE|ADMITTED|STALE|RETRACTED|REBUILD_REQUIRED`;
- authoritative current Graph readouts require admitted projection state;
- exploratory reads may use explicit bounded lag;
- stale Graph never mints truth and should normally be bypassable.

## Delta D — ReplayClockV1 + canonical time encoding

Target temporal probe showed both dimensions of the time problem:
- `query_receipts` has no explicit as-of/read-clock field;
- Python-style ISO text (`2026-...T...+00:00`) and SQLite `CURRENT_TIMESTAMP` text can compare incorrectly under raw lexical TEXT order even though SQLite's datetime parser identifies the represented instant as not future.

The current views therefore contain two implicit variables: wall clock and timestamp serialization format.

Repair direction:
- canonical timestamp storage (prefer one integer UTC epoch representation at defined precision, or one canonical UTC text format);
- typed/canonical comparisons, never mixed raw lexical formats;
- explicit `as_of_valid_time` plus semantic epoch/root in QueryReceiptV2;
- live cognition resolves now once per cycle/assembly and receipts that choice;
- replay reuses the captured as-of value.

Required repair falsifiers: `BYTE_STABLE_TIME_SHIFT` and `MIXED_TIMESTAMP_ENCODING`.

## Delta E — SnapshotManifestV2 and immutable snapshot artifact

Target snapshot probe reproduced a deeper bug than the generic WAL-copy concern. The current checkpoint flow can:
- hash live UnifiedDB;
- later insert the snapshot receipt into that same DB, immediately changing the file whose prior hash was stored;
- capture graph epoch before serial file hashing;
- allow a legitimate Graph epoch advance between UnifiedDB and Graph hashes;
- record the old graph epoch with the new Graph file hash.

The target result had `unified_hash_invalidated_by_own_receipt_commit=true` and `graph_epoch_and_graph_hash_from_different_logical_instants=true`, while both DB integrity checks remained `ok`.

Repair direction:
- first materialize an immutable, transactionally consistent snapshot artifact;
- verify and hash that immutable artifact;
- persist the receipt outside the artifact or use an explicit canonical-exclusion scheme;
- authoritative recovery can snapshot UnifiedDB alone and rebuild ClayGraph, or capture both under a proven barrier;
- never claim pair-consistent epoch/hash without an atomic/barriered snapshot protocol.

For WAL profiles, main-file-only hashing/copying is additionally insufficient because the WAL is persistent database state. Prefer Online Backup API, `VACUUM INTO`, or an explicitly complete journal-aware bundle.

## Delta F — SemanticDependencyManifestV1 instead of exact Git HEAD authority

Target probe changed only the observed Git HEAD from one synthetic commit id to another. DB epoch, graph epoch, semantic root and both integrity checks stayed identical. Nevertheless both UnifiedDB and ClayGraph verification rejected because exact repo-head equality was treated as authority identity.

Repair direction:
- keep full `source_repo_head` as audit provenance;
- authority validity binds a content-addressed **minimal semantic dependency manifest**: relevant migration/runtime/materializer blobs + contract/schema identities + canonical semantic root;
- unrelated documentation/evidence/UI commits do not invalidate canonical state;
- Graph dependency manifest additionally binds canonical UnifiedDB identity.

Derived law: **provenance may record a superset of context; authority may depend only on the semantically relevant content-addressed subset.**

## Delta G — CanonicalRootChainV1

`state_epochs.root_hash` must become a deterministic protocol, not merely a text column. Candidate construction:

`SHA256('FRANK_SEMANTIC_ROOT_V1' || parent_root || epoch || tx_receipt_hash || ordered_typed_op_digests || authority_scope_digest || provenance_digest)`

Requirements:
- canonical bytes and type identities;
- no ambient wall clock;
- no activation/rank/unadmitted derived payload;
- deterministic replay;
- any semantic mutation changes the root;
- parent epoch/root compare-and-swap on admission.

This is required for same-epoch sibling discrimination, transplanted-state rejection and exact replay.

## Delta H — SelectionReceiptV2

Record provenance and selection provenance remain different invariants. Authentic canonical records can still be selected incorrectly by stale/manipulated Graph/index/ranker structure.

Required receipt surface:
- semantic root + explicit as-of;
- projection/index identity + index content digest;
- candidate-universe hash;
- normalized query digest;
- retrieval operator/ranker identity;
- filter policy digest;
- ordered candidate digest/count;
- selected refs digest;
- score-trace digest;
- admissibility digest;
- final selection receipt hash.

Emergent retrieval, Hyperposition, Graph, FTS and vector search produce candidate structures; none directly upgrade truth authority.

## Delta I — DerivedIndexHealthV1

Every derived index needs source-root identity, builder/version, content digest, health state and rebuild receipt. SQLite FTS5 provides `integrity-check` and `rebuild`; the local binding exposed these primitives successfully. Target compile/runtime capability still needs a dedicated capability receipt before product use.

## Delta J — SQLiteDefensiveOpenV1

Local binding supports `PRAGMA trusted_schema=OFF`; official SQLite guidance recommends disabling trusted schema when application-defined functions/virtual tables must not gain schema-controlled authority. Candidate normal open should evaluate:
- `trusted_schema=OFF`;
- extension loading disabled;
- `writable_schema` off;
- `SQLITE_DBCONFIG_DEFENSIVE` where the deployed binding exposes it;
- full Frank schema regression under hardened mode.

This complements, not replaces, live-schema attestation.

## Delta K — storage profiles are distinct recovery protocols

### SYSTEM_SAFE_DELETE
- SQLite 3.45.1 target-safe component profile;
- `DELETE + synchronous=FULL`;
- official SQLite semantics allow atomic transactions across file-backed ATTACHed DBs when not in WAL;
- candidate use: bounded semantic-head + projection-admission/batch co-commit;
- risk: writer serialization/fsync/lock cost.

### PRIVATE_FIXED_WAL
- use only after exact loader/source-id and regression evidence;
- WAL may improve read/write concurrency;
- multi-ATTACH transaction is not atomic across files as a set;
- therefore use canonical UnifiedDB commit + durable projection outbox + async Graph materialization + StateProjectionCertificate replay/admission.

One semantic contract, two physical lowerings.

## Delta L — effect causal/recovery closure remains orthogonal

The database findings do not replace earlier effect-chain deltas:
- immutable pre-action EffectIntent/DecisionReceipt;
- origin executor separated from current reconciler/recovery executor;
- post-hoc support mint rejected;
- historical DONE validity frozen in immutable closure receipt;
- ordinary semantic supersession cannot rewrite historical effect validity.

These belong in the final continuity conjunction because an exact DB snapshot is not enough if its external-effect history is ambiguous.

## Architecture set

The run retains six alternatives for target comparison:
1. specialized physical baseline;
2. logically unified API over specialized stores;
3. canonical UnifiedDB + durable outbox + async derived stores;
4. DELETE/FULL + bounded ATTACH atomic projection;
5. private fixed WAL + async projection admission;
6. physical monolith benchmark.

Do not select by conceptual elegance. First require replay, recovery, selection, authority-direction and crash correctness; then compare p50/p95/p99, lock wait, fsync/I/O, write amplification, RSS/CPU, projection lag and rebuild time.

## Current evidence matrix

On candidate head `d615d91b...` / tested merge `e5297e853...`:
- six deep negative discriminators: **SUCCESS — all six gaps reproduced**;
- UnifiedDB storage + pair continuity: **SUCCESS**;
- self.root current-head: **SUCCESS**;
- execution anchor: **SUCCESS**;
- effect/provider contract: **SUCCESS**;
- canonical state mutated by negative probes: **false**;
- external effect performed by negative probes: **false**.

This is exactly why the result is useful: broad component success can coexist with deeper proof-surface failures. F-V01-04 therefore stays OPEN.

## Next implementation order

1. split symmetric pair certificate into canonical UnifiedDB certificate + downstream Graph certificate;
2. add LiveSchemaAttestationV1;
3. repair temporal representation + ReplayClockV1;
4. replace live mutable snapshot hashes with immutable SnapshotManifestV2 artifacts;
5. replace exact repo-HEAD authority with SemanticDependencyManifestV1;
6. add StateProjectionCertificateV1 and Graph read gating;
7. shadow CanonicalRootChainV1 and run sibling/transplant/replay tests;
8. add SelectionReceiptV2 and repeat selection-integrity adversaries;
9. target A/B DELETE+ATTACH vs fixed-WAL+outbox;
10. compose all passing storage/schema/root/projection/clock/snapshot/selection/external-floor/effect layers into one crash/restart/rollback/rebuild/replay acceptance receipt.

## Promotion boundary

**HOLD_AND_SPLIT_PROOF_SURFACES.**

No whole Frank v0.1 acceptance, canonical DB migration, external provider effect, Frank/self.root Harness mutation authority or final training authorization follows from these negative results.
