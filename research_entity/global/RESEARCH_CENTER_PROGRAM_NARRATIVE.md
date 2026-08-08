# FRANK Research Center — Shared Program Narrative

**Status:** PROJECT_OWNER_OPERATING_DIRECTIVE
**Applies to:** every registered research trigger, every research room, fusion/hypofusion and Harness work
**Coordination substrate:** `research_entity/global/REPO_NATIVE_RESEARCH_CENTER_PROTOCOL.md`

## 0. Principle

The existing repo-native research center remains the coordination architecture. This document does **not** replace rooms, trigger loyalty, roles, leases, pulses, cross-room deltas, fusion or evidence governance.

It adds one shared program narrative so all rooms know what the whole research organism is currently trying to build.

Each room remains loyal to its own domain:

- `clay` researches Synthetic Clay / integrated mechanisms;
- `frank` researches the whole FRANK architecture;
- `gwt` researches workspace mathematics and causal closure;
- `emergenz` researches causal emergence measurements;
- `claycode` researches/builds the native language/runtime;
- `hyperposition` researches higher-order coupling/topology;
- `claygraph` researches graph/memory/topology representation;
- `unifieddb` researches persistence/query/transaction unification;
- `harness` builds/executes/falsifies the architecture.

But every room must ask:

> What does my domain need to discover, build, falsify or validate for the **current program stage**?

A room must not abandon its domain merely to work directly on another stage's implementation. It publishes targeted `CROSS_ROOM_DELTA`, `HANDOFF`, `QUESTION`, `CHALLENGE` or evidence for the appropriate room.

## 1. Cross-cutting mandatory knowledge

Across every stage, all rooms must preserve and use:

1. current RAE mesh knowledge;
2. repo-native research-center room state/live deltas;
3. FRANK architecture archaeology from `gschaidergabriel/Project-Frankenstein`;
4. first-principles/emergent-coupling analysis;
5. current ClayCode/ClayGraph/UnifiedDB/GWT/FRANK research;
6. negative results, historical bugs, boot/order/state failures and superseded mechanisms;
7. exact evidence/provenance/ancestry status.

Required cross-cutting protocols:

- `research_entity/global/FRANK_ARCHITECTURE_ARCHAEOLOGY_PROTOCOL.md`
- `research_entity/global/FRANK_FIRST_PRINCIPLES_EMERGENT_COUPLING_LENS.md`
- `research_entity/global/HARNESS_CLAYGRAPH_CONTRACT.md`

The Project-Frankenstein history is not legacy clutter. It is an active invention/experiment lineage that must be mined for mechanisms, successes, failures, equations, coupling patterns, original ideas and reusable constraints.

## 2. Fixed program sequence

The shared program proceeds in this order only:

`H1 Reference Harness`
`-> H2 ClayCode Harness`
`-> H3 One-Module FRANK`
`-> Unified Database`
`-> LoRA Training-Data Build`
`-> WAIT`

Stage advancement requires explicit machine-readable gate evidence. A later stage may be researched conceptually before its turn when that helps the current stage, but its implementation/promotion may not bypass the sequence.

---

# STAGE H1 — Reference Harness

## Goal

Build a **normal host-language Reference Harness** (primarily Python/ordinary deterministic host code) that executes/simulates the complete current FRANK architecture faithfully enough to serve as the reference oracle for all later implementations.

H1 is not a mega-prompt and not a thin mock. The repo must execute the architecture around the model boundary.

Every H1 release includes its own ClayGraph:

`Reference Harness <-> REFERENCE_HARNESS_ARCHITECTURE.claygraph.json`

plus dynamic run graph/graph-delta evidence for Golden Traces and experiments.

## H1 release properties

At minimum:

- exhaustive architecture freeze with current compatible branch overlays;
- architecture archaeology coverage for every frozen module/coupling;
- canonical event/state ledger, epochs, provenance and snapshots;
- deterministic replay and explicit nondeterminism receipts;
- translator/Needle boundary exactly as current FRANK specifies;
- UnifiedDB semantics as currently needed by H1 without prematurely forcing final physical unification;
- ClayGraph memory/admissibility/Assembly semantics;
- GWT competition/workspace/broadcast/receiver causal chain;
- personality/self/world/digital-body/goals;
- effect/authority/resource/outcome/re-entry boundaries;
- recovery/checkpoint/idempotency/crash behavior;
- ablations/interventions and coupling-edge lesions;
- unit/integration/property/fuzz/mutation/concurrency/adversarial/long-horizon tests;
- static and dynamic Harness ClayGraph validation;
- complete Golden Trace corpus.

## Domain duties during H1

- `harness`: build and execute Reference Harness.
- `frank`: resolve architecture ambiguities exposed by implementation; publish exact state/transition contracts.
- `claycode`: finish the language/runtime in parallel because H2 depends on it; use H1 counterexamples as semantic requirements.
- `gwt`: provide exact computable workspace equations, receiver semantics, ablations and causal metrics H1 can execute.
- `claygraph`: define/validate H1 static + dynamic topology, memory/admissibility/Assembly graph semantics.
- `unifieddb`: support H1 logical state/query/replay requirements but do not jump to final UnifiedDB consolidation stage.
- `hyperposition`: identify higher-order coupling/state/topology relations that H1 must expose/intervene on.
- `emergenz`: define measurement/intervention surfaces; do not promote emergence claims from mere Harness complexity.
- `clay`: integrate cross-domain constraints, especially emergent coupling and Safe-Effect research.

H1 completion artifact: `REFERENCE_HARNESS_RELEASE_MANIFEST.json` with `PASS`.

---

# STAGE H2 — ClayCode Harness

## Prerequisite

`CLAYCODE_RELEASE_GATE = PASS` and `REFERENCE_HARNESS_RELEASE_GATE = PASS`.

## Goal

Rebuild the **same frozen H1 FRANK architecture in ClayCode**.

H2 is an independent implementation of the same semantic machine, not a simplified clone.

Every H2 release includes its own ClayGraph:

`ClayCode Harness <-> CLAY_HARNESS_ARCHITECTURE.claygraph.json`

## Primary scientific/engineering test

Use H1 as a differential oracle:

- same initial state;
- same inputs;
- same deterministic model fixtures;
- same seeds/receipts;
- same interventions;
- same Golden Traces;
- compare every architecture-relevant state transition, epoch, receipt and dynamic ClayGraph.

Unexplained semantic/topological divergence reopens the responsible stage. If ClayCode cannot express required FRANK semantics, ClayCode is not finished.

## Domain duties during H2

- `claycode`: own executable Clay implementation and repair semantic gaps.
- `harness`: differential runner, Golden Trace execution and failure localization.
- `claygraph`: compare Reference-vs-Clay static/dynamic graph equivalence.
- `frank`: arbitrate intended architecture semantics when the two implementations expose ambiguity.
- `gwt`: verify identical workspace math/receiver closure under both implementations.
- `unifieddb`: verify query/state/replay semantics are representation-independent.
- `hyperposition`: compare coupling topology/timing across implementations.
- `emergenz`: use differential implementations to test whether observed system-level effects survive implementation changes.
- `clay`: synthesize language/architecture/coupling deltas without allowing shared ancestry to masquerade as replication.

H2 completion artifacts include `CLAY_HARNESS_RELEASE_MANIFEST.json` and `HARNESS_CLAYGRAPH_DIFFERENTIAL_VALIDATION.json`, both PASS.

---

# STAGE H3 — One-Module FRANK

## Prerequisite

H1 and H2 PASS with unexplained differential divergence = 0 for required semantics.

## Goal

Build a **radically consolidated one-module FRANK implementation** while preserving the same proven architecture semantics, state transitions, emergent couplings, safety/authority boundaries, GWT mathematics, memory behavior and observability.

"One module" means architectural/runtime consolidation, not deleting the functional distinctions that produce FRANK behavior.

The H1/H2 pair is the semantic oracle. H3 must demonstrate that a much more unified implementation realizes the same required organism-level behavior with lower coupling overhead/latency/complexity where possible.

H3 gets its own static/dynamic ClayGraph:

`One-Module Harness <-> ONE_MODULE_HARNESS_ARCHITECTURE.claygraph.json`

## Core H3 question

> Which current module boundaries are implementation accidents, and which are causally necessary functional boundaries?

H3 uses differential tests, edge lesions, timing perturbations and state equivalence to answer that rather than assuming "fewer modules = better".

## Domain duties during H3

- `harness`: build one-module implementation and differential oracle against H1/H2.
- `frank`: distinguish conceptual/causal modules from deploy-time process/module boundaries.
- `claycode`: express the consolidated system cleanly without opaque host escape hatches.
- `claygraph`: preserve functional substructure/coupling even when deploy-time module count becomes one.
- `gwt`: ensure consolidation does not collapse receiver/candidate/workspace distinctions needed for causal tests.
- `hyperposition`: optimize shared/incremental state and coupling topology while measuring semantics/latency.
- `unifieddb`: observe H3 access/state patterns to inform the *next* database stage; no premature irreversible merge.
- `emergenz`: test whether behavior depends on genuine coupling structure rather than service/process boundaries.
- `clay`: integrate performance, safety, dynamics and architecture trade-offs.

H3 completion artifact: `ONE_MODULE_HARNESS_RELEASE_MANIFEST.json` with PASS.

---

# STAGE UDB — Unified Database

## Prerequisite

H3 PASS.

## Goal

Only after the three Harness stages have exposed the real state/query/access/replay topology, build the final **UnifiedDB architecture** from measured needs rather than from abstract database aesthetics.

The target remains logical/semantic unification first. Physical consolidation is evidence-driven and may retain specialized sidecars/stores where benchmarks, authority isolation, crash domains or query semantics justify them.

## Required comparisons

- current specialized baseline;
- logically unified semantic/query interface;
- canonical-store + derived sidecars;
- selective physical consolidation;
- one-store designs where technically plausible.

Measure correctness, snapshot/replay consistency, query equivalence, selection integrity, latency, amplification, concurrency, crash recovery, migration rollback and authority-domain separation.

All Harnesses become validation clients of UDB and must rerun relevant Golden Traces after migration candidates.

UDB completion requires its normal UnifiedDB release/decision artifacts plus explicit Harness compatibility evidence.

---

# STAGE DATA — LoRA Training-Data Build

## Prerequisite

H1, H2, H3 and final UDB stage gates PASS; ClayCode release remains PASS.

## Goal

Build and freeze **training data only** for the first Clay-native FRANK LoRA.

Do NOT start training in this stage.

The corpus must teach the target 4B:

- native ClayCode reading/reasoning/speaking;
- FRANK personality/self-model semantics;
- goal development/revision semantics;
- digital-body/data-structure embodiment;
- GWT mathematics, competition, ignition/broadcast/receiver causal distinctions;
- FRANK state/coupling concepts it must understand;
- general-purpose Clay reasoning/program transformation;
- UNKNOWN/conflict/provenance/effect-intent semantics;
- clear separation between cognitive understanding and external runtime authority.

The external Harness architecture must not be collapsed into memorized prompt imitation.

## Dataset rules

- derive examples from frozen executable semantics/Harness traces where possible;
- separate training vs held-out generators/corpora by construction;
- include positive, negative, repair, counterfactual and adversarial examples;
- include historical Project-Frankenstein lessons where they define personality/cognitive concepts, but do not train obsolete bugs as desired behavior;
- preserve provenance and generator version/hash;
- build target-model-independent eval suites before training;
- freeze exact corpus and manifests.

Completion artifact: a training-data release manifest with hashes and a separately frozen held-out evaluation manifest.

---

# STAGE WAIT — Deliberate stop

After the LoRA training-data stage is complete:

**STOP. WAIT FOR THE PROJECT OWNER.**

No worker may automatically:

- launch Together fine-tuning;
- spend training/inference budget;
- deploy a trained adapter;
- advance to a new major architecture stage.

Further training starts only after a new explicit project-owner instruction after the data build is complete.

This WAIT rule supersedes any earlier conditional wording that could be interpreted as automatic LoRA start after prior gates.

## 3. Stage-sensitive room behavior

At JOIN and every mandatory PULSE, workers should read:

- `research_entity/global/RESEARCH_CENTER_PROGRAM_NARRATIVE.md`
- `research_entity/rooms/PROGRAM_STATE.json`

A material current-stage delta should carry the stage ID in its event payload/dependencies where practical.

Cross-room relevance is strongly boosted when a result can:

- block the current stage;
- change a current-stage architecture choice;
- close a current-stage test/release gate;
- reveal a historical failure likely to recur;
- provide an executable counterexample;
- improve the next-stage prerequisite without abandoning trigger loyalty.

## 4. Stage advancement

No persistent global chief decides truth. Stage advancement is a **gate state**, not a personality role.

A stage can advance when its required machine-readable release evidence is PASS and no current `INTERRUPT_NEXT_SAFE_POINT` blocker invalidates that evidence.

`fusion`/`hypofusion` may audit stage readiness across all rooms. They do not manufacture PASS by consensus.

## 5. Shared success criterion

The research center succeeds when many independent sessions can work simultaneously in their specialist rooms while all contributions converge on the same staged build program, without the user manually dispatching them and without erasing disagreement, provenance or invention history.
