# ClayCode — Hyperposition TypedIR / Faceted Lowering

Run: `claycode-20260810T2347p0700-chatgpt-secondary-hyperposition-lowering`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program target: Frank v0.1 / `self.root` on accepted Hostinger Ubuntu VPS  
Evidence class: local executable compiler-research slice; not target-VPS acceptance evidence.

## Input delta from Hyperposition

The immediately preceding Hyperposition run supported a faceted design:

- preserve n-ary higher-order relation identity at the semantic plane;
- do not require native n-ary physical storage/execution;
- permit a latent-factor pairwise lowering only with explicit projection-equivalence evidence;
- keep semantic, active and physical topology identities separate;
- use exact reduction/intervention/cost vectors rather than one opaque Hyperposition score;
- keep PID/PEID estimator-specific and optional rather than a universal promotion gate.

## Current ClayCode grounding

The selected BASE semantic freeze remains in force: language semantics are not reopened without an executable counterexample.

The frozen G9 substrate already exposes the ingredients needed for this candidate: `Set`, `Ordered`, `Hyperrelation`, typed graph hyperrelation roles, `GraphDelta.hyperrelations`, `Conflict`, `Unknown`, evidence refs and semantic/projection hashes. Therefore this run tests implementation closure rather than proposing a new language dialect.

Current Frank v0.1 ClayCode component status remains:

- semantic freeze: PASS;
- parser/canonicalizer: PASS;
- TypedIR: OPEN;
- type/effect: OPEN;
- evaluator: OPEN;
- compiler/lowering: OPEN;
- runtime/FFI/stdlib/concurrency/real Frank component: OPEN.

## Executable TypedIR / lowering prototype

`claycode_hyperposition_typed_ir_v1.py` implements an isolated candidate slice:

### `HyperRelationIR`

Semantic identity contains:

- relation id;
- ordered role vector;
- set of admitted tuples.

Evidence/provenance remains outside the semantic hash domain, consistent with the existing ClayCode identity law.

### Backend A — `NATIVE_NARY`

Physical representation stores the admitted tuples directly.

### Backend B — `LATENT_FACTOR_STAR`

A latent factor `H` receives one state per admitted tuple. Pairwise compatibility edges bind each `H` state to each role/value coordinate. The decoder reconstructs the semantic n-ary relation and fails closed on incomplete/misaligned role bindings.

### Identity law

Both backends carry the same semantic relation hash but compute different physical hashes. A backend change is therefore observable without changing semantic identity.

## Results

### XOR fixture

Observed:

- semantic hash: `b61926cc5dd8bd899307069e238447018fc863f4ac98d7b6c889fd8e92509525`;
- native physical hash: `20ecac5d47a52659293efb5786f270b2935dc3bb4315699e89e591eec927613e`;
- latent-star physical hash: `bacd2cbbe70a4bd29e3a36313e036e527a91653de202c3bf973eaf7f67ef3e2a`;
- semantic hash preserved across backends: PASS;
- physical hash differs across backends: PASS;
- latent-star roundtrip: PASS.

### Random differential fuzz

One complete local run executed:

- seed: `0xC1A7`;
- trials: **2000**;
- arity: **3..6**;
- per-variable domain size: **2..4**;
- semantic projection mismatches: **0**;
- semantic hash drift across backends: **0**;
- accidental equal physical hashes across the two backends: **0**;
- malformed latent plans rejected: **2000 / 2000**.

A later repeated timing sweep exceeded the local invocation budget and was interrupted. No data from the interrupted execution is credited.

## ClayCode architecture delta

### WP03 — Typed canonical IR

Implement the semantic/physical separation explicitly:

`HyperRelationIR -> HyperpositionLoweringPlan -> BackendArtifact`

Required typed fields:

- stable semantic relation id/hash;
- ordered role identity;
- admitted alternative/tuple set or equivalent relation payload;
- source/state epoch;
- evidence/provenance refs;
- backend identity;
- physical hash;
- explicit latent-node identities when used;
- lowering verification receipt;
- rollback/recovery ref.

This should extend the existing TypedIR implementation rather than create an independent second IR.

### WP04 — type/effect checker

Fail closed on:

- tuple/role arity mismatch;
- duplicate role identity;
- semantic hash drift during lowering;
- incomplete latent compatibility bindings;
- stale source/state epoch;
- backend/readout attempting to mint epistemic truth;
- backend/readout attempting to mint effect authority.

`HyperpositionReadout`, graph salience, GWT ignition and backend choice remain descriptive/causal evidence, never capability possession.

### WP06 — compiler/lowering

Implement at least two differential lowering targets behind the same semantic identity:

1. `NATIVE_NARY`;
2. `LATENT_FACTOR_STAR`.

`PAIRWISE_ONLY` over the original variables is legal only when a reduction verifier establishes exact equivalence. Backend selection may optimize latency, memory, contention, incremental invalidation and recovery cost only after semantic equivalence is proven.

### WP11 — fuzz/conformance

Promote the prototype fixtures into a production property corpus covering:

- native <-> latent projection equivalence;
- semantic hash stability;
- physical hash discrimination;
- role permutation handling;
- malformed/incomplete factor plans;
- context clamps;
- relation lesion/rescue;
- stale epoch rejection;
- crash/restart replay;
- sparse/dense relations;
- weighted/probabilistic/continuous-boundary counterexamples.

## Current-source integration risk discovered

The accepted production frontend currently defaults to the V18 reward-relations grammar. The current `tools/claycode_base_typed_ir.py` source, however, still declares a default grammar path named `D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark`.

This is **not yet promoted as a bug**. The correct next step is an exact current-source differential execution:

1. compile the current G9/Dialect corpus through the accepted V18 frontend;
2. feed the exact FrontendArtifact into the current TypedIR builder without silent reparse;
3. compare current default behavior against explicit V18 binding;
4. if the default V7 binding diverges/fails, patch only that minimal integration seam and rerun the WP02->WP03 receipt chain on the target VPS.

This directly matches the existing WP02 acceptance receipt's next falsifier: receipt-bound V18 FrontendArtifact -> TypedIR without silent reparse.

## Goodman anti-echo result

The accompanying review concludes:

- n-ary semantic identity: `REFINED` — needed for direct relation/intervention identity in the tested counterexample, but not evidence for mandatory native hyperedge storage;
- native n-ary physical backend mandatory: `REFUTED_FOR_TESTED_FINITE_RELATIONS`;
- PID/PEID as universal irreducibility gate: `REFUTED_AS_UNIVERSAL_GATE`;
- reopen frozen G9 semantics for this Hyperposition design: `REFUTED_NO_CHANGE`.

Project-branch agreement was not treated as independent evidence.

## Cross-branch feedback

### Frank

This gives F-V01-05 a concrete implementation candidate that can later be consumed by the one cognitive loop-core without allowing unresolved alternatives to become truth or effect authority.

### ClayGraph

Keep logical hyperrelation identity stable while exposing backend-specific factor nodes/edges only as derived physical/active projections. Projection receipts must link the two.

### UnifiedDB

Persist the semantic relation and lowering plan as distinct typed records under the same source epoch/transaction lineage. Logical unification does not require one physical representation.

### GWT / Emergence

GWT episode identity and causal-use receipts must survive backend swaps. A backend that changes selection/outcome/re-entry under a supposedly equivalent semantic relation is a falsification signal, not an optimization win.

## Decision

**No ClayCode semantic-freeze amendment.**

The supported next delta is implementation work in WP03/WP04/WP06/WP11. The local executable prototype is sufficiently discriminating to justify a target-VPS production-path falsifier, but not to promote any ClayCode work package or Frank v0.1 component to PASS.

## Next exact falsifier

On fresh current main and the accepted Hostinger Ubuntu VPS:

`accepted V18 FrontendArtifact -> current TypedIR -> HyperRelationIR -> {NATIVE_NARY, LATENT_FACTOR_STAR} -> execute matched fixtures -> compare semantic/causal/replay/resource receipts`

Gate on:

- zero semantic projection mismatch;
- stable semantic hash across backend changes;
- distinct physical hash where representation differs;
- exact role/arity preservation;
- lesion/rescue equivalence;
- GWT selection/use/outcome/re-entry equivalence where the relation participates;
- stale-epoch rejection;
- crash/restart recovery;
- CPU/RAM/latency/storage/contention metadata;
- no truth/effect-authority escalation.
