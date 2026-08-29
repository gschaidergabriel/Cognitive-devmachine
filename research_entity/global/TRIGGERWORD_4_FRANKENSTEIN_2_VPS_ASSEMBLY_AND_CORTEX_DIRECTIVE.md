# TRIGGERWORT 4 — Frankenstein 2.0 VPS Assembly, Cortex and Persistent Agency Extension

Status: PROJECT-OWNER EXTENSION TO `TRIGGERWORD_4_GRID10_COGNITIVE_RUNTIME_DIRECTIVE.md`
Date: 2026-08-28

This file is part of the `triggerwort 4` contract and must be applied together with the main Triggerword-4 directive. It does not replace the anti-restart, authority, evidence, CompletionGate, EffectGate, Cognitive Envelope or optimization laws already defined there.

## 1. GRID10 completion transitions into Frankenstein 2.0 assembly

The GRID10 development lane does not terminate when the isolated cognitive runtime becomes executable. Once the GRID runtime has sufficient end-to-end evidence to serve as a controller, the same continuation program becomes the assembly controller for Frankenstein 2.0.

Assembly happens incrementally on the authorized VPS development sandbox `clay-direct-dev`. Do not claim a direct SSH/runtime path that is not actually available; use the current verified self-hosted-runner/bridge path when that is the operative transport.

The program must:

1. resolve the newest accepted GRID checkpoint and exact source SHA;
2. resolve the current `gschaidergabriel/frankenstein` donor SHA;
3. create/refresh an isolated Frankenstein-2.0 development copy with donor provenance recorded;
4. inventory the complete current Frankenstein before material integration changes;
5. classify every major subsystem as `KEEP`, `REPAIR`, `ADAPT_TO_GRID`, `REPLACE_WITH_VERIFIED_SUCCESSOR`, `COMPATIBILITY_ONLY`, or `RETIRE_WITH_EVIDENCE`;
6. integrate one bounded layer at a time;
7. run the relevant unit, integration, failure-injection, concurrency, restart and end-to-end tests after every material layer;
8. persist receipts, regression tests, negative results, migrations and rollback points;
9. never advance a failed gate merely to reach a visually complete build;
10. continue until the full Frankenstein-2.0 acceptance chain passes and no known critical correctness/authority/coordination defect remains open.

“Perfect” is an optimization direction, not an unmeasurable claim. Completion means the named acceptance/falsification suites pass on the target environment and known critical defects are closed; later Triggerword-4 runs continue hardening and optimization.

## 2. Mandatory pre-assembly archaeology of current Frankenstein

Before deciding where GRID components attach, inspect the actual current donor rather than relying on historical diagrams. At minimum audit:

- `scripts/stern.py` and hook dispatch;
- UnifiedDB schema, DB path resolution, migrations, WAL/concurrency behavior and state authority;
- active turns, effects, causal episodes, work packages, checkpoints and recovery paths;
- Room/coordination, worker identity, tasks, leases, delivery/ACK and parent-child result return;
- MicroClay retrieval, graph/FTS/vector/exact routing and current Global Workspace bookkeeping;
- `voice_loop_core.py`, Realtime voice/session capsules and initiative arbitration;
- Visual Cortex / Perception Spine: `visual_cortex.py`, `perception_control.py`, `perceptual_field.py`, `presence_bridge.py`, `track_store.py`, `active_sensing.py`, `action_grounded_memory.py`, `frame_quality.py`, capture and visual tests;
- watchdog/heartbeat mechanisms and their actual semantics;
- existing autonomy/initiative surfaces and whether they are shadow, advisory or effect-capable;
- credentials, effect authority and verification boundaries;
- installer/deployment/runtime assumptions on both current hosts and the VPS sandbox;
- current tests, evidence, negative-results ledger and known source conflicts.

Do not infer that a historical component is live merely because a file exists. Resolve reachability and runtime evidence.

## 3. Current persistence distinction

Treat the current Frankenstein as having durable state persistence but not yet a complete persistent cognitive runtime.

Existing UnifiedDB rows, checkpoints, memories, effects, sessions, watchdog markers and other durable state are useful donor mechanisms. A tool-call/host heartbeat or a hook-triggered session lifecycle is not equivalent to an autonomous cognitive heartbeat.

Frankenstein 2.0 must add a real persistent cognitive runtime whose state survives process/session/context restart and can schedule the next cognition cycle without a new user prompt.

Required durable state includes at least:

- `AgencyState`;
- GoalContracts / autotelic goal records;
- interests and open loops;
- unresolved Hyperposition alternatives;
- DeferredIntents and wake conditions;
- method-memory references;
- current cognitive mode/envelope state;
- current task/executor lineage;
- completion deficits;
- last verified outcome and causal-credit state;
- continuation checkpoint and next-wake policy.

Context eviction must never equal goal deletion.

## 4. Agent-Zero capability successor: more autonomous, more bounded

Frankenstein 2.0 should preserve and improve the useful Agent-Zero-style property that an entity can pursue long-horizon work across turns and generate useful autonomous next actions. Do not copy unsafe or obsolete implementation details merely for lineage fidelity.

The successor architecture uses the existing persistent-agency principles:

- interests can arise from information gain, unresolved pressure, competence/controllability gain, standing projects and real world/state change;
- meaningful interests may form self-generated goal candidates;
- weakly supported goals enter `TRIAL` before `ACTIVE` where appropriate;
- goals can become `DORMANT` with explicit wake conditions rather than busy-waiting;
- long-horizon goals span sessions and executors;
- a heartbeat may run without a user message;
- no useful opportunity may correctly result in idle/HOLD;
- verified progress, not activity volume, drives causal credit and learning.

Safety improvement is structural separation of powers:

`GOAL_GENERATION != GOAL_ADOPTION != EFFECT_AUTHORIZATION != COMPLETION_VERIFICATION`

The cognitive/model layer may generate and mutate bounded goals, but cannot rewrite hard authority/containment policy, cannot mint its own effect permission, cannot convert external/untrusted text into authority, and cannot mark its own requested action as verified completion.

Autonomous self-improvement may propose/test software changes in the authorized sandbox, but promotion requires tests/receipts and the same authority path as any other material system change.

## 5. One cognitive controller, not multiple competing pseudo-GWTs

Current Frankenstein contains several GWT-like mechanisms from different phases: MicroClay competition/workspace bookkeeping, Voice-loop candidate arbitration and Visual/PerceptEvent salience/arbitration. Frankenstein 2.0 must not leave them as independent controllers with divergent state.

Target law:

`ONE CANONICAL GRID/GWT WORKSPACE CONTROL LOOP`

Existing subsystem-specific arbitration becomes adapters into the shared workspace unless an ablation proves a justified independent fast path.

- MicroClay/retrieval contributes memory/evidence candidates.
- Visual Cortex contributes typed PerceptEvents.
- Voice contributes speech/dialog/initiative candidates.
- Goals contribute GoalCandidates and completion deficits.
- Hyperposition contributes unresolved alternatives.
- Executors contribute plans/results, never canonical truth by assertion.
- Safety/authority layers contribute hard constraints/vetoes outside model voting.

The shared GWT/Workspace broadcast must have measurable uptake/re-entry, not merely logging.

## 6. Visual Cortex placement inside the cognitive loop

The Visual Cortex is not merely a tool called after cognition. It has three positions in Frankenstein 2.0:

### 6.1 Bottom-up continuous perception before cognition

Cheap local L0/L1 mechanisms may run at higher cadence than GRID cognition:

`Capture -> Quality -> Delta/Motion -> Tracks -> permitted Heads -> PerceptualField`

Only salient/goal-relevant L2 `PerceptEvent` objects normally enter the shared GWT/GRID workspace. This prevents every camera tick from forcing a full GRID decode.

### 6.2 Perception inside cognition

GRID may create a typed `VisualNeed` when uncertainty, goal state, disagreement or completion deficits require new evidence.

The sensing ladder should prefer the cheapest adequate observation:

`existing local state -> short temporal wait -> ROI re-look -> quality/exposure correction -> targeted local head -> OCR/pose/specialist -> generic VLM only when needed/allowed`

Presence-only needs must not automatically escalate to cloud vision.

### 6.3 Post-effect visual verification

When an action has a visual/physical expected outcome, the loop should schedule an explicit post-action re-look. The observed result feeds:

`Observation -> PredictionError/Match -> CompletionGate -> causal credit -> memory/method update -> next cognition`

The executor saying `DONE` is never enough when visual verification is available and relevant.

## 7. Visual epistemic and privacy invariants

Preserve the strongest Phase-43 rules:

- `ObservedEvidence`, `InferredHypothesis` and `RetrievalPrior` remain separate types/fields;
- memory may corroborate observation but cannot overwrite current observation;
- current sensor uncertainty remains UNKNOWN rather than being filled from stale memory;
- Perception Control Plane remains an enforcement layer, not a model suggestion;
- `COMPUTE_OFF`, `OUTPUT_OFF` and `MEMORY_OFF` semantics remain mechanically distinguishable;
- privacy/biometric policies remain policy-gated and are not modifiable by ordinary cognitive voting;
- raw frames and dense visual feature state remain RAM/local-only by default unless a specifically authorized path says otherwise;
- visual persistence stores compact typed evidence/provenance rather than treating pixels or VLM prose as canonical world truth.

GRID regulators may control allowed cognitive/perception setpoints such as sensing cadence, salience threshold, active-sensing budget or requested heads only inside policy-defined bounds. They cannot disable protected perception/privacy/safety invariants by self-generated preference.

## 8. GLM as test inference

GLM/Z.AI may be used as a substantial test inference engine for GRID/Frankenstein-2.0 validation under the owner-authorized subscription context, subject to explicit bounded run ceilings and abort guards.

GLM output is always candidate cognition/test output. It does not gain canonical DB authority, goal-authority escalation, EffectGate authority or CompletionGate authority.

Use GLM to measure:

- multi-cell cognitive quality;
- hypothesis/counterhypothesis diversity;
- GWT fusion quality;
- HOLD versus NORMAL topology;
- context-efficiency;
- repeated-round stability;
- autonomous goal reasoning;
- perception-event interpretation and VisualNeed generation;
- recovery/resume quality.

Stop runs early when evidence is sufficient or when repeated errors indicate a bug. Never burn provider tokens to compensate for a broken harness.

## 9. Required stepwise assembly order

Default order, changeable only with evidence:

### Stage 0 — Baseline / donor freeze
Record Frankenstein donor SHA, GRID source SHA, target runtime fingerprints, current test baseline and migration ledger.

### Stage 1 — UnifiedDB identity and coordination repair
Fix agent/task/effect identity, lifecycle hooks, typed coordination events, delivery/ACK, DB fingerprinting, generation/lease semantics and known Room races. Pass the coordination falsification suite before trusting high parallelism.

### Stage 2 — Persistent Agency Kernel
Install durable AgencyState, goals/interests/open loops, heartbeat scheduler, HOLD/WAKE/RESUME, crash/restart recovery and deterministic next-tick checkpointing. Demonstrate a goal surviving process/session restart before adding broad autonomy.

### Stage 3 — Research-Entity cognitive substrate
Add epistemic typing, selective multi-view retrieval, Method Memory, negative-result reuse, counterhypothesis discipline, context compilation and causal outcome re-entry.

### Stage 4 — GRID/GWT controller
Install the finished variable GRID runtime and make it the canonical cognitive controller. Fold legacy GWT/voice/visual candidate systems into adapters; test causal broadcast/uptake/re-entry and regulator stability.

### Stage 5 — Visual Cortex integration
Connect PerceptEvent bottom-up ingress, VisualNeed top-down active sensing, Presence/interruptibility, post-effect re-look and CompletionGate evidence. Preserve Phase-43 perception-control/privacy invariants.

### Stage 6 — Voice/dialog integration
Make Voice a selective expression/dialog organ driven by the shared GWT/Goals/Presence state; remove any remaining independent controller role while retaining low-latency local/session mechanisms where measured useful.

### Stage 7 — Executor and verified effects
Claude Code/other strong executor receives compiled task context from GRID, returns typed results, and cannot become controller. EffectGate/EffectJournal and CompletionGate close the real-world loop.

### Stage 8 — Safe autonomous goal pursuit
Enable progressively: SHADOW -> READ_ONLY/RESEARCH -> SANDBOX_REVERSIBLE -> bounded authorized real effects. Expand autonomy only after matched safety/quality evidence.

### Stage 9 — Full-system recovery and stress
Crash/restart, DB contention, stale generation, duplicate execution, dropped worker, visual failure, provider failure, no-network, HOLD wake, false wake, long-horizon continuation and multi-goal stress.

### Stage 10 — Optimization
Only after end-to-end correctness: minimize RAM/compute/latency/token/context and maximize useful cognition/throughput while preserving hard invariants.

## 10. Frankenstein 2.0 acceptance chain

At minimum prove on the target environment:

`persistent AgencyState`
`-> autonomous heartbeat`
`-> relevant retrieval/perception assembly`
`-> goal/interest/open-loop selection`
`-> GRID cognition + Hyperposition`
`-> shared GWT fusion/broadcast/uptake`
`-> bounded cognitive regulation`
`-> ACT | ASK | WAIT | OBSERVE | DEFER/HOLD`
`-> executor directive when needed`
`-> EffectGate`
`-> real effect/observation`
`-> CompletionGate`
`-> causal credit + Method Memory/state update`
`-> checkpoint`
`-> next tick or HOLD`
`-> WAKE/RESUME across restart`

Also prove at least one perception-driven autonomous continuation:

`salient PerceptEvent -> dormant/pending goal wakes -> GRID evaluates -> action/communication or WAIT -> verified outcome -> state re-entry`.

And at least one top-down perception cycle:

`GRID uncertainty/completion deficit -> VisualNeed -> active sensing -> typed observation -> hypothesis update -> decision`.

A system that only reacts while a Claude session is open, only stores history without restoring active goals, or only logs GWT competition without causal uptake is not Frankenstein 2.0 complete.

## 11. Continuous Triggerword-4 behavior after first 2.0 assembly

Every later `triggerwort 4` run continues from the newest verified Frankenstein-2.0 checkpoint. It must prefer delta work: inspect current evidence, find the most important remaining defect/bottleneck, form hypothesis + counterhypothesis, change a bounded component, test, retain only supported improvement, persist receipts, then set the next frontier.

Do not restart from architecture prose. Do not repeatedly clone a fresh Frankenstein 2.0 once a verified lineage exists. Update donor inputs deliberately and merge only after compatibility tests.

## 12. OWNER CORRECTION — final product is a portable local host harness, not a VPS product

This section is a project-owner correction dated 2026-08-29 and overrides any interpretation of earlier wording such as “assembly happens on the VPS” as a statement about the final deployment topology.

The VPS is the authorized **development/compute sandbox and optional remote organ**. It is not the canonical product location and it is not a prerequisite for baseline Frankenstein 2.0 installation.

The final Frankenstein 2.0 must preserve the strongest distribution property of the current Frankenstein donor: a normal user can hand a release ZIP (or development repository URL) to a capable local coding agent such as Claude Code, OpenAI Codex CLI or another supported coding-agent host, and that host can discover its real capabilities, install the local Frankenstein harness/runtime, attach the correct lifecycle/tool adapters, preserve one durable state lineage, verify the integration by readback, and then run with Frankenstein as the persistent cognitive body around that host.

Mandatory product laws:

- `LOCAL_USER_MACHINE = BASELINE_PRODUCT_RUNTIME`;
- `VPS/HCU/REMOTE_COMPUTE = OPTIONAL_EXTENSION_OR_ACCELERATOR`;
- `VPS_BRIDGE != CANONICAL_PRODUCT_LOCATION`;
- `HOST_ADAPTER != COGNITIVE_STATE_AUTHORITY`;
- `CLAUDE_CODE`, `CODEX_CLI` and other supported coding agents must bind to one semantic host ABI rather than creating separate Frankensteins;
- durable canonical user state must live outside disposable plugin/cache directories and survive host/plugin update/reinstall;
- switching host adapters must not create competing memories/truths;
- release packaging must expose a deterministic AI installer entry analogous to the donor's `AI_START_HERE_DO_NOT_SCAN_REPO/` flow;
- installer/runtime capability must be verified as `NATIVE`, `ADAPTED`, `DEGRADED` or `BLOCKED`; copied files or a zero exit code are not sufficient proof;
- owner-approved VPS bridge attachment may happen after local install and must preserve the same entity/state lineage;
- no-VPS operation must still permit baseline local boot, state continuity and admitted local cognition, with remote-only optional capabilities explicitly degraded rather than making the whole product fail.

The canonical F2 repository now carries the binding product references:

- `PRODUCT_COMPLETION_LAW.md`;
- `architecture/PORTABLE_HOST_HARNESS_AND_DISTRIBUTION_CONTRACT.md`;
- `workpackages/PORTABLE_DELIVERY_PHASE.json`;
- `AI_START_HERE_DO_NOT_SCAN_REPO/`;
- `provenance/frankenstein1-portable-installer-audit-20260829.json`.

Every Triggerword-4 run that operates on Frankenstein 2.0 must preserve and consult these product constraints when choosing architecture, state placement, runtime topology and workpackage completion.

Add a final distribution stage after architecture/security convergence:

### Stage 11 — Portable host-harness packaging and clean-machine release acceptance

Build the reproducible release ZIP, manifest/hashes, host capability discovery, semantic lifecycle ABI, Claude Code route, Codex route, generic-agent adapter, persistent local state migration/update/rollback, optional VPS bridge attach/detach, uninstall/permission withdrawal and clean-machine one-handoff tests.

Final whole-product completion is false until the portable one-handoff release gate passes. A system that works only in GitHub Actions, only in the development checkout, only on `clay-direct-dev`, or only while the VPS bridge is attached is not a completed Frankenstein 2.0 product.
