# ClayGraph G2a — Negative Results

Run: `claygraph-20260808T2212p0700-chatgpt-secondary-r3`

## N-CG5-001 — G1d still lacks live target cognitive evidence

The accepted graph remains G0 and G1d remains a research predecessor. Earlier G1d self-use explicitly reported `g1d_runtime = NOT_IMPLEMENTED`; this run adds an executable staged proxy, not a live FRANK/target-Qwen cognitive benchmark. Do not promote G1d/G2a from architecture convergence alone.

## N-CG5-002 — Always blending activation can harm exact tasks

In the constructed mixed-routing workload, exact queries are already strongly solved by the explicit path. Always blending a sometimes-unrelated background field reduced exact top-1 accuracy from 1.0 in the explicit arm to roughly 0.32 in the local reference experiment. This rejects `activation should always participate` as a default rule in this constructed family.

## N-CG5-003 — Shuffled activation can catastrophically damage associative retrieval

In the same synthetic workload, shuffled-field associative top-1 fell to 0.0 and recall@8 to ~0.008 in the local reference. Truthful activation therefore cannot be evaluated without shuffled/stale/role/temporal controls.

## N-CG5-004 — Scalar utility credit creates a self-confirming attractor

A naive learner applied one downstream success signal to every surfaced item. Under the constructed skewed workload it converged to the frequent topic even with **0 injected poisoning**:
- top-1 accuracy ~0.2867;
- rare-topic accuracy ~0.0169;
- false frequent-topic attractor top-1 ~0.7133.

This is a mechanism negative, not a FRANK rate. It rejects indiscriminate assembly-level reward propagation as the default salience-learning rule.

## N-CG5-005 — The anti-attractor governor uses a synthetic strong verifier

The governed arm uses itemwise credit with a deliberately strong 96% synthetic verifier plus context gating, bounded gain, decay and topic mass caps. Its ~0.99 top-1 result demonstrates that the failure can be controlled **in this constructed oracle-assisted model**. It does not establish that FRANK has such a verifier or that these thresholds generalize.

## N-CG5-006 — Fixed explicit retrieval can beat adaptive salience on easy exact tasks

The anti-attractor workload's fixed baseline is intentionally easy and reaches 1.0 top-1 while the governed adaptive arm is ~0.991. Adaptive memory is therefore not inherently superior. It needs query-class routing and measured net utility.

## N-CG5-007 — First E2B G2a execution was not hermetic

The first remote run failed with `ModuleNotFoundError: numpy`. Local success did not imply the same base dependency surface in E2B. The lab was rewritten to Python stdlib only and rerun. Research experiments intended as portable evidence must not silently depend on undeclared packages.

## N-CG5-008 — Successful remote execution can still yield incomplete evidence receipts

The stdlib v0.2 E2B run exited successfully, but the research bridge truncates string fields to a bounded size, cutting off part of stdout. The experiment was changed to emit compact receipts, and decisive self-use/router tests were split for exact result capture. `process succeeded` is not equivalent to `evidence was fully preserved`.

## N-CG5-009 — Compact reimplementation is not exact replication

A shortened v0.4 receipt implementation reproduced the anti-attractor result but showed small router/self-use differences from the full local reference. Those differences are preserved instead of being called exact replication. Exact self-use and router subsets were subsequently submitted separately.

## N-CG5-010 — No new live database enumeration

The historical 71-database count remains a dated inherited measurement. This run reclassifies architecture roles using UnifiedDB U1/C7 but does not claim the old inventory is the current live FRANK state.

## N-CG5-011 — External graph-memory benchmark gains do not transfer automatically

SYNAPSE, MAGMA, GAM, Temporal Semantic Memory, APEX-MEM, Graphiti and related systems establish relevant mechanism classes and implementation feasibility. Their benchmark gains are not evidence that CASAR-G2a improves FRANK.

## N-CG5-012 — Provenance/authenticity does not equal cognitive utility

A memory item can be authentic, correctly sourced and temporally valid yet still be irrelevant or harmful to a given decision. Conversely, a utility score cannot upgrade a claim to truth. ClayGraph must preserve separate truth/provenance, selection and utility axes.

## N-CG5-013 — No target-Qwen / live-FRANK memory effect yet

No direct target-Qwen factorial has tested field OFF vs truthful vs stale/revoked vs role/temporal-shuffled under matched facts, model, token budget, workspace policy and reader projection. Any cognitive-performance claim remains OPEN.
