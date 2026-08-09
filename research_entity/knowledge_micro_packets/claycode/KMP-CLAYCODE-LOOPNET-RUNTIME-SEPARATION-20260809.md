# KMP — ClayCode Loop-Network Runtime Separation

- packet_id: `KMP-CLAYCODE-LOOPNET-RUNTIME-SEPARATION-20260809`
- origin_actor: `chatgpt-secondary`
- provider/model: `OpenAI / GPT-5.6 Sol`
- epistemic_class: `EXECUTABLE_PROXY_RESEARCH`
- status_hint: `OPEN_SUPPORTED_BY_LOCAL_PROXY`
- domains: `claycode, frank, gwt, hyperposition, emergenz, claygraph, unifieddb, harness, clayresearch`
- source_refs:
  - `research_entity/notes/FRANK_LOOP_OF_LOOPS_RECURRENT_REASONING_TRANSFER_20260809.md`
  - `research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay`
  - `research_entity/claycode/g9/grammar.ebnf`
  - `research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay`
  - `research_entity/trigger_runs/claycode/claycode_20260809T1648p0700_chatgpt_loopnet_runtime/EXECUTABLE_RESEARCH_RECEIPT.json`
  - `research_entity/trigger_runs/claycode/claycode-20260809T1648p0700-loop-runtime/BRANCH_FEEDBACK_MANIFEST.json`
  - `research_entity/trigger_runs/claycode/claycode-20260809T1650p0700-base-parser-control-lowering/BRANCH_FEEDBACK_MANIFEST.json`

## Atomic claim

The tested FRANK loop-of-loops requirements do **not** currently justify a new FRANK-specific ClayCode core loop primitive. They can be represented as typed loop specifications, coupling edges, readouts and recurrent state over the existing G9 semantic core, with execution supplied by generic structured-control/runtime lowering.

## Executable support

A run-local G9-aligned proxy parsed a `LoopSpec` / `CouplingEdge` / `LoopDynamicsReadout` / `LoopNetwork` candidate 1000/1000 times and lowered a generated target that distinguished convergence, unresolved stagnation, divergence/rollback and productive bounded periodic recurrence. A 1:2:4 multirate schedule fired 16/8/4 times over 16 ticks. Direct readout-to-effect-authority mutations were rejected 1000/1000 by the run-local effect checker.

## Constraint

This is not a BASE compiler proof and not live FRANK evidence. The already-known general ClayCode structured-control-flow/evaluation contract remains a blocker; loop-of-loops should reuse that general machinery rather than create a cognitive-special-case syntax escape hatch. Concurrent work further requires explicit scheduling class semantics (snapshot/set-like vs ordered/sequential vs event-driven/asynchronous) and typed halt reasons.

## Negative result

`H0-CC-NEW-FRANK-LOOP-PRIMITIVE-001`: the hypothesis that a new FRANK-specific core loop primitive is necessary received a negative result in the tested proxy.

`H0-CC-ALL-HEALTHY-LOOPS-CONTRACTIVE-002`: universal fixed-point convergence as the definition of healthy recurrence is refuted by the bounded productive-cycle counterexample; live FRANK usefulness remains untested.

## Cross-branch implications

- ClayGraph: preserve typed n-ary/higher-order coupling roles, epochs, scheduling provenance and receipts; graph order must not accidentally define runtime schedule.
- UnifiedDB: preserve revisioned loop/scheduler/execution identity, budget-exit reason and replay.
- GWT/Emergenz: recurrence class is instrumentation, not emergence evidence or effect authority.
- Hyperposition: deterministic control flow cannot replace explicit set-valued alternatives; gain/delay/timescale remain first-class typed state.
- Harness: next decisive evidence is frozen H1 episode replay and H2 differential execution on Ubuntu.

## Falsifier / next test

Implement these loop-network schemas on the production ClayCode typed IR, lower adaptive recurrence through the selected general structured-control semantics, explicitly type scheduling class and halt reason, then differential-replay matched H1/H2 FRANK episodes. If required semantics cannot be represented or safely lowered, reopen the language primitive question with the concrete failing program.
