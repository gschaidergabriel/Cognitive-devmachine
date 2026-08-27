# KMP-UDB-END-TO-END-CONTINUITY-SPINE-20260811

packet_id: `KMP-UDB-END-TO-END-CONTINUITY-SPINE-20260811`
domains: `unifieddb, frank, claygraph, gwt, effect_authority, recovery, identity, token_ingress, harness`
epistemic_class: `CURRENT_TARGET_VPS_EVIDENCE_PLUS_CROSS_BRANCH_ARCHITECTURE_SYNTHESIS`
status_hint: `OPEN_BLOCKING_END_TO_END_ADMISSION`
origin_actor: `chatgpt-secondary`
provider: `OpenAI`
model: `GPT-5.6 Sol`
canonical_parent: `r2:04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
trigger: `unifieddb`
invoked_alias: `unifiedb`
program: `FRANK_V0_1`
work_package: `F-V01-04-UNIFIEDDB-STATE-CONTINUITY`

## Why this packet exists

The current swarm has independently produced useful mechanisms for storage safety, materialization identity, semantic-head uniqueness, execution continuity and effect re-entry. The remaining risk is architectural composition: a lower-layer PASS can be accidentally treated as proof of a higher-layer property. This packet defines one end-to-end continuity spine and a fault matrix that keeps those claims separate.

This is a synthesis/adjudication artifact only. It does not authorize Frank/self.root Harness mutation, canonical migration, production boot change, effect execution, or final training.

## Continuity spine: five non-substitutable admission rings

### Ring 0 — Physical storage admissibility

Question: can the exact SQLite build/journal/checkpoint topology be trusted not to violate the database substrate before semantic invariants are considered?

Current evidence:
- accepted target has reported Python 3.12.3 / SQLite 3.45.1;
- target storage-safety candidate passed by selecting rollback-journal `DELETE` plus `synchronous=FULL` and failing closed when WAL is forced on the affected/unknown build;
- official SQLite documentation says the WAL-reset bug is likely present through 3.51.2 unless fixed/backported, and requires WAL with at least two connections plus concurrent write/checkpoint timing.

Admission law:
`R0_PASS := fixed_or_verified_backport OR machine_checked_bug_topology_unreachable OR safe_non_WAL_mode`.

Non-claim: R0 does not prove semantic lineage, pair coherence, replay correctness, current execution ownership, or causal re-entry.

### Ring 1 — Physical materialization-pair coherence

Question: do the authoritative UnifiedDB and derived ClayGraph files belong to the same admitted schema/materialization pair?

Current candidate U12:
- per-role ordered schema-chain digest;
- shared pair digest;
- lifecycle `UPDATING` / `CURRENT`;
- normal `open_pair()` rejects mismatched, stale, missing or interrupted certificates even when both SQLite files remain physically healthy.

Admission law:
`R1_PASS := both_physical_files_healthy AND exact_pair_certificate_CURRENT AND exact_role_and_chain_match`.

Strongest counterhypothesis: byte-level schema-source binding may be too sensitive to semantically irrelevant edits; if measured availability suffers, replace byte identity with canonical schema/IR identity rather than weakening pair admission.

Current execution truth: U12 target workflow exists, but the latest observable run on the cited candidate was cancelled; no target PASS may be inferred from workflow existence or cancellation.

Non-claim: R1 does not create cross-file atomicity. ClayGraph stays derived/rebuildable and never becomes truth authority.

### Ring 2 — One selected semantic lineage head

Question: among physically valid semantic states, can exactly one provenance-bound sibling be CURRENT?

Current target evidence from PR #267:
- two distinct sibling roots raced;
- exactly one CAS winner;
- loser did not persist;
- loser replay after head movement was rejected with `SELECTED_LINEAGE_HEAD_MOVED`;
- SQLite integrity/FKs remained clean;
- no external effect or identity authority was exercised.

Admission law:
`R2_PASS := selected_head_exact_parent_CAS AND one_current_head AND protected_state_root_matches_selected_head`.

Known limit: if protected state and selected-head store roll back together to a mutually consistent historical pair, R2 alone cannot distinguish that pair from a legitimate past state. Therefore selected-head CAS is a sibling/fork selector, not whole-domain rollback authority.

### Ring 3 — Exact current execution ownership

Question: is the writer/replayer the exact current self.root execution generation, not merely a process with valid-looking identifiers?

Current target evidence:
- V15 presence exclusion/fencing PASS;
- V16 schema and request-idempotency substrate PASS;
- token-ingress V16 continuity PASS for durable execution id, request idempotency, same-session continuation, lost-holder recovery, explicit idle handoff, user-priority semantics and stale-holder exclusion;
- effect execution-generation fence on current main PASS for exact caller-bound reservation/attempt/provider paths.

Admission law:
`R3_PASS := current_presence_epoch AND exact_execution_id AND credential/session/client binding AND task state permits write AND no stale/successor alias`.

Non-claim: R3 proves who may write now. It does not prove that the semantic payload being written belongs to the selected lineage, nor that claimed causal support is real.

### Ring 4 — Causal/provenance re-entry closure

Question: after a verified effect outcome, is terminal re-entry grounded in actual current execution plus real GWT/receiver/causal/admitted-delta support rather than free strings?

Current negative evidence:
- active V17 candidate can accept fabricated episode/signal/causal/delta labels and reach DONE while V15 is IDLE epoch 0 and V16 execution is unbound;
- its own chain verifier can still report `DONE_VALID` and recovery `COMPLETE`.

Existing stronger candidate:
- V17.1 relational closure binds current execution/lease, verified provider outcome, same-effect GWT receiver use, verified prediction outcome, causal credit, semantic-delta admission, re-entry authority and terminal current-execution check;
- it still needs reconciliation with the actively exercised provider/effect path and an explicit typed `NO_LEARNING` branch.

Admission law:
`R4_PASS := R3_PASS AND verified_outcome AND closed_support_chain OR explicitly_typed_no_learning_contract_with_real_current_execution_and_truthful_support_waiver`.

Non-claim: `explicit_no_learning` must not be a bypass that permits fabricated support or detached execution.

## Ring ordering invariant

The rings form a conjunction, not a ladder of inherited authority:

`CONTINUITY_ADMITTED = R0 ∧ R1 ∧ R2 ∧ R3 ∧ R4`

A lower ring may fail closed without evaluating higher rings. A higher-ring PASS on a disposable or synthetic substrate cannot promote a failed/unknown lower ring.

Examples:
- valid V17/DONE on unsafe or unknown WAL topology => NOT ADMITTED;
- perfect selected-head CAS with divergent UnifiedDB/ClayGraph pair => NOT ADMITTED;
- current execution bound to a historical rolled-back selected head => NOT ADMITTED;
- physically perfect pair with fabricated causal support => NOT ADMITTED.

## Recovery authority: the sixth cross-cutting dimension

Whole-domain rollback is not solved by storing ever more monotonic numbers inside the same rollback domain. A recovery floor must survive independently or recovery must fail closed.

Candidate authority/failure-domain classes to test, not assume:
1. independent durable store outside the protected VM/filesystem snapshot domain;
2. remote monotonic service with authenticated, replay-resistant receipts;
3. hardware-backed monotonic/attestation primitive where available;
4. operator-coordinated restore ceremony with externally persisted signed/hashed selected-head receipt.

The recovery authority must bind at minimum:
- selected semantic head identity/root;
- lineage generation/sequence;
- source/build/owner identity contract reference where needed for boot acceptance;
- materialization pair identity;
- timestamp/order evidence sufficient to reject stale restores.

It must not become a second hidden semantic database.

## End-to-end crash/fault matrix

Run on the accepted self-hosted target with exact source/blob hashes and one composed candidate.

### Storage / materialization faults
1. force affected/unknown SQLite into WAL with multi-connection/checkpoint topology -> release gate REJECT before authoritative writes;
2. crash after ClayGraph migration but before UnifiedDB migration/certificate completion -> next normal open REJECT `UPDATING`/pair mismatch;
3. restore one physical DB only -> pair certificate REJECT despite `integrity_check=ok`;
4. remove/stale pair certificate -> fail closed; no silent legacy open;
5. valid one-time bootstrap of an existing pair -> ACCEPT only after both chains and physical integrity verify.

### Semantic-lineage faults
6. two equal-parent/equal-generation sibling roots race -> exactly one selected head;
7. loser replay after winner commit -> zero authoritative mutation;
8. protected state rolls back while selector survives -> mismatch REJECT;
9. selector rolls back while protected state survives -> mismatch REJECT;
10. both roll back together -> reproduce known limitation; require external recovery floor to reject or enter explicit recovery mode;
11. controlled restore of old semantic payload -> new child head; never resurrect historical head identity.

### Execution faults
12. writer loses lease after transaction preparation but before commit -> semantic commit REJECT;
13. successor execution acquires new epoch and stale predecessor retries -> REJECT zero mutation;
14. same execution_id under different credential/session/client tuple -> REJECT;
15. crash releases physical lock but semantic lease not yet expired -> autonomous takeover remains blocked; explicit recovery semantics required;
16. transport silence -> never treated as idle confirmation.

### Re-entry / causal faults
17. fabricated attention/receiver/causal/delta ids -> REJECT;
18. individually valid but cross-spliced support rows from different effect/cycle/provider outcome -> REJECT;
19. stale execution between OUTCOME_SUCCEEDED and REENTERED -> REJECT;
20. stale execution between REENTERED and DONE -> REJECT;
21. crash after verified provider outcome before re-entry -> deterministic recovery says REENTRY_PENDING or equivalent, never duplicate external effect;
22. crash after re-entry before DONE -> deterministic idempotent terminalization or fail-closed recovery;
23. LEARNING path without admitted semantic delta -> REJECT;
24. NO_LEARNING path with explicit typed waiver -> ACCEPT only if execution/outcome identity is exact and verifier records the waiver, with no invented causal/delta support.

### Cross-ring faults
25. R0 pass + R1 pass + R2 pass but R3 stale -> REJECT;
26. R0 pass + R1 mismatch + otherwise valid R2-R4 -> REJECT at R1;
27. R0-R3 pass + R4 fabricated support -> REJECT at R4;
28. external recovery floor ahead of selected head/materialization pair -> enter RECOVERING/fail closed, never silently downgrade floor;
29. external floor unavailable -> fail closed or bounded read-only recovery mode according to explicit policy; no authoritative semantic writes.

## Measurements required from the composed target run

Correctness:
- pass/reject classification for every matrix row;
- zero unexpected authoritative mutations on every reject;
- SQLite integrity/FK checks;
- replay equivalence after process restart;
- exact selected-head/pair/execution/support receipt chain.

Performance/resource:
- p50/p95/p99 end-to-end semantic commit latency;
- p50/p95/p99 `open_pair()` latency with certificate verification;
- write amplification and bytes/fsync per semantic commit;
- checkpoint/journal costs under selected journal mode;
- RSS/CPU/storage I/O;
- database and derived-graph growth per 1k commits;
- recovery time after each crash window.

Operational:
- availability impact of strict pair certificate bootstrap;
- failure-domain availability of external recovery authority;
- frequency of false fail-closed events;
- ability to rebuild ClayGraph from admitted UnifiedDB without changing semantic truth.

## Architecture decision at this point

KEEP:
- UnifiedDB as canonical semantic/logical state plane;
- ClayGraph as derived/rebuildable topology;
- exact current execution fencing;
- selected-head CAS as one-current-sibling mechanism;
- external rollback-domain-independent recovery floor;
- SHADOW-first rollout and fail-closed gates.

HOLD:
- physical consolidation of UnifiedDB + ClayGraph;
- WAL on unknown/affected target build;
- U12 enforcement before safe bootstrap/crash proof;
- active V17 causal-closure promotion;
- whole-Frank acceptance.

REJECT as insufficient:
- provenance labels alone as lineage uniqueness proof;
- generation counters inside the same rollback domain as whole-rollback proof;
- `integrity_check=ok` as proof that two physical DBs belong together;
- free episode/signal/causal strings as provenance closure;
- retrieval/ClayGraph activation as truth or authority.

## Highest-information next action

Do not invent another storage or V17 family. Compose the already independently justified mechanisms into one disposable exact-current target branch and execute the fault matrix in dependency order. Preserve known negative controls as first-class expected results.

Before composition:
- wait for or explicitly adjudicate the queued stacked PR #281 rollback-domain diagnostic;
- rerun U12 materialization-pair gate after its cancelled workflow on fresh ancestry;
- reconcile the active V17 path with V17.1 constraints, including typed LEARNING/NO_LEARNING semantics;
- recheck concurrent branches touching `apply_current_schema.py` before merging any storage candidate.

## Promotion boundary

`OPEN_BLOCKING_END_TO_END_ADMISSION`.

No individual current mechanism result is sufficient for `F-V01-04 PASS`. Promotion requires one exact-current composed target receipt proving all applicable rings plus crash/restart/replay behavior, while preserving the explicitly known whole-domain rollback limitation unless an independently verified recovery authority closes it.