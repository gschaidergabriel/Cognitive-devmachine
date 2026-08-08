# H3 Intra-Run Mesh Addendum

New upstream artifacts appeared after the initial H3 Fusion 2 while the run was being materialized. Per the Interconnected Research Mesh rule they were inspected before closure.

## Clay G9 read-aware epoch maintenance

`KMP-G9-READ-AWARE-EPOCH-MAINTENANCE` reports a separate seeded economics proxy using the same ClayGraph C4 cost lineage: a noisy read-aware selector had ~2.4% regret versus oracle, versus ~18.7% for a fixed 5% threshold and ~23.8% for 10%. A debt-aware alternative lowered p95 while raising mean cost.

**Effect on H3:** strengthens, but does not independently replicate, H-HYP3-010/011 because both H3 and G9 inherit the ClayGraph C4 proxy cost surface. HYP-RC3 rematerialization objective is expanded from mean amortized cost to an explicit vector: mean/tail latency, write amplification, memory/overlay debt, cascade risk and recovery.

## Clay G9 deterministic-before-generative projection

`KMP-G9-DETERMINISTIC-BEFORE-GENERATIVE` reports 6/10 raw-state versus 8/10 trusted candidate projection on its fixed Groq 8B proxy corpus with prompt tokens 487→324, while also preserving a negative result: the compiled arm still made a deterministic min/max error and omitted a unique answer.

**Effect on H3:** strengthens the Assembly compiler boundary. Deterministic filter/join/min/max/uniqueness/version/capability operations should be executed by trusted runtime semantics before model projection where sound; unresolved alternatives plus witnesses go to the model. Model output remains a proposal. Metric disagreements across branches remain provenance-visible rather than silently reconciled.

## GWT Cycle 4 causal-stage orthogonality

New GWT4 evidence reports a constructed identifiability calibration where bundled graph+workspace+projection ablation produced ~0.2396 apparent gain despite a true workspace effect of zero; the orthogonal workspace contrast was zero. With a nonzero constructed workspace mechanism, bundled delta was ~0.3113 while isolated workspace contrast was ~0.0845. Groq 8B proxy evidence also shows projection/order/context metadata can materially change deterministic selections.

**Effect on H3:** upgrades `TopologyBasis` from replay witness to **experimental orthogonality witness**. Hyperposition, GWT, projection and activation must be separately lesionable; bundled interventions cannot identify which causal stage produced an effect.

## FRANK Cycle 5 Cognitive Epoch Capsule

FRANK C5 appeared during H3 closure with a new `S.COGNITIVE_EPOCH_CAPSULE` and `M.COGNITIVE_EPOCH_COORDINATOR`. Its state contract seals frame identity, exact-state root, memory/Assembly reference, operation semantics, semantic-graph schema and reader contract before workspace competition. It also keeps graph activation non-authoritative and reader projection separately receipted.

**Effect on H3:** this is strong cross-branch convergence but not independent replication because both workers share RAE ancestry and current upstream material. H3 will **not invent a competing FRANK state object**. `TopologyBasis` remains the abstract Hyperposition semantic contract; FRANK's `CognitiveEpochCapsule` is the current implementation envelope that should realize it. Hyperposition tests should therefore target capsule/basis invariants rather than introduce parallel schemas.

## Decision after intra-run feedback

- `HYP-RC3`: RETAIN / STRENGTHEN, still OPEN.
- `TopologyBasis`: abstract semantic/replay/orthogonality contract; map to FRANK `CognitiveEpochCapsule` for implementation.
- Add rematerialization tail/debt objectives.
- Add deterministic-before-generative reader projection rule.
- Add orthogonal intervention identity to basis/projection receipts.
- No canonical promotion; no target/live claims.
