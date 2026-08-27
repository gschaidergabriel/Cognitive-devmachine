# FRANK Dual-Time Causal Feedback Bridge — late-but-valid outcomes are not stale feedback

**Status:** OPEN_RESEARCH_DELTA_NOT_CANONICAL_PROMOTION  
**Date:** 2026-08-10  
**Origin actor:** chatgpt-secondary  
**Provider/model:** OpenAI / GPT-5.6 Sol  
**Canonical parent:** revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**Research parents:** `FRANK_PERFECT_FEEDBACK_LOOP_SYNTHESIS_20260810.md`, `FRANK_FEEDBACK_INNOVATION_PACKET_REFINEMENT_20260810.md`  
**Operational target:** Frank v0.1 on Andreas' Ubuntu developer system  
**Authority:** Research Entity research proposal/evidence only; no Frank self-harness authority.

## 0. GO-cycle question

The prior feedback refinement proposed rejecting stale/wrong-epoch feedback. This GO cycle isolates one high-value ambiguity:

> What should happen when an outcome is old relative to the current semantic epoch but is still causally valid because it belongs to a tool/action episode that completed asynchronously?

A strict `packet.state_epoch == current_epoch` rule would reject legitimate delayed outcomes. Blindly applying an old outcome to the current state is also wrong. The required distinction is between **temporal age** and **causal validity**.

## 1. Current architecture gap

Current ClayCode G9 V3 has useful pieces:

- `Delta<T>.logical_time` and optional `valid_time`;
- `IncrementalReceipt.source_epoch/output_epoch`;
- GWT `reentry` as an explicit causal axis;
- `gwt.reentry requires observed_outcome_or_state_delta`;
- main cycle `outcome=verify(...) -> credit=causal_credit(outcome,ws) -> reenter(Delta(outcome))`.

But the current contract does not yet distinguish:

1. the epoch in which the causal episode/action originated;
2. the wall/logical time at which the outcome was observed;
3. the time at which verification completed;
4. the current semantic epoch into which a consequence may be admitted;
5. retrospective credit closure from forward influence on current control state.

Therefore `wrong epoch` is underspecified. An old origin epoch can be legitimate; a current-looking packet can still be causally wrong.

## 2. Fresh external evidence fused in this GO cycle

### 2.1 Delayed reward makes temporal proximity a poor credit rule

`Counterfactual Shapley Credit Assignment`, arXiv:2607.16999v2 (revised 2026-08-07), explicitly targets sparse causality, environmental stochasticity and delayed rewards using counterfactual causal attribution rather than temporal proximity.

Transfer to Frank: receipt arrival time must not determine which earlier action/state receives credit.

### 2.2 Long-horizon tool agents benefit from state-transition-level credit

`TRACE: Turn-level Reward Assignment via Credit Estimation for Long-Horizon Agents`, arXiv:2607.13988, models rollouts as state transitions at tool-call boundaries and derives dense per-action credit from value changes.

Transfer: tool-call/action boundaries are natural causal episode boundaries for Frank feedback; terminal outcome alone should not be broadcast indiscriminately across all active state.

### 2.3 Delayed measurements can remain informative

`Learning-Based Sensor Scheduling for Delay-Aware and Stable Remote State Estimation`, arXiv:2601.21482, explicitly incorporates delayed measurements and models delay-dependent information gain instead of treating age alone as uselessness.

Transfer: delayed Frank outcome evidence can remain valuable, but its current-state influence should be delay/context aware.

### 2.4 Asynchronous event-triggered control does not require simultaneous sampling

`Asynchronous Event-Triggered Control for Non-Linear Systems`, arXiv:2211.13846v2, provides an asynchronous event-triggered control formulation in which measurement/control triggers do not require periodicity or simultaneity and uses timer/state conditions to avoid pathological triggering.

Transfer: Frank's multirate loop should support asynchronous feedback delivery without forcing one global semantic tick.

## 3. Leading hypothesis and counterhypothesis

### H-DUALTIME

Frank should use a **Dual-Time Causal Feedback Bridge**:

`late verified outcome -> close exact origin episode retrospectively -> derive typed innovation/credit -> explicitly rebase/transport only the still-applicable consequence into the current semantic epoch`.

Temporal age alone never determines causal validity.

### H0-SIMPLE

A simpler origin-bound verified-outcome update with ordinary staleness decay may be sufficient. Explicit rebase/transport semantics could add state, latency and failure modes without measurable benefit.

This counterhypothesis remains live because the synthetic experiment below did not show a consistent advantage for the more elaborate rebased update law over simple verified origin-bound outcome updates.

## 4. Proposed primitive refinement

Extend `FeedbackInnovationPacket` or equivalent with explicit dual-time fields:

```text
CausalFeedbackPacket {
  packet_id
  idempotency_key

  origin_episode_id
  origin_signal_id
  origin_state_epoch
  origin_receiver
  origin_action_or_operation
  origin_prediction
  origin_uncertainty

  outcome_observed_at
  outcome_verified_at
  verification_class
  verified_outcome
  innovation_typed
  utility_delta
  residual_delta

  causal_use_receipt_ids
  causal_credit_vector
  credit_uncertainty

  semantic_validity_scope
  valid_time
  schema_version
  transformation_chain

  arrival_epoch
  apply_epoch?
  rebase_required
  rebase_receipt?
  drift_distance?
  applicability_class

  proposed_gain
  applied_gain
  gain_cap
  rollback_ref
}
```

## 5. New hard distinction

```text
OLD_EPOCH != STALE
```

Classify feedback instead as:

- `LATE_CAUSALLY_VALID` — old origin epoch, valid exact causal identity/outcome;
- `CURRENT_CAUSALLY_VALID` — current origin/current state and valid;
- `PROVENANCE_INVALID` — identity/receipt chain broken;
- `SCHEMA_INCOMPATIBLE` — cannot safely interpret;
- `SEMANTICALLY_EXPIRED` — causal result is true about the old episode but no longer applicable to current fast control state;
- `DUPLICATE_ALREADY_ADMITTED` — outcome/credit already consumed for the same durable update;
- `CONFLICTING_OUTCOME` — competing verified outcome receipt requires adjudication/quarantine.

Only provenance/schema invalidity requires outright rejection of the evidence object. Semantic expiry can block **forward fast-state application** while still preserving retrospective episode closure, memory evidence and research/credit history.

## 6. Two-stage application law

### Stage A — retrospective causal closure

For a valid outcome, regardless of current epoch:

```text
verify packet identity
-> resolve exact origin episode/action/receiver
-> close outcome on origin episode
-> compute/attach innovation
-> compute causal credit with uncertainty
-> mark exactly-once retrospective admission
```

This stage changes historical/episodic causal truth, not current action authority.

### Stage B — forward semantic transport

Only after Stage A:

```text
origin delta + current state
-> applicability/drift check
-> typed rebase/transport
-> current receiver-specific bounded delta
-> current-epoch admission receipt
```

Possible results:

- `APPLY_FAST` — same task/state family and still decision-relevant;
- `APPLY_SLOW_ONLY` — useful for memory/value/prediction/homeostasis, not current focus;
- `REPLAN` — outcome invalidates assumptions and should reopen current planning/GWT;
- `ARCHIVE_ONLY` — causally true but no current operational relevance;
- `QUARANTINE` — conflicting or insufficiently verified;
- `REJECT` — provenance/schema invalid.

## 7. Exactly-once / out-of-order law

A delayed outcome may arrive after newer outcomes or after restart. Therefore:

- idempotency key binds `origin_episode + effect/action + outcome identity + verifier`;
- retrospective closure is exactly-once;
- durable learning admission is exactly-once per declared learning target/version;
- arrival order does not overwrite newer semantic state;
- duplicate receipts return the prior admission receipt;
- rebase is deterministic under the same current-state snapshot/version;
- restart reconstructs pending/closed/admitted state from UnifiedDB receipts.

This is a stronger requirement than `latest timestamp wins`.

## 8. One bounded out-of-the-box experiment — asynchronous causal-time stress test

**Status:** SYNTHETIC_MECHANISM_TEST_ONLY_NOT_FRANK_RUNTIME_EVIDENCE.

Purpose: deliberately model Frank feedback as a networked asynchronous control problem rather than a synchronous cognition loop.

Protocol:

- contextual task with 4 recurring semantic contexts and 4 actions;
- each context has a stable different optimal action;
- context switches every 3–9 steps;
- outcome delay is random up to 12 steps, producing frequent out-of-order arrival after context change;
- reward noise is matched across candidates;
- corruption sweep: 0%, 8%, 25% misbound provenance;
- 250 matched seeds per corruption level;
- 900 decision steps per seed;
- same exploration and learning-rate family across candidates.

Compared feedback laws:

1. `STRICT_EPOCH`: reject any feedback whose origin epoch is not the current epoch;
2. `RECEIPT_CURRENT`: assign arriving outcome to current context/receiver without origin binding;
3. `ORIGIN_BOUND`: apply to reported origin context/action but trust provenance;
4. `ORIGIN_VERIFIED`: exact origin binding + reject corrupted provenance;
5. `ORIGIN_INNOVATION_RAW`: exact origin + origin-time innovation with delay attenuation;
6. `ORIGIN_REBASED_PACKET`: exact origin + provenance validation + current receiver-state rebasing with mild delay attenuation.

Representative mean results:

```text
corruption=0%
STRICT_EPOCH            optimal_rate 0.2493  regret 0.7502
RECEIPT_CURRENT         optimal_rate 0.3133  regret 0.6655
ORIGIN_BOUND            optimal_rate 0.8869  regret 0.1078
ORIGIN_VERIFIED         optimal_rate 0.8869  regret 0.1076
ORIGIN_INNOVATION_RAW   optimal_rate 0.8882  regret 0.1060
ORIGIN_REBASED_PACKET   optimal_rate 0.8870  regret 0.1075

corruption=8%
RECEIPT_CURRENT         optimal_rate 0.3110  regret 0.6699  miscredit ~0.691
ORIGIN_BOUND            optimal_rate 0.8856  regret 0.1102  miscredit ~0.075
ORIGIN_VERIFIED         optimal_rate 0.8847  regret 0.1097  corrupted rejected ~65.8/run
ORIGIN_INNOVATION_RAW   optimal_rate 0.8845  regret 0.1094
ORIGIN_REBASED_PACKET   optimal_rate 0.8838  regret 0.1108

corruption=25%
RECEIPT_CURRENT         optimal_rate 0.3091  regret 0.6764  miscredit ~0.733
ORIGIN_BOUND            optimal_rate 0.8619  regret 0.1331  miscredit ~0.233
ORIGIN_VERIFIED         optimal_rate 0.8721  regret 0.1212  corrupted rejected ~205.5/run
ORIGIN_INNOVATION_RAW   optimal_rate 0.8693  regret 0.1236
ORIGIN_REBASED_PACKET   optimal_rate 0.8716  regret 0.1215
```

### Experiment interpretation

Supported strongly inside this constructed model:

1. **causal origin binding dominates receipt-time/current-state attribution** under asynchronous delay;
2. strict current-epoch equality is catastrophic when outcomes are legitimately delayed;
3. provenance validation becomes useful as corruption rises;
4. an old valid outcome can still improve the correct recurring context when attached to its origin causal episode.

Not supported:

5. raw origin innovation did **not** consistently dominate simple verified origin-bound outcome feedback;
6. the more elaborate rebased packet update did **not** consistently beat simple `ORIGIN_VERIFIED` on task regret/optimal action rate.

Therefore this GO cycle promotes **the research priority of dual-time causal identity**, not a specific complex numerical update law.

## 9. Architecture delta candidate

Refine the prior law:

```text
PRIMARY_REENTRY = VERIFIED_INNOVATION_PACKET
```

into:

```text
PRIMARY_FEEDBACK_OBJECT = CAUSALLY_BOUND_VERIFIED_OUTCOME/INNOVATION
RETROSPECTIVE_CLOSURE = origin_episode_time
FORWARD_REENTRY = explicit_current_epoch_transport_or_NO_APPLY
```

A feedback packet may be late and still valid. The system must never confuse arrival time with causal origin.

## 10. Consequences for historical Frank organs

- **ResponseAnalyzer**: should compile verified outcome against exact originating prediction/action episode, not just mutate current state.
- **Thalamus**: current gain should receive only forward-admitted/rebased consequences; raw late outcome cannot directly boost a current channel.
- **NAcc/RewardState**: phasic credit binds to origin action/outcome; tonic persistence/homeostasis may receive a slower admitted consequence if still semantically relevant.
- **ACC/conflict**: late evidence can create a current contradiction/replan event if it invalidates a still-live assumption.
- **E-PQ/personality**: slow durable updates require exact outcome/credit admission and should tolerate legitimate latency while remaining exactly-once and rollbackable.
- **GWT**: a late outcome may reopen the workspace only when its forward applicability is material; retrospective closure alone is not ignition.
- **Memory/consolidation**: retain late causally valid outcomes even when they no longer affect fast control.

## 11. Required H1 discriminating experiment

On real/frozen original-Frank episodes with asynchronous effects/tools, compare:

A. historical/current-style direct feedback;
B. strict epoch rejection;
C. receipt-time current-state application;
D. exact origin-bound verified outcome;
E. origin-bound outcome + explicit forward rebase/transport.

Inject controlled:

- 0/short/long delays;
- out-of-order outcome delivery;
- duplicates;
- restart between action and outcome;
- receiver/time shuffle;
- provenance break;
- schema/version mismatch;
- valid old outcome whose task context later recurs;
- valid old outcome whose current relevance has expired.

Measure task outcome, false credit, missed credit, current-state contamination, duplicate durable learning, correction latency, replan quality, recurrence count, GWT ignition, replay equivalence, recovery and resource cost.

## 12. Promotion gate

Do **not** promote the full rebasing mechanism until H1 real traces show incremental value over simple origin-bound verified outcome feedback.

What is strong enough to make mandatory as a test obligation now:

- origin episode identity must survive delay;
- arrival epoch must not overwrite origin epoch;
- `old` must not automatically mean `invalid`;
- retrospective closure and forward current-state application must be separable;
- duplicates/out-of-order/restart must be measurable and exactly-once for durable learning.

## 13. Current conclusion

The strongest refined feedback hypothesis after this GO cycle is:

> Frank's feedback loop needs **two times**: causal origin time and current application time. A verified result first closes the exact episode that caused it, even if that episode is old. Only then may a separately validated, receiver-specific consequence be transported into the current epoch. This prevents both loss of delayed truth and contamination of the present by blindly replaying the past.

This is an OPEN research refinement, not canonical promotion and not Frank runtime proof.