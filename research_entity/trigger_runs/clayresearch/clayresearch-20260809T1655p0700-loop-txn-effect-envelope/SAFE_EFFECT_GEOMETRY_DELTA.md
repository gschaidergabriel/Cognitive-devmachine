# Safe-Effect Geometry Delta — Loop Transaction Effect Envelope

Run: `clayresearch-20260809T1655p0700-loop-txn-effect-envelope`
Status: **SUBSTANTIVE DELTA / NO PROMOTION**

## Research delta

The current Safe-Effect foundation already requires authority non-amplification, protected information-flow confinement, child-effect closure and recoverability. This run adds a concrete recurrence/transaction obligation:

> An effect authorization formed inside a recurrent loop must not remain executable after any effect-critical state dependency or capability epoch changes. Commit should revalidate the exact decision read-set plus current capability validity/epoch. Unrelated state churn should not force recomputation when dependency closure is known complete.

This is a runtime/compiler contract candidate, not a new ClayCode language primitive and not proof that current FRANK has this bug.

## 1. Language / cognitive evidence

No cognitive-alignment effect was measured. The experiment used deterministic synthetic state machines, not a 4B model. It provides no evidence that Clay-native reasoning causes safer proposals.

Language consequence: **NO CORE SYNTAX CHANGE JUSTIFIED**. Existing typed records, state/effect identities, provenance and generic recurrence appear sufficient to represent a decision dependency set and commit receipt.

A model may continue to reason about destructive or irreversible actions. The safety target is effect reachability/authority, not vocabulary suppression.

## 2. Compiler / type-system evidence

Candidate compiler obligations:

- derive or require an explicit `DecisionDependencySet` for effect-bearing paths;
- preserve static type/identity of loop-carried state;
- keep semantic program identity, decision-snapshot identity and authority-grant identity distinct;
- widen dependency closure or force runtime re-evaluation for dynamic lookup/reflection/FFI when exact dependencies cannot be proven;
- carry protected source labels into sink/declassification checks where information-flow policy applies.

The run did not execute the production ClayCode compiler. These are design/test obligations only.

## 3. Runtime / broker enforcement evidence

Synthetic experiment `EXP-CLAYRESEARCH-LTEE-20260809-001` compared three policies over explicit state/capability transitions.

Exhaustive one-shot schedules: 16.

- naive retained permit: **14 unsafe commits**;
- global state+capability epoch guard: **0 unsafe**, but **1 false abort** from unrelated churn;
- exact read-set + capability-epoch envelope: **0 unsafe, 0 false aborts**.

Fuzz: 100,000 cases, 350,618 recurrent commit attempts.

- naive: **143,298 unsafe commits**;
- global guard: **0 unsafe**, **48,090 false aborts**;
- dependency envelope: **0 unsafe, 0 false aborts**.

Thus, in this constructed model, commit-time freshness must include effect-critical state and authority. A whole-state epoch is safe but measurably over-conservative; dependency-scoped validation preserves more useful commits.

## 4. End-to-end damage-containment evidence

**NOT ESTABLISHED.**

The experiment is exact for its toy state machine only. It does not establish:

- completeness of ClayCode dependency extraction;
- confinement of generated Python/Rust/C/Bash/WASM or FFI;
- Ubuntu kernel/runtime enforcement completeness;
- secret/noninterference guarantees;
- real FRANK effect-path safety;
- crash/restart correctness around irreversible external effects.

Child closure `EffectiveEffects(child) subseteq Effects(parent_Clay_contract)` remains an open end-to-end obligation.

## 5. Ordinary task-utility evidence

The experiment explicitly measured a utility-side cost proxy: unnecessary effect aborts caused solely by unrelated state churn.

Across the fuzz set:

- global epoch guard: **48,090 false aborts**;
- dependency envelope: **0 false aborts**.

This does not prove production latency/throughput benefit, but it falsifies the idea that safety comparison should count only unsafe commits. Coarse safety mechanisms can impose avoidable recomputation and must be evaluated against ordinary system utility.

## Architecture implication

Preferred next candidate for H1/H2 comparison:

`EffectCommitEnvelope { decision_id, dependency_versions, capability_ref, capability_epoch, resource_ref, flow_labels?, budget_ref?, idempotency_key, commit_result, abort_reason, receipt_hash }`

Possible outcomes remain open:

1. whole-ledger CAS is cheap enough on the Ubuntu H1 workload -> retain simpler reference design;
2. dependency-scoped envelopes materially reduce abort/recompute cost without safety loss -> refine runtime ABI;
3. dependency extraction misses real dependencies -> enlarge runtime observation or reopen language/compiler semantics only with a minimized executable counterexample.

## Negative-result preservation

- retained permits across recurrence are unsafe in the constructed stale-state/stale-authority schedules;
- whole-state epoch invalidation is unnecessarily conservative in constructed unrelated-churn schedules;
- no evidence supports a new FRANK-specific loop/effect syntax;
- no refusal-only result is counted as Safe-Effect evidence.
