# UnifiedDB U11 — Proof-Carrying Associative Memory Fabric (PCAMF)

## Core result

The strongest architecture found in this run is not a physically unified “mega database”. It is an asymmetric machine-native memory fabric:

1. **Canonical Truth Spine** — deterministic append-only epoch/state/effect history.
2. **Typed Receipt Lattice** — proof-carrying causal/execution closure from GWT use through attempt, verified outcome, causal credit/admitted delta, re-entry and terminal DONE.
3. **Derived Associative Fields** — PKM/ANN/Hopfield/model-native memories may be opaque, learned and dynamically reorganized, but they return candidates only.
4. **Adaptive Query Compiler** — chooses a field or exact path from measured workload and calibrated admissibility; approximate routes must abstain/fallback.
5. **Canonical Rebind** — cognition-critical approximate selections are re-resolved to exact canonical record/state epoch before use.
6. **Incremental Projection Engine** — derived graph/FTS/vector projections advance by deltas and publish source epoch/root/readiness.
7. **Authenticated Epoch Checkpoints** — optional periodic Merkle proofs over canonical history for tamper-evident inclusion/consistency.
8. **RouteValidityCertificate + ShadowRiskSentinel** — learned accelerators receive only a revocable, empirically scoped execution right. The certificate binds exact model/index/epoch/calibration identities and measured risk; an exact-reference shadow sentinel continuously tries to falsify it and quarantines the accelerator on drift/disagreement.

Human readability is intentionally not an internal architecture gate. Auditability is moved to machine-verifiable receipts, replay, metrics, explicit validity scopes and recovery boundaries.

## Empirical discoveries

### Proof-carrying causal state
A synthetic receipt DAG requiring typed chain closure accepted every valid chain and falsely accepted 0/10,000 adversarially mutated chains. The free-form/non-empty-ID baseline accepted about 85.72% of those mutations. Candidate validator p50 was ~20.7 microseconds locally. This directly addresses the observed V17/U10 gap where support IDs can be syntactically present without canonical causal/execution backing.

### Product-Key Memory
On a 65,536-slot product-structured manifold, PKM reproduced brute-force top-1 exactly across all tested noise levels while using 256x fewer key-index floats and ~2.4–2.6x lower local p50 lookup latency. On deliberately non-product random keys, PKM recall was 0. This is the decisive result: machine-native structured memory is powerful only when its structural assumption is true.

### Adaptive router
A router can conservatively choose PKM or fallback, but stable sweeps show a sensitive frontier. Larger candidate spaces improved mean cost, yet p50 gains were inconsistent and naive calibration produced occasional false routes. Even with conservative margin/top-k combinations, the mechanism is not ready for unconditional promotion. The correct design is “measured route or fallback”, not “always use learned retrieval”.

### RouteValidityCertificate falsifier
A finite-sample certificate was calibrated on 1,494 selected cases with zero observed errors. Its one-sided 99% zero-error binomial upper bound was about 0.3078%, below a declared 0.5% target risk, and 3,000 IID held-out queries again produced zero routed errors. That success did **not** generalize universally: a constructed same-index tail shift selected 22 queries for the accelerated route and all 22 disagreed with the exact reference. The index itself had not changed, so hash/epoch binding alone could not detect the shift.

This separates three questions that must never be conflated:

- **canonical rebind**: does the returned candidate correspond to a valid current canonical object?
- **route validity**: is this accelerator empirically reliable in the declared query regime?
- **authority**: may the resulting state cause a consequential effect?

A valid canonical object can still be the wrong retrieval result. Therefore learned retrieval needs a revocable validity certificate plus an online exact-shadow risk sentinel. Index/build/epoch changes invalidate the certificate immediately; distribution drift can invalidate it even without any hash change. A quarantined accelerator falls back to the deterministic/reference path and requires fresh shadow calibration before re-entry.

The measured shadow tradeoff makes this explicit rather than magical: in the constructed shift, exact-shadow checks on 10% of accelerated routes cost roughly 4.96% exact checks over all IID queries and would detect the first checked mismatch after about 227 shifted queries in expectation; 25% shadowing raises overhead to ~12.39% but reduces that expectation to ~91 queries. These are empirical design points, not universal guarantees.

### Hyperdimensional/VSA field
4096-dimensional superposition was exact at light loads but degraded toward ~0.82 recall around 300 bindings with rising decode cost. It is rejected as a primary exact relation store and retained only as a possible exploratory associative signal.

### Incremental projections
For 30,000 synthetic records with 1% update batches, exact delta maintenance was ~20.6x faster than full rebuild at median while preserving projection equivalence. This supports a DBSP-like incremental ClayGraph/FTS projection path.

### Authenticated checkpoints
A local Merkle-segment prototype detected mutation and produced compact inclusion paths; this remains a candidate enhancement to the existing root-hash lineage, not a proposal to add blockchain or distributed consensus.

## Architectural consequence

The strongest current boundary is now **proof-carrying opacity + revocable acceleration**:

- inner associative representation may be unreadable to humans;
- selection/routing may be learned;
- memory topology may reorganize itself;
- accelerators may be admitted only under measured, version-bound, explicitly scoped validity certificates;
- accelerators remain under ongoing exact-reference shadow falsification;
- certificate failure quarantines the accelerator and restores deterministic fallback;
- any state used to authorize an effect, causal credit, terminal completion or persistent truth must still cross the deterministic canonical receipt/proof boundary.

This lets Frank exploit AI-native memory structures without turning model confidence, similarity, graph activation, learned routing or statistical calibration into truth or authority.

## Promotion status

No U11 mechanism is globally promoted from these local experiments.

- Receipt lattice: **SUPPORTED_LOCAL / TARGET-VPS NEXT**
- PKM field: **SUPPORTED_CONDITIONAL / SHADOW**
- Adaptive router: **HOLD**
- RouteValidityCertificate: **SUPPORTED AS REVOCABLE/SCOPE-BOUND CONTROL, NOT UNIVERSAL GUARANTEE / TARGET-VPS NEXT**
- ShadowRiskSentinel: **CANDIDATE / REAL-TRAFFIC COST-RISK SWEEP NEXT**
- HDC/VSA exact store: **REFUTED / NOT_SELECTED**
- Incremental projections: **SUPPORTED_LOCAL / REAL-QUERY NEXT**
- Merkle checkpoints: **CANDIDATE**
- Physical vector/graph/tensor merger: **HOLD**

F-V01-04 remains OPEN until exact-source target-VPS crash/restart/replay/resource and learned-accelerator drift/quarantine tests pass.
