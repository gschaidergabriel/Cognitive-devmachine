# Fusion 1 — unresolved alternatives are semantically cheap but can be physically expensive

## Current problem graph

Frank v0.1 requires unresolved alternatives/Hyperposition without truth promotion. The current Hyperposition branch is deliberately unchanged and imposes entity/version/provenance preservation. At the same time the loop core, GWT consumer surfaces and UnifiedDB state have finite context/RAM/serialization budgets. A naive realization of N possible worlds duplicates mostly-identical self/world/goal/memory/workspace state N times.

The architectural question is therefore not whether alternatives are allowed; that is already a current semantic requirement. The open question is the **physical representation and transition geometry**:

`one shared history/state + sparse divergences ?`

versus

`N independent state copies ?`

versus

`persistent copy-on-write structures / hash-consed DAG / decision-diagram guarded values ?`

## Accepted invariants

1. An unresolved alternative is not truth, SELF, user intent, permission or effect authority.
2. Branch identity must include exact entity/version/state epoch/provenance; equal payload is not enough to merge semantically distinct evidence histories when those histories matter.
3. Downtime cannot fabricate cognitive states that never occurred.
4. Collapse requires admitted evidence or policy, never salience alone.
5. Effects are not speculatively executed merely because a branch exists.
6. Pure/read-only internal transitions may be simulated; external effects remain proposals until a single current branch/intent passes normal authority and verification.
7. Reconstruction of any represented branch must be exact for the declared state model.

## Bottleneck hypothesis

Suppose each possibility has `F` state fields and only `d << F` fields differ. Naive copy cost is approximately `O(NF)`. A shared-base sparse-delta representation could approach `O(F + Nd)` storage, but only if:

- branch reads do not become too expensive;
- updates do not trigger large delta cascades;
- provenance/epoch metadata does not dominate;
- merge/collapse remains deterministic;
- shared execution across branches is semantically legal only for pure operations whose read-set sees equal values under all relevant guards.

The key danger is that an apparently compressed representation simply moves the cost into lookup, branch-condition evaluation or repeated materialization.

## Strong baseline set

The run must not compare only against deep-copy worlds. Required strong controls:

- `FULL_COPY`: independent materialized dict/state per branch;
- `SPARSE_OVERLAY`: one immutable base plus one ordinary override map per branch;
- `PERSISTENT_PATH_COPY`: structural sharing by path-copying immutable maps/trees;
- `HASH_CONSED_DAG`: deduplicate identical branch states/content nodes;
- `GUARDED_VALUE`: field values represented as condition->value alternatives, decision-diagram/faceted-style;
- `PSW`: shared base + branch guards + sparse deltas + read-set-aware shared pure transition lifting + exact collapse/merge.

## Discriminator

PSW is only interesting if it yields a Pareto improvement in at least one meaningful regime **against the strongest conventional shared-state baseline**, while preserving exact branch reconstruction and provenance/epoch isolation.

A useful result can also be negative: identify the sparsity/divergence/branch-count region where sparse shared possibility state stops paying for itself, and route that as a representation-selection rule rather than a new organ.

## Measurements

- exact reconstruction error;
- false semantic merge rate;
- stale-epoch acceptance rate;
- provenance-collision merge rate;
- approximate deep-size bytes;
- bytes per branch;
- read latency p50/p95/p99;
- update latency p50/p95/p99;
- transition operations executed versus naive per-branch execution;
- shared-transition hit rate;
- collapse/merge latency;
- serialization bytes;
- cost as branch count and divergence density vary;
- pathological write-heavy/random-read regimes.

## Strongest initial counterhypothesis

A simple persistent/sparse overlay representation plus ordinary memoization gives essentially all useful sharing. PSW's explicit guard mesh and transition lifting merely reimplement known variational/faceted execution with more metadata and worse constant factors. If this is true, do not promote PSW; keep only a measured representation-envelope and implementation obligation.
