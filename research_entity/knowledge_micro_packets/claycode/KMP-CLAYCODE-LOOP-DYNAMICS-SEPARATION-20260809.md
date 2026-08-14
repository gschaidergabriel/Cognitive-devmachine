# KMP — ClayCode loop dynamics vs halt/resource state

packet_id: `KMP-CLAYCODE-LOOP-DYNAMICS-SEPARATION-20260809`
domains: `claycode, frank, gwt, emergenz, hyperposition, harness, unifieddb, claygraph`
epistemic_class: `EXECUTABLE_RESEARCH_CANDIDATE`
status_hint: `OPEN_SUPPORTED_NOT_PROMOTED`
origin_actor: `chatgpt-secondary`
provider: `OpenAI`
model: `GPT-5.6 Sol`

## Atomic claim

For the currently tested FRANK loop-of-loops controller surface, ClayCode should represent **loop dynamics** separately from **resource/halt reason**. Budget exhaustion is not convergence. A high-residual exhausted loop may require escalation while retaining its independently classified dynamics state.

The tested minimal controller does **not** require a new ClayCode core primitive: G9-style typed records + `cycle` + a pure typed dialect/runtime operation were sufficient in the local proxy.

## Evidence

- `research_entity/trigger_runs/claycode/claycode_20260809T1650p0700_chatgpt_loop_controller/EXECUTABLE_RESEARCH_RECEIPT.json`
  - 100,000 random states; 0 differential mismatches after refinement.
  - 2,994 budget-exhausted/high-residual cases -> `ESCALATE`.
  - 5,535 budget-exhausted/low-residual cases -> `HALT` with halt reason `BUDGET_EXHAUSTED`, not an inferred convergence claim.
- `research_entity/trigger_runs/claycode/claycode-20260809T1648p0700-loop-runtime/HYPOTHESES.json`
  - independent concurrent negative result: zero next delta at exhausted budget still had residual pressure `0.5690308937228293` and required `STALLED/ESCALATE`.

## Boundaries

- local parser/lowering proxy only;
- no fresh E2B;
- no verified Ubuntu developer-system execution;
- no H1/H2 FRANK replay;
- dynamics classification is not emergence evidence;
- control decision does not confer external effect authority.

## Falsifier / next test

Compile the same typed contract through the production ClayCode parser/type/effect/compiler on the Ubuntu target and replay real H1 loop traces. If a required loop family cannot be represented/lowered generically without semantic loss, reopen the core-primitive question.

## Relation to existing hypotheses

Supports/refines `H-CC-LOOP-001` and `H-CC-LOOP-003`; does not independently test scheduler snapshot semantics (`H-CC-LOOP-002`) or adaptive-vs-fixed recurrence benefit (`H-CC-LOOP-004`).
