# Agent Zero cognitive process census v1

Status: **GO frontier artifact / ABI precursor**  
Date: 2026-08-25  
Owner target: `research_entity/global/OWNER_CORRECTION_UNBOUNDED_AGENT_ZERO_COGNITIVE_GRID_2026-08-25.md`  
Owner target commit: `72bc01e5562391528cd3a91c2851f77ad33ebf00`  
Census base main: `310289774c72bba3a8439a312a1f4d748e99bab8`  
Product: EntityOS  
Compute/cognition architecture: HCU / dynamically sized Xeno grid

## 0. Purpose

The current owner target makes `AGENT_ZERO_PROCESS_CENSUS` the first unresolved gate on the shortest `go` path toward a size-independent distributed Agent-Zero-equivalent cognitive machine.

This document is the first stable functional census for that gate. It identifies cognitive/runtime **process families**, not historical module boundaries and not fixed agent personalities. The next artifact is `COGNITIVE_PROCESS_ABI/v1`, which may split or fuse these families only if the resulting machine preserves the declared observables, authority boundaries and functional behavior.

`GRID10` has no architectural authority here. Every process family is specified without assuming a fixed node count.

## 1. Evidence law

Classification used below:

- `R0_PROJECT`: directly observed in the current project AgentZero export/code at the cited path.
- `R0_UPSTREAM`: directly observed in the pinned upstream Agent Zero source used only as donor/reference evidence.
- `OWNER_REQUIRED`: explicitly required by the current owner correction but not yet fully observed as one integrated runtime process in the current target architecture.
- `R1_INFERRED`: functional decomposition inferred from multiple observed surfaces; not promoted to runtime fact.

A process may have several classifications. `OWNER_REQUIRED` does not turn a missing implementation into an observed fact.

Pinned evidence:

- Clay owner authority: `gschaidergabriel/clay-global-research-entity@72bc01e5562391528cd3a91c2851f77ad33ebf00`.
- Current project base for this census: `gschaidergabriel/clay-global-research-entity@310289774c72bba3a8439a312a1f4d748e99bab8`.
- Project AgentZero export manifest: `agentZero/MANIFEST.json` (blob observed as `72e3e2c8c92e9d153a0d5f0e4121b6485ebc2dbb`).
- Upstream Agent Zero donor/reference: `agent0ai/agent-zero@b22a144bf59f15b1516084c9e7b88133ba92c8a9`, especially `agent.py`.

The project export itself contains persistent evidence surfaces for turns, causal episodes, workspace episodes, effects, checkpoints, retrieval, durable memory, graph, pulse/events, product code and a 140-table UnifiedDB schema. Those surfaces justify a functional census, but not full distributed-runtime acceptance.

## 2. State and authority classes

- `S0`: canonical durable truth/effect/security authority. Model/cognitive output cannot mint it.
- `S1`: live shared cognitive/workspace/process state. It may coordinate cognition but cannot override S0.
- `S2`: ephemeral/request-local model proposals, alternatives, packets and transient context.

Distribution classes:

- `LOCAL`: naturally executes inside one process/node for one work unit.
- `SHARDABLE`: multiple independent instances can operate on partitioned work.
- `COORDINATOR_SCOPED`: write/fusion requires deterministic scoped coordination.
- `GLOBAL_BOUNDARY`: semantic authority must remain singular/deterministic even if implementation is replicated.

## 3. Census

| ID | Process family | Evidence state | Primary inputs | Primary outputs | State | Distribution | Real-effect authority | Key observed / required evidence |
|---|---|---|---|---|---|---|---|---|
| AZP-01 | INPUT_ADMISSION_AND_CONTEXT_BINDING | R0_PROJECT + R0_UPSTREAM | user/system/autonomy message, session/user identity, resources | admitted turn/context identity, bounded prompt context | S0/S1 boundary | SHARDABLE + GLOBAL_BOUNDARY validation | NONE | `agentZero/code/produkt/turn_lifecycle.py`; upstream `AgentContext.communicate/_process_chain` in `agent.py` |
| AZP-02 | STATE_RECONSTRUCTION_AND_WORLD_ASSEMBLY | R0_PROJECT | canonical session/generation, recent turns, memory, resources | reconstructed bounded world/context | S1/S2 | SHARDABLE | NONE | `turn_lifecycle.py`, `zustand.py`, retrieval/world assembly imports |
| AZP-03 | MEMORY_RETRIEVAL_AND_CONTEXT_PACKING | R0_PROJECT | query/context cues, durable memory, policy state | ranked bounded memories + retrieval receipt | S1/S2 | SHARDABLE | NONE | `microclay_retrieval.py`; retrieval episodes/policy/feedback in manifest |
| AZP-04 | GOAL_INTENT_STATE_MACHINE_AND_PLANNING | R0_PROJECT | live goal state, evidence, previous step/result | typed reason/effect/completion candidate step | S0/S1/S2 boundary | SHARDABLE with deterministic goal authority | NONE DIRECT | `autonomy_planner.py`; planner cannot grant effect authority |
| AZP-05 | MAIN_COGNITIVE_LOOP_AND_MODEL_INFERENCE | R0_UPSTREAM + OWNER_REQUIRED | system/protocol/history/context | reasoning/response/tool request candidates | S2 | SHARDABLE | NONE | upstream `Agent.monologue`, `prepare_prompt`, model/tool loop in `agent.py`; owner requires equivalent distributed cognition |
| AZP-06 | WORK_DECOMPOSITION_AND_SUBORDINATE_DELEGATION | R0_UPSTREAM + OWNER_REQUIRED | task/context, delegation decision | child work contexts, child result returned to superior/fusion path | S1/S2 | SHARDABLE | NONE | upstream subordinate lifecycle / `_process_chain`; owner requires decomposition across grid |
| AZP-07 | HYPERPOSITION_ALTERNATIVE_GENERATION | R0_PROJECT + OWNER_REQUIRED | observation/work state | bounded competing alternatives/branches | S1/S2 | SHARDABLE | NONE | `workspace.py` alternatives; owner requires alternative generation/simulation/Hyperposition where needed |
| AZP-08 | GLOBAL_WORKSPACE_COMPETITION_BROADCAST_REENTRY | R0_PROJECT_PARTIAL + OWNER_REQUIRED | competing alternatives, salience/evidence, prior workspace | selected/broadcast/re-entered workspace state | S1 | COORDINATOR_SCOPED | NONE | `workspace.py`, workspace episodes; owner requires competition/broadcast/re-entry. Full distributed causal broadcast remains unverified |
| AZP-09 | TOOL_REQUEST_EXTRACTION_VALIDATION_ROUTING | R0_UPSTREAM + R0_PROJECT_PARTIAL | model candidate output, tool schema/capabilities | validated tool/effect proposal or rejection | S2 -> S0 boundary | SHARDABLE validation + GLOBAL_BOUNDARY authority | NONE DIRECT | upstream Agent Zero tool extraction/validation/processing; project effect/request surfaces |
| AZP-10 | EFFECT_PROPOSAL_GATE_EXECUTION_JOURNAL | R0_PROJECT | typed effect request, session/generation, capability, lease | denied/failed/verified effect receipt + journal identity | S0 | GLOBAL_BOUNDARY | **YES, ONLY HERE THROUGH DETERMINISTIC GATE/JOURNAL** | `effects.py`, `effect_journal.py`; generic direct host process execution is denied |
| AZP-11 | CAUSAL_OUTCOME_RECONCILIATION_AND_CREDIT | R0_PROJECT | effect receipt/outcome, causal episode, observation | re-entry, bounded causal credit/evidence linkage | S0/S1 | GLOBAL_BOUNDARY | NONE | `turn_lifecycle.py`, `recovery.py`, causal episodes; unknown outcome is preserved and not blindly replayed |
| AZP-12 | MEMORY_COMPACTION_GRAPH_AND_DURABLE_LEARNING_UPDATE | R0_PROJECT | terminal turns/outcomes/retrieval feedback | durable memory/projection/policy updates | S0 + rebuildable projection | COORDINATOR_SCOPED / GLOBAL_BOUNDARY | NONE | `turn_lifecycle.py`, `microclay_retrieval.py`, graph/memory surfaces; adaptive retrieval cannot change truth/effect rights |
| AZP-13 | AUTONOMOUS_WAKE_SCHEDULING_AND_CONTINUATION | R0_PROJECT + OWNER_REQUIRED | runnable goals, wake/activity/runtime safety state | reserved dispatch / one bounded next cognitive step | S0/S1 | SHARDABLE scheduling with lease discipline | NONE DIRECT | `autonomy_pulse.py`; owner requires autonomous continuation without fixed topology |
| AZP-14 | FAILURE_RECOVERY_GENERATION_REJOIN_NO_REPLAY | R0_PROJECT + OWNER_REQUIRED | active turns, effects, leases, persisted outcomes, generation | closed/re-entered UNKNOWN-or-known state, advanced generation, safe rejoin | S0 | GLOBAL_BOUNDARY with shardable inspection | NONE NEW | `recovery.py`; owner requires node failure/rejoin without canonical-state loss |
| AZP-15 | HUMAN_INTERVENTION_FEEDBACK_AND_CORRECTION | R0_PROJECT + R0_UPSTREAM | human intervention/feedback, current context/retrieval | bounded intervention or external learning signal | S1/S2; some durable receipts | SHARDABLE | NONE | upstream intervention propagation; `microclay_retrieval.menschliche_rueckmeldung` |
| AZP-16 | OBSERVABILITY_MEASUREMENT_AND_UNKNOWN_PRESERVATION | R0_PROJECT | canonical DB/runtime probes | measurements with explicit UNKNOWN/None, telemetry/receipts | S0 read / measurement | SHARDABLE | NONE | `zustand.py`, manifest telemetry; `0 != UNKNOWN` is explicit project law |
| AZP-17 | CLAYCODE_COGNITIVE_REPRESENTATION_AND_EXECUTION | OWNER_REQUIRED + R0_PROJECT_COMPONENTS | cognitive process packets/IR/protocol structures | compact ClayCode representations and executable deterministic transforms | S1/S2, bounded S0 effects only through gate | SHARDABLE + deterministic VM boundary | NONE DIRECT | owner explicitly requires ClayCode as machine substrate; repository contains ClayCode/VM/compiler/migration artifacts. **End-to-end Agent-Zero process mapping remains open** |
| AZP-18 | DISTRIBUTED_NODE_ADMISSION_WORK_SELECTION_RESULT_FUSION_AND_DYNAMIC_COORDINATION | OWNER_REQUIRED + R0_PROJECT_DONOR | node/runtime identity, shared state, pending work, result packets | admitted work selection, typed result, scoped coordinator/fusion update | S1/S2 | COORDINATOR_SCOPED | NONE | current autonomous-boot acceptance contract plus open donor lanes #1966/#1967. **Integrated size-independent runtime not yet accepted** |
| AZP-19 | SCALE_COMPRESSION_AND_SELECTIVE_STATE_DISTRIBUTION | OWNER_REQUIRED + R1_INFERRED | process graph, shared state, resource budget, node count N | bounded state views/compressed packets/work placement | S1/S2 | SHARDABLE + COORDINATOR_SCOPED | NONE | owner requires N=1 through arbitrary larger N and bounded shared-state/compression. **No scale-independent acceptance evidence yet** |
| AZP-20 | TERO_ENTITYOS_FUNCTIONAL_SURFACE_REPRODUCTION | OWNER_REQUIRED | process outputs + EntityOS/Tero required behavior/state | system-level equivalent observable functions/state transitions | crosses S0/S1/S2 | depends on function | only through AZP-10 | owner requires EntityOS/Tero functional reproduction where in target. **Exact current Tero behavior census is unresolved and MUST be separately bound before equivalence claims** |

## 4. Dependency spine

The minimal non-fixed-N functional spine is:

`AZP-01 admission`
` -> AZP-02 state reconstruction`
` -> AZP-03 retrieval/context`
` -> AZP-04 goal/planning`
` -> AZP-05 cognition`
` -> {AZP-06 delegation, AZP-07 alternatives, AZP-08 workspace}`
` -> AZP-09 tool/proposal routing`
` -> AZP-10 deterministic effect boundary when needed`
` -> AZP-11 outcome reconciliation`
` -> AZP-12 durable update`
` -> AZP-13 autonomous continuation`
` -> AZP-14 recovery/rejoin around every durable boundary`.

`AZP-15` and `AZP-16` are cross-cutting correction/measurement processes.

`AZP-17`, `AZP-18`, and `AZP-19` are the current transformation layers that convert the observed single-/few-runtime behavior into the owner-required ClayCode-native distributed HCU/Xeno substrate.

`AZP-20` is an acceptance surface, not permission to invent undocumented Tero behavior.

## 5. Process-to-authority invariants for the ABI

Every future `COGNITIVE_PROCESS_ABI/v1` packet must bind enough identity to prevent cross-process authority inflation. At minimum, each process invocation/result must be able to carry or resolve:

- process family ID (`AZP-*`) and ABI version;
- causal event / work identity distinct from transport/admission identity;
- state generation/epoch and exact state digest or content-addressed references;
- node/runtime/model identity where model-specific evidence matters;
- input provenance and capability authority reference;
- resource/budget envelope;
- parent/dependency/workspace identity;
- output class: `OBSERVATION | CANDIDATE | SELECTION | RESULT | EFFECT_REQUEST | EFFECT_RECEIPT | MEASUREMENT`;
- canonical-credit flag/scope;
- replay/idempotency identity;
- error/UNKNOWN representation;
- for model paths, trace identity sufficient for later GWT/J-Space lesion/shuffle/rescue controls;
- for S1 writes, deterministic scoped coordinator authorization;
- for real effects, handoff to the single EffectGate/EffectJournal authority only.

No ABI packet may self-grant capability, S0 truth, coordinator authority or effect authority.

## 6. Distribution hypotheses and counterhypotheses

### H1 — process families are a better scale unit than agents

If the grid distributes `AZP-*` work units rather than fixed personalities, the same runtime/checkpoint can dynamically execute different functions as state and load change, satisfying the owner’s size-independent target more directly.

**Counterhypothesis:** process boundaries may be too fine and create coordination/context-transfer overhead that destroys functional equivalence. The ABI must therefore measure transfer bytes/tokens, latency, duplicate work and causal reconstruction cost instead of assuming finer decomposition is better.

### H2 — S1 shared state can replace peer-chat topology as the primary coordination substrate

The existing project already has durable state, workspace, causal, retrieval and lease concepts. A shared-state process ABI should allow nodes to disappear/rejoin without requiring a fixed conversational hierarchy.

**Counterhypothesis:** some Agent Zero subordinate behavior depends on transient parent-child context that cannot be reconstructed economically from bounded S1. The cheapest discriminator is a matched task where child-context handoff is reconstructed from ABI packets and compared with direct upstream subordinate lifecycle behavior.

### H3 — one effect authority can coexist with distributed cognition

Distributed cognition can remain candidate-only while the existing deterministic EffectGate/EffectJournal stays singular in semantics.

**Counterhypothesis:** coordinator/fusion layers may accidentally become a second effect or truth authority. Mandatory negative tests must attempt to smuggle capability/effect/security fields through nested S1/process packets and verify hard rejection.

## 7. Unknowns that block promotion

The following are intentionally unresolved:

1. Exact `COGNITIVE_PROCESS_ABI/v1` schema and packet canonicalization for all AZP families.
2. Exact current Tero functional census needed by AZP-20.
3. Exact ClayCode mapping for each AZP family, including which transformations are VM-executable versus model-mediated.
4. Whether upstream Agent Zero subordinate-context behavior can be reconstructed from bounded shared-state packets without semantic loss.
5. Distributed GWT broadcast/re-entry acceptance and model-specific J-Space causal evidence.
6. Contention/failure behavior for dynamic coordinators under arbitrary N.
7. Scale/compression curves: bytes/tokens/latency/quality versus N and process partitioning.
8. End-to-end Agent Zero functional-equivalence benchmark and matched-budget challenger definition.

No whole EntityOS/HCU, full HCU, J-Space model, training or final-acceptance credit follows from this census.

## 8. Next exact gate

Build `COGNITIVE_PROCESS_ABI/v1` from this census, starting with the highest-confidence observed spine:

`AZP-01 -> AZP-02 -> AZP-04/05 -> AZP-09 -> AZP-11`

and cross-cut it with `AZP-16 UNKNOWN/provenance` plus the existing deterministic S0/effect fences.

The first executable discriminator should show that **the same node/runtime can receive two different AZP work types from shared state, emit typed process results with exact causal/state identity, and rejoin after restart without self-assigning coordinator or effect authority**. This remains size-independent: N=1 is valid for the fixture, and a larger N is only added when it increases information gain.

## 9. Credit boundary

- Whole EntityOS/HCU runtime: `0`
- Full HCU runtime: `0`
- End-to-end Agent Zero equivalence: `0`
- Model-specific J-Space runtime: `0`
- Training: `0`
- Final acceptance: `false`

This artifact advances architecture/implementation readiness only; it is not runtime evidence.