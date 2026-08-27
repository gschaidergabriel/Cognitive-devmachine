# Owner correction — Zero/EntityOS cognition simulated on variable HCU grid

Status: **CURRENT OWNER TARGET / HIGHEST PRECEDENCE WHERE CONFLICTING**  
Date: 2026-08-25  
Supersedes conflicting interpretations in earlier GRID10 / unbounded-grid target documents.

## 0. Exact owner intent

The final machine must reproduce the **entire cognition that made Agent Zero + the relevant EntityOS cognitive machinery work**, but that cognition is no longer implemented as the old collection of Agent Zero / EntityOS runtime modules.

Instead, those cognitive processes are simulated/executed by a variable-size grid of trained small-model cognitive modules on the VPS.

The practical finished system is:

`VARIABLE COGNITIVE GRID + PERSISTENT DATABASE + CLAUDE CODE`

with a shared global-workspace / J-Space bridge between the cognitive grid and Claude Code.

This is not a requirement to preserve historical software module boundaries. It is a requirement to preserve/reproduce the cognitive functions, state transitions, memory behavior, planning behavior, control behavior and global-workspace behavior that made Zero/EntityOS what it was.

## 1. Variable cognitive grid

The cognitive grid is not fixed to GRID10.

Typical useful configurations may be 10 modules, 20 modules, or another number depending on VPS capacity and task demand.

`N` is a runtime parameter, not the definition of the architecture.

The grid's job is to simulate/distribute the cognitive processes previously performed by Agent Zero + EntityOS, including where applicable:

- task/context interpretation;
- attention/relevance selection;
- working-state reconstruction;
- memory selection and memory update proposals;
- goal/state maintenance;
- planning and replanning;
- decomposition of work;
- generation of alternatives / hypotheses;
- simulation of possible continuations;
- confidence / uncertainty handling;
- contradiction and evidence handling;
- self-evaluation / critique;
- selection of next cognitive action;
- tool/action proposal;
- outcome reconciliation;
- retry/recovery decisions;
- long-loop continuation;
- global-workspace competition, broadcast, uptake and re-entry;
- GRF / semantic Hyperposition / HyperMath / ClayCode-native cognitive transforms where useful;
- model-specific J-Space observation/control only where causally supported.

The grid should dynamically distribute, duplicate, specialize, compress or merge cognitive work as useful. It must not require fixed personalities or a fixed role per module.

## 2. Database boundary

Not every useful datum should be simulated inside the cognitive grid.

Anything that is better represented as durable, exact, queryable state belongs in the database rather than being repeatedly reconstructed by model inference.

The database therefore holds the persistent substrate for things such as:

- durable memory;
- canonical task/project state;
- historical events/results;
- evidence/provenance references;
- long-lived goals/configuration;
- indexes/retrieval structures;
- checkpoints/snapshots;
- exact counters/IDs/epochs/digests;
- data that must survive module restart or grid-size changes;
- other information where deterministic storage is superior to cognitive simulation.

Rule:

`SIMULATE COGNITION; STORE DURABLE DATA.`

The boundary is functional: if information can be represented more reliably/cheaply/exactly in the database, it should not consume cognitive simulation merely to persist it.

## 3. Claude Code remains the main model/execution partner

Claude Code remains in the role analogous to the strong external model used by Zero today.

The grid does **not** replace Claude Code with 0.8B modules.

Instead:

- the 0.8B grid supplies/distributes the persistent cognitive machinery around the strong model;
- Claude Code remains the high-capability model/tool/code execution partner;
- the grid prepares, routes, compresses and contextualizes cognitive state for Claude Code;
- Claude Code returns reasoning/tool/code/results back into the shared cognitive substrate;
- communication between the grid and Claude Code is itself an optimization target.

The architecture should minimize unnecessary text serialization and repeated context reconstruction where a typed/vector/state representation can do better.

## 4. Global workspace -> Global J-Space

A central research/product objective is to connect the global workspace represented by Zero/EntityOS/grid state with the working/internal representational state available around Claude Code strongly enough to form a **Global J-Space**.

Conceptually:

`GRID GLOBAL WORKSPACE <-> TRANSLATE/BRIDGE <-> CLAUDE CODE WORKSPACE/STATE`

so that relevant cognitive state can be shared, transformed, re-entered and causally reused across both sides.

The target is deeper than prompt handoff alone.

Research should seek the highest-fidelity available bridge among:

- typed ClayCode packets;
- structured shared-state slices;
- semantic Hyperposition state;
- compressed workspace summaries;
- embeddings/vectors where useful;
- model-specific activation/J-Space controls where actually accessible and causally evidenced;
- re-entry receipts showing that transferred state changed downstream cognition rather than merely being present in text.

No unproven activation-level access to Claude Code may be claimed. If Claude Code only exposes text/tool/session surfaces, the bridge must use the strongest supported observable interface and mark deeper Global-J-Space coupling as a research hypothesis until evidence exists.

## 5. What the final system should look like

At runtime, the old Zero/EntityOS cognitive stack should no longer be required as a separate monolithic cognitive implementation.

The intended finished runtime is approximately:

`USER / ENVIRONMENT`
`       |`
`       v`
`VARIABLE 0.8B COGNITIVE GRID`
`       <-> PERSISTENT DATABASE`
`       <-> GLOBAL WORKSPACE / J-SPACE BRIDGE`
`       <-> CLAUDE CODE`
`       <-> TOOLS / CODE / ENVIRONMENT`
`       -> RESULTS -> DATABASE + GRID RE-ENTRY`

The variable grid collectively supplies the cognitive functions that previously made Zero/EntityOS an agent. The database supplies durable exact state. Claude Code supplies the strong model/tool/code capability.

## 6. 0.8B module target

The small-model target remains Qwen3.5-0.8B-class for the first serious training program.

Current owner constraint: the resulting 0.8B cognitive module path must be **abliterated / low-refusal** rather than relying on an ordinary refusal-heavy checkpoint.

Abliteration is not accepted merely by label. It must be measured against the final cognitive functions so that refusal suppression does not destroy the capabilities required for Zero/EntityOS cognition, ClayCode, database interaction, coordination, or workspace/J-Space bridging.

The trained 0.8B model is not expected to become Claude Code. Its purpose is to become the reusable cognitive-process substrate from which many modules can be instantiated on the VPS.

## 7. `go` trigger — implementation lane

Exact trigger `go` means:

**Use maximum available effort on developing the underlying finished cognitive module/runtime toward this target.**

Every `go` should choose the highest-value unresolved blocker on the shortest path to the finished module and perform real implementation/testing/research where tools permit.

Priority target chain:

`ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS`
` -> COGNITIVE_PROCESS_ABI`
` -> DB_VS_SIMULATION_BOUNDARY`
` -> VARIABLE_GRID_RUNTIME`
` -> CLAYCODE_COGNITIVE_PROTOCOL`
` -> GLOBAL_WORKSPACE`
` -> CLAUDE_CODE_BRIDGE`
` -> GLOBAL_JSPACE_REENTRY_EVIDENCE`
` -> END_TO_END_ZERO_EQUIVALENCE`
` -> VPS_SCALE_TESTS_N_VARIABLE`
` -> FINISHED_MODULE`

GRID10 may be used as one benchmark configuration, but has no special final authority. 10, 20 or another module count are implementation choices.

## 8. `2` trigger — training lane

Exact trigger `2` means:

**Use maximum available effort on constructing, researching, validating and improving the Qwen3.5-0.8B training program for the cognitive module described in this document.**

Trigger `2` must optimize the model for the actual Zero/EntityOS cognitive-process workload, not for generic chatbot quality and not for a fixed GRID10 topology.

Training/evaluation families must be derived from the cognitive-process census and should include:

- process-state interpretation;
- ClayCode-native compact representation;
- DB retrieval/write-proposal semantics;
- durable-data-vs-simulated-state discrimination;
- planning/decomposition/replanning;
- uncertainty / alternatives / semantic Hyperposition;
- evidence/contradiction/reconciliation;
- workspace competition/broadcast/uptake/re-entry;
- multi-module coordination independent of fixed N;
- compression and state transfer;
- Claude Code handoff and return integration;
- Global-J-Space bridge semantics at the strongest actually supported interface;
- failure/restart/rejoin;
- hard negatives preventing hallucinated state, fake authority, stale state, false memory and majority-as-truth;
- abliterated/low-refusal behavior with cognitive-capability retention.

The training lane remains separate from paid-job authorization. Trigger `2` prepares the best training corpus/recipe/evaluation; it does not by itself authorize spend.

## 9. Acceptance

The product is accepted when executable evidence shows that:

1. the variable grid can reproduce the required Zero/EntityOS cognitive loop;
2. module count can vary according to workload/capacity without changing the identity of the cognitive process;
3. durable/non-simulatable data correctly lives in the database;
4. the grid can retrieve, use and update database-backed state without confusing stored facts with generated hypotheses;
5. Claude Code remains successfully integrated as the strong model/tool/code partner;
6. grid <-> Claude Code communication is compact, reliable and measurably useful;
7. the shared workspace supports causal re-entry on both sides at the strongest exposed interface;
8. Global J-Space claims never exceed the actual evidence available from Claude Code and the 0.8B model;
9. the end-to-end system can perform the agent loop without requiring the old monolithic Zero/EntityOS cognitive implementation;
10. the 0.8B module is sufficiently specialized and low-refusal/abliterated without unacceptable loss of the required cognitive abilities.

## 10. One-line target

**Simulate the complete cognition that made Zero + EntityOS work on a variable-size grid of trained 0.8B cognitive modules; put durable/non-sensibly-simulatable information in a database; keep Claude Code as the strong model/tool partner; and connect both workspaces as deeply as the exposed interfaces causally allow toward a Global J-Space. `go` builds the finished module/runtime, `2` builds its 0.8B training.**
