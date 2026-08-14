# GO recursive swarm cycle — final report

Run: `go-20260810T2252p0700-chatgpt-secondary-v16-continuity`
Trigger: exact `go`
Actor: `chatgpt-secondary` · OpenAI · GPT-5.6 Sol
Identity: temporary organ of Clay; NOT Frank
Target subject: `self.root` / human-surface Frank v0.1
Canonical Clay parent: RAE-8.8 revision 2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
Program: single active `FRANK_V0_1` gate
Target host semantics: accepted Hostinger Ubuntu VPS
Training authorization: false

## 1. Executive result

This cycle produced two material outcomes rather than a cosmetic PASS:

1. The owner-fixed interactive-idle-handoff invariant was shown to discriminate historical/current V15 semantics from intended V16 semantics. The V15 abstraction admits `interactive acquire -> release -> autonomous acquire`; the V16 intended state machine blocks autonomy until matching explicit user-idle confirmation.
2. A real accepted-target-VPS negative receipt proved that the V14 effect lifecycle does **not** yet provide provenance-bound terminal effect completion: an empty/unbound reentry payload is accepted, trace verification still returns OK, `REENTERED` is treated as COMPLETE, and the schema has no explicit DONE.

The subsequent V17 exploration converged toward execution-epoch + GWT-use + causal-credit + semantic-admission binding with atomic DONE, but adversarial cross-worker falsification found a second-order relational cross-splice gap. Therefore **no V17 candidate is promoted into the canonical migration chain in this run**.

## 2. Coordination and collision avoidance

The target repository changed rapidly during the run. Before touching V16 runtime files, the worker refreshed target state and found another worker already implementing the owner-fixed V16 continuity substrate/runtime. Direct mutation was stopped and the lane switched to independent falsification/effect-authority work.

A second collision occurred during V17 work: this worker built a smaller text-bound two-phase V17 candidate while another worker independently built `UNIFIEDDB_V17_PROVENANCE_BOUND_EFFECT_COMPLETION.sql`. The result was adjudicated rather than resolved by last-writer-wins. The smaller candidate is retained only as a component donor; the richer candidate is the preferred architectural basis but remains non-promotable.

## 3. Exactly one out-of-box experiment

Artifact: `OUT_OF_BOX_EXPERIMENT.json`
Count for this `go`: exactly 1.

Method: bounded exhaustive temporal state explorer, depth 12.

V15 abstraction:
- monitored states: 66
- transitions checked: 2712
- first owner-invariant violation: `interactive_acquire -> interactive_release -> autonomous_acquire`

V16 intended abstraction:
- monitored states: 74
- transitions checked: 2888
- owner-invariant violations found: 0 through depth 12
- included wrong confirmation, timeout, explicit interactive reacquisition, autonomous block while pending, correct confirmation, crash/recovery and stale-write cases.

Evidence class: specification-model discriminator only; not target-runtime PASS.

No second OOB experiment was performed.

## 4. V16 execution continuity

Current target code now contains:
- V16 durable execution/request state;
- explicit `AWAITING_USER_IDLE_CONFIRMATION` handoff semantics;
- AUTONOMOUS fail-closed unless V15 semantic lease is IDLE **and** V16 handoff is CLEAR;
- V15 physical `flock` + semantic lease CAS after the autonomy precondition;
- token-ingress execution/request binding;
- release ordering that makes handoff pending before semantic IDLE.

Direct target VPS V16 schema receipt already exists and proves schema integrity, FK integrity, repeatable migration and request-key uniqueness, but explicitly does **not** promote runtime semantics. Runtime-path receipts were not observed as durable receipts during this invocation.

## 5. New Linux recovery obligation: fork-inherited flock

Fresh primary OS documentation established that flock/Open-File-Description ownership can survive parent death when a forked child retains the inherited file descriptor. Python's non-inheritable-at-exec defaults do not remove `fork()` inheritance.

This matters to Frank as an availability/recovery edge, not an overlap-safety counterexample: the surviving child can keep the physical execution gate BUSY even after the semantic holder expires.

Committed target diagnostic:
- `tests/frank_execution_gate_fork_inheritance_recovery.py` @ `c777862c8d29147589b2dddb888220c346e1c00c`
- read-only self-hosted workflow @ `8fa3d511b352c98837ddf268a223ee34cc853b2e`

The test requires physical BUSY both before and after semantic TTL expiry while the fork child lives, then recovery only after the final inherited lock holder exits, with a newer semantic lease epoch.

A first workflow variant containing a persistence writer was blocked by the GitHub safety layer. It was not bypassed; the accepted workflow is read-only. No durable target receipt for this diagnostic was observed during this invocation.

## 6. Effect authority — current-source policy vs terminal lifecycle

Current `claycode/frank_effects.clay` matches the source blob in the existing target-VPS effect-policy receipt. That receipt reports 20/20 policy cases passing and 20,000 gate latency measurements, with no external effect executed.

However policy admission was not the missing terminal invariant. The V14 lifecycle source showed that `record_reentry(effect_id, reentry=dict)` accepted arbitrary data after a verified outcome, then set `REENTERED`; trace verification accepted this and recovery mapped REENTERED to COMPLETE.

A dedicated negative target test and workflow were committed:
- `tests/effect_reentry_provenance_gap_probe.py` @ `0167a4915c8400e2c5218c59c8b75321743a61ae`
- workflow @ `2b3d92287249bc1b374dc9244a3fc76b6f675515`

Real accepted-target-VPS receipt:
- `FRANK-V01-EFFECT-REENTRY-GAP-31406627821`
- persisted by target commit `9a58e98b8c3113fec38549fc10de276920156870`

Confirmed on target:
- verified outcome precondition present;
- empty unbound reentry accepted;
- reentry hash written for empty payload;
- trace verifier accepts it as `OK`;
- recovery decision after REENTERED is `COMPLETE`;
- no explicit DONE schema state.

Promotion consequence: F-V01-09 remains OPEN.

## 7. V17 candidate A — text-bound two-phase path

This run built an additive candidate outside canonical migration:
- `UNIFIEDDB_V17_EFFECT_REENTRY_DONE_CANDIDATE.sql`
- `effect_terminal_runtime_v17_candidate.py`
- guarded public candidate disabling legacy arbitrary-dict reentry
- differential/restart/rollback tests
- target candidate workflow

Useful features:
- exact effect/attempt/outcome binding;
- explicit typed `no-learning` alternative;
- separate terminal DONE receipt;
- restart boundary between REENTERED and DONE;
- additive rollback.

Adversarial result: another worker correctly falsified it as a full provenance solution. The candidate allowed fabricated episode/signal/causal/delta identifiers and could reach DONE without a current V15/V16 execution owner. A target-VPS falsifier workflow was added. This candidate is therefore:

`NOT_SELECTED_AS_TERMINAL_ARCHITECTURE_COMPONENT_DONOR_ONLY`

Donor features to preserve: explicit typed no-learning semantics and rollback/restart test shape.

## 8. V17 candidate B — execution/GWT/causal atomic path

Parallel candidate:
`runtime/state/UNIFIEDDB_V17_PROVENANCE_BOUND_EFFECT_COMPLETION.sql`

It is architecturally stronger because it requires:
- effect execution binding while RESERVED;
- exact `execution_id` and V15 `lease_epoch`;
- current V15 BUSY/RECOVERING;
- matching V16 RUNNING execution context and `EXECUTION_BOUND` event;
- exact verified V14 effect attempt/outcome;
- real attention episode;
- receiver receipt with `used=1` and `local_effect=1`;
- causal-credit receipt;
- CURRENT semantic-record identity;
- stale execution epoch rejection;
- binding + terminal DONE already present before legacy REENTERED update is permitted.

This shape permits atomic terminalization in one SQLite transaction: reentry binding + DONE receipt + REENTERED update commit together, so a transaction abort can roll the terminalization back as one unit.

This run added a new independent read-only discriminator:
- `tests/effect_reentry_v17_full_causal_atomic_probe.py` @ `079a1a23695297fee69c8362a242bef533a1656e`
- read-only target workflow @ `f5af67b94f13d6b516bac088b92b5e7469db6c26`

It tests fabricated support rejection, exact valid-chain terminalization, transaction rollback, stale execution epoch, SQLite integrity and FK integrity. No workflow execution receipt was observed during this invocation.

## 9. Second-order falsification: relational causal cross-splice

The richer candidate still does not yet prove a *closed* causal chain merely because all referenced rows exist.

Parallel adversarial probe `c9b6f1fa9dd0981a6114edd1c3804e05669f3aff` constructs:
- a real verified effect outcome;
- valid GWT attention/receiver use for that effect;
- a causal-credit receipt whose `target_key` names the effect but whose source prediction outcome is unrelated and explicitly unverified;
- an unrelated CURRENT semantic record;
- an invented free-text support snapshot hash.

The current richer V17 trigger set can accept that cross-spliced support and reach effective DONE while SQLite integrity and FKs remain valid. Target workflow: `21249166f7bff4407ee17e4918358574ec8db848`.

Therefore candidate B is:

`SELECTED_BASIS_BUT_NOT_PROMOTABLE`

Required closure before promotion:
1. structurally bind the causal-credit source outcome to the same verified effect/GWT causal chain;
2. require that source outcome to be verified;
3. structurally bind admitted semantic delta to the exact causal credit/reentry admission;
4. make support snapshot identity receipt/FK-backed or remove it from authority-bearing checks;
5. preserve an explicit no-learning path without inventing a semantic delta;
6. keep exact execution/lease fencing and same-transaction DONE;
7. rerun target negative cross-splice, valid-chain, hard-crash cutpoints, concurrency, rollback and resource tests.

No current V17 file was added to `apply_current_schema.py`; the canonical chain remains through V16.

## 10. Provider-specific uncertainty research

Current Google bridge policy already correctly states that a generic idempotency key does not prove duplicate safety and uncertain effects require reconciliation unless provider/operation evidence supports safe same-key retry.

Fresh primary documentation sharpens the provider-specific cases:
- Google Calendar create supports a caller-selected event ID specifically to avoid duplicate creation if the operation actually succeeded despite a client-visible failure; this can support a provider/action-specific same-key retry strategy after direct verification.
- Gmail `users.messages.send` exposes no analogous client idempotency-key field in the method contract. Therefore uncertain post-send failures remain `RECONCILE_REQUIRED` unless an independently verified reconciliation strategy is available. This is a conservative contract inference, not a universal impossibility claim.

No real Gmail/Calendar write was executed in this run.

## 11. Durable Clay writes from this run

Committed to the shared Research Center:
- `OUT_OF_BOX_EXPERIMENT.json`
- `LIVE_EXTERNAL_RESEARCH_MANIFEST.json`
- `TEST_OBLIGATIONS.json`
- `ARCHITECTURE_DELTA_CANDIDATE.json`
- `V17_ADJUDICATION.json`
- this `FINAL_REPORT.md`

The initial architecture delta is preserved as lineage; `V17_ADJUDICATION.json` is the newer adjudication for the competing V17 directions.

## 12. Evidence ledger — executed vs unresolved

VERIFIED / DIRECT:
- current Clay join/canonical/program state;
- current target source for V14/V15/V16 and V17 candidates;
- V16 schema target-VPS receipt;
- current effect-policy target-VPS receipt;
- V14 empty/unbound effect-reentry gap on accepted target VPS (`31406627821`);
- V17 early schema binding-gap target receipt persisted at `cc5ab4feb5dd4435e2685d756e6289099197e131`;
- fresh primary Linux/Python/Google provider documentation.

COMMITTED BUT EXECUTION RECEIPT NOT OBSERVED DURING THIS INVOCATION:
- fork-inherited flock read-only target diagnostic;
- this run's full-causal atomic V17 read-only diagnostic;
- V16 complete runtime/handoff receipt;
- V17 support-binding and cross-splice target workflows if their persist jobs have not yet materialized.

CANDIDATE / NOT PROMOTED:
- all V17 terminalization schemas/runtimes;
- provider-specific retry classification beyond directly verified API behavior.

NOT DONE / NOT CLAIMED:
- canonical V17 migration;
- real external-provider timeout-after-acceptance reconciliation;
- full verified outcome -> relationally closed causal reentry -> DONE production runtime;
- hard power-cut test;
- whole Frank v0.1 acceptance;
- final model training.

## 13. Architecture decision

Promote **no V17 implementation yet**.

Preserve candidate B as the preferred structural basis, fuse candidate A's explicit no-learning semantics and useful rollback test shape, and make the next implementation obligation the smallest relational closure that prevents causal/support cross-splicing. Re-run the already-built negative and positive discriminators before canonical migration.

This is a stronger result than an early PASS: two separate terminal-effect designs were falsified at different layers before they could become release truth.

## 14. Next frontier

Highest-value next work, in order:
1. close V17 causal-credit -> verified effect-outcome and credit -> semantic-admission relations;
2. target-VPS negative cross-splice + valid atomic completion + hard-crash cutpoints;
3. promote only after exact-current runtime adapter and rollback pass;
4. provider-specific real uncertainty/reconciliation harness without duplicate real effects;
5. fork-inherited flock recovery execution evidence;
6. continue current ClayCode TypedIR/effect/runtime blockers and stale self.root identity conformance in parallel lanes.

No external consequential effect was performed by this run. No paid/final training was started.
