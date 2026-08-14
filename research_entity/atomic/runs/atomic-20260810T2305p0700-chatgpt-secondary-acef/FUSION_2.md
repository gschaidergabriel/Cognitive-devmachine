# FUSION 2 — after external prior-art destruction

The first hypothesis field overestimated novelty in several components. Semantic transactions, belief commits, event sourcing, speculative durable execution, truth maintenance, lattices/CRDTs, differential recomputation and capability safety all have strong prior art.

The surviving research opportunity is therefore compositional and Frank-specific.

## Recombined candidate

ACEF makes every state-bearing cognitive recurrence a lease-fenced `CognitiveTxn` over immutable `SemanticDelta`s. A delta carries monotonicity, visibility, branch, provenance, causal parents, epistemic class, authority/effect class and source/state epochs. Monotone observations may become globally queryable early through a join-safe evidence plane. Non-monotone belief/goal/reward/personality changes remain branch-local until a commit certificate proves current lease/schema/identity epochs and all required validation predicates. Effects remain outside ordinary rollback: intent/reservation/attempt/unknown-outcome/verification follow the existing Frank effect contract and are linked to the cognitive transaction through an effect edge. Re-entry is admitted only from committed or explicitly failure/unknown evidence deltas.

GWT is not truth authority. A WorkspaceEpisode references a transaction/branch and can broadcast provisional candidates. Hyperposition is the branch set. ClayGraph is a differential projection over committed plus explicitly viewable provisional deltas. UnifiedDB remains canonical persistence. The target has one global external execution lease, but may explore multiple internal branch-local hypotheses under the same execution epoch.

## Key deletion

If ACEF is promoted, cognitive organs should lose direct canonical-state write APIs. They emit typed deltas. The commit fabric becomes the sole semantic admission boundary. This is the architecture-compression claim and the highest-risk delta.

## What would refute ACEF

ACEF should be rejected if current narrower semantics already produce zero cross-surface inconsistency under exhaustive fault/replay testing and a simpler task transaction matches safety with materially lower latency/complexity; if monotonicity classification cannot be made reliable; if causal metadata explodes state/resources; if branch management causes combinatorial blow-up; or if ClayCode implementation needs opaque escape hatches that create a second semantic architecture.
