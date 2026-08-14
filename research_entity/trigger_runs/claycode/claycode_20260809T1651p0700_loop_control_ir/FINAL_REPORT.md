# ClayCode Trigger Run — Generic Structured Recurrence for FRANK Loop-of-Loops

Run: `claycode_20260809T1651p0700_loop_control_ir`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` — IN_PROGRESS  
Promotion: **NONE**  
Gate advancement: **NONE**

## Executive result

A new FRANK research input landed after the previous ClayCode run: FRANK should be treated as a heterogeneous **loop-of-loops**, not one monolithic loop. This run tested what that actually requires from ClayCode.

The strongest result is deliberately narrower than the architectural analogy:

> FRANK's loop-of-loops currently justifies a **generic structured recurrence/control-flow IR** with explicit loop-carried state, finite budgets, continuation/exit conditions, halt reasons, provenance and effect boundaries. It does **not** yet justify a FRANK-specific ClayCode cognitive primitive or new biological-style organ.

A local executable compiler proxy parsed a small nested recurrence surface, canonicalized it, lowered it to Python structured control flow, and compared execution against a separate AST interpreter. Across **2,000 randomized differential cases there were 0 semantic mismatches**; **4/4 negative cases were rejected**. The generated program also executed successfully in a separate `/usr/bin/python3` process.

The current checked G9 grammar nevertheless has a real completeness gap: it declares `cycle(...)` but does not provide a general checked `while/for/break/return` path, while the current G9 V3 source already contains an `if` form that is not represented by `grammar.ebnf`. This is a compiler/control-flow gap, not evidence for a new cognitive organ.

No E2B evidence is claimed because E2B is not exposed on this ChatGPT tool surface. No production parser, H1 runtime, Qwen-reader, emergence or general-purpose application gate is claimed.

## Canonical / program grounding

Current canonical identity was verified from GitHub:
- entity version: RAE-8.8;
- canonical revision: 2;
- state hash: `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`.

Current program stage is BASE ClayCode release. `CLAYCODE_RELEASE_WORKSPACE.json` still has all 14 work packages OPEN and no application-acceptance item passed. The governing law remains:

`less change, more compile`

Frank v0.1 remains targeted exclusively at the Ubuntu/Linux developer system; Android/mobile/edge are outside the v0.1 gate.

## Internal grounding / Fusion 1

### FRANK

Inputs included the current C9 ClayCode architecture/mapping, the complete architecture-lineage Fusion and the newer `FRANK_LOOP_OF_LOOPS_RECURRENT_REASONING_TRANSFER_20260809.md` note.

The current FRANK architectural invariants remain:
- `presence != admissibility != selection != authority`;
- `effect_intent != effect_permit`;
- semantic organ boundary != process/storage/authority boundary;
- state/replay/effect identities must remain typed and versioned;
- FRANK may self-observe/propose but may not modify its own Harness.

The loop-of-loops note adds an OPEN requirement to observe heterogeneous recurrent processes across timescales and distinguish convergence, productive bounded cycles, stalls and unstable/overthinking trajectories.

### ClayCode CURRENT G9

CURRENT G9 already has:
- typed records and rules;
- explicit `Delta`, provenance and epochs;
- `CapabilityToken` / `EffectIntent` separation;
- ClayGraph deltas and hyperrelations;
- GWT delivery/reconstruction/use/effect/reentry distinctions;
- budget structures;
- one main `cycle(...)`.

But the checked grammar has no general structured loop/control-flow family. This means the current semantic vocabulary is richer than the current executable grammar/toolchain surface.

### ClayGraph

ClayGraph V2 already preserves:
- typed hyperrelations and typed member roles;
- graph/source epochs;
- projection receipts;
- selection receipts;
- receiver delivery/reconstruction/use/effect/outcome/reentry receipts;
- invalidation queues;
- the hard boundary `activation != semantic truth/authority`.

No new graph semantic primitive is required for loop control. Loop/cross-loop relations may be represented as typed relations/hyperrelations only when justified, but recurrence control must not turn activation into truth or authority.

### UnifiedDB

UnifiedDB V9 already contains revisioned work specs, resource/capability observations, scheduler receipts, leases and execution receipts with explicit truth classes. It can persist loop-control observations/receipts without requiring physical store consolidation.

No UnifiedDB physical merge or semantic rewrite is justified by this run.

### GWT / Hyperposition / Emergenz / Harness / Clayresearch

The complete current Fusion plus moving stack were used as compact cross-branch grounding.

- GWT: recurrence count is not workspace ignition, uptake, causal use or re-entry.
- Hyperposition: preserved alternatives and higher-order codependencies must survive loop routing; a controller cannot erase alternatives merely to force convergence.
- Emergenz: recurrence, oscillation, convergence or semantic-hash stability are not emergence evidence.
- Harness: true validation belongs first in frozen H1 reference replays, then H2 differential ClayCode execution.
- Clayresearch: generic runtime/compiler semantics are preferred over FRANK-only syntax unless a real counterexample forces specialization.

## External research

Evidence classes were kept separate.

### Primary papers — recurrent computation

- Kohli et al., **Loop, Think, & Generalize: Implicit Reasoning in Recurrent-Depth Transformers**, arXiv:2604.07822. Recurrent depth can extend inference-time computation/depth extrapolation; excessive recurrence can produce overthinking.
- Blayney et al., **A Mechanistic Analysis of Looped Reasoning Language Models**, arXiv:2604.11791. Studied looped models often approach cyclic fixed points and stabilized attention behavior; recurrent block design/input injection/normalization affect dynamics.
- Prairie et al., **Parcae: Scaling Laws For Stable Looped Language Models**, arXiv:2604.12946 plus SandyResearch implementation. Treats looping as a nonlinear dynamical system and constrains recurrent/injection dynamics to reduce instability.
- Bae et al., **Mixture-of-Recursions**, arXiv:2507.10524. Demonstrates adaptive recursive depth allocation rather than fixed equal recurrence.
- Graves, **Adaptive Computation Time**, arXiv:1603.08983. Provides a generic learned-halting precedent for adaptive recurrent compute.
- Bai et al., **Deep Equilibrium Models**, arXiv:1909.01377. Provides a fixed-point perspective for recurrent/deep computation.

These sources do **not** prove that FRANK is equivalent to a looped Transformer. They support generic mechanisms and measurement/control questions.

### Primary implementation documentation — structured control flow

MLIR's official `scf` dialect represents structured `for` and `while` control flow with explicit continuation conditions and loop-carried values, then lowers to lower-level control-flow/targets. This independently supports keeping loop semantics generic and typed rather than embedding FRANK-specific recurrence meaning into syntax.

## Fusion 2 — hypotheses and counterhypotheses

### H-CC-LOOP-001 — generic structured recurrence is sufficient for current FRANK requirement

Status: `OPEN_SUPPORTED_NOT_PROMOTED`.

Claim: nested FRANK loops can currently be represented with generic structured control flow + typed state/receipts/budgets/effect boundaries, without a FRANK-specific loop primitive.

Support:
- current local executable differential proxy: 0/2,000 mismatches;
- 4/4 negative cases rejected;
- MLIR SCF independent generic control-flow precedent;
- current FRANK/G9 state/provenance/effect semantics already carry the needed non-control meaning.

Falsifier: a real FRANK recurrence requirement in H1 cannot be represented/lowered with generic structured control flow without semantic loss.

### H-CC-LOOP-002 — adaptive recurrence should outperform fixed budgets in selected FRANK loops

Status: `OPEN_UNTESTED_ON_FRANK`.

Counterhypothesis: most FRANK recurrence is better handled by ordinary event-driven scheduling/queueing, and adaptive recurrence adds complexity without useful outcome gain.

Falsifier/test: matched H1 frozen replay comparing fixed budgets versus typed adaptive continue/exit policies while holding evidence input constant.

### H-CC-LOOP-003 — spectral/attractor diagnostics improve FRANK loop regulation

Status: `OPEN_UNRESOLVED`.

Counterhypothesis: spectral/fixed-point diagnostics predict numerical stability in latent recurrent models but do not predict cognitive usefulness in heterogeneous FRANK loops; simpler residual-pressure + outcome-utility + cost features may work as well or better.

Falsifier/test: H1 replay/intervention dataset where these diagnostics fail to improve classification/control over simpler baselines.

### H-CC-LOOP-004 — one global stability controller is appropriate

Status: `NOT_SELECTED`.

Current evidence favors heterogeneous typed loop families and local/shared control composition, but no production test was performed.

## Executable experiment

Experiment: `EXP-CC-G9-STRUCTURED-RECURRENCE-20260809`.

Artifact: `EXECUTABLE_RESEARCH_RECEIPT.json`.

Pipeline:

`small ClayCode recurrence surface -> parser -> canonical IR -> generic Python lowering -> execution`

Independent oracle:

`same parsed AST -> separate interpreter`

Tested semantics:
- nested bounded loops;
- loop-carried numeric state;
- explicit continuation threshold;
- finite recurrence budget;
- explicit last halt reason;
- deterministic lowering;
- malformed/unsupported input rejection.

Observed:
- randomized differential cases: **2,000**;
- semantic mismatches: **0**;
- negative cases rejected: **4/4**;
- base outer iterations: **4**;
- base inner iterations total: **2** across four inner-loop invocations;
- base halt reasons: `CONDITION_FALSE` for outer and final inner state;
- generated subprocess exit: **0**;
- separate-process wall time: ~**0.025 s** (tooling proxy only, not production performance).

An initial attempt to launch the generated program through `/opt/pyvenv/bin/python` timed out on the tool bridge. The failure was preserved and the same generated program was rerun successfully via `/usr/bin/python3`.

## Negative results / constraints

1. `NR-CC-G9-STRUCTURED-CONTROL-GRAMMAR-GAP-20260809` — CURRENT checked `grammar.ebnf` does not provide general structured `while/for/break/return` control flow despite current semantic/runtime needs and an `if` form already appearing in G9 V3 source.
2. `NR-CC-FRANK-SPECIFIC-LOOP-PRIMITIVE-NOT-JUSTIFIED-20260809` — current executable evidence does not justify a FRANK-specific loop organ/primitive; generic control flow suffices for the tested nested recurrence semantics.
3. `NR-CC-E2B-NOT-AVAILABLE-THIS-SURFACE-20260809` — preferred E2B execution could not be used and no E2B evidence is claimed.
4. The first local subprocess bridge path timed out; repaired through `/usr/bin/python3`. This is tooling evidence only, not a ClayCode semantic failure.

## Goodman anti-echo review

Artifact: `FRANK_CLAYCODE_GOODMAN_REVIEW.json`.

Main verdicts:
- bounded/adaptive loop control requirement: **REFINED** into generic structured-control semantics;
- spectral/attractor LoopDynamicsReadout usefulness: **UNRESOLVED** until H1 evidence;
- new FRANK-specific loop organ/primitive: **REFUTED** for this run.

Shared FRANK↔ClayCode ancestry was collapsed. Independent evidence came from the current executable discriminator and primary external papers/MLIR documentation.

The repo-local Goodman validator was not executable from this connector-only tool surface, so official validator PASS is **not** claimed.

## ClayGraph finding

No schema/semantic change is required now.

If future FRANK loop traces create stable cross-loop relations, ClayGraph may represent them as typed relations/hyperrelations with provenance/epochs. But loop coupling/activation is derived relevance and must not become semantic truth, emergence proof or effect authority. Dynamic-binding candidates remain subject to shuffled temporal order, duplicate-provenance, lesion/rescue and OOD controls.

## UnifiedDB finding

No physical consolidation change is required.

Current UnifiedDB can persist loop definitions, controller versions, budgets, execution receipts, loop/cycle identities, work revisions and result truth classes. A future production loop subsystem should add/route typed loop-dynamics receipts through the existing semantic identity/replay plane rather than create a separate authoritative store.

## FRANK finding

The new FRANK loop-of-loops perspective is useful as a whole-system dynamical model, but the language response should remain generic:

`FRANK loop families -> generic typed structured recurrence/control IR -> runtime scheduling/lowering -> explicit receipts`

Do not introduce a monolithic global loop module or FRANK-only control syntax without a real counterexample.

The proposed `LoopDynamicsReadout` is best treated for now as ordinary typed observability data, not a privileged ClayCode semantic class. H1 tests should determine which fields are causally useful.

## Harness finding

No Harness gate advances.

Highest-information Harness experiment:
1. select frozen H1 replay episodes containing workspace selection, prospection, memory activation, adaptive recognition/learning and outcome/reentry loops;
2. instrument loop ID, state epoch, delta, unresolved pressure/error, budget, cost, outcome utility and halt reason;
3. compare fixed vs adaptive recurrence budgets;
4. estimate local dynamics only where meaningful;
5. lesion/rescue candidate controllers;
6. compare truthful re-entry with shuffled/no re-entry;
7. measure task outcome, correction time, latency, compute, false halt, stalls, divergence and recovery;
8. carry the same semantics into H2 ClayCode differential execution.

## GWT / Hyperposition / Emergenz findings

- GWT: `recurrence != broadcast != uptake != causal use != outcome != reentry` remains mandatory.
- Hyperposition: loop regulation must preserve explicit alternatives/codependencies; forced convergence is not automatically correct.
- Emergenz: no causal-emergence or consciousness claim changes. Recurrent dynamics become an additional observability/intervention axis only.

## Knowledge compilation / mesh write-back

New micro-packet:

`research_entity/knowledge_micro_packets/claycode/KMP-CLAYCODE-GENERIC-STRUCTURED-RECURRENCE-20260809.md`

Cross-room delta:

`research_entity/rooms/center_events/20260809T1651p0700_claycode_loop_control_to_mesh.json`

Feedback was routed to FRANK, clayresearch, ClayGraph, UnifiedDB, GWT, Hyperposition, Emergenz and Harness.

## Required artifacts

Written in this run:
- `INTERCONNECT_MANIFEST.json`;
- `TOOL_EXECUTION_MANIFEST.json`;
- `FRANK_CLAYCODE_GOODMAN_REVIEW.json`;
- `EXECUTABLE_RESEARCH_RECEIPT.json`;
- `FINAL_REPORT.md`;
- one ClayCode knowledge micro-packet;
- one cross-room mesh delta.

## Completion boundary

Completed:
- verified canonical boot and current trigger routing;
- current program/release workspace grounding;
- newest FRANK architecture plus newer loop-of-loops input;
- deep ClayGraph and UnifiedDB raw input;
- compact all-branch current assembly;
- independent primary-source research;
- executable parser/canonicalizer/lowering/interpreter differential experiment;
- negative/adversarial tests;
- Goodman anti-echo review;
- durable GitHub research write-back and mesh feedback.

Not completed and not falsely claimed:
- repo-local interconnect-preflight PASS;
- repo-local Goodman-validator PASS;
- E2B execution;
- production G9 parser implementation;
- production structured-control IR freeze;
- H1 FRANK replay/intervention evidence;
- Qwen-4B reader test;
- any application-acceptance item;
- any ClayCode work-package PASS;
- BASE gate PASS;
- canonical scientific promotion.

## Highest-information next step

Implement the smallest production-grade **generic structured-control IR** needed by the general-purpose compiler, not a FRANK-specific loop language:

- typed `if`/branch;
- bounded `while`/`for` or equivalent canonical loop op;
- loop-carried values;
- explicit exit/halt reason;
- break/continue/return/error semantics;
- async/concurrency interaction;
- effectful-body authority revalidation;
- translation validation against an independent interpreter/oracle.

Then use that frozen semantics in H1/H2 replay for the FRANK loop-of-loops hypothesis.
