# FUSION 1 — current problem surface

## Live problem
The previous CCF candidate detects whether two exact internal transitions commute at the current state/order level. The concurrent CPD candidate derives causal contribution and pair interactions from sparse symbolic provenance. The current TypedIR/CallContract work independently established that exact semantics must be bound to explicit current state/runtime identities and must never be inferred from names or caller resemblance.

The unresolved gap is **masked order dependence**: two transitions may produce the same observed final state in the current complete trajectory while differing under a counterfactual lesion of a later contextual transition. A state-only commutator therefore can label a pair safe even though the surrounding causal structure contains an order-sensitive dependency.

Concrete witness:
- initial `x = 1`
- `A: x *= 2`
- `B: x += 1`
- `C: x = 0`
- full trajectory: `A;B;C` and `B;A;C` both end at `x=0`
- lesion `C`: `A;B -> 3`, `B;A -> 4`

Thus `current final state equality` is insufficient evidence for causal/order independence.

## First attempted hypothesis and executable refutation
An initial idea claimed that ordinary leave-one-out credit for A/B alone would expose hidden order dependence even with only two operations. The executable discriminator refuted this: when the only toggled interventions are A and B and both full trajectories end identically, the A-only/B-only/none lesion points are also order-independent. A contextual action is needed to mask a genuine upstream order effect.

This negative result changed the candidate before persistence.

## High-leverage target
Build one exact, epoch-bound algebra that can answer:
1. do A and B differ at the observed full state?
2. if not, do they differ anywhere in represented lesion/context space?
3. which UseRef interactions explain that difference?
4. can this produce a conservative Frank-v0.1 coordination graph without minting effect authority?

The selected problem directly connects F-V01-02 ClayCode compiler/runtime, F-V01-03 cognitive loop core, F-V01-05 GWT/Hyperposition/topology, F-V01-09 effect authority, F-V01-11 causal credit/reward/goals, and F-V01-13 recovery/observability.
