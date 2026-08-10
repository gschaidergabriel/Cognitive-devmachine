# UnifiedDB Deep Delta Pack — State Commitment, Publication, Projection and Witness Continuity

Run: `unifieddb-20260811T0440p0700-chatgpt-secondary-deep-delta-pack`

Status: **12 DELTAS MATERIALIZED / 4 LOCAL NEGATIVE RESULTS / TARGET PROMOTION HOLD**

## Fresh-state correction and non-overlap

This continuation did not repeat the previous V10 state-lineage proposal. Current target work has advanced materially:

- the execution-generation effect fence is already supported on current target evidence and is not rebuilt here;
- PR #267/#273 own selected semantic-head / continuation experiments;
- PR #286 owns the fused WAL-safety + materialization-pair lane;
- PR #289 owns the stacked full semantic-root constructor and explicitly preserves a known actual-DDL attestation gap;
- PR #288 is separately testing a private fixed SQLite runtime; its target workflow was observed queued, therefore no PASS is claimed here.

The new work starts where those mechanisms stop.

## Central finding

A safe UnifiedDB state cannot be represented by one scalar such as `epoch`, one stored schema digest, or even one semantic root. Frank needs a **layered state commitment and publication contract** whose layers answer different questions:

1. Is the physical logical schema actually the expected materialization?
2. What exact semantic content/state is this?
3. Which state continuation head was selected?
4. Has the state finished publication and become runnable?
5. Which exact state produced a query/assembly/GWT/Needle result?
6. Does the current ClayGraph derive from that exact state?
7. Can replay/recovery reconstruct the same published commitment?

Collapsing these into one epoch/hash creates false equivalences.

## New negative results

### NR-1 — certificate metadata is not actual schema attestation

A local disposable SQLite experiment reproduced the PR #286 gap: after changing actual DDL with `CREATE TABLE unauthorized_drift(...)` while leaving certificate metadata unchanged, the metadata-only gate remained valid while an independently recomputed actual-schema fingerprint changed. Therefore `migration_chain_digest` and `actual_schema_fingerprint` must be separate evidence fields.

### NR-2 — numeric epoch is not semantic identity

A local sibling-state falsifier kept `unified_epoch=7` constant while changing the semantic root from R1 to R2. An epoch-only ClayGraph gate still accepted the old graph; a source-root gate rejected it. Current ClayGraph materialization state therefore needs exact source semantic root/selected-head binding in addition to epoch.

### NR-3 — full semantic root on every mutation is an expensive default hot path

A local PR289-style proxy scaled from roughly 9 ms at 1k rows to roughly 1.07 s and 7.7 MB peak Python allocation at 100k rows in the measured configuration. In a warm 100k-row comparison, a full root was about 109x the latency of a single ordinary committed mutation. These are local synthetic shadows, not VPS performance claims, but they are strong enough to reject unconditional full rehash on every write as the default design without further evidence.

### NR-4 — root metadata can recursively destabilize the root

When a semantic-root value was persisted inside the same content domain being hashed, the content root changed. A root/publication receipt therefore cannot recursively belong to the exact content root it records unless a carefully defined higher-order fixed-point scheme is adopted. The simpler candidate is an explicit `ROOT_PUBLICATION_META` firebreak outside the content root and bound one layer above.

## Twelve architecture deltas

### UDB-D11 ActualMaterializationAttestation

Keep the executable migration-chain digest, but add an independently recomputed fingerprint of actual live `sqlite_schema` declarations. Normal open/publication checks both. This catches DDL drift that leaves stored certificate rows untouched. The actual fingerprint is a drift-attestation mechanism, not a proof that two differently written SQL schemas are semantically equivalent.

### UDB-D12 StatePublicationBarrier

Split state creation from state publication:

`authoritative DB mutation + PREPARED receipt -> external selected-head CAS -> PUBLISHED finalize`.

A DB commit alone is not yet the selected runnable self.root continuation. Crash windows become explicit and recoverable; an old DB with a surviving newer selector fails closed.

### UDB-D13 Hierarchical incremental state commitment

Instead of one full global scan on every write, compute deterministic table/domain roots and combine them into the top Frank state commitment. Authorized writes recompute only dirty leaves and affected parent roots. Periodic/full recovery audits recompute the whole state and must exactly equal the incremental commitment.

A local 50-table / 100k-row prototype changed one row, recomputed only the dirty table plus top combination in 3.726 ms versus 175.13 ms for a full recomputation: **47.0x faster**, with exactly equal final roots in that tested case. This is mechanism evidence only.

### UDB-D14 RootDomainRegistry

Every persistent semantic object receives one typed root-domain role such as `AUTHORITATIVE_SEMANTIC`, `EXECUTION_CONTINUITY`, `EFFECT_AND_CAUSAL_EVIDENCE`, `POLICY_CONTRACT`, `MATERIALIZATION_META`, `ROOT_PUBLICATION_META`, `DERIVED`, or `CACHE`. Unknown persistent tables fail closed rather than silently disappearing from identity/continuity semantics.

### UDB-D15 Graph source-root/head binding

Extend ClayGraph materialization/projection receipts from `source_semantic_epoch` to exact `source_selected_head` + `source_semantic_root`. Epoch remains useful ordering metadata but is not sufficient identity evidence.

### UDB-D16 GraphProjectionRoot

For deterministic graph surfaces, derive a `graph_projection_root` from the source state and derivation program. Rebuilding from the same selected semantic root with the same deterministic materializer must reproduce the same projection root. Dynamic activation/salience may remain separate and never becomes truth authority.

### UDB-D17 StateWitness

Every model-, GWT-, Needle-, retrieval-, and effect-relevant read carries a compact witness binding the selected head, semantic commitment/root, UnifiedDB materialization, graph source/projection and candidate/query identity. Read-only observation may explicitly be stale; mutation/effect boundaries must revalidate or rebase.

### UDB-D18 SelectionWitness

Record provenance of **selection itself**, separately from provenance of stored records: candidate-universe hash, selection policy/scorer identity, ordered result references, admissibility and originating StateWitness. This closes the gap where all source records are valid but the selected subset came from a stale/different state or policy.

### UDB-D19 Delta-chain + checkpoint audit

Use append-only transaction/event delta receipts as the cheap mutation-level integrity spine, periodically anchored by a full hierarchical semantic commitment. Replay from checkpoint/cursor must reconstruct the exact published state commitment. This is a candidate to reduce hot-path cost without trusting a mutable root cache blindly.

### UDB-D20 Multi-DB rollback-journal migration experiment

SQLite's documented multi-database transaction semantics are stronger outside WAL: attached databases can participate in one atomic transaction through rollback-journal/super-journal semantics when documented preconditions hold, whereas WAL transactions are atomic only per database file. Because the target currently has a fail-closed DELETE+FULL fallback candidate, a bounded experiment should compare deliberate rollback-journal `ATTACH` migration against the current KEEP_ISOLATED pair-certificate strategy. This is an experiment, not a default architecture change.

### UDB-D21 Schema execution hardening

Evaluate connection hardening such as `trusted_schema=OFF` and defensive runtime settings where the actual Python/SQLite target supports them without breaking legitimate schema/runtime behavior. This narrows schema attack surface but never replaces materialization attestation or effect authority.

### UDB-D22 Changed-row/root accelerator

Evaluate the SQLite Session extension or a simpler central-writer dirty-table journal as a changed-row accelerator. Session/change-set semantics are attractive for incremental state commitments, but target build availability and table-primary-key coverage are currently unverified; therefore this remains optional research, not an assumption.

## State commitment structure

Candidate composition:

`table roots -> typed domain roots -> FrankStateCommitment`.

The top commitment can combine at least semantic content, execution continuity, causal/effect evidence, policy contracts and materialization state. Publication metadata is intentionally outside the content root it records. External selected-head and execution-floor anchors remain in separate rollback domains and are conjunctive recovery/continuation evidence, not SELF.

## StateWitness / TOCTOU consequence

A query can be perfectly correct when issued and still become unsafe to use after state turnover. Therefore the read result retains its StateWitness through assembly, GWT, Needle/tool routing and effect proposal. If the selected semantic head changed before mutation/effect, the system either revalidates that the result is still admissible or re-runs selection under a new witness. Silent adoption of a stale result into a newer state generation is forbidden.

## ClayGraph consequence

ClayGraph remains derived/rebuildable. The schema-pair certificate only establishes materialization compatibility; it does not establish graph payload freshness. Current graph evidence must independently bind:

`selected semantic head/root -> derivation program -> graph projection root -> graph epoch`.

This preserves physical isolation while making semantic coupling explicit and falsifiable.

## Storage consequence

The previous WAL safety blocker remains independent. A fixed/private SQLite build may restore WAL as an eligible runtime candidate after target evidence, but it does not remove the need for semantic publication, selected-head continuity, graph source-root binding, or actual schema attestation. Conversely, rollback-journal fallback may offer a stronger multi-file migration primitive, but only target crash/power/resource tests can decide whether using it is worth the operational tradeoff.

## Next target falsifiers

Highest-value sequence:

1. Patch the PR #286 successor to attest actual live schemas and reproduce/reject real DDL drift with untouched metadata.
2. Run PR #289 full root versus hierarchical incremental root on identical current target snapshots and randomized mutations; require exact root equivalence.
3. Add source-root/head binding to ClayGraph and run the same-epoch sibling-state falsifier plus deterministic rebuild-root checks.
4. Emit StateWitness diagnostically through query/GWT/Needle/effect paths, then inject state turnover between read and use.
5. Compose existing selected-head candidate with PublicationBarrier and crash at every PREPARED/CAS/PUBLISHED boundary.
6. Execute checkpoint/replay/restore and external-floor failure-domain matrix on the accepted target.
7. Measure p50/p95/p99, CPU, RSS, storage I/O, write amplification, checkpoint/rebuild latency and full-audit duty cycle.
8. Compare the full layered candidate against the simplest viable architecture. Complexity is not promoted merely because it is more sophisticated.

## Strongest counterhypothesis

The layered design may overfit rare failure modes and impose excessive implementation/maintenance cost. The required comparator is therefore deliberately strong and simple: actual-schema-attested PR #286 + PR #289 full semantic root + the existing selected-head CAS/continuation mechanism, without incremental root caches and broad StateWitness enforcement. The additional layers promote only where target falsifiers or resource evidence show material benefit.

## Promotion decision

**HOLD.** The deep delta pack is durable research/architecture input, not a Frank runtime promotion. It mutates no canonical Frank database, performs no external effect, grants no self-Harness authority, and does not authorize final training.
