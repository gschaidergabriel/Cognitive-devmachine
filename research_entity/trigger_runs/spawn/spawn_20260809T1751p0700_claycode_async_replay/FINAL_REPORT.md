# SPAWN Research Run — ClayCode Async/Concurrency Replay Contract

**run_id:** `spawn_20260809T1751p0700_claycode_async_replay`  
**trigger:** `spawn`  
**origin branch:** `claycode`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**program stage:** `BASE_CLAYCODE_RELEASE`  
**decision:** **RESEARCH DELTA COMMITTED · NO SCIENTIFIC PROMOTION · BASE GATE REMAINS NOT_PASS**

## 1. Stochastic selection

The branch was drawn using OS CSPRNG `/dev/urandom`: raw u32 `238253034`, mapped to approximately 5.5474% of the weighted distribution, selecting **ClayCode** (50% interval). Five evidence-derived microdirections were generated. A second OS-CSPRNG draw `2542952372 % 5 = 2` selected:

> deterministic replay semantics for async concurrency, cancellation, choice and effect receipts

A late novelty check reviewed concurrent spawn runs that appeared while this run was executing. Two recent ClayCode candidate sets contained related async/cancellation ideas but selected other directions (incremental delta equivalence and affine capability revocation). No duplicate reroll was required.

## 2. Why this direction matters now

ClayCode BASE explicitly requires async/concurrency/atomics/resource semantics and APP-04 requires a concurrent service with cancellation/error paths and deterministic receipt semantics. The freshest ClayCode effect-closure run already supported compositional typed effect requirements without changing surface syntax, but left async/control/resource closure open.

The current Reference Harness state ledger already supplies epoch checks, idempotency keys, semantic/execution chains and deterministic replay of a fixed event sequence. Its current stress test does not vary true concurrent interleavings, so it cannot by itself answer what ClayCode must make schedule-insensitive versus what must be recorded as intentional nondeterminism.

## 3. Core research result

The best-supported design is a hybrid contract:

`deterministic-by-default semantic regions + explicit receipted nondeterminism + idempotent authority-gated effects`

not:

`one globally fixed deterministic scheduler = ClayCode concurrency semantics`.

### 3.1 Race-free semantic determinism

The type/effect checker should use the existing compositional effect direction to determine whether concurrent tasks can interfere. Pure, disjoint or otherwise proven-commutative semantic effects should be schedule-insensitive. Conflicting writes/effects should require synchronization/transaction semantics or an explicit nondeterministic construct/contract rather than silently inheriting host scheduling.

### 3.2 Intentional nondeterminism becomes data

`select`/race/first-response/external-readiness outcomes may legitimately depend on order. Their selected semantic result should therefore be represented by a typed `ChoiceReceipt`, e.g. stable choice identity, candidate semantic IDs, selected candidate and selection basis. Replay consumes the recorded choice rather than rerunning a host race and hoping the same branch wins.

### 3.3 Stable semantic task identity

Task identity should be derived from semantic lineage such as parent task + spawn-site semantic identity + spawn ordinal. Physical worker/thread/process and execution-attempt identity remain separate trace facts. This allows H1/H2/H3 to compare semantic task graphs even if their schedulers differ.

### 3.4 Cancellation is a state transition

Cancellation should not be modeled only as implicit future/task destruction. A minimal runtime contract should distinguish states such as:

`ACTIVE -> CANCEL_REQUESTED -> CANCEL_ACK | COMPLETED_BEFORE_ACK -> TERMINAL`

and expose typed cancellation points / cancel-safety metadata. Cancel-unsafe operations need transaction/rollback/cleanup or an explicit boundary. The goal is replayable semantics, not a claim that every operation must be cancel-safe.

### 3.5 Effect intent != execution attempt

Externally visible effects need a stable semantic `EffectIntent` identity plus a fresh execution-attempt identity. The intent should bind resource, task, required effect summary, capability binding, base epoch/idempotency identity and later `EffectOutcome`. Retries may reuse semantic intent identity for deduplication where the gateway/adapter supports it, while authority must still be checked at effect/commit time.

This does **not** justify a universal exactly-once promise for arbitrary external systems.

## 4. Executable discrimination

`EXPERIMENT_ASYNC_REPLAY_CONTRACT.py` was executed in the hosted Python runtime. It is a proxy, not production ClayCode or Ubuntu-target evidence.

Results:

- disjoint write pairs: **43,823**; schedule divergences: **0**;
- conflicting write pairs: **6,177**; reversed-order divergences: **6,177**;
- intentional race workflows: **100,000**;
- replay mismatches without `ChoiceReceipt`: **66,583**;
- replay mismatches with `ChoiceReceipt`: **0**;
- invalid/tampered choice receipts detected: **100,000 / 100,000**;
- cancel/retry workflows: **100,000**;
- naive duplicate-effect failures: **50,094**;
- stable idempotent-intent failures: **0**;
- stable task-ID schedule cases: **20,000**; failures: **0**;
- fairness counterexample: fixed biased order let shutdown win **0 / 10,000**; randomized order **4,967 / 10,000**.

The experiment therefore supports the narrow architecture law that determinism should be guaranteed where semantics are meant to commute/noninterfere, while legitimate race outcomes must be explicitly recorded for replay. It also falsifies the stronger proxy claim that a fixed branch order is automatically a safe production substitute for receipted nondeterminism.

## 5. External triangulation

Primary/official sources were used as architecture comparisons, not as proof of ClayCode correctness:

- Deterministic Parallel Java: deterministic-by-default semantics through compile-time effect reasoning, with explicit safe nondeterminism.
- Tokio `select!`: first-completing branch wins; remaining branches are cancelled; default randomized checking exists for fairness; biased deterministic order transfers fairness responsibility to the programmer; cancellation safety depends on the operation.
- FoundationDB simulation: deterministic simulation is used to make difficult failures reproducible, while real multithreading can reintroduce nondeterminism.
- Temporal architecture: append-only event history recreates workflow state; deterministic workflow logic is separated from external activities, which must be idempotent or non-retryable.
- rr: record nondeterministic execution once and deterministically replay that exact execution.

These independent systems point to complementary strategies rather than one universal solution: prevent unintended nondeterminism where feasible, and record/replay the nondeterminism that is semantically legitimate or imposed by the environment.

## 6. Counterhypotheses and negative results

1. **Global deterministic scheduler is sufficient.** Weakened: deterministic simulation remains valuable for tests, but fixed scheduling can change fairness/liveness and cannot remove all external completion nondeterminism.
2. **Event history alone is enough.** Weakened: a history can reproduce a chosen order but does not stop accidental race-sensitive semantics before execution.
3. **Forbid all race-dependent constructs.** Weakened: timeout, first-response, external-readiness and cancellation patterns need intentional nondeterminism.
4. **Cancellation can stay implementation-only.** Weakened: partial progress/effects create replay and retry ambiguity.
5. **Universal exactly-once effects.** Not selected: deduplication depends on the external authority/effect substrate; ClayCode should expose the semantic intent and receipt contract without claiming impossible guarantees.

Infrastructure negative result preserved: current interconnect preflight tooling has been reported to retain stale `clay` naming while the registry uses `clayresearch`. This run therefore materialized explicit nine-branch coverage instead of claiming the executable preflight passed.

## 7. Recommended ClayCode IR/runtime contract

No new surface syntax is justified yet. First implement these concepts in canonical IR/compiler/runtime metadata:

- `TaskSpawn { task_id, parent_task_id, scope_id, spawn_site_id, ordinal, fn_semantic_id }`
- `ChoiceReceipt { choice_id, scope_id, candidates, winner, basis, causal_task_ids, execution_ref }`
- `CancelTransition { task_id, request_id, from, to, checkpoint_id, reason }`
- `EffectIntent { intent_id, task_id, effect_summary_id, resource_id, capability_binding_id, idempotency_key, base_epoch }`
- `EffectOutcome { intent_id, attempt_id, commit_epoch_or_external_receipt, outcome_hash, authority_receipt_id }`

The exact schema remains falsifiable and should be simplified if the production compiler can preserve the same invariants with fewer fields.

## 8. Cross-branch implications

- **ClayCode:** direct WP-09/APP-04 constraint; implement before claiming concurrent-service proof.
- **Harness:** H-WP-11/13/14 need real schedule perturbation and receipt-aware differential replay, not only serial event replay.
- **FRANK:** semantic task/effect/re-entry identity should remain independent of physical scheduling; Frank itself gains no Harness mutation authority.
- **UnifiedDB:** persist semantic task/choice/cancel/effect identities separately from physical attempts/trace metadata.
- **ClayGraph:** represent dynamic semantic-vs-physical execution edges distinctly; no graph truth/activation promotion.
- **GWT/Emergenz:** scheduler variation must be recorded/controlled so causal workspace or emergence measurements are not confounded by race order.
- **Hyperposition:** topology variation must not destroy stable semantic identity.
- **ClayResearch:** integrate deterministic regions and explicit nondeterminism rather than forcing one global physical scheduler.

## 9. Evidence boundary and next discriminating experiment

This run does **not** pass any ClayCode BASE package. It is not production parser/typechecker/runtime evidence, not APP-04 acceptance, not execution on Andreas' Ubuntu developer target, and not live-FRANK evidence.

Highest-information next test:

1. implement the minimal task/choice/cancel/effect-intent contracts in the production ClayCode canonical IR and type/effect checker;
2. build APP-04 as a real concurrent service with timeout/cancellation plus a sandboxed effect;
3. execute many perturbed schedules in the Reference Harness and ClayCode runtime;
4. compare semantic state/task/effect hashes while replaying recorded choices;
5. prove that race-free programs remain schedule-insensitive, explicit races replay exactly, cancellation does not lose/duplicate committed effects, and fairness/liveness remains acceptable;
6. repeat on Andreas' Ubuntu developer target before any BASE completion claim.

## 10. Durable artifacts / commits

- experiment source: `73bf52df140414188409e0b514a0b1389e403519`
- spawn receipt: `10e1dbd750553cff3046f60a6c7079702f99c0e3`
- interconnect manifest: `6e56050c16e0ff9d6db6cacfc52d178135c208f6`
- hypotheses: `b33ce4735594f290fb2b98f5c8ff8a8a77974514`
- evidence manifest: `e5660b6e650614b0511f69abe276707ef9f358e7`
- execution receipt: `b0cb1e0ef04cabcf0f197e3ee5dd50f46d92e00b`
- branch feedback: `8f1bd87b240df314f3591fc884f5ce20be1ad62d`

One GitHub 409 occurred because another worker advanced `main` during writeback. No existing file was overwritten; the missing new file was retried after refreshing the remote head.

## Final decision

`RESEARCH_DELTA = COMMITTED`  
`SCIENTIFIC_PROMOTION = NONE`  
`CLAYCODE_SURFACE_CHANGE = NO`  
`CONCURRENCY_DIRECTION = DETERMINISTIC_BY_DEFAULT_PLUS_EXPLICIT_RECEIPTED_NONDETERMINISM`  
`CANCELLATION_DIRECTION = FIRST_CLASS_REPLAYABLE_STATE_TRANSITION`  
`EFFECT_DIRECTION = STABLE_SEMANTIC_INTENT_PLUS_FRESH_AUTHORITY_CHECK_AND_OUTCOME_RECEIPT`  
`BASE_GATE = NOT_PASS`
