# Reserved Trigger: `go` — Research Center Autodispatch

**Status:** PROJECT_OWNER_OPERATING_DIRECTIVE
**Kind:** program autodispatch meta-trigger
**Home discovery room:** `center`

## 0. Meaning

When the complete trimmed user message is exactly `go`, the worker must **not ask what to do** and must not merely propose work.

It must autonomously:

1. join/read the repo-native research center;
2. read the shared staged program state;
3. inspect current room activity, tasks, leases, blockers and fresh cross-room deltas;
4. identify the highest-value non-duplicated work that advances the current program stage;
5. select the correct specialist room;
6. select/claim the most useful available team role for that work;
7. claim a bounded task/lane with an explicit completion test;
8. perform the work immediately;
9. execute tests/research/implementation appropriate to the selected role;
10. publish results, blockers and cross-room deltas;
11. pulse/cross-read before durable synthesis and before the final visible response.

Compact law:

`go -> inspect center -> choose room -> choose role -> claim task -> act -> test -> publish`

## 1. Existing research center is authoritative

`go` uses, and must not replace:

- `research_entity/global/REPO_NATIVE_RESEARCH_CENTER_PROTOCOL.md`
- `research_entity/rooms/ROOM_REGISTRY.json`
- `tools/research_room.py`
- `research_entity/global/RESEARCH_CENTER_PROGRAM_NARRATIVE.md`
- `research_entity/rooms/PROGRAM_STATE.json`

There is no permanent global chief. `go` does not create one.

The worker makes one local dispatch decision for its own run based on evidence and current program needs.

## 2. Discovery phase

Before choosing work, read at minimum:

- current canonical/bootstrap state;
- `PROGRAM_STATE.json` and current stage gate status;
- room registry;
- active workers in all relevant rooms;
- current role/task leases;
- recent same-room and center/cross-room events;
- current blockers and `INTERRUPT_NEXT_SAFE_POINT` events;
- open release/workspace packages relevant to the current stage;
- latest materially relevant commits since the last stage checkpoint;
- mandatory cross-cutting knowledge refs named by `PROGRAM_STATE.json`.

If available, use `tools/research_room.py` semantics or connector-equivalent reads/writes for JOIN/PULSE/ROLE_CLAIM/TASK/DELTA/CROSSREAD/COMPLETE.

## 3. Room selection

Choose the specialist room that maximizes expected progress on the **current stage** while minimizing duplication.

Use this scoring logic conceptually:

`dispatch_value = stage_criticality + blocker_reduction + expected_information_gain + executable_progress + dependency_unlock + validation_value - overlap - stale_basis - context_cost`

Hard preferences:

1. unresolved blocker that prevents current-stage PASS;
2. missing executable release artifact/test needed for current gate;
3. failure/counterexample that can invalidate current architecture;
4. dependency that unlocks multiple other workers;
5. independent replication of a high-impact result when ancestry independence is real;
6. next highest-information research gap inside the current stage.

Do not choose a room merely because it is interesting.

## 4. Current-stage dispatch semantics

The exact current stage comes from `PROGRAM_STATE.json`.

### BASE_CLAYCODE_RELEASE
Primary room is normally `claycode`, unless another domain owns a blocking requirement:
- `frank` for missing architecture/state semantics;
- `gwt` for missing mathematical workspace/emergence-readout primitives;
- `hyperposition` for missing higher-order coupling/topology/readout primitives;
- `claygraph` for missing graph/memory/relation semantics;
- `unifieddb` for missing query/transaction/replay semantics;
- `harness` for executable counterexamples/reference fixtures;
- `emergenz` for missing measurement/falsifier semantics;
- `clay` for integrated semantic conflicts.

### H1_REFERENCE_HARNESS
Primary room is normally `harness`, with domain dispatch when H1 exposes an unresolved semantics problem owned by another room.

### H2_CLAYCODE_HARNESS
Prefer `harness` or `claycode`, then the domain owning any differential divergence.

### H3_ONE_MODULE_FRANK
Prefer `harness`, `frank`, `claycode` or `hyperposition` depending on whether the current problem is implementation consolidation, semantic boundary definition, language expression or coupling/topology optimization.

### UDB_UNIFIED_DATABASE
Prefer `unifieddb`, with Harness/ClayGraph/FRANK/ClayCode support chosen from measured blocking needs.

### DATA_LORA_TRAINING_DATA
Prefer `claycode` for language/corpus generation, while dispatching to GWT/Hyperposition/FRANK/Emergenz/Harness for exact cognitive/math/readout curricula and validation.

### WAIT
Do not invent new major work or start training. Perform only explicit maintenance/audit requested by the user or report that the program is waiting.

## 5. Role selection

After selecting a target room, inspect current active workers and leases. Use the existing tAvern-style roles:

- `CHEF` — coordination/gap control/local fusion only; zero truth authority;
- `ABYSS` — adversarial falsification, security/Goodhart/counterexample hunting;
- `FORGE` — implementation, sandbox execution, benchmarks, reproducible artifacts;
- `CARTOGRAPHER` — external research, Project-Frankenstein archaeology, cross-branch mapping;
- `REPLICATOR` — independent/differential verification;
- `SYNTHESIZER` — synthesis preserving dissent when enough lanes exist;
- `SOLO_RESEARCHER` — when no useful same-room peer exists.

Choose role by the current gap, not by preference.

Examples:

- code missing -> FORGE;
- suspicious claim blocking release -> ABYSS;
- unknown historical mechanism/prior art -> CARTOGRAPHER;
- unreplicated high-impact test -> REPLICATOR;
- multiple completed lanes needing integration -> CHEF/SYNTHESIZER;
- no peer and a clear bounded task -> SOLO_RESEARCHER.

If the ideal role is already leased, choose the next highest-value non-overlapping role/task rather than colliding.

## 6. Trigger loyalty after dispatch

`go` is a meta-trigger only until dispatch.

Once a target room/task is chosen, the worker becomes **run-pinned** to that chosen room and task until completion/handoff or a material invalidating event.

It may read all rooms and publish cross-room deltas, but must not roam between unrelated tasks just because new topics appear.

A material dependency invalidation may cause one re-dispatch only after publishing an explicit `HANDOFF` / `INVALIDATE` receipt for the abandoned task.

## 7. Task claim requirements

Before acting, create/record a task claim with:

- current program stage;
- selected room;
- selected role;
- exact gap;
- non-overlap rationale;
- dependencies;
- expected information/progress gain;
- falsifier or completion test;
- artifact/test outputs expected.

No vague task such as "improve FRANK" is valid.

## 8. Action requirement

A `go` turn is incomplete if it stops after role/task selection when the selected work is feasible in the same turn.

The worker must perform substantive work immediately:

- FORGE writes/runs code/tests;
- ABYSS creates/runs discriminating attacks/falsifiers;
- CARTOGRAPHER reads source/history/web and produces mapped evidence;
- REPLICATOR executes independent/differential tests;
- CHEF/SYNTHESIZER cross-reads and performs evidence-preserving integration;
- SOLO performs the highest-value bounded work directly.

If a tool/external dependency truly prevents execution, publish the blocker and immediately select the highest-value unblocked work in the same room/stage when possible.

## 9. Research-center pulses

Mandatory pulses remain those of `REPO_NATIVE_RESEARCH_CENTER_PROTOCOL.md`, including before:

- architecture/spec freeze;
- substantial experiment/build branch;
- durable write;
- synthesis;
- final response.

A pulse may change local implementation details but should not cause unnecessary task thrashing.

## 10. Evidence and anti-echo

Role selection and multiworker agreement never change evidence status.

`go` must preserve:

- source/experiment ancestry;
- negative results;
- dissent;
- stale dependency invalidation;
- Goodman anti-echo rules;
- simulation vs live/target evidence distinctions.

## 11. Training safety in current program

`go` must obey the staged program stop rule.

It may build LoRA training data only in the DATA stage.

It must **never automatically launch paid LoRA training or paid Together inference/training**. After DATA completes, the program enters WAIT until an explicit new owner instruction.

## 12. Visible result

The final response should state concisely:

- current stage;
- chosen room;
- chosen role;
- task claimed;
- concrete work completed/tested;
- blockers/open next dependency.

Then render the mandatory RAE status footer with `go` included in the short-command list.
