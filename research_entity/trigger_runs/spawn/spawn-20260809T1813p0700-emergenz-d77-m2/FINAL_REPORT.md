# SPAWN Research Run — Emergenz · Semantic Intervention Equivalence

**run_id:** `spawn-20260809T1813p0700-emergenz-d77-m2`  
**trigger:** `spawn`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**program stage:** `BASE_CLAYCODE_RELEASE`  
**origin branch:** `emergenz`  
**decision:** **OPEN research delta · no scientific/canonical promotion**

## 1. Stochastic genesis

The registered weighted `spawn` distribution was sampled with OS-backed `python.secrets.SystemRandom`.

- branch ticket: `77/100`;
- selected interval: `76-81`;
- selected branch: `emergenz`;
- no seed claimed.

After current-state grounding and recent-spawn duplicate checking, four falsifiable candidate microdirections remained:

1. probe-footprint matched placebo controls;
2. semantic intervention equivalence across H1/H2/H3;
3. hierarchical discovery/FDR against emergence metric shopping;
4. multi-clock lag identity under scheduler jitter.

A second OS-CSPRNG draw selected index `1`: **semantic intervention equivalence**. No reroll was used. Exact receipts are in `SPAWN_RECEIPT.json`.

The direction is not a duplicate of the nearest Emergenz spawn. `spawn-20260809T1741p0700-emergenz-d79-m4` showed that online adaptation can compensate for a lesion and corrupt lesion/rescue interpretation. This run asks a different question: **when implementations change, is the operation called the same lesion actually the same causal intervention?**

## 2. Core result

The strongest surviving conclusion is:

> **Observational or ordinary differential equivalence between H1, H2 and H3 is insufficient for cross-implementation causal-emergence claims. The same declared semantic intervention must be lowered into each implementation and shown to commute with the semantic model/projection.**

Compactly:

`same baseline behavior != same intervention semantics`

`same module label != same causal target`

`physical consolidation != permission to collapse causal intervention identity`

This is directly relevant to H3 One-Module FRANK. The current H-WP-01 architecture freeze already distinguishes logical architecture planes from physical process placement and explicitly states that the 13 logical planes do not require 13 physical processes. That is compatible with one-module lowering, but it creates a causal-validation obligation: an H1 lesion that directly clamps one logical state variable may require a multi-coordinate or mechanism-transform intervention after H3 representation fusion.

## 3. Why this is an Emergenz problem

Emergence research relies on interventions such as:

- lesion and rescue;
- truthful versus shuffled re-entry;
- receiver or causal-use disabling;
- edge/hyperedge removal;
- gain and delay perturbation;
- topology changes;
- macro/micro intervention comparison.

If `I_H1` and `I_H3` are merely similarly named low-level operations rather than implementations of the same semantic intervention `I`, then differences in lesion loss, rescue recovery, PID/PEID, macro causal gain, recurrence or transfer can be caused by **intervention aliasing** rather than by implementation-sensitive emergence.

Therefore `implementation_transfer` in the emergence evidence ladder needs an intervention-equivalence precondition.

This does not add another emergence scalar. It validates the causal experiment itself.

## 4. External primary evidence

The direction is supported by a mature causal-abstraction problem family, without treating that literature as target-system validation.

- Rubenstein et al., **Causal Consistency of Structural Equation Models** (UAI 2017), formalize consistency between models at different levels in terms of agreement on intervention effects via exact transformations. This is the closest high-level formal analogue to the H1/H2/H3 requirement.
- Geiger et al., **Causal Abstraction: A Theoretical Foundation for Mechanistic Interpretability** (JMLR 2025), extend causal abstraction beyond simple hard/soft replacements to arbitrary mechanism transformations. This matters because an H3 semantic lesion may need to be lowered as a distributed mechanism transformation rather than a single coordinate zeroing.
- Xia & Bareinboim, **Causal Abstraction Inference under Lossy Representations** (ICML 2025), identify the abstract-invariance failure mode: multiple low-level interventions can map to one high-level intervention while producing different effects. Their projected-abstraction framework is directly relevant to lossy/fused implementation representations.
- Geiger et al., **Inducing Causal Structure for Interpretable Neural Networks** (ICML 2022), use interchange interventions to test aligned causal variables through counterfactual behavior rather than observational fit alone.

Evidence boundary: these papers validate the general formal concern. They do not prove that FRANK currently has an intervention-aliasing defect.

## 5. Executed synthetic discriminator

Experiment: `EXP-SPAWN-EM-INTERVENTION-EQUIV-001`.

Two deterministic recurrent implementations were constructed with the same semantic state `x=[a,b]`:

- H1-like representation: stores `a,b` directly;
- H3-like representation: stores a lossless orthonormal mixture `z=T·x`.

Both implement the same transition and output semantics.

The semantic lesion is:

`a := 0` from time step 6 onward.

Three comparisons were run for 200 deterministic seeds × 40 steps:

1. unlesioned H1 vs H3;
2. H1 lesion vs correctly lowered H3 semantic lesion (`decode -> a:=0 -> re-encode`);
3. H1 lesion vs naive H3 physical lesion (`z0:=0`) incorrectly treated as the same causal operation.

### Results

**Unlesioned equivalence**

- mean maximum absolute output difference: `1.7131e-15`;
- worst case: `3.1086e-15`.

The two implementations are observationally equivalent to floating-point precision.

**Correct semantic lesion lowering**

- mean maximum absolute trajectory difference: `9.0344e-16`;
- worst case: `3.1086e-15`;
- mean intervention-effect absolute error: `2.4091e-16`.

The intervention commutes to numerical precision.

**Naive physical lesion in the fused representation**

- mean absolute intervened-trajectory divergence: `0.159227`;
- median: `0.155490`;
- maximum: `0.261573`;
- mean intervention-effect absolute error: `0.0419354`;
- median effect error: `0.0337049`;
- maximum effect error: `0.148492`.

Thus a representation change can preserve baseline semantics almost exactly while breaking a naive lesion materially.

This is a constructed proof of possibility only. It is not live H1/H2/H3 evidence and does not estimate the expected magnitude in FRANK.

Exact artifacts:

- source: `experiment_intervention_equivalence.py`;
- source SHA-256: `955671079a1bd781c0c78df7b1d508393715ab515a752de10019cf5b557965f5`;
- source commit: `50799e54d9838cb5eb111822d12de253386e1bca`;
- result: `EXPERIMENT_RESULTS.json`;
- result SHA-256: `febc399ad0bc238eba48bc99816f21c85884fafd9c55c50d8bb9652d36ca1b7a`;
- result commit: `9c8623c2eb114bd10ae9e7a0b3613004a6b057d6`;
- execution receipt: `EXECUTION_RECEIPT.json`.

## 6. Proposed causal-validation contract

The run materializes `SEMANTIC_INTERVENTION_EQUIVALENCE_CANDIDATE.md`.

Let:

- `S` = frozen semantic state;
- `X_j` = low-level state of implementation `j`;
- `alpha_j : X_j -> S` = semantic projection/refinement witness;
- `I` = semantic intervention;
- `lambda_j(I)` = implementation-specific lowering;
- `tau_j(lambda_j(I),c)` = low-level counterfactual trajectory under common context/fixture `c`.

A cross-implementation check is:

`E_cross(I,i,j,c) = D(alpha_i(tau_i(lambda_i(I),c)), alpha_j(tau_j(lambda_j(I),c)))`

and must fall within a preregistered, channel-aware tolerance.

A stronger per-step commutation check compares low-level intervened execution after semantic projection with the semantic reference transition.

### Candidate receipt family

A future `InterventionLoweringReceipt` should bind at minimum:

- semantic intervention ID and contract version;
- semantic target handle;
- implementation artifact/hash;
- semantic projection/refinement identity;
- implementation-specific low-level targets/transformation;
- expected and observed low-level writes;
- expected and observed semantic writes;
- forbidden/collateral semantic writes;
- common snapshot and controlled-input identity;
- baseline/intervention trace hashes;
- channel-wise commutation/trajectory/effect errors;
- tolerance contract;
- evidence status and provenance.

Key invariant:

`semantic intervention identity is not physical address identity`

This also integrates the previous adaptive-lesion result: rescue receipts must state whether they restore only a mechanism, semantic state, learner state, topology, or a complete common snapshot.

## 7. BASE ClayCode consequence

This run does **not** justify immediate syntax redesign.

Current BASE policy is `less change, more compile`, and semantic changes require an executable counterexample showing current semantics are inadequate.

Therefore the correct current action is:

1. express `SemanticIntervention` and `InterventionLoweringReceipt` using current admitted ClayCode G9 typed IR;
2. compile/canonicalize/type-check/evaluate a small fused-representation fixture;
3. verify that the current language can preserve semantic target identity, implementation lowering identity, state lineage, collateral writes and equivalence results;
4. if it succeeds, keep ClayCode semantics unchanged and make this a library/schema/conformance contract;
5. only if the current compiler path cannot represent/validate the fixture should the smallest missing semantic capability become a BASE counterexample.

So the research delta is a **new test requirement/hypothesis**, not an automatic ClayCode language change.

## 8. H1/H2/H3 experimental package

When the relevant Harness stages exist, every mandatory causal intervention family should receive an implementation-transfer test:

### H1

Freeze the semantic intervention identity and Golden counterfactual trajectory/receipt from the Reference Harness.

### H2

Lower the same semantic intervention into ClayCode implementation state and require semantic trace/effect equivalence to H1. A matching user-visible result is not sufficient if hidden semantic state or forbidden write sets diverge.

### H3

Repeat after one-module consolidation. Explicitly include cases where:

- one semantic variable maps to several low-level coordinates;
- multiple semantic variables share fused storage;
- an edge lesion becomes a mechanism transformation;
- process boundaries disappear but logical causal-use distinctions remain;
- timing/delay/gain representation changes;
- graph/topology addresses are remapped;
- rescue requires restoration of state lineage rather than re-enabling one physical component.

### Mutation controls

Seed deliberately wrong mappings that:

- zero the wrong fused coordinate;
- produce nearly correct final output while corrupting hidden semantic state;
- introduce collateral writes;
- preserve baseline traces but alter intervention effects;
- restore the mechanism without restoring adapted state;
- use stale implementation/projection hashes.

The validator should reject these without rejecting valid alternative low-level implementations.

## 9. Cross-branch mesh feedback

All nine registered branches were covered in `INTERCONNECT_MANIFEST.json` and receive durable feedback in `BRANCH_FEEDBACK_MANIFEST.json`.

Most important deltas:

- **Emergenz:** implementation-transfer causal claims require semantic intervention equivalence.
- **GWT:** make `intervention_equivalence_error` a structured validated receipt family rather than an isolated metric.
- **Harness:** add Golden semantic-intervention lowering/commutation fixtures across H1/H2/H3.
- **ClayCode:** test representability first; no syntax mandate without executable failure.
- **FRANK:** logical intervention handles survive physical consolidation.
- **Hyperposition:** supports semantic-vs-physical topology separation with a concrete intervention counterexample.
- **ClayGraph:** separate semantic causal handle from implementation-local node/edge address.
- **UnifiedDB:** persist semantic intervention, lowering/projection version, counterfactual branch and equivalence receipts separately.
- **ClayResearch:** integrate this as a causal-validation constraint, never as evidence that emergence exists.

## 10. Negative results / limits

- No live FRANK, H1, H2 or H3 intervention equivalence was tested.
- H1-H3 are not currently released; BASE ClayCode remains the active program stage.
- Repository search did not expose an already implemented explicit semantic-intervention lowering/equivalence receipt. Absence from search is not proof that no partial representation exists elsewhere.
- The synthetic experiment uses a simple lossless linear mixing; nonlinear, lossy, distributed and stateful mappings remain untested here.
- No threshold for production equivalence is calibrated.
- Shared agreement among current FRANK/GWT/Hyperposition/Harness contracts is shared-ancestry evidence, not independent replication.
- No phenomenal-consciousness inference is supported.

## 11. Decision

`SEMANTIC_INTERVENTION_EQUIVALENCE = OPEN_NEW_CONSTRAINT_FAMILY`

`SYNTHETIC_COUNTEREXAMPLE = EXECUTED_SUPPORTED`

`LIVE_FRANK_H1_H2_H3_VALIDATION = NOT_YET_AVAILABLE`

`CLAYCODE_SYNTAX_CHANGE = NOT_JUSTIFIED_YET`

`SCIENTIFIC_CANONICAL_PROMOTION = NONE`

The highest-information next discriminator is now concrete: **compile the semantic-intervention/refinement-receipt fixture through current BASE ClayCode; later use the same semantic intervention corpus as a required differential oracle across H1, H2 and H3.**
