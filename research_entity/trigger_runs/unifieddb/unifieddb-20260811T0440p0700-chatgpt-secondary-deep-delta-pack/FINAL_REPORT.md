# UnifiedDB Deep Delta Pack — State Commitment, Publication, Projection and Witness Continuity

Run: `unifieddb-20260811T0440p0700-chatgpt-secondary-deep-delta-pack`

Status: **14 DELTAS MATERIALIZED / 4 LOCAL NEGATIVE RESULTS / ONE NEW PARALLEL TARGET PREFLIGHT PASS / PRODUCT PROMOTION HOLD**

## Fresh-state correction and live refresh

This continuation starts after the previous V10 state-lineage work and does not rebuild mechanisms already owned by current target lanes. PR #267/#273 own selected semantic-head and continuation/restore experiments; PR #280 owns current V17 causal-support closure; PR #286 owns the fused WAL-safety + materialization-pair lane; PR #289 owns the stacked full semantic-root constructor and explicitly preserves an actual-DDL attestation gap.

During this run PR #288 advanced from queued to **target-VPS PASS as a bounded private-runtime preflight**. On `clay` / `digital-retina`, Python 3.12.3 was proven to load an official private SQLite 3.53.4 library with exact source-id `2026-07-24 19:02:57 bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc`; V16 ingress remained PASS and a 256-write two-connection WAL smoke ended with integrity `ok` and zero FK violations. No system install or canonical Frank state mutation occurred and whole-Frank acceptance was not claimed.

The same refresh exposed a new cross-candidate incompatibility: the current system SQLite 3.45.1 reports `ENABLE_SESSION` in its compile options, while the successful private 3.53.4 Python runtime build did not. Therefore a runtime upgrade must be evaluated as a **capability-vector change**, not just a version number change. Exact-head PR #286 and #289 target workflows observed in this refresh were cancelled, not PASS.

## Central finding

A safe UnifiedDB state is not one scalar. `epoch`, stored migration digest, semantic root, selected continuation head, graph epoch and SQLite runtime identity answer different questions. Frank needs a layered contract:

`actual materialization -> typed semantic commitment -> selected continuation -> publication closure -> witnessed reads/selections -> source-root-bound derived projections -> replay/recovery audit`.

Collapsing these layers produces false equivalences.

## Four reproduced negative results

**NR-1 — metadata certificate != actual schema.** A disposable DDL mutation with untouched certificate rows remained accepted by the metadata-only check while an independently recomputed `sqlite_schema` fingerprint changed. `migration_chain_digest` and `actual_schema_fingerprint` must remain separate evidence.

**NR-2 — epoch != semantic identity.** A sibling state retained `unified_epoch=7` but changed root R1 -> R2. An epoch-only ClayGraph gate still accepted the old graph; an exact source-root gate rejected it.

**NR-3 — full root per mutation is a poor default hot path.** A local PR289-style proxy scaled from ~9 ms/1k rows to ~1.07 s and ~7.7 MB peak Python allocation at 100k rows in one configuration. In another warm 100k-row comparison the full root was ~109x the latency of one ordinary committed row mutation. These are local mechanism/resource shadows, not VPS measurements.

**NR-4 — root self-reference is unstable.** Persisting a root receipt inside the exact content domain being hashed changed that root. Publication/root metadata needs a separate hash domain or higher-layer commitment.

## Fourteen deltas

### D11 — ActualMaterializationAttestation

Retain the executable migration-chain digest but independently fingerprint actual live `sqlite_schema` declarations by physical role. Normal open/publication must verify both. The actual fingerprint detects drift; it is not a claim of general SQL semantic equivalence.

### D12 — StatePublicationBarrier

A DB commit is not automatically the selected runnable continuation. Candidate protocol:

`DB mutation + PREPARED receipt -> external selected-head CAS -> DB PUBLISHED`.

Crash windows become explicit: prepared/new DB with parent selector can resume publication; prepared DB with already-advanced selector can finalize; rolled-back DB with surviving newer selector fails closed. Whole-domain rollback of DB plus selector remains an explicit outer failure-domain limitation.

### D13 — Hierarchical incremental commitment

Use deterministic table/domain roots and combine them into a top `FrankStateCommitment`. Authorized writes recompute dirty leaves only; periodic/full recovery audits recompute the complete state and must match. In a local 50-table/100k-row proxy, one-row mutation + dirty-table recomputation took 3.726 ms versus 175.13 ms for full recomputation, a 47.0x difference, with equal final roots in that case.

### D14 — RootDomainRegistry / self-reference firebreak

Every persistent state surface is typed into domains such as `AUTHORITATIVE_SEMANTIC`, `EXECUTION_CONTINUITY`, `EFFECT_AND_CAUSAL_EVIDENCE`, `POLICY_CONTRACT`, `MATERIALIZATION_META`, `ROOT_PUBLICATION_META`, `DERIVED`, `CACHE`, or `EXTERNAL_BACKING`. Unknown persistent state fails closed. `ROOT_PUBLICATION_META` is not recursively included in the content root it records.

### D15 — ClayGraph source-root/head binding

`source_semantic_epoch` is retained for ordering but current graph validity additionally binds exact source selected-head and semantic root. This closes same-epoch sibling-state ambiguity.

### D16 — GraphProjectionRoot

Deterministic graph surfaces emit a projection root bound to source root/head and derivation-program identity. Rebuild from identical source + deterministic materializer must reproduce the projection root. Activation/salience remains separate and non-authoritative.

### D17 — StateWitness

Model/GWT/Needle/retrieval/effect-relevant reads carry a compact witness containing selected head, semantic commitment, materialization, graph source/projection and candidate/query identity. Explicitly stale read-only observation can be allowed; mutation/effect boundaries must revalidate or rebase after state turnover.

### D18 — SelectionWitness

Selection provenance is separate from record provenance. Bind candidate-universe hash, selection policy/scorer identity, ordered result refs, admissibility and originating StateWitness. Valid source records do not prove that a stale or mismatched selection is valid now.

### D19 — Delta chain + checkpoint audit

Use immutable transaction/event delta receipts as a cheap mutation-integrity spine and periodically anchor them in a full semantic commitment. Replay from checkpoint/cursor must reconstruct the exact published commitment. Cached/incremental roots remain non-authoritative unless full audit and transaction-bound dirty tracking agree.

### D20 — Rollback-journal multi-DB migration experiment

SQLite documents atomic transactions across attached databases under rollback-journal conditions, while WAL only guarantees atomicity per file. A local crash-before-commit proxy over two attached DELETE+FULL databases restored both old values, while a normal commit advanced both. This supports a bounded comparison between deliberate rollback-journal `ATTACH` schema migration and the KEEP_ISOLATED pair-certificate strategy; it is not target power-loss proof or a default architecture decision.

### D21 — Schema execution hardening

Evaluate `trusted_schema=OFF` and defensive connection settings where the exact target runtime supports them without breaking legitimate behavior. Hardening narrows schema attack surface; it never replaces materialization attestation, provenance or effect authority.

### D22 — Changed-row/root accelerator, now feature-gated

SQLite Session/change-set support is attractive for changed-row tracking but may not survive the selected fixed-runtime build. The current system build advertises `ENABLE_SESSION`; the successful private 3.53.4 Python runtime observed here did not. Therefore the simpler portable baseline is central-writer dirty-table tracking; Session is optional only if the accepted runtime capability contract explicitly guarantees it.

### D23 — StorageRuntimeCapabilityContract

An accepted SQLite runtime is identified by more than `sqlite_version`: bind version, `sqlite_source_id`, loaded library identity/hash, thread-safety and the required compile-feature vector. Runtime swaps must run feature compatibility and Frank regression tests. A fixed WAL bug with missing required capabilities is not a complete replacement.

### D24 — Semantic identity vs physical runtime identity

SQLite runtime identity/capabilities belong in a materialization/runtime commitment, **outside Frank semantic content identity**. A safe engine upgrade can change version/source-id/compile options without pretending Frank's logical memories/goals/world/self changed, while still invalidating physical assumptions and requiring revalidation/rebuild where necessary.

## New composition

Candidate top-level structure:

`typed table roots -> domain roots -> semantic/state commitment`

plus conjunctive, separately scoped evidence:

`actual materialization attestation + storage runtime capability receipt + external selected continuation head + publication receipt + GraphProjectionWitness + State/SelectionWitness + replay audit`.

None of these hashes or witnesses mints SELF, truth or effect authority.

## Why this is deeper than V10

V10 primarily attacked stale execution, sibling lineage and rollback-domain continuity. This run shows that continuity can still fail **after** those protections if the physical schema drifts, the graph comes from a sibling root with the same epoch, a correct query is used after state turnover, the root receipt recursively contaminates its own identity domain, or a storage upgrade silently changes feature capabilities. Those are orthogonal failure classes and therefore require separate falsifiers.

## Next target sequence

1. Extend PR #286 successor with independently recomputed actual-schema fingerprints and reject real DDL drift with untouched metadata.
2. Recompose PR #289 semantic root on that attested materialization and compare full versus hierarchical commitments on identical target snapshots/randomized mutations.
3. Bind ClayGraph materialization to source selected-head/root and add deterministic projection-root replay.
4. Emit StateWitness/SelectionWitness diagnostics, then inject state turnover between read, GWT/Needle selection and mutation/effect use.
5. Compose existing selected-head mechanism with the PublicationBarrier and crash at every transition.
6. Decide the SQLite runtime capability vector: integrate the target-PASS private 3.53.4 path or build an equivalently fixed runtime with all required capabilities; do not assume Session support.
7. Run crash/restart/checkpoint/replay/restore plus external-selector/floor failure-domain matrix and measure p50/p95/p99, CPU, RSS, storage I/O, write amplification and full-audit duty cycle.
8. Compare against the simplest viable architecture; extra machinery promotes only if correctness/recovery/resource evidence justifies it.

## Strongest counterhypothesis

The layered architecture may overfit rare failures and cost too much complexity. The comparator remains deliberately simple: actual-schema-attested pair state + full semantic root + existing selected-head continuation + integrated fixed SQLite runtime, without hierarchical caches and broad witness enforcement. Additional layers promote only if target falsifiers demonstrate material failure prevention or resource benefit.

## Promotion decision

**HOLD.** Research is durable in Clay Draft PR #227, but `main` synchronization and current-head target execution remain pending. No canonical Frank database was mutated, no external effect was performed, no whole Frank v0.1 acceptance is claimed, no target self-Harness authority was granted, and final training remains unauthorized.
