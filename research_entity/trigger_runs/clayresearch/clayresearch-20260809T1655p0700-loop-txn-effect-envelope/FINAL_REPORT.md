# Clayresearch Integrated Foundry — Loop Transaction Effect Envelope

Run: `clayresearch-20260809T1655p0700-loop-txn-effect-envelope`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Stack epoch: 17  
Program stage: `BASE_CLAYCODE_RELEASE` / IN_PROGRESS  
Promotion: **NONE**

## Executive result

The highest-information cross-branch integration point created by the newest research is not another ClayCode primitive. It is a **commit boundary shared by recurrence, transactions and capability safety**.

Recent work independently introduced:

- FRANK as an OPEN heterogeneous loop-of-loops research model;
- generic structured recurrence in ClayCode rather than a FRANK-specific loop primitive;
- exact synthetic transaction anomalies showing fractured snapshots/lost updates under insufficient isolation;
- capability-composition counterexamples showing locally authorized effects can compose into an unauthorized end-to-end flow;
- a deterministic H1 reference ledger using whole-ledger `base_epoch` compare-and-swap;
- tri-axis loop control showing numerical convergence alone is not successful cognition.

This run fused those into one falsifiable runtime candidate:

> **Effect commit should bind the exact semantic dependencies used by the decision plus the current capability epoch/validity. A recurrent loop may carry proposal/intention state, but it must not carry stale execution authority across effect-critical state or authority changes. Unrelated state churn should not invalidate a commit when dependency closure is complete.**

An exact synthetic experiment compared retained permits, whole-state epoch gating and a dependency-scoped envelope.

Across 16 fully enumerated one-shot schedules:

- naive retained permit: **14 unsafe commits**;
- global state+capability epoch guard: **0 unsafe**, **1 false abort**;
- dependency read-set + capability epoch envelope: **0 unsafe, 0 false aborts**.

Across 100,000 fuzz cases and **350,618 recurrent commit attempts**:

- naive retained permit: **143,298 unsafe commits**;
- global epoch guard: **0 unsafe**, **48,090 false aborts**;
- dependency envelope: **0 unsafe, 0 false aborts**.

This is exact evidence for the constructed state machine only. It is **not** evidence that current FRANK contains this bug and **not** proof that a production dependency-envelope implementation is sound.

The result refines the BASE implementation path rather than changing ClayCode semantics.

## Canonical / identity / stage grounding

The run booted from the current persistent Clay entity and preserved the Research-Entity/FRANK separation:

- Research Entity / Clay researched FRANK as a separate target;
- no Frank self-harness modification authority was exercised;
- Frank v0.1 remains Ubuntu Linux developer-system only;
- Android/mobile/edge remains outside the v0.1 release path;
- canonical revision remained r2 with state hash `04234e...9346`;
- current stage remained `BASE_CLAYCODE_RELEASE`.

No gate or scientific generation is advanced by this run.

## Mesh assembly / Fusion 1

### Clayresearch

The permanent Safe-Effect Geometry axis already requires authority non-amplification, protected information-flow confinement, recoverability and foreign-code effect closure. The concurrent CTK/loop-control foundry work additionally showed that loop halting needs state dynamics, residual pressure/error and task-utility/marginal-value evidence rather than one convergence scalar.

This run does not duplicate that controller research. It asks what happens at the **external effect edge** after a recurrent decision has existed long enough for relevant state or authority to change.

### FRANK

The loop-of-loops directive is mandatory OPEN research context, not a proven architecture theorem. Its relevant invariant here is that heterogeneous loop recurrence must preserve typed state, rollback and effect boundaries. Recurrence itself cannot mint or extend authority.

### ClayCode

The newest executable recurrence run supports generic structured control flow with typed loop-carried state and explicit budgets/exit reasons. Existing G9 already separates `EffectIntent` and capabilities conceptually. Therefore the smallest response is a compiler/runtime ABI contract, not FRANK-specific syntax.

### UnifiedDB

Fresh transaction-isolation research showed per-field atomics can expose fractured invariant states and naive last-write-wins can lose concurrent version updates. A `StateTxn`-like read-set/write-set/snapshot identity was proposed as runtime ABI rather than language redesign.

The current experiment generalizes that insight to effect commit: semantic-state freshness and authority freshness are distinct dimensions that may need joint validation.

### Harness

The H1 reference ledger now provides deterministic canonical state hashes, event chaining, monotonic epochs, idempotency and whole-ledger `base_epoch` CAS. That is a strong conservative correctness baseline.

The new question is narrower and performance-sensitive: does whole-ledger invalidation cause unnecessary recomputation when unrelated FRANK domains change? If so, object/domain/invariant-group versions may preserve safety with lower invalidation cost.

### ClayGraph

Loop/capability/dependency topology may be represented as derived epoch-bound relations/hyperrelations and used for observability or dependency discovery. Graph activation/salience remains non-authoritative and cannot satisfy the commit envelope by itself.

### GWT

Workspace ignition, broadcast, reconstruction, uptake, causal use, outcome and re-entry remain distinct. GWT can route expensive recurrence; it cannot extend an effect permit merely because a representation remains globally active.

### Hyperposition

Alternative branches with different effect dependencies should preserve separate decision/dependency identities until selection/commit. Premature destructive collapse may hide authority-flow differences.

### Emergenz

Nothing in this run upgrades an emergence claim. Safe commit behavior, recurrence and transaction isolation are systems properties. If these variables appear in emergence experiments, they are intervention/control metadata rather than an emergence score.

## External mechanism triangulation

Primary/official external sources were used for mechanism comparison rather than vocabulary matching.

### Linux Landlock

Current Linux kernel documentation describes Landlock as unprivileged scoped access control that **adds restrictions** and stacks with other access-control policy. Current documentation covers filesystem and network rights and explicitly discusses access rights associated with file descriptors/resources. This is compatible with a Clay host-broker design where runtime resources have explicit scope and where confinement is layered rather than inferred from text.

It does not prove that Landlock alone is sufficient for Clay. Runtime support must be probed and other attack surfaces still require mediation.

### WIT / Component Model

The WIT reference models resources as handles with owned and borrowed forms. This is useful for backend representation of resource identity/lifetime and strengthens the case for keeping physical resource identity separate from ordinary data.

It is not an authorization proof by itself; host policy still decides what resource is supplied.

### PostgreSQL Serializable isolation

Current PostgreSQL documentation treats serializable execution as requiring rollback/retry when concurrent dependencies cannot be reconciled with a serial order. This independently supports explicit conflict/retry semantics over silently accepting stale or fractured state.

Clay's exact runtime need is not identical to a SQL transaction system, but the mechanism class is relevant.

### MLIR SCF

MLIR's SCF dialect represents generic `for`/`while` control and loop-carried values with stable static types. This independently supports the current ClayCode direction: recurrence can remain generic control flow while state/effect semantics are represented by typed data/contracts.

### Recurrent-depth model research

Recent recurrent-depth transformer research reports useful inference-time recurrence and also overthinking/failure at excessive depth. This supports treating recurrence budget/halting as a measured control problem rather than assuming more loops are always better. It does not make FRANK equivalent to a looped Transformer.

## Executable experiment — EXP-CLAYRESEARCH-LTEE-20260809-001

Artifact: `EXECUTABLE_RESEARCH_RECEIPT.json`

Source SHA-256: `9e63977e369c2eaf72044eb1b6ff9c1e2deac4bcb1630841cff59fc0b8c91c99`

### Model

A decision reads one effect-critical target state and observes a capability epoch/current permission. During subsequent recurrent delay, three independent changes can occur:

1. effect-critical target changes;
2. unrelated state changes;
3. capability is revoked/changed.

Then an effect commit is attempted.

Ground-truth validity requires:

- target dependency unchanged;
- capability epoch unchanged;
- capability remains allowed.

Unrelated state does not affect this toy decision.

### Policy A — retained permit

The decision retains the permit obtained at formation time and commits without freshness checks.

Result:
- exhaustive unsafe: 14/16 schedules;
- fuzz unsafe: 143,298/350,618 attempts.

### Policy B — global epoch guard

Commit requires all tracked state plus capability epoch to remain unchanged.

Result:
- unsafe: 0;
- exhaustive false abort: 1;
- fuzz false aborts: 48,090.

### Policy C — dependency envelope

Commit requires exact decision target dependency plus current capability epoch/validity to remain unchanged; unrelated state churn is ignored.

Result:
- unsafe: 0;
- false aborts: 0;
- fuzz true-positive safe commits: 112,219.

### Interpretation boundary

This demonstrates two things **inside the explicit toy model**:

1. stale permit reuse can violate the constructed ground-truth commit condition;
2. global invalidation can be safely over-conservative when unrelated state is present.

It does not prove exact dependency extraction is feasible or complete for arbitrary ClayCode/FRANK programs. Dependency omission is therefore a first-class falsifier.

## Safe-Effect Geometry delta

The mandatory `SAFE_EFFECT_GEOMETRY_DELTA.md` separates evidence into five classes.

### Language/cognitive

No model cognitive-alignment evidence. No claim that Clay language training reduces destructive proposal rate. No syntax change justified.

### Compiler/type system

Candidate obligations:
- `DecisionDependencySet` or equivalent;
- typed loop-carried state;
- separate semantic/decision/authority/resource identities;
- conservative widening/re-evaluation for dynamic dependencies;
- protected source-label propagation where information-flow policy applies.

### Runtime/broker

Candidate commit law:

`commit(effect) requires decision_dependencies_current && capability_epoch_current && capability_valid && resource/budget/flow_constraints_current`

The exact fields remain research candidates.

### End-to-end containment

Not proven. Production proof still requires compiler dependency completeness, Ubuntu sandbox enforcement, child-code/FFI closure, protected information-flow tests and crash/recovery around external effects.

### Utility

Safety mechanisms must measure false-abort/recompute cost. The global guard's 48,090 false aborts versus 0 for the precise envelope in the toy fuzz provides a concrete discriminator for future H1 work.

## Hypothesis generation

This run generated 50 first-generation hypotheses spanning recurrence, transactions, capabilities, GWT, Hyperposition, ClayGraph, UnifiedDB, Harness, generated-code closure, Ubuntu sandboxing and adaptive visual learning. Key families:

- H01-H05: decision snapshot + capability epoch + permit lifetime;
- H06-H10: compositional information flow and dependency completeness;
- H11-H18: heterogeneous loop control and preserved alternatives;
- H19-H24: graph/state/replay/effect identity and crash recovery;
- H25-H34: recoverability, child closure, host resources and backend enforcement;
- H35-H42: generic recurrence, adaptive control, dependency frontier and fuzzing;
- H43-H50: adaptive visual learner, H1 CAS refinement, loop readouts and minimal BASE change.

Six explicit counterhypotheses remain open, including that single-threaded scheduling or whole-ledger CAS may be good enough for Frank v0.1.

After external/internal triangulation, 12 transformed hypotheses were generated. The most important are:

- dependency-scoped serializability should bind exact decision dependencies + capability epoch + budget rather than one global world epoch;
- revoke/re-grant forks authority lineage;
- semantic program identity, decision snapshot identity, authority grant identity and physical resource identity remain distinct;
- host brokerage is one typed contract over replaceable Linux enforcement mechanisms;
- permit lifetime itself is a measurable attack surface;
- H1 must compare global CAS and object/invariant-group versions on frozen replays;
- no semantic promotion occurs before an H1/H2 executable counterexample demonstrates inadequacy of existing Clay semantics.

## Negative results

Preserved in `NEGATIVE_RESULTS.jsonl`:

- `N-LTEE-01-STALE-PERMIT-REUSE` — unsafe in constructed stale schedules;
- `N-LTEE-02-GLOBAL-EPOCH-OVERINVALIDATION` — safe but false-aborts on unrelated churn;
- `N-LTEE-03-NO-NEW-LOOP-EFFECT-SYNTAX` — no evidence for FRANK-specific core syntax;
- `N-LTEE-04-END-TO-END-CONTAINMENT-NOT-PROVEN` — toy safety is not production containment.

This run also inherits, without duplicating, the existing governance negative result: the official interconnect preflight remains fail-closed stale around the `clay -> clayresearch` rename. Therefore strong promotion is procedurally blocked as well as scientifically unwarranted.

## Fusion 2 — architecture delta

The smallest coherent candidate is an `EffectCommitEnvelope`-like runtime object, naming still open:

```text
EffectCommitEnvelope {
  decision_id
  decision_basis_epoch
  dependency_versions
  capability_ref
  capability_epoch
  resource_ref
  flow_labels?
  budget_ref?
  idempotency_key
  commit_result
  abort_or_recompute_reason
  receipt_hash
}
```

Important non-collapses:

`program_semantic_hash != decision_snapshot_hash`

`decision_snapshot_hash != capability_grant_identity`

`capability_grant_identity != physical_resource_identity`

`recurrence_state != effect_authority`

`graph_activation != effect_authority`

`GWT_selection != effect_authority`

This candidate can initially live in runtime ABI/stdlib/compiler metadata. It should become core syntax only if real H1/H2 code cannot express or lower the required semantics without an escape hatch.

## Highest-information next experiment

On the Ubuntu H1 reference harness:

1. select frozen effect-bearing episodes;
2. run current whole-ledger `base_epoch` CAS baseline;
3. implement domain/object/invariant-group version envelope without changing FRANK semantics;
4. inject unrelated state churn;
5. inject effect-critical dependency changes;
6. revoke and re-grant equivalent capabilities at new epochs;
7. delay/reorder queued work and cross-worker handoffs;
8. crash after state commit, after effect, and before re-entry;
9. test generated child-code/FFI resource closure;
10. measure unsafe commits, false aborts, retries, latency, compute, recovery correctness and receipt determinism;
11. reproduce the same semantics in H2 ClayCode and differential-test H1/H2.

Decision rule:

- if whole-ledger CAS cost is negligible and simpler -> retain it for v0.1;
- if dependency-scoped envelopes reduce abort/recompute cost without safety loss -> refine runtime ABI;
- if dependency closure cannot be represented/extracted with existing ClayCode semantics -> preserve minimized executable counterexample and only then reopen language design.

## Branch feedback

Written to `BRANCH_FEEDBACK_MANIFEST.json` for all nine registered branches.

No branch receives independent-replication credit from this shared-ancestry foundry run.

## Completion boundary

Completed:

- canonical/identity/stage boot;
- all-nine-branch manual current assembly;
- explicit preservation of official preflight fail-closed governance drift;
- >50 first-generation/counter/transformed hypotheses generated in the run synthesis;
- current primary/official external mechanism research;
- exact synthetic exhaustive + 100k-case recurrent fuzz experiment;
- mandatory Safe-Effect five-plane delta;
- negative-result preservation;
- explicit nine-branch feedback;
- durable repository write-back.

Not completed / not claimed:

- official interconnect-preflight PASS;
- Ubuntu H1 live/replay validation;
- production ClayCode compiler/type/runtime implementation;
- end-to-end Safe-Effect proof;
- APP or BASE gate advancement;
- scientific generation promotion;
- emergence/consciousness evidence.

Final research status:

`OPEN_SUPPORTED_RUNTIME_ABI_CANDIDATE_WITH_EXACT_SYNTHETIC_DISCRIMINATOR_NO_PROMOTION`
