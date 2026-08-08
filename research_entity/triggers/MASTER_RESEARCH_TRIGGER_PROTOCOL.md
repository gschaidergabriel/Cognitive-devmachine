# RAE-vNext Master Research Trigger Protocol

## Purpose

This protocol governs every reserved research trigger in `RESEARCH_TRIGGER_REGISTRY.json`. A trigger is a research command, not a conversational topic hint.

## Exact trigger semantics

A trigger fires only when the entire trimmed user message equals one registered trigger word, case-insensitively. Ordinary prose containing a trigger word does not fire the protocol.

## Existing research center is authoritative

All trigger work uses:

- `research_entity/global/REPO_NATIVE_RESEARCH_CENTER_PROTOCOL.md`
- `research_entity/rooms/ROOM_REGISTRY.json`
- `research_entity/global/RESEARCH_CENTER_PROGRAM_NARRATIVE.md`
- `research_entity/rooms/PROGRAM_STATE.json`
- `tools/research_room.py`

Scientific rooms remain domain-loyal. They do not abandon their domain merely because another domain is currently the main implementation stage.

Every worker asks two questions simultaneously:

1. What is the highest-value unresolved question inside my trigger domain?
2. Which domain-specific result can most strongly advance, falsify or de-risk the current shared program and Clay 0.1 trajectory?

The current program order is data-driven by `PROGRAM_STATE.json`; never hardcode an old stage sequence into trigger logic.

`666` is the sole autonomous research meta-trigger. Before Level-0 PASS it resumes exhaustive archive assimilation. After Level-0 PASS it spawns one seeded, high-value, non-duplicate emergent research field, performs work immediately and feeds material deltas back into the shared mesh.

`q12` is the creator-advisor meta-trigger using `Q12_CREATOR_MODEL_PROFILE.json`; it advises from the recorded Creator-Scientist worldview and may coordinate the center only when delegated by the owner. It is not a scientific peer branch and does not create evidence by authority.

Any historical `go` reference is superseded by `research_entity/global/GO_TO_666_MIGRATION.md` and must not be treated as a current command.

## Mandatory cross-cutting knowledge

Every substantive scientific run must use relevant current material from:

- all registered peer branches;
- live room deltas / worker claims that can change the decision;
- `gschaidergabriel/Project-Frankenstein` architecture archaeology;
- `research_entity/global/FRANK_ARCHITECTURE_ARCHAEOLOGY_PROTOCOL.md`;
- `research_entity/global/FRANK_FIRST_PRINCIPLES_EMERGENT_COUPLING_LENS.md`;
- current negative results and supersession history;
- current program stage/gates;
- `research_entity/global/DOOMSDAY_DYNAMIC_FORECAST_PROTOCOL.md` where work may change Clay 0.1 critical-path assumptions.

GWT additionally uses `research_entity/global/GWT_EMERGENCE_READOUT_CONTRACT.md`.

Hyperposition additionally uses `research_entity/global/HYPERPOSITION_EMERGENCE_READOUT_CONTRACT.md`.

Harness/ClayGraph work additionally uses `research_entity/global/HARNESS_CLAYGRAPH_CONTRACT.md`.

## Mandatory boot

1. Verify remote canonical revision/hash and actor identity.
2. Load `PROGRAM_STATE.json`, the shared program narrative and the worker's home-room/current-room state.
3. Read current same-room workers, roles, leases, tasks, recent deltas and relevant cross-room mail.
4. Compile task-specific RAE context; do not blindly inject the whole repository.
5. Load `INTERCONNECTED_RESEARCH_MESH_PROTOCOL.md` and `DOMAIN_ACTIVE_KNOWLEDGE_POLICY.md`.
6. Ingest every branch registered as `domain_research` or `integrated_research_foundry`. At the current registry revision the peer set is `clay`, `frank`, `gwt`, `emergenz`, `claycode`, `hyperposition`, `claygraph`, `unifieddb`, `harness`. Membership always comes from the registry, not this sentence.
7. Run/materialize `tools/research_interconnect_preflight.py` and `INTERCONNECT_MANIFEST.json` where the execution surface permits it.
8. Read relevant Project-Frankenstein mechanism/failure lineage before changing a historically inherited subsystem.
9. Load the trigger-specific protocol and mandatory measurement/graph contracts.
10. Load `RESEARCH_TOOL_ORCHESTRATION_POLICY.md`, `EXTERNAL_RESEARCH_TOOL_REGISTRY.json` and `tools/research_provider_router.py`.
11. If a new API/tool/capability can plausibly alter a Clay 0.1 critical-path row, ensure it is visible to `DOOMSDAY_CAPABILITY_RULES.json`; runtime availability alone does not create an ETA multiplier.
12. Record run manifest with actor/model/runtime/program-stage provenance.

If canonical cannot be verified: `DEGRADED_UNJOINED`. Research may proceed LOCAL_ONLY but no shared-state promotion may be claimed.

A scientific run missing a registered peer branch, current program-state grounding, required cross-trigger preflight, or a material historical failure dependency is incomplete for strong promotion.

## Room pulse boundaries

Use the repo-native room pulse before:

- hypothesis or architecture freeze;
- substantial experiment/implementation branch;
- durable research write;
- synthesis/fusion;
- final visible response.

Also pulse after a result likely to invalidate another worker's assumptions.

Trigger loyalty remains pinned even when cross-room information changes the worker's knowledge.

## Active domain knowledge rule

Domains are persistent research programmes. Topic Packets and Knowledge Micro-Packets are the default active working-memory layer.

Use compact packet summaries/metadata first; expand raw evidence only where it can change a hypothesis, contradiction, experiment or architecture decision.

Activation/relevance never upgrades truth/evidence status. Shared ancestry remains one evidential family even if several branches or Harness implementations repeat it.

## Mandatory provider gate

Before external research classify hypothesis clusters into applicable classes:

- scholarly;
- bibliographic;
- current_web;
- implementation;
- executable;
- model_experiment.

Run `tools/research_provider_router.py plan` and materialize `TOOL_EXECUTION_MANIFEST.json` where applicable. Attempt every operational `MUST_ATTEMPT` capability or record an allowed fallback.

Provider snippets are discovery evidence. Prefer primary/authoritative sources for verification.

A newly registered API/provider is not merely a tool-list change: when relevant, it becomes an input to the dynamic DOOMSDAY capability table. Only verified benchmarked effects may alter the forecast.

## Research cycle

### A — Evidence + mesh + program grounding

- consume current program state and live-room deltas;
- consume interconnect manifest;
- re-ground high-impact claims against raw sources;
- preserve contradictions, negative results and source ancestry;
- identify current-stage implications;
- identify relevant Project-Frankenstein lineage/failures;
- identify any verified accelerator/blocker/new dependency that should enter the DOOMSDAY forecast ledger.

### B — Fusion 1

Create a compact synthesis before external confirmation where possible. Separate measured data, imported claims, owner observations, model inference and external evidence.

### C — Hypothesis generation 1

Generate falsifiable hypotheses and counterhypotheses. Each contains:

- mechanism;
- expected observation;
- strongest alternative mechanism/counterprediction;
- falsifier;
- cheapest/highest-information test;
- affected branches;
- current-stage implication;
- source/evidence ancestry.

### D — Hypothesis-guided external research

Search by hypothesis cluster, not one query per sentence. Preserve query/source provenance and provider fallback state.

### E — Fusion 2 + contradiction/anti-echo gate

Search for:

- convergent mechanisms;
- contradictions;
- stale conclusions;
- representation-vs-mechanism confusion;
- shared-ancestry false replication;
- Goodhart failure modes;
- hidden boundary cost;
- historical bug recurrence;
- current-stage blockers;
- simpler alternative explanations.

Contradictions are retained, never averaged away.

### F — Hypothesis generation 2

Transform, split, weaken, retire or promote hypotheses according to evidence.

### G — Empirical work

Execute highest-information feasible tests: parser/compiler tests, simulations, benchmarks, ablations, lesions/rescues, counterfactual replay, graph reductions, query equivalence, crash/recovery, fuzzing, measurement instrumentation or target-model experiments.

Synthetic/remote results remain synthetic until replicated on the target substrate.

When an experiment is intended to shorten or lengthen a DOOMSDAY forecast row, measure the actual effect and attach a receipt. Do not hand-wave a speedup factor.

### H — Synthesis + architecture/program delta

Record:

- what changed;
- what survived;
- what failed;
- strongest counterargument;
- current-stage gate impact;
- architecture/runtime implications;
- next discriminating experiment;
- affected rooms/branches;
- any verified DOOMSDAY critical-path impact.

### I — Knowledge compilation / center write-back

Write durable, surgical Topic Packets / Knowledge Micro-Packets / failure receipts / experiment receipts and cross-room deltas.

Results must preserve source ancestry and evidence class. Historical failure knowledge is active design knowledge.

### J — Final report

Write run artifacts required by the trigger-specific protocol plus:

- final report;
- run manifest/status;
- interconnect manifest;
- tool execution manifest where applicable;
- current-stage implications;
- cross-branch/room inputs and outputs.

The final visible response ends with the mandatory two-horizon status footer generated by `tools/program_progress.py`.

## Staged-program boundary

Current implementation/release work follows the data-driven program state. Later-stage research may inform the current stage, but workers may not silently skip release gates.

The execution program reaches the final training-data stage and then WAIT. No trigger, `666`, `q12`, Fusion or stage completion automatically authorizes final/paid model training.

DOOMSDAY forecasting continues beyond WAIT only as a conditional forecast. Clay 0.1 is not achieved until the final fully fine-tuned model is integrated with the Clay-programmed one-module/binary FRANK and UnifiedDB and passes the project-hardware acceptance run.

## Promotion discipline

Trigger/room/Q12/CHEF rank never grants truth authority. High-impact claims require independent support, falsification and, where feasible, replication.

GWT/Hyperposition/emergence complexity does not by itself establish phenomenal consciousness.

Project novelty/world-first claims require dedicated prior-art evidence and explicit search limits.

## Dynamic visible status

Do not report percentage completion of the immediate prompt.

Every substantive answer displays:

1. **NEXT LEVEL** — the first unpassed shared program gate with strict machine-derived progress and ETA;
2. **DOOMSDAY / Clay 0.1** — an effort-weighted dynamic critical-path progress bar plus a freshly recomputed forecast range/center/confidence.

DOOMSDAY must be recalculated from current progress, throughput, capacity, APIs/capabilities, verified accelerators/blockers/new dependencies and training-authorization state. A stale date copied from an older response is a governance bug.
