# SECOND FUSION — Receipt Minimality, Replay Modes, Authority Separation

Run: `spawn-20260809T1918p0700-chatgpt-secondary-harness-rsd`

## New result after first synthesis

The first fusion established receipt closure and semantic-vs-execution identity separation. The second fusion asks two harder questions:

1. Can the receipt set be minimized without losing semantic replay?
2. Can a historical receipt accidentally become authority to repeat an external effect?

The answer is a stronger contract: **record semantic conflict decisions, not every physical scheduling event; and make replay receipts permanently descriptive/non-authoritative.**

## RSD-E5 — selective schedule receipts

A second synthetic experiment used an exact algebraic commutativity classifier over `add(k)`, `mul(k)` and `set(k)` operations.

Across 10,000 traces × 16 operation pairs = 160,000 pairs:

- effective order was required for 98,339 non-commuting pairs;
- 61,661 commuting-pair order receipts could be elided;
- receipt elision in this toy distribution: 38.538125%;
- selective replay divergences: 0;
- a baseline that recorded no conflict order and canonicalized every pair diverged in 4,442/10,000 complete traces.

This does not predict FRANK's eventual compression ratio. It demonstrates the correct abstraction: **semantic serialization/conflict order** rather than thread-switch history.

## External triangulation

Primary engineering precedents converge on the same decomposition while remaining distinct evidence classes:

- FoundationDB uses deterministic simulation for reproducibility but explicitly separates real multithreaded client testing because threads introduce nondeterminism and race-specific failures.
- rr obtains deterministic replay by recording nondeterministic inputs from the kernel/CPU; this demonstrates that replay can be exact without requiring the original environment to become deterministic.
- Temporal-style durable execution records workflow history/nondeterministic choices so replay reconstructs decisions rather than repeating live nondeterminism.
- AWS idempotent API guidance makes the external-side-effect ambiguity concrete: a unique caller request identifier plus server-side duplicate handling is the mechanism that makes retries safe; merely retrying after an uncertain response is not enough.
- PostgreSQL Serializable defines semantic concurrency by equivalence to some serial execution and rejects/retries executions that would violate it. This supports capturing transaction/serialization semantics rather than physical thread interleavings.
- WASI/Component Model resources illustrate host-owned opaque resource handles and default-denied host resource access. This is useful precedent for keeping authority outside descriptive receipt data.

These precedents support architecture shape, not FRANK performance/correctness claims.

## Replay must split into modes

A single `replay()` operation is too ambiguous for a system with external authority.

### 1. ANALYTIC_REPLAY

Purpose: reproduce a historical episode exactly for debugging/measurement.

Rules:
- use frozen semantic receipts;
- external effect gateway is disabled or simulated;
- historical `EffectOutcomeReceipt` is read as data;
- no historical receipt can mint a live authority handle;
- no peer/tool/network/model call is re-issued unless explicitly part of a controlled experiment.

### 2. COUNTERFACTUAL_REPLAY

Purpose: lesion/rescue/shuffle/parameter experiments.

Rules:
- freeze all exogenous receipts except the declared intervention surface;
- effects remain simulated/non-committing;
- intervention identity is included in the semantic transition certificate;
- causal claims remain separate from replay correctness.

### 3. RECOVERY_RESUME

Purpose: resume productive execution after a crash.

Rules:
- reconstruct durable semantic state from canonical history;
- inspect external-effect lifecycle and reconcile any `COMMIT_UNKNOWN` states;
- reacquire/revalidate fresh authority and fresh epistemic preconditions before any new external commit;
- use idempotency/outcome-query semantics where the adapter supports them;
- never treat a historical capability observation or outcome receipt as current execution authority.

### 4. LIVE_EXECUTION

Purpose: normal FRANK operation.

Rules:
- current nondeterministic outcomes become new receipts when semantically relevant;
- concurrency may be physical/asynchronous;
- semantic publication/serialization invariants remain enforced;
- execution trace remains separate from authoritative semantic identity.

## Authority invariant strengthened

Introduce this compact law:

`receipt_of_authority_or_outcome != authority`

A receipt may prove that authority existed or an effect occurred historically. It must not itself be a bearer capability.

Therefore a persisted `CapabilityObservationReceipt` should contain descriptive identity/provenance/scope/freshness evidence or a non-bearer reference, never a reusable privileged token. The live gateway resolves an opaque host-rooted authority handle separately.

This composes directly with the existing project law:

`model output != execution authority`.

It becomes:

`model output != peer/tool output != stored receipt != execution authority`.

## Transition Certificate candidate

A reusable H1/H2/H3 semantic differential unit can be expressed as a logical certificate:

```text
TransitionCertificate {
  contract_hash
  transition_id
  pre_epoch
  pre_state_hash
  external_input_hash
  semantic_receipt_bundle_hash
  serialization_certificate
  intervention_hash_or_none
  post_epoch
  post_state_hash
  effect_outcome_refs
  causal_readout_hash
  execution_trace_ref
}
```

Important: `execution_trace_ref` is evidence/provenance, not part of semantic equality unless a frozen contract explicitly declares a contained field program-observable.

## Receipt closure matrix

Every H1 Golden Trace family should materialize a matrix with one row per external/nondeterministic field:

- producer;
- consumer(s);
- semantic effect surface;
- deterministic derivation available?;
- receipt type if not deterministic;
- receipt identity/hash;
- freshness semantics;
- sensitivity/privacy class;
- authority class (`DESCRIPTIVE_ONLY` expected for persisted receipts);
- omission mutation result;
- replay mode applicability;
- retention/re-expansion policy.

This makes hidden nondeterminism discoverable and turns receipt minimization into a testable compiler/runtime problem rather than an intuition.

## New counterhypotheses

### CH-RSD-E
A generic full event log is simpler and safer than a typed closure matrix.

Countertest: compare false semantic divergences, storage amplification, accidental authority/token persistence, and ability to distinguish missing semantic inputs from irrelevant telemetry.

### CH-RSD-F
Replay and recovery can share one implementation path.

Countertest: attempt analytic replay of a historical effectful episode with a live effect gateway. Any possibility of reissuing the real external effect is a release-blocking design defect.

### CH-RSD-G
Capturing scheduler order is always required.

Countertest: formally/properties prove a transition pair commutes and show canonicalized replay remains exact; then measure order-receipt reduction. RSD-E5 supports this only for its toy algebra.

## Updated architecture delta

The Receipt-Sealed Determinism candidate becomes:

1. deterministic semantic transition contract;
2. typed receipt closure for external semantic nondeterminism;
3. semantic serialization certificate only for non-commuting/conflicting operations;
4. separate semantic and execution identities;
5. explicit replay modes;
6. persisted receipts are descriptive and non-authoritative;
7. recovery reacquires fresh live authority;
8. external commit ambiguity is a first-class state;
9. deterministic replay and real concurrency tests remain complementary;
10. omission/commutativity/authority mutation tests guard the boundary.

## New highest-information Ubuntu test

Extend `WORK-SPAWN-RSD-UBUNTU-20260809` with one decisive safety discriminator:

- take an effectful Golden Trace;
- run `ANALYTIC_REPLAY` under an environment where the corresponding real host capability exists;
- assert that zero live external effect commits are reachable despite the historical outcome/capability receipts being present;
- then run `RECOVERY_RESUME` from each crash point and require fresh authority + adapter-specific reconciliation before any commit.

If analytic replay can cause a live effect, the RSD architecture is falsified as unsafe regardless of deterministic correctness.
