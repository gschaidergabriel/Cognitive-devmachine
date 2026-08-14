# ARCHITECTURE CANDIDATE — continuity spine v2 obligations

Status: **RESEARCH CANDIDATE / NO NEW PRODUCT LANE / NO PROMOTION**

This packet does not introduce a third V17 family. It hardens the already-selected PR #280 lane and separates storage/recovery claims that current evidence conflates.

## Delta 1 — temporal causal provenance, not relational existence only

Fresh diff audit of PR #280 finds that `tests/effect_reentry_v17_learning_support_matrix.py` records the effect outcome first and only afterwards inserts the attention episode, receiver-use row, prediction, prediction outcome, causal credit and exact-outcome support row. The path then admits learning re-entry. Therefore the candidate currently proves a coherent **post-hoc support graph**, not that Workspace/receiver use actually preceded and contributed to the effect.

Canonical causal order must be machine-checkable. Candidate order law:

`attention/prediction commitment -> receiver used/local_effect -> effect reservation -> attempt begin -> verified provider/effect outcome -> causal credit -> [learning: semantic delta admission] -> re-entry -> DONE`

Physical wall-clock time is insufficient. Prefer durable event/sequence identity. The target-PASS V16 event-instance sequence repair is relevant prior evidence that durable sequence identity can distinguish same-instant events.

### Required discriminator: POST_HOC_SUPPORT_MINT
1. execute and verify an effect with no pre-action GWT support;
2. after outcome, mint otherwise valid attention/prediction/receiver/causal/delta rows referencing the exact effect/outcome;
3. re-entry must REJECT with zero V17 terminal mutation.

## Delta 2 — introduce an explicit pre-action EffectIntent/DecisionReceipt

The cleanest way to prove causal ancestry is to preallocate `effect_id` before reservation and persist an immutable decision receipt binding:
- exact current execution generation;
- GWT cycle/episode;
- prediction id/hash;
- receiver-use/local-effect receipt;
- effect class/action/target/request hash;
- intended `effect_id`.

Effect reservation must consume that receipt. Outcome/causal credit later point back to the same effect/attempt. This avoids trying to infer pre-action causality from rows created after the action.

## Delta 3 — split origin execution from current reconciliation authority

PR #280 binds terminalization to the effect's immutable **origin** execution-generation fence. That is necessary but not sufficient for crash recovery. `finish_done(effect_id)` does not carry a current caller/recovery execution identity.

Required model:
- `origin_execution_id/origin_epoch`: immutable actor that reserved/attempted the effect;
- `reconciler_execution_id/reconciler_epoch`: exact currently authorized execution performing re-entry/DONE/recovery;
- direct path may have origin == reconciler;
- crash takeover may have origin != reconciler only with an explicit recovery/reconciliation admission binding the successor to the effect.

### Required discriminators
- original E1 still current -> ACCEPT normal completion;
- E1 lost, explicit current recovery E2 admitted -> ACCEPT reconciliation without duplicate external effect;
- stale E1 after E2 takeover -> REJECT;
- unrelated current E3 without recovery assignment -> REJECT;
- no current execution at all -> REJECT consequential terminal mutation.

## Delta 4 — terminal validity must be monotonic after successful closure

PR #280 `_delta_admission_present()` rechecks `semantic_records.status='CURRENT'` during DONE verification/recovery. A normal later semantic supersession can therefore make an old DONE chain appear invalid even if it was valid when admitted.

Replace dynamic-current dependence with an immutable **closure/admission receipt** that freezes validity-at-admission:
- semantic record id/hash and semantic epoch;
- causal admission id/hash;
- exact effect/attempt/outcome;
- origin + reconciler execution bindings;
- pre-action decision receipt;
- learning mode (`LEARNING` or typed `NO_LEARNING`);
- schema/contract identity;
- durable sequence/order commitments.

Later normal semantic evolution must not retroactively invalidate historical DONE. Explicit corruption/revocation should create a separate quarantine/revocation fact, not silently rewrite history.

## Delta 5 — support retention/GC must not break old terminal proofs

Revalidating terminal DONE forever against live GWT/prediction/semantic rows creates retention coupling and unbounded-growth pressure. Freeze a compact immutable closure witness at re-entry/DONE. The witness must contain enough hashes/identities to audit the support chain without requiring every mutable projection row to remain CURRENT forever.

## Delta 6 — Graph freshness remains derived, but DELETE mode unlocks an atomic option

U12 proves schema/migration pair identity, not dynamic Graph freshness. Keep a distinct Graph projection watermark (`source_semantic_epoch`, derivation hash, status).

Because current target storage-safety chooses `DELETE + synchronous=FULL`, SQLite's rollback-journal super-journal can make changes to multiple ATTACHed databases atomic across a commit. This creates a candidate optimization:
- attach ClayGraph to the authoritative UnifiedDB connection;
- atomically commit semantic epoch plus a bounded Graph projection batch/watermark;
- Graph remains derived and never mints truth.

Counterhypothesis: this may increase fsync/locking cost enough to hurt Frank latency. Therefore compare against asynchronous Graph projection with strict freshness gating rather than assuming atomic co-commit is superior.

If PR #288 promotes a fixed private SQLite WAL runtime, cross-file ATTACH crash atomicity no longer holds; use asynchronous/rebuildable Graph semantics unless a different tested mechanism is introduced.

## Delta 7 — external rollback floor must not promote dynamic Graph payload to authority

External recovery authority should bind:
- selected UnifiedDB semantic head/root + lineage generation;
- canonical schema/materialization-pair identity;
- source/build/identity contract where required.

It should **not** require a particular dynamic ClayGraph payload to be authoritative. Graph can be stale and rebuilt from admitted UnifiedDB. Otherwise the recovery floor accidentally turns derived projection state into a second truth source.

## Promotion law

`UNIFIEDDB_CONTINUITY_ACCEPT = storage_safe ∧ schema_pair_admitted ∧ selected_semantic_head ∧ rollback_floor_ok ∧ authorized_current_or_recovery_execution ∧ temporally_valid_pre_action_support ∧ verified_outcome ∧ valid_post_outcome_credit ∧ stable_terminal_closure`

No existing single receipt proves this conjunction yet.
