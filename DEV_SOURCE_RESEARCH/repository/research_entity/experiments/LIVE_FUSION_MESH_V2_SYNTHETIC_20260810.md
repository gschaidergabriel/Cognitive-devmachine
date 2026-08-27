# LIVE FUSION MESH V2 — SYNTHETIC ROUTING EVIDENCE

Run: `20260810T1419p0700-live-fusion-mesh-v2`
Actor: `chatgpt-secondary`
Provider/model: `OpenAI / GPT-5.6 Sol`
Evidence class: `SIMULATION_ONLY`
Canonical parent: revision `2`, state hash `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
Candidate: `research_entity/global/CLAY_LIVE_FUSION_MESH_V2_CANDIDATE.clay` v0.2-candidate
Deterministic test: `research_entity/experiments/live_fusion_mesh_v2_sim.py`

## Question

Can Clay strengthen live fusion/networking by routing provenance-bound semantic deltas through current work/claim/dependency topology instead of either:

1. broadcasting every material payload to all nine peer branches, or
2. routing only by semantic/tag similarity?

The candidate must preserve the existing rule that connectivity/distribution does not increase evidence strength or effect authority.

## Hypothesis

A dependency-aware delta fabric can materially reduce full-payload fanout versus broadcast while preserving substantially more invalidation recall than tag-only routing. Projection incompleteness is expected to be the main failure mode and therefore requires explicit anti-entropy/repair.

## Strongest counterhypothesis

Incremental/targeted propagation can be worse than dense fanout when a small change has a large downstream dependency cone, when dependency projections are stale/incomplete, or when repair overhead dominates. Therefore targeted delta routing must not become dogma; route planning should be cost-aware and may deliberately choose dense fanout.

Fresh external evidence supporting the counterhypothesis includes the 2026 Enzyme work on cost-based incremental refresh strategy selection and incremental graph work showing that small graph changes can propagate globally.

## External research fused

Primary/near-primary sources retrieved live during this run:

- McSherry, Murray, Isaacs, Isard — `Differential dataflow`, CIDR 2013. Incremental changes can be propagated through iterative/nested computations instead of complete recomputation.
- Murray et al. — `Naiad: A Timely Dataflow System`, SOSP 2013. Logical timestamps support low-latency cyclic/incremental distributed dataflow.
- Budiu et al. — `DBSP: Automatic Incremental View Maintenance for Rich Query Languages`, PVLDB 2023; extended journal version 2025. General incremental view maintenance applies to rich and recursive query structures.
- Yadav et al. — `Enzyme: Incremental View Maintenance for Data Engineering`, arXiv:2603.27775, 2026. Production-scale IVM uses cost-based refresh planning rather than assuming one incremental strategy is always optimal.
- Yu et al. — `Layph: Making Change Propagation Constraint in Incremental Graph Processing by Layering Graph`, arXiv:2304.07458. Small changes can trigger global propagation; constraining propagation can reduce communication cost.
- Preguiça et al. — `Dotted Version Vectors: Logical Clocks for Optimistic Replication`, arXiv:1011.5808. Compact causal tracking is possible without requiring a global total order.

No external source is treated as direct proof that the Clay candidate is correct.

## Synthetic test design

- 9 peer branches.
- 10 current synthetic work/claim nodes per branch.
- Cross-branch claim dependencies sampled with semantic bias plus hidden cross-domain dependencies.
- 5,000 material deltas.
- Delta classes: NEW, REFINES, CONFIRMS, CONTRADICTS, SUPERSEDES, NO_MATERIAL_CHANGE.
- Ground-truth affected branches are derived from the full synthetic claim dependency graph plus direct semantic impact.
- Candidate routing sees a deliberately degraded dependency projection with 8% of dependency edges missing.
- Baselines:
  - `broadcast`: full payload to all 9 branches;
  - `tag_only`: origin + semantic tag overlap;
  - `candidate`: origin + semantic overlap + observed causal dependents for refinements/invalidations.

Important limitation: the candidate router has no fabricated dependency edges in this synthetic test, so precision is artificially favorable. Real ClayGraph can contain stale or incorrect projections; false-positive routing and false interrupts require real replay/fault injection.

## Deterministic result

Exact deterministic run logic corresponding to the committed script produced:

| Router | Full payloads / delta | Micro recall of required branch deliveries | Perfect-event recall | Missed required deliveries | Redundant full deliveries |
|---|---:|---:|---:|---:|---:|
| broadcast | 9.0000 | 1.0000 | 1.0000 | 0 | 30,175 |
| tag_only | 1.7474 | 0.58934 | 0.6210 | 6,088 | 0 |
| dependency candidate | 2.8444 | 0.95933 | 0.9202 | 603 | 0 |

Derived comparison:

- candidate full-payload fanout is ~68.4% lower than broadcast in this synthetic workload;
- candidate branch-delivery recall is ~37.0 percentage points higher than tag-only;
- the remaining ~4.1% missed required deliveries are caused by the intentionally incomplete observed dependency projection, directly motivating anti-entropy/projection repair;
- broadcast achieves complete recall but delivers more than three times as many full payloads as the candidate here.

This is `SIMULATION_ONLY`, not live runtime evidence and not a promotion result.

## Exactly one out-of-the-box experiment

Name: `high_centrality_premise_inversion`.

Method: choose the synthetic premise whose transitive dependency impact is maximally under-represented by its local vocabulary, then flip it from accepted premise to `CONTRADICTS`.

Selected origin claim: `unifieddb:7`.
Required affected branches: all nine peer branches.

Result:

- broadcast: 9 messages, recall 1.0;
- tag-only: 1 message, recall 0.1111, misses 8 affected branches;
- dependency candidate: 9 messages, recall 1.0.

Interpretation: a high-centrality contradiction is exactly where stronger networking should intentionally become dense. This observation plus the fresh Enzyme counterevidence caused candidate v0.2 to add an adaptive `RoutePlan` with `TARGETED_DELTA | DENSE_FANOUT | DIGEST_ONLY` rather than forcing targeted delivery globally.

## Architecture delta

Created and revised:

`research_entity/global/CLAY_LIVE_FUSION_MESH_V2_CANDIDATE.clay`

Key mechanisms:

- provenance/content-hash-bound `KnowledgeDeltaV2`;
- current branch work/claim `BranchDependencyIndex`;
- adaptive cost-aware `RoutePlan`;
- dependency-aware invalidation traversal;
- compact payload references instead of repeated global context;
- causal-predecessor checking without mandatory global total order;
- per-epoch `AntiEntropyDigest` and repair on ack/projection/predecessor gaps;
- `FusionReceipt` separating delivered -> reconstructed -> plan revalidated -> used -> effect;
- explicit degraded-coordination state on repair failure;
- measurement of recall, fanout, latency, stale window, false interrupts, repair success, resources and route-cost prediction error.

## Negative/uncertain results preserved

1. `CURRENT_DYNAMIC_WORK.clay`, referenced by the current work-event protocol, returned 404 at the expected repository path during this run. This is a coordination/projection risk, not proof the runtime materialization is globally broken.
2. Dependency routing is not sufficient by itself: an 8% missing-edge projection still lost 603 required synthetic deliveries before anti-entropy repair.
3. Adaptive cost-aware route selection in candidate v0.2 has not yet been empirically benchmarked.
4. Anti-entropy recovery semantics have not yet been executed against real repo worker state.
5. No Hostinger/Ubuntu runtime test was executed in this run.

## Required next falsifiers

1. Real repository replay over current work events/branch feedback: compare broadcast/tag-only/v0.2 adaptive routing.
2. Inject stale projection, missing edge, duplicate delta, out-of-order causal predecessor and crash/restart faults.
3. Measure permanent miss rate after anti-entropy, repair latency, control bytes, full payload bytes, CPU/RAM/I/O and false interrupts.
4. Validate that invalidated work is interrupted before the next material effect.
5. Only after real replay + recovery evidence consider promotion into owner-fixed mesh protocols.

## Decision

`SUPPORTED_AS_RESEARCH_CANDIDATE`, not promoted.

The strongest current design is adaptive dependency-aware delta fusion with explicit anti-entropy and dense-fanout fallback. The strongest current reason not to promote it is absence of real shared-worker/UnifiedDB/ClayGraph replay and recovery evidence.
