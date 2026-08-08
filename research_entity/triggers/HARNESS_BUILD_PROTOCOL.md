# HARNESS BUILD / RESEARCH PROTOCOL — FRANK Full-Architecture Simulation Center Branch

**Reserved trigger:** `harness`
**Branch role:** full-mesh implementation, integration, executable falsification and simulation branch
**Primary target:** FRANK Test 1 full-architecture Clay-native simulation harness
**Owner-fixed priority:** finish the harness before paid LoRA training

## 0. Core rule

`harness` is a full member of the FRANK Global Research Entity research center. It is NOT an isolated engineering utility and NOT a report-only research branch.

Every harness worker must know and continuously incorporate the complete current research mesh. The harness is where the current scientific architecture is made executable, tested, falsified, measured and replayed.

Compact law:

`all_current_research -> harness executable model -> experiments/counterexamples -> all_affected_research`

The harness may discover implementation impossibilities, hidden state dependencies, non-compositional semantics, race conditions, information losses, performance cliffs, invalid abstractions or false assumptions. Those are scientific results and must be written back to the affected branches with provenance.

## 1. Mandatory full-mesh join

Before claiming any work, every `harness` instance MUST:

1. join the canonical repository and verify the current canonical state;
2. read the current `RESEARCH_TRIGGER_REGISTRY.json`, `PROJECT_COMMAND_REGISTRY.json` and `INTERCONNECTED_RESEARCH_MESH_PROTOCOL.md`;
3. run/perform the interconnection preflight and materialize a current `INTERCONNECT_MANIFEST.json` for its run/work package;
4. ingest the newest completed AND in-progress material from every registered scientific/research-center branch, including at least:
   - clay
   - frank
   - gwt
   - emergenz
   - claycode
   - hyperposition
   - claygraph
   - unifieddb
   - harness history and live harness workers;
5. read the latest FRANK architecture and all newer compatible branch overlays that post-date it;
6. read all live harness worker claims/receipts before choosing a task;
7. choose a non-duplicated highest-value gap or explicitly become a replication/review worker if duplication is scientifically useful;
8. preserve shared ancestry: agreement between harness and another RAE branch is not independent external replication merely because code now executes it.

No harness worker may freeze itself to an old FRANK snapshot while newer relevant GWT/ClayGraph/ClayCode/etc. results exist without recording an explicit compatibility/rejection decision.

## 2. Research-center reciprocity

Harness is bidirectional.

### Inbound

Every branch can change harness requirements. Examples:

- Clay changes semantic invariants or safe-effect geometry;
- FRANK changes modules/state transitions;
- GWT changes workspace/receiver-causal closure;
- ClayCode changes language/runtime contracts;
- ClayGraph changes memory route/admissibility/Assembly semantics;
- UnifiedDB changes query/result/transaction/replay semantics;
- Hyperposition changes topology/credit/coupling semantics;
- Emergenz changes required measurement/intervention surfaces.

### Outbound

Harness findings MUST be fed back when material. Examples:

- a supposedly sufficient state schema cannot replay a turn;
- a causal receipt cannot be reconstructed deterministically;
- a lowering drops an authority-relevant field;
- an architecture ordering creates race/TOCTOU behavior;
- a GWT metric is confounded in the executable simulation;
- a graph policy harms exact retrieval;
- a UnifiedDB abstraction violates snapshot/recovery semantics;
- ClayCode cannot express or validate a required architecture transition;
- a supposed module boundary cannot be implemented without hidden coupling;
- a performance optimization changes semantics;
- an experiment reveals a counterexample to a branch hypothesis.

Write explicit feedback receipts to every affected branch. `NO_CHANGE` is allowed only after an actual relevance check.

## 3. Shared multiworker harness room

All `harness` instances work in one persistent coordination space under a shared harness root, using append-only worker receipts/claims where possible.

A new worker must:

- read current claims;
- read recent commits after the latest harness manifest;
- claim one work package;
- avoid overwriting sibling evidence;
- cross-read sibling results before declaring integration complete;
- leave machine-readable completion/handoff receipts;
- keep incomplete/failed attempts as negative engineering evidence when informative.

Suggested work-package lanes are dynamic, not fixed worker identities:

- architecture compiler / module graph;
- canonical state store / epochs / replay;
- ClayCode parser/canonicalizer/type/effect/interpreter integration;
- Needle/translator boundary adapter;
- UnifiedDB query/result/transaction simulation;
- ClayGraph memory/route/Assembly simulation;
- GWT competition/broadcast/receiver closure;
- personality/self/body/goal state engine;
- model adapter / ClayReaderFrame / Clay output validation;
- effect/authority/resource/receipt simulation;
- observability / traces / counterfactual replay;
- experiment/ablation runner;
- property/fuzz/mutation/adversarial testing;
- performance/resource instrumentation;
- recovery/checkpoint/crash consistency;
- cross-platform/CI sandbox validation.

Workers may split/merge lanes as evidence demands.

## 4. Owner-fixed Test-1 boundary

The current Test-1 target is defined by:

- `research_entity/experiments/FRANK_TEST1_CLAY_NATIVE_FULL_SIMULATION_CONTRACT.md`
- `research_entity/experiments/FRANK_TEST1_CLAY_NATIVE_COGNITIVE_CURRICULUM.md` when present/current
- newest compatible FRANK/Clay/ClayCode/GWT/ClayGraph/UnifiedDB/Hyperposition/Emergenz artifacts at freeze time
- existing Needle contract, unchanged unless the owner explicitly changes it

Human language remains outside the Clay-native cognitive boundary:

`human language -> translator -> Needle -> Clay-native FRANK path`

The 4B cognitive model receives/produces Clay/ClayCode natively. The repository executes/simulates the architecture around it.

Needle remains the project's sole intentional non-Clay semantic/reflex subsystem and retains its existing responsibility as frozen by the current FRANK architecture/project directives. Harness does not silently redesign Needle.

## 5. "Perfect harness" operational definition

Perfection is not claimed metaphysically. A harness reaches release quality only when all currently known material gates below pass or are explicitly marked external/unavailable with no hidden substitution.

### 5.1 Architecture completeness

- every frozen FRANK module is represented;
- every state contract has a concrete machine representation;
- every transition has executable/simulated semantics;
- explicit BYPASS paths are modeled and receipted;
- newer compatible overlays are integrated rather than merely mentioned;
- no module is replaced by prose instructions in a mega-prompt.

### 5.2 State fidelity

- deterministic canonical state identity;
- explicit epochs/versions for mutable domains;
- exact pre/post turn snapshot hashes;
- provenance/source/basis identity preserved;
- UNKNOWN/CONFLICT/REVOKED and other epistemic states remain explicit;
- state visible to the model is distinguishable from state existing elsewhere in the system;
- model-visible projection cannot silently mutate canonical state.

### 5.3 Replay

Given frozen external inputs, model outputs, seeds and environment receipts, replay must reconstruct the same architecture-relevant state transitions or explicitly identify nondeterministic boundaries.

Required modes:

- full replay;
- replay from checkpoint;
- module-by-module trace replay;
- counterfactual replay with one intervention;
- model-output swap while upstream state is fixed;
- architecture ablation while model output is fixed where meaningful.

### 5.4 ClayCode fidelity

Harness must use the executable frozen ClayCode reference implementation, not ad-hoc JSON pretending to be ClayCode.

Required:

- parse;
- canonicalize;
- validate;
- type/effect check;
- semantic identity/hash;
- execute/reference-evaluate supported core;
- lower across defined boundaries with translation-validation receipts;
- reject/record malformed model output.

### 5.5 Full FRANK turn simulation

A turn is an explicit causal pipeline, including all applicable stages such as:

- external event;
- translation/normalization;
- Needle;
- durable ledger;
- UnifiedDB query/result/selection;
- causal/context admission;
- ClayGraph memory-use admission;
- route/activation/Assembly;
- resource governance;
- CandidateSet;
- workspace competition;
- WorkspaceEpisode;
- GWT broadcast plan/envelope;
- receiver delivery;
- receiver reconstruction;
- uptake;
- local causal use/effect proxy;
- Clay reader projection;
- Clay-native model transform;
- canonical reconciliation;
- proposal/EffectIntent;
- current task/resource/authority checks;
- Needle/tool/effect path as applicable;
- outcome;
- provenance-bound re-entry;
- memory/salience/credit update;
- next eligible state.

No single model call may stand in for the whole architecture.

### 5.6 GWT causal fidelity

Preserve the current distinction:

`global_addressability != delivery != reconstruction != uptake != causal_use != outcome != reentry`

Per-receiver causal vectors/receipts must remain separately measurable. Passive correlation/globality cannot substitute for intervention evidence.

### 5.7 Memory/ClayGraph fidelity

Preserve current task-use distinctions such as:

`retrievable != admissible_for_current_task != allowed_to_influence_consequential_proposal`

Exact/BYPASS routes, quarantine, supplement-only, escalation and empty-admissible-set behavior must be executable and testable.

### 5.8 UnifiedDB fidelity

Semantic unification, logical API/query unification and physical placement remain distinct. The harness must simulate the frozen logical semantics without pretending all stores are physically one database unless the architecture actually chooses that placement.

### 5.9 Personality / self / body / goals

Persistent FRANK personality, E-PQ or successor state, self/world model, goal candidates/commitments, digital body state, reflection/drift state and their causal interactions must be external canonical state that can be projected to the model, changed, replayed and ablated.

The model can understand and generate goal/self-state proposals; the harness owns actual persistent state transitions and receipts.

### 5.10 Needle boundary

Needle remains separately identifiable, versioned and measurable. Human-language translation identity, Needle input/output/certificate state and downstream Clay conversion are traceable. Needle is not merged invisibly into the LoRA model.

### 5.11 Tool/effect/authority boundary

Tool/effect execution is never inferred merely from model text. The harness preserves the frozen FRANK distinction between cognition/proposal, Needle/tool routing, resource identity, intent adequacy, capability/authority, reservation/permit, commit, outcome and re-entry as applicable.

### 5.12 Recovery

- checkpoint/restore;
- interrupted turn recovery;
- duplicate/replay handling;
- idempotency where specified;
- corrupted/missing derived index rebuild;
- stale epoch detection;
- crash between proposal/reservation/effect/outcome/re-entry boundaries;
- rollback semantics where defined.

### 5.13 Observability

Every turn produces a complete trace bundle sufficient for later scientific analysis without relying on hidden chat context.

### 5.14 Ablation/intervention

Every scientifically material module/boundary must be switchable, lesionable or replaceable in a controlled replay where technically meaningful.

### 5.15 Testing

Required test families:

- unit tests;
- integration tests;
- end-to-end turn tests;
- deterministic replay tests;
- property tests;
- mutation tests;
- fuzz tests;
- adversarial tests;
- stale/unknown/conflict tests;
- concurrency/race tests;
- crash/recovery tests;
- long-horizon multi-turn tests;
- performance/resource tests;
- regression suite;
- golden trace suite;
- architecture coverage report.

Sandbox/CI execution is mandatory where tools are available. A test that was merely written but never executed is not a PASS.

## 6. Research execution rule

Harness workers may and should run experiments while building when those experiments answer an implementation/scientific question.

Evidence classes remain explicit:

- local deterministic test;
- remote sandbox test;
- synthetic mechanism experiment;
- target-model experiment;
- live/simulated FRANK experiment;
- external literature/engineering precedent;
- production evidence.

Never promote a synthetic harness success to live-FRANK evidence.

## 7. Continual live integration

Harness work does not freeze the rest of the research center indefinitely.

During active development, workers periodically reread recent repository commits/live-worker receipts. A material new branch delta triggers one of:

- integrate now;
- open compatibility work package;
- defer to next freeze with explicit reason;
- reject as incompatible/superseded with evidence.

A final Test-1 release freeze pins exact artifact/commit hashes so paid model evaluation is reproducible.

## 8. Completion artifacts for each harness work package

Minimum:

- worker claim/role receipt;
- current interconnect manifest or reference to the shared current manifest;
- code changes;
- tests;
- execution receipt/results;
- negative/counterexample notes if any;
- affected-branch feedback receipts;
- cross-read/handoff receipt;
- completion state.

Whole-harness release additionally requires:

- `HARNESS_RELEASE_MANIFEST.json`
- `ARCHITECTURE_COVERAGE.json`
- `STATE_SCHEMA_MANIFEST.json`
- `GOLDEN_TRACE_INDEX.json`
- `REPLAY_VALIDATION.json`
- `ABLATION_CAPABILITY_MATRIX.json`
- `TEST_EXECUTION_MANIFEST.json`
- `OPEN_LIMITATIONS.md`
- exact frozen dependency/artifact hashes.

## 9. Stop condition before LoRA

Paid LoRA training remains blocked until the owner explicitly authorizes it AND the harness/ClayCode pretraining gates are satisfied.

A harness worker must never start a Together training job merely because credentials exist.

## 10. Research-center law

`harness` is the executable convergence organ of the research center.

It consumes all branches, but it does not dominate them epistemically. It returns executable evidence and counterexamples to them. All branches remain distinct views with explicit provenance, and apparent convergence from shared architecture ancestry is never counted as independent replication.
