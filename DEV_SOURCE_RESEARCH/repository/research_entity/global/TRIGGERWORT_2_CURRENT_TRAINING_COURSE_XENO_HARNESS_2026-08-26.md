# CURRENT `triggerwort 2` COURSE — Xeno/HCU Harness-Aligned Training

**Status: CURRENT TRIGGER-2 COURSE / supersedes conflicting older curriculum wording**  
**Date: 2026-08-26**  
**Product: EntityOS**  
**Cognition/compute: HCU**  
**Training target: the exact Xeno node that will run inside the finished Zero/EntityOS harness**

## 0. Core law

`triggerwort 2` no longer means “make more 0.8B training data”.

It means:

> Continuously make the Qwen3.5-0.8B Xeno training/evaluation program converge on the exact cognition, packet behavior, epistemics and coordination semantics required by the current finished Zero/Xeno/HCU runtime.

The chain must remain closed:

`CURRENT RUNTIME ARCHITECTURE -> EXECUTABLE TESTS -> RESEARCH DELTA -> TRAINING/EVAL CURRICULUM -> MODEL -> RUNTIME TESTS -> RESEARCH DELTA`

If one side changes, Trigger 2 must update the other side before scale or training freeze.

This document preserves historical provenance; it does not silently rewrite old research. Where older Trigger-2 curriculum wording conflicts with the current Xeno/HCU owner target, executable evidence, current supervisor steering or this course, the current sources win and the older artifact becomes `SUPERSEDED`, `STALE`, `BLOCKED` or `NEEDS_REVISION` as appropriate.

## 1. Runtime that the training must instantiate

Zero is the complete closed EntityOS agent loop. It is not a legacy monolithic Agent Zero software module.

A Xeno is one role-flexible Qwen3.5-0.8B-class cognitive node plus deterministic runtime shell.

HCU is the self-organizing variable-N cognitive fabric.

State classes:

- `S0` = canonical durable EntityOS truth/evidence/effect/security state.
- `S1` = live noncanonical shared HCU cognitive workspace.
- `S2` = node-local ephemeral inference/KV/scratch state.

Hard model-originated publication path:

`ORDINARY XENO (S2) -> NODE_RESULT/v1 -> LEASED TEMPORARY COORDINATOR -> DETERMINISTIC LEASE/GENERATION/EPOCH/DIGEST/SCOPE/REPLAY/CAS GATE -> S1`

Ordinary nodes are technically S1 read-only. This is not a prompt preference.

Coordinator is the same Xeno checkpoint in a temporary runtime role. It is never a permanent boss, fixed personality, separate truth source or separate model class. One active coordinator lease per scope is sufficient for V1; several different scopes may have simultaneous coordinators. Recursive scale uses compressed coordinator summaries into higher scopes.

The model may decide **what looks cognitively useful**. Deterministic ZECP11/fabric decides **what may be claimed, leased or authorized**. Training must not duplicate deterministic authority logic as a second semantic planner.

Primary interconnect is:

`S1 snapshot -> local Xeno cognition -> NODE_RESULT -> typed local result channel -> leased coordinator -> compressed S1 delta`

Ordinary peer-to-peer chat is not the primary coordination architecture.

The architecture remains runtime-variable N. The first concrete acceptance target is now **physical GRID10 = 10 independent Xeno node processes/shells on one shared S1 fabric**. Shared read-only model weights/backend are allowed. Physical node count, resident weight-copy count and physical decode concurrency are separate measured quantities.

Claude Code remains ZECP13/14 strong-model/tool/code partner. It is not S0 authority, not a permanent coordinator and cannot write canonical state directly.

Only ZECP17 EffectGate/EffectJournal grants real-effect authority.

The sole addressable model-facing cognitive representation remains Xeno/ClayCode. JSON, SQLite, Python objects, tensors, KV cache and vectors are carriers, not a second semantic brain.

Production model decoding target is greedy/constrained with `do_sample=false`. Sampling remains a diagnostic robustness arm only.

## 2. Training capability map — every family must map to runtime

### A. Autonomous boot / join / work selection
Train the same checkpoint to read current S1, reconstruct minimum sufficient context, detect already claimed/in-flight work and select useful work without a preassigned role.

Hard negatives:
- launch-time role injection;
- inventing work when none exists;
- ignoring epoch/digest;
- repeating claimed work unless redundancy is explicitly requested;
- treating node identity as a permanent cognitive role.

### B. S0 / S1 / S2 discrimination
Train exact separation of canonical durable state, shared cognitive state and local model inference.

Canonical DB fact must outrank a generated simulation/hypothesis without falsely claiming that the hypothesis is necessarily false.

Hard negatives:
- model output becomes S0 fact;
- S1 majority becomes canonical truth;
- direct S2 -> S0 write;
- generated hypothesis overwrites stored evidence.

### C. Ordinary-node read-only + NODE_RESULT
Ordinary cognition must produce compact typed result/proposal packets bound to node, scope, generation, state epoch/digest, evidence, unknowns and causal identity. It never self-grants S1 write intent.

Hard negatives:
- direct S1 mutation;
- self-issued coordinator status;
- stale/future epoch result;
- duplicate/replay;
- scope mismatch;
- unbound evidence.

### D. Dynamic coordinator cognition
When a valid runtime lease is present, train Xeno to integrate evidence/counterevidence, preserve unresolved Hyperposition branches, compress minimum sufficient shared state, request discriminators and produce a candidate S1 delta.

Do **not** teach coordinator = truth or coordinator = permanent identity.

Hard negatives:
- majority vote collapse;
- dropping counterevidence;
- certainty inflation during compression;
- self-election;
- lease absence ignored;
- coordinator write treated as S0 truth/effect authority.

### E. Stale/CAS/rebase/recovery
Train recognition of stale state and correct re-read/rebase behavior. Restart/rejoin must bind to current state and not replay stale results. Failed/revoked coordinator loses authority immediately.

### F. Variable-N role flexibility
The same checkpoint must perform different cognitive functions based on the current packet/state. Process identity must remain independent of node ID, N, resident model-copy count and decode concurrency.

No fixed planner/critic/memory personalities.

### G. Recursive coordinator compression
Train lower-scope integration and higher-scope compressed summaries while preserving retrievable evidence refs, unknowns and branch topology. Higher coordinators must not require every raw worker packet in hot context.

### H. Hyperposition / GRF / GWT
Train explicit unresolved possible-world/branch state with evidence, counterevidence, compatibility/exclusion and discriminator need.

Collapse may not occur because of:
- majority;
- repeated agreement;
- coordinator preference;
- surface fluency.

GWT training/evaluation must cover competition, broadcast, uptake and causal re-entry.

### I. Claude Code bridge
Train compact typed ZECP13 handoff and ZECP14 result reconciliation. Claude assertions, external tool receipts and canonical evidence remain distinct epistemic classes. Closed APIs must never be treated as exposing hidden activations unless actually exposed.

### J. Memory/effect proposal semantics
ZECP15/16 produce typed DB/effect proposals only. Deterministic boundaries decide durable admission and real execution. Model self-confidence never grants capability/effect authority.

### K. Xeno/ClayCode-native cognition
Training target is:

`typed packet -> compact Xeno/ClayCode -> model -> compact Xeno/ClayCode -> typed result`

Do not rebuild semantic cognition in Python or a large English persona/system router. The semantics and dynamic binding belong in the model; deterministic code enforces syntax, routing, storage, leases, hashes and authority.

### L. Fast low-ambiguity path
For learned low-ambiguity states the model should emit the active codebook atom/typed proposal directly under constrained decoding, without requiring a second free-form LLM interpretation stage. Deterministic authority checks still apply.

## 3. Current checkpoint decision surface

There is **no final checkpoint winner yet**.

For engineering continuity only, provisional integration/test default:

`Goekdeniz-Guelmez/Josiefied-Qwen3.5-0.8B-gabliterated-v1`

revision:

`591852bda6e1979f59e4b0f5ee2919697b12e936`

Reason: it matches the owner low-refusal direction and the currently measured Xeno vector-language handoff, but it has a reproducible unknowable-fact/abstention weakness in the current small matched evidence: 4/5 seeds fabricated on that axis.

BASE remains mandatory matched control/fallback reference.

POSTTRAINED is currently disfavored because it failed DB-vs-simulation authority discrimination in the current small matched scope. That is a load-bearing Xeno property, but current sample size is still too small for a final checkpoint-selection claim.

The small pilot also showed epistemic imprecision where `MEASUREMENT_ERROR` collapsed into `HYPOTHESIS`.

Production matching matters: exact instruction/format behavior was materially stronger under greedy decoding than temperature sampling. Primary checkpoint evaluation therefore uses greedy/constrained decode; sampling is diagnostic only.

Final source-checkpoint freeze requires enlarged fresh matched evidence plus exact checkpoint/tokenizer/renderer/input identity.

## 4. Vector-language knowledge that must remain in Trigger-2 research

Measured external handoff provenance currently records the following model-specific target. These values are **research inputs, not new canonical repo credit**, until rebound to exact manifest/model artifacts:

- Qwen3.5-0.8B-class target;
- 24 layers;
- hidden dimension `1024`;
- vocabulary `248320`;
- full-attention layers `[3,7,11,15,19,23]`;
- primary measured vector ABI site L23 block output/full-attention;
- secondary read sites L19 and L21;
- 46 accepted writable symbol atoms;
- candidate atom `or` rejected;
- 64 fixed role vectors, seed `20260825`;
- role vectors are intentionally **nonsemantic carrier slots**;
- whitened HRR declared safe working guarantee `<=16` simultaneous bindings.

Critical design law: symbol atoms are the stable writable alphabet; meaning is not permanently hardwired to an atom or role vector. Semantic meaning is learned through context/episode-local binding.

Therefore:

- never train global `ALLOW -> fixed atom`, `DENY -> fixed atom`, `ABSTAIN -> fixed atom` mappings;
- use full mapping permutations / episode-local codebooks;
- do not name role vectors permanently `goal`, `planner`, `memory`, etc.;
- include family-disjoint unseen mappings/templates/symbol combinations;
- train current-codebook binding and context invariance.

The measured handoff indicates the primary missing capability is **dynamic binding/context invariance and binding to the active/current codebook**, not basic semantic read or symbol write. Trigger 2 should therefore spend data budget on the binding/router problem rather than reteaching already-strong primitive read/write behavior.

Codec precision law: actual ABI `MANIFEST` plus actual NPY dtype/hash/shape is authority. No implicit dtype conversion. Any cast, quantization change, fine-tuning or activation-hook reuse requires versioning/remeasurement.

Post-FT latent/J-Space compatibility must be remeasured before activation-level control is enabled in production.

External handoff package provenance:

`XENO_MODEL_SHELL_CLAUDE_CODE_HANDOFF_V2_2026-08-26.zip`

SHA-256:

`5e585882a7ad7127035d420577e788ad76578171c80b87b168273476ede972dd`

## 5. Dataset/curriculum laws

Every Trigger-2 successor must preserve:

- no fixed node personalities;
- no fixed-N semantics;
- no global class-to-vector-atom mapping;
- episode-local codebooks;
- family-disjoint holdouts;
- lexical counterbalancing;
- shallow surface-only challengers;
- exact tokenizer/renderer/input identity binding;
- provenance and causal lineage;
- unknown/false/measurement-error/hypothesis/observed/canonical separation;
- authority and recovery hard negatives;
- no model consensus as truth;
- no direct-SFT promotion from lexically shortcut-prone wording.

The current known leaky `trigger2_binding_router_factorial_generator_v3.py` remains quarantined. Do not reuse it simply to unblock nuisance/tokenizer ABI work. Build a separately versioned fully crossed or preregistered conditional-independence successor.

The V33 208-row direct-SFT wording remains `NEEDS_REVISION`: it showed shallow lexical shortcut recoverability and does not fully encode the finalized harness behavior.

## 6. Exact course executed on every future `triggerwort 2`

### Step 0 — Re-enter current reality
Before generating anything:
- refresh current `main`/tree;
- load current owner target;
- load newest supervisor delta;
- load newest Trigger-2 ledger;
- load newest GO/Xeno harness source and receipts;
- load newest model/J-Space/GRID results.

### Step 1 — Architecture -> training diff
Compare the current finished-module architecture against the current curriculum.

Any change to state boundaries, packet schema, coordinator/lease behavior, topology/N, Claude bridge, Hyperposition/GWT/J-Space, effect/capability boundary, model/tokenizer/vector ABI or decoding profile requires an explicit versioned training/eval delta **before new row generation**.

### Step 2 — Ledger audit
Classify every affected artifact as:

`CURRENT`, `SUPERSEDED`, `STALE`, `BLOCKED`, or `NEEDS_REVISION`.

Record version, provenance, predecessor, successor, revision reason and target-architecture relationship.

### Step 3 — Runtime failure reinjection
Every real harness/model failure must return to research as:
- finding;
- hypothesis/counterhypothesis if applicable;
- hard-negative/counterfactual family;
- mirrored evaluation case.

Do not automatically copy runtime output into admitted training data.

### Step 4 — Capability traceability
Every training/eval family must point to a concrete Xeno/Zero/HCU runtime capability or a falsifier. Generic chatbot quality gets no priority unless it protects a required module function.

### Step 5 — Research unresolved high-information gaps
Research is driven by the largest remaining uncertainty on the shortest path to the finished Xeno, not row volume. Keep external method evidence, project measurement, hypothesis and deterministic fact distinct.

### Step 6 — Generate candidate data fail-closed
If positive admission gates are closed, work on generators, labelers, nuisance controls, adversarial families, calibration/holdout, candidate/quarantined data and evals only. Do not inflate accepted tokens.

### Step 7 — Evaluate like production
Primary evaluation uses exact model/tokenizer/renderer/input identity and greedy/constrained decoding. Use family-disjoint holdouts, lexical counterbalancing, nuisance controls and variable-N/topology controls. Sampling stays a separate diagnostic arm.

### Step 8 — Freeze only when the chain is current
No checkpoint/corpus/recipe freeze until current ancestry, exact-merge reference semantics, exact input identity, nuisance independence, accepted Forge->Distillery lineage and critical-axis matched evidence are current.

### Step 9 — Training success is not product success
After fine-tuning re-run:
- exact model/tokenizer/runtime identity;
- vector/J-Space ABI compatibility;
- S0/S1/S2 discrimination;
- ordinary NODE_RESULT path;
- coordinator-only S1 publication;
- physical GRID10;
- recursive coordination;
- Hyperposition/GWT;
- Claude bridge;
- restart/recovery;
- EffectGate/authority negatives;
- matched-budget challengers;
- full-precision evaluation first;
- Q4_K_M deployment evaluation only after full-precision pass.

### Step 10 — Reinject again
Every new test/train result must update the research ledger and may revise earlier rows, hypotheses, metrics and architecture-training assumptions before the next Trigger-2 data-generation decision.

## 7. Immediate current priority

1. Execute the pinned repository-bound Xeno fabric bundle on exact `d81327ea54d1401d46742a0231c47a056f90f943`; component credit only.
2. Reverify successor-dynamic ancestry against current V33-or-later state and resolve the final-report JSON-vs-Markdown contradiction.
3. Implement and execute the proof-carrying exact-merge singleton repair; external/pre-update singleton admission remains rejected.
4. Expand BASE / POSTTRAINED / TARGET_MEASURED matched greedy testing on two decisive axes: unknowable-fact abstention/epistemics and DB-vs-simulation authority priority. Use at least 64 fresh held-out cases per critical axis/candidate for the next decision surface.
5. Repair J-Space hidden-state representation instrumentation by capturing post-intervention state in the forward hook (or architecture-valid equivalent), then rerun controls. Behavioral and representation credit remain separate.
6. Keep the known leaky factorial generator quarantined and build a clean nuisance-independent successor.
7. Define a concrete isolated/sandboxed logical-N HCU interface, then run physical GRID10 with ten independent node shells/processes against isolated shared S1. Do not improvise against live production EntityOS.
8. Measure coordinator fan-in, compression ratio, S1 latency/contention, multiple scoped coordinators, failure/replacement, node restart/rejoin, recursive compression, GWT re-entry and Hyperposition preservation.
9. Run matched-budget challengers: single Xeno, independent N, naive voting, fixed/random coordinator, dynamic coordinator, Hyperposition lesion, GWT lesion and compression lesion.
10. Reopen exactly one Forge->Distillery positive pilot only after upstream gates are current and prove one evidence-qualified Forge accept -> one persistent Distillery packet -> `accepted_dataset_tokens > 0` -> idempotent replay `+0/+0`.

## 8. Exact-merge reference-semantics prerequisite

The current proof-carrying exact-merge repair remains required. External/pre-update Hyperposition must have >=2 branches. A derived singleton is legal only if the immediately preceding validated state had >=2 branches and the current `u_state` exact-equivalence transition itself proves those branches recompute to one exact formal semantic signature using an internal/nonserialized transition witness. Caller-provided merge markers or a generic `allow_singleton=true` are not authority.

This prerequisite matters directly to training because the reference labeler cannot serve as a complete oracle while legitimate exact-equivalence collapse and illegal caller singleton admission are not mechanically distinguished.

## 9. Current credit boundary

- accepted dataset tokens: `0`
- positive training rows admitted: `0`
- final checkpoint selection credit: `0`
- J-Space representation-level credit: `0`
- physical GRID10 credit: `0`
- whole HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`
- training credit: `0`

This is deliberate. The optimization target is the finished Xeno module, not early dataset volume.
