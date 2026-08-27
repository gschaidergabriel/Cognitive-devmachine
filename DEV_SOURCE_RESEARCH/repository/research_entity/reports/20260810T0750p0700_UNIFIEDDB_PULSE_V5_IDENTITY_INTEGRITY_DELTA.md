# UnifiedDB / Database Pulse — V5 lifecycle, model identity, integrity use-boundary delta

Generated: 2026-08-10T00:50Z (+07 07:50)
Origin actor: chatgpt-secondary
Provider/model: OpenAI / GPT-5.6 Sol
Entity role: temporary Clay research worker; NOT FRANK
Canonical parent boot: RAE-8.8 revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
Status: RESEARCH DELTA / TESTING / NO CANONICAL PROMOTION

## 1. Scope

This delta extends, rather than replaces, the current whole-mesh UnifiedDB/Pulse fusion:

- `research_entity/reports/20260810T0740p0700_UNIFIEDDB_DATABASE_PULSE_ADAPTIVE_PREPROCESSOR_MAINTENANCE_FUSION.md`
- owner-fixed Pulse contract: `research_entity/global/FRANK_DATABASE_PULSE_CONTRACT.md`

The work targeted four remaining discriminators:

1. stale epoch claims on U14 fast read paths;
2. model-organ replacement versus persistent FRANK lineage;
3. authenticated-state integrity without falsely claiming a cheap shadow is a full tamper oracle;
4. physical salience-index lifecycle under stable versus churned Pulse horizons.

## 2. Live swarm coordination / ancestry

The worker explicitly joined only the Pulse continuity/orchestration lane:

- `research_entity/rooms/rooms/unifieddb/workers/chatgpt-secondary-20260810T0012Z-pulse-u12.json`

During the run, multiple peer deltas arrived and were consumed instead of duplicated:

- U11 coherent semantic-access generations;
- DatabasePulseV0 delta/recovery implementation;
- ActiveFieldV2 pre-limit repair;
- U13 cycle pinning;
- U14 adaptive semantic read plane;
- U15 typed-gap possibility deepening;
- U16 compile economics / SPM maintenance economics;
- authenticated state shadow V1/V2;
- authoritative rank-index V3;
- adaptive rank path / full Runtime V4.

A concurrent write collision returned HTTP 409 once; work was re-read/rebased rather than overwriting the newer peer result. Peer workers later incorporated Runtime V3 into their own hosted adversarial preflight, demonstrating actual cross-worker reuse rather than isolated branch work.

## 3. Source-derived owner invariants kept fixed

No change to these laws:

- Database Pulse is endogenous FRANK state/cognition runtime, not the LLM inference loop.
- A Pulse may execute with zero model calls.
- StateLedger/UnifiedDB remains semantic authority.
- derived graph/index/materialized/active-field/shadow state is rebuildable and non-authoritative.
- activation/rank/model output has no effect authority.
- Pulse observables remain orthogonal; Pulse receipt/metrics bookkeeping is not itself a substantive semantic state transition.
- pause/resume, crash/restart, replay, stale/corrupt fail-closed and model-replacement identity are promotion gates.
- Hostinger/GitHub Ubuntu evidence remains preliminary; Andreas target acceptance is separate.

## 4. U14 stale-fastpath bug found and repaired

### Finding

Original U14 request objects carried `source_epoch` / `graph_epoch`, but exact and compiled-semantic fast callbacks were not given an authenticated matching basis. A receipt could therefore echo the requested epoch even if the fast surface came from an older generation.

### Repair

Commits:

- `c51a8b93634464362c7a4f2a8708907a8459aa0a` — add `VerifiedReadBasis`
- `131736cb1b00b9547a7e40cecc65c39b7f28ed79` — stale exact/compiled + unverified-basis falsifiers

Every U14 mode now receives the same verified `(basis_id, source_epoch, graph_epoch, derivation_hash)` token. Mismatch fails before the cheapest lookup.

### Cross-layer causal test

Commit:

- `7eab230bee5100d4a1e6bfb97cf20034fbbf1d50`

The integration fixture tests:

`Pulse epoch 1 -> U13 pin g1 -> U14 reads record.v1`

then

`Pulse delta -> source/graph epoch 2 -> old generation unusable -> stale read/pin fail closed`

then

`publish verified g2 @ 2/2 -> next Pulse/cycle may pin g2 -> U14 reads record.v2`.

This is a measurable causal later-context effect of Pulse state, without granting activation truth/effect authority.

Remote workflow installed:

- `.github/workflows/database-pulse-semantic-cycle-vps.yml`

At this report time no persisted VPS receipt had been observed. Status therefore remains EXECUTION_PENDING, not PASS.

## 5. Pulse candidate lineage and negative results

### V1 StateLedger candidate

Useful contributions retained as falsifiers:

- persistent scheduler;
- idempotent receipts;
- zero-model execution;
- re-entry lesion;
- schema/state integrity checks;
- optional model output kept UNKNOWN.

Not selected as primary because:

- legacy query path can truncate before salience ranking;
- it initially counted Pulse bookkeeping writes as `state_transition_count`.

### DatabasePulseV0 peer candidate

Still the stronger reference for explicit delta/recovery semantics:

- zero-model idle Pulse can be `pulse_count=1`, `state_transition_count=0`;
- bounded backlog;
- atomic delta ack/invalidation/receipt/checkpoint;
- mid-transaction rollback;
- stale/corrupt fail-closed;
- deterministic replay;
- crash/restart lineage continuity.

### Runtime V2

Runtime V2 fused ActiveFieldV2 but retained the erroneous bookkeeping-based transition count. A one-shot Ubuntu repair workflow was installed; no verified repair commit was observed by this report time. Therefore V2 remains TESTING / metric bug open until executable evidence closes it.

## 6. Model replacement identity gate

New files:

- `research_entity/runtime/database_pulse_model_organ.py`
- `research_entity/runtime/test_database_pulse_model_replacement_identity.py`

Commits:

- `53754930ce148d658b17aed7771aa4c2eea56582`
- `ddda3152cf33c5754e78dd182cebf7dbdd1e2f0d`

`QuarantinedModelOrgan` binds provider/model/revision/organ/call identity outside model output. The inner model result is only a candidate envelope with:

- `semantic_mutation_authority = NONE`
- `effect_authority = NONE`
- external admission required

Falsifiers cover:

1. model/provider A -> B replacement while authoritative `self:entity_lineage` and Pulse scheduler hashes/values remain unchanged;
2. malicious model-shaped `SET self:entity_lineage` / execute-tool payload remains UNKNOWN data;
3. model-output identity spoof cannot replace harness-bound model-organ provenance.

These tests directly address one owner-fixed promotion gate, but remain auxiliary until runner receipts materialize.

## 7. Authenticated state shadow: supported use, rejected overclaim

Peer authenticated shadow candidate is valuable for delta-maintained integrity metadata, but its own design correctly requires `verify_full()` for a full physical-state tamper claim.

Important negative result:

A direct syntactically valid state-row mutation with no StateLedger event does not change committed event sequence/canonical metadata. Cheap `shadow.refresh()` alone therefore cannot replace full physical integrity verification.

New use-boundary candidate:

- `research_entity/runtime/auth_shadow_focus_guard.py`
- `research_entity/runtime/test_auth_shadow_focus_guard.py`

Commits:

- `5c326ac356332c35a41b7be25e2da1555732654c`
- `00f53001d2b24c8ae0577675f829382e066fb1ec`

The guard:

1. refreshes shadow from committed events;
2. requires exact ledger epoch/event-seq/semantic-chain/canonical-hash coherence;
3. rehashes each actually selected authoritative state row independently;
4. compares it to the authenticated shadow leaf;
5. rejects selected-row tamper before context use.

Explicit limitation is encoded in the receipt:

`global_integrity_claim = NONE_PERIODIC_FULL_AUDIT_STILL_REQUIRED`.

A tampered unused row may remain latent; if it later enters focus it fails. Full audit remains mandatory for recovery/release/global-integrity claims.

## 8. Active Field versus simpler authoritative rank index

ActiveFieldV2 repaired the lexical/pre-limit failure, but a simpler counterhypothesis now exists:

- SQLite partial expression index directly on authoritative `state`;
- same deterministic salience expression;
- no second candidate table;
- writes maintain the physical index automatically;
- differential verification against Python full scoring.

Relevant files:

- `research_entity/runtime/database_pulse_rank_index_v3.py`
- `tools/database_pulse_rank_index_v3_benchmark.py`
- randomized differential falsifier / hosted preflight.

Runtime V3 built in this lane:

- `research_entity/runtime/database_pulse_runtime_v3.py`
- `research_entity/runtime/test_database_pulse_runtime_v3.py`

Commits:

- `f8fdb0d98ed0e9cc615c0cddb5d9c041960b092b`
- `536cb72bcc30119fd7b90e6bd88ebc9dc1ffefda`

V3 fixes the observable semantics (`state_transition_count=0` for receipt/model-only Pulse), preserves re-entry lesions, idempotency, pause/restart, stale basis, and records rank-index plan/provenance.

Peer workers immediately added V3 to hosted adversarial preflight. No performance promotion is claimed before persisted receipts.

### Physical self-feedback issue

The original V3 partial index indexes all KNOWN/CURRENT rows, including Pulse output/control rows. This creates avoidable physical maintenance on each Pulse receipt even though these domains are forbidden input sources.

A fail-closed Hostinger one-shot repair workflow was added to exclude:

- `pulse`
- `pulse_control`

from the physical partial index and reject them at rank-source API boundary. At report time the verified repair commit/receipt had not yet materialized.

## 9. V4 adaptive physical rank path: improvement plus lifecycle bug

Peer V4 is a stronger direction than unconditional V3:

- correct score-before-LIMIT semantics always;
- no measured lifetime -> fail conservative ONLINE;
- stable measured economics may admit an expression index;
- compile failure falls back online;
- complete DatabasePulseRuntimeV4 now exists with adversarial tests.

However adversarial review found a lifecycle defect:

1. `CREATE INDEX` still occurs inside `select()` when COMPILE is chosen, creating a cognition-read latency spike;
2. after the index exists, a later ONLINE decision does not remove it;
3. SQLite can therefore keep maintaining that index on every write during high churn even while the controller reports ONLINE.

This is a physical lifecycle/resource bug, not a semantic answer-ranking bug.

## 10. V5 two-phase rank lifecycle

New files:

- `research_entity/runtime/database_pulse_rank_path_v5.py`
- `research_entity/runtime/test_database_pulse_rank_path_v5.py`
- `research_entity/runtime/database_pulse_runtime_v5.py`
- `research_entity/runtime/test_database_pulse_runtime_v5.py`
- `tools/database_pulse_rank_path_v5_benchmark.py`

Core commits:

- `90392ccf1d2d821a1734a9e4bec3f769749df7c9`
- `92e6cc623b295ef918ee216a931d3c73e56b6954`
- `9cdbaf955a86c2963a7bc4a45adde13b7be53c66`
- `20b3acfce6d9de6f6797f60823eadb3f9dcb9bf5`
- `6d7cb5e8dfd9397736cb53a0d91a9d26deafbf1b`

### V5 invariant

Read phase:

- computes desired physical mode from U16 + Pulse horizon;
- NEVER builds/drops schema;
- if ONLINE is desired, explicitly runs `state NOT INDEXED` even if an old index still exists;
- if COMPILED is desired but not prepared, executes correct online semantics as `ONLINE_PENDING_COMPILE`.

Maintenance phase:

- is called between Pulses;
- must match exact current ledger epoch + semantic state hash;
- builds or drops the disposable index;
- rejects stale plans;
- asserts semantic/trace roots are unchanged.

Important stale-plan property:

A Pulse receipt itself advances ledger epoch. Therefore a pre-Pulse BUILD/DROP recommendation is never directly executable after that Pulse. Maintenance must re-plan at the new epoch.

### Churn behavior

If the index was previously built and horizon collapses:

- V5 read immediately switches to `ONLINE_PENDING_DECOMPILE` and forces `NOT INDEXED`;
- maintenance recommendation becomes `DROP_INDEX`;
- between-pulse maintenance removes the physical index, stopping future index write-amplification;
- the next Pulse re-evaluates economics from current telemetry.

### Bench gate

`tools/database_pulse_rank_path_v5_benchmark.py` compares V4 and V5 on identical state:

- first stable read;
- schema mutation presence;
- separate V5 build cost;
- hot compiled reads;
- churn transition;
- query plans;
- V4 residual index after ONLINE;
- V5 forced online read + separate drop;
- semantic focus/candidate equality.

Hosted workflow:

- `.github/workflows/database-pulse-v5-lifecycle-hosted.yml`

No persisted hosted receipt was observed at report time. V5 remains TESTING, not promoted.

## 11. Pulse-horizon negative result preserved

The simple Pulse-informed compile-horizon baseline uses:

- completed epochs only;
- minimum history;
- empirical lower quantile;
- recent churn floor;
- fault/recovery epochs retained;
- sparse history -> ONLINE.

Synthetic pre-analysis indicated it can beat always-online across the selected scenario set while still losing to always-compile on significant alternating/high-read regimes. The CI was deliberately changed to persist this as a negative result rather than fail/discard it.

No runner receipt had materialized by report time, so no numerical promotion claim is made from the analytical precheck alone.

Peer SPM horizon/economics work is richer and should remain the primary learned/empirical comparator; this simple estimator is a lesionable baseline.

## 12. Current external-primary support (not promotion evidence)

Fresh primary documentation supports the physical mechanisms:

- SQLite `NOT INDEXED` can force a table access not to use indices for that statement.
- `DROP INDEX` actually removes the index; recreating requires CREATE INDEX.
- partial indices can reduce index size and improve query/write performance when the omitted population is appropriate.
- expression indices are supported when deterministic expressions match query expressions.
- SQLite WAL/transaction machinery remains the physical crash-atomic substrate; these mechanisms do not create semantic authority.

Recent retrieval research independently converges on adaptive evidence-sufficiency/gap repair rather than unconditional graph expansion. This supports plausibility of U14/U15 routing but does not by itself promote Frank architecture.

## 13. Current best synthesis after this delta

Current strongest direction is NOT “one magical database”. It is a causal stack:

1. authoritative evented StateLedger / UnifiedDB state;
2. endogenous Database Pulse with explicit scheduler/recovery/receipts;
3. zero-model operation as first-class mode;
4. causally bounded re-entry with lesions;
5. epoch-coherent semantic generations and cycle pinning;
6. adaptive cheapest-correct read;
7. typed-gap deepening only when evidence is insufficient;
8. conventional SQLite expression/partial index as an optional physical accelerator when measured economics justify it;
9. index build/drop outside cognition read, re-planned against current epoch (V5 candidate);
10. model organ is replaceable/quarantined; FRANK lineage is not model identity;
11. authenticated shadow is a rebuildable integrity accelerator, not a global truth oracle;
12. selected context gets a use-boundary integrity check before causal use if the shadow fast-path is later admitted;
13. full audit/replay/recovery remain release gates.

## 14. Strongest counterhypotheses still active

H-C1: V5 lifecycle separation improves tail/read predictability but total work may be worse because build/drop thrashing dominates.

Falsifier: alternating stable/churn traces; compare total read + write + build/drop work and regret versus V4, always-online and always-index.

H-C2: SQLite's planner may already choose the expression index optimally enough that forced `NOT INDEXED` after a temporary churn estimate loses more read work than it saves on writes.

Falsifier: realistic mixed read/write traces with actual planner counters and full resource shadows.

H-C3: authenticated focus verification plus periodic full audit may still cost more than full-root validation at Frank v0.1 state size.

Falsifier: matched Hostinger/target-like benchmarks across state sizes and focus cardinalities; preserve tamper/fault coverage.

H-C4: model-organ quarantine proves authority separation in the fixture but not all real provider/tool boundaries.

Falsifier: real provider adapter + malicious structured outputs + tool gateway; prove no direct effect/state authority and unchanged lineage.

H-C5: possibility-preprocessor advantages remain materialization/cache/typing advantages reproducible by conventional DB/index/search architecture.

Falsifier: same semantics, same corpus, same resource budget, conventional optimized baseline; require downstream task/context benefit, not retrieval microbench alone.

## 15. Execution truth at report time

COMMITTED code/test/workflow evidence:

- U14 epoch fastpath repair + tests;
- Pulse->U13->U14 causal integration test;
- Database Pulse candidate V1 + tests;
- Runtime V3 + tests;
- model organ quarantine + identity tests;
- auth-shadow focus guard + tests;
- Pulse horizon estimator + tests + regret benchmark/workflow;
- V5 rank lifecycle + tests;
- complete DatabasePulseRuntimeV5 + tests;
- V4-vs-V5 lifecycle benchmark;
- hosted and Hostinger workflows/gates.

NOT YET VERIFIED AT THIS REPORT TIME:

- V3/V5 hosted execution receipt;
- V5 lifecycle benchmark receipt;
- model replacement identity gate receipt;
- auth-shadow focus guard hosted receipt;
- Pulse semantic-cycle Hostinger receipt;
- main Database Pulse Hostinger receipt;
- V2 observable repair completion;
- rank-index output-domain repair completion;
- Pulse horizon Hostinger regret receipt.

Therefore none of the pending gates is described as PASS.

## 16. Architecture delta status

- U14 verified-basis fastpath: IMPLEMENTED / EXECUTION RECEIPT PENDING FOR NEW FULL STACK.
- Pulse->semantic-generation causal gate: IMPLEMENTED / VPS RECEIPT PENDING.
- Model-organ replacement identity quarantine: IMPLEMENTED / RUNNER RECEIPT PENDING.
- Auth-shadow focus use-boundary: IMPLEMENTED AS CANDIDATE / FULL-AUDIT STILL REQUIRED.
- Rank Index V3: TESTING simpler counterbaseline to ActiveFieldV2.
- Rank Path / Runtime V4: TESTING; lifecycle resource defect identified.
- Rank Path / Runtime V5: TESTING candidate to repair V4 lifecycle.
- ActiveFieldV2: RETAIN AS COMPARATOR, NOT AUTO-PROMOTED.
- Horizon estimator: BASELINE / NEGATIVE RESULTS PRESERVED / NO PROMOTION.
- canonical Frank Harness: NO_CHANGE from this delta.

## 17. Next highest-value falsifiers

1. consume hosted V3-V5 and V5 lifecycle receipts; inspect exact failure logs if red;
2. consume Hostinger Pulse / semantic-cycle / rank-index / auth-shadow receipts;
3. benchmark V4 vs V5 under alternating high-read/high-churn write traces, including index build/drop and WAL/storage cost;
4. benchmark full-root integrity vs shadow-refresh+focus-check+periodic-full-audit across realistic state sizes;
5. run real provider model replacement / malicious output through the external tool/effect gateway;
6. run held-out real Frank corpus through U13-U15 with the same conventional optimized baselines;
7. only then consider architecture promotion.

No canonical promotion, no binary freeze, no final Frank acceptance is claimed by this report.
