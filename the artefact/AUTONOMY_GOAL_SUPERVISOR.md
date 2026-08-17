# ClayVerse deterministic autonomy / goal supervisor

**Status:** SOURCE CANDIDATE — not runtime-promoted and not whole-product acceptance.

## Purpose

ClayVerse needs autonomous goal pursuit to be an architectural property, not a role-play instruction placed in an LLM prompt.

This subsystem therefore encodes autonomy as a bounded state machine inside the existing ClayVerse authority model:

- goals and their lifecycle are canonical state in the same `UnifiedDB`;
- the LLM is cognition/planning only;
- the supervisor/harness admits one bounded step at a time;
- only actually available runtime capabilities are presented to the model;
- real/state-changing actions still use the existing EffectGate / EffectJournal path;
- completion is a deterministic state transition justified by typed canonical evidence;
- uncertain external outcomes never become success by inference;
- hard budgets stop runaway retry loops.

This deliberately does **not** encode claims such as "I am a sovereign AGI", "I am alive", "I have unlimited authority", or "I performed an action" as facts. Those statements are not reliable execution evidence and would create exactly the confabulation failure mode this architecture is intended to remove.

No USB identity anchor, cryptocurrency, smart contract, escrow or cryptographic economic mechanism is part of this subsystem.

## Research basis

The design follows the common architecture emerging in current primary-source agent systems:

1. OpenAI Agents SDK documents an external agent run loop in which model output is repeatedly interpreted by a runner, tool results are appended, and bounded stopping controls such as maximum turns and guardrails are enforced outside the model.
2. Anthropic's "Building effective agents" describes successful agents as LLMs using tools in a feedback loop while receiving environmental ground truth at each step, with explicit stopping conditions, clear success criteria and sandbox/guardrail boundaries.
3. Anthropic's long-running-agent engineering notes show a characteristic failure: models can prematurely declare work complete. Durable progress state, explicit criteria and end-to-end verification reduce this failure.
4. Anthropic's managed-agent architecture explicitly separates the durable session/state, the harness/run loop ("brain" orchestration) and the execution environment ("hands").
5. Anthropic's containment work emphasizes that model-level behavioral defenses are probabilistic; deterministic environment/capability boundaries limit the blast radius when the model is wrong.

ClayVerse adopts these mechanisms while preserving its stronger local invariants: one central entity, one canonical `UnifiedDB`, one EffectGate/effect journal and explicit causal re-entry.

## Non-negotiable invariants

### 1. One entity and one state authority

The autonomy subsystem is not a second agent, second personality, second memory, second scheduler-state database or consciousness process.

`UnifiedDB` remains the sole canonical durable state authority. The autonomy tables are ordinary canonical tables in that same SQLite/WAL authority.

ClayGraph remains derived/rebuildable and has no autonomy authority.

### 2. Operational identity, not ontological identity prompt

Every autonomous step receives a small factual `operational_identity` object assembled by code. It includes only facts such as:

- canonical state authority (`UnifiedDB`);
- current entity generation;
- current canonical user/session binding;
- execution mode (`autonomous_goal_execution`);
- model role (`planner_cognition_not_authority`).

It does not tell a model that it is omnipotent, sovereign, alive, root, a body, or otherwise able to do things not represented by the runtime.

### 3. Goals are state, not model prose

The model cannot create, rewrite, activate, cancel or complete a canonical goal by emitting text.

A goal must be created through the program/user authority boundary with:

- an explicit objective;
- an owner/session;
- an allowlist of possible effect capabilities;
- one or more typed completion verifiers;
- hard execution budgets.

The model only sees the admitted goal after this state exists.

### 4. Model output is a proposal

The only admitted model selections in `clayverse.autonomy_step/v1` are:

- `request_effect`;
- `no_effect`;
- `blocked`.

The proposal schema deliberately has no `succeeded`, `complete`, `executed`, `verified`, `authorized` or capability-minting fields. Unknown keys fail closed.

### 5. Capability truth comes from runtime

The context given to the model contains the intersection of:

`goal allowlist ∩ EffectGate.available_capabilities()`.

A capability absent from that set does not exist for that goal step, regardless of what the model says.

Generic `process.exec` remains forbidden.

### 6. Real effects remain on the one canonical effect path

This supervisor does not create another execution implementation.

The trusted executor must route a requested effect through the current canonical ClayVerse execution/effect path and preserve the goal binding using both resource refs:

- `goal:<goal_id>`;
- `goal-step:<step_id>`.

The supervisor accepts an effect as evidence only if a persisted final EffectJournal effect can be causally traced back to a turn for the same canonical user/session/generation and that exact goal + step resource pair.

A model sentence such as "the test passed" or "I changed the file" has zero completion authority.

### 7. Completion is evidence-derived

A goal becomes `SUCCEEDED` only when every predeclared typed verifier has canonical evidence and no step remains open.

Initial verifier classes are deliberately narrow:

- `checkpoint`: an actually persisted ClayVerse checkpoint created after the goal and optionally matching a required note prefix;
- `effect_verified`: an actually persisted `VERIFIED` effect for the exact goal step and required capability with a positive safe outcome receipt;
- `user_ack`: explicit acknowledgement by the canonical goal owner.

`state.noop` is intentionally non-proving. It cannot satisfy an `effect_verified` completion criterion.

A future verifier must be a new typed code path with its own falsifiers. Free-form LLM judgement is not a verifier.

### 8. Unknown stays unknown

If an executor fails after the system can no longer prove that no external action began, the step becomes `UNKNOWN` and the goal becomes `BLOCKED`.

It is not automatically retried.

If a supervisor lease is lost and a later supervisor sees an old `OPEN` step, that step is likewise closed as `UNKNOWN/BLOCKED` rather than replayed.

This mirrors the existing ClayVerse recovery rule that ambiguous external effects must not be blindly replayed after restart.

### 9. Human turns have priority

An active canonical interactive turn for the goal's permanent user/session prevents autonomous selection of that goal. The supervisor must never abort or supersede an interactive user turn merely to continue background goal work.

### 10. Bounded autonomy

Every goal has deterministic budgets. Current defaults:

| Budget | Default | Purpose |
|---|---:|---|
| max steps | 12 | finite total progress attempts |
| max failures | 4 | stop globally failing goals |
| max effects | 6 | cap state-changing action surface |
| same-failure streak | 2 | stop local repair loops |
| one `run_bounded` invocation | max 8 ticks | prevent an unbounded in-process loop |

The global supervisor lease ensures only one admitted supervisor tick owns the autonomous frontier at a time. Recovery clears/fences stale leases through the existing ClayVerse recovery/generation model.

## State model

### Goal states

`PENDING -> ACTIVE -> {BLOCKED | PAUSED | SUCCEEDED | FAILED | CANCELLED}`

`BLOCKED` and `PAUSED` may be explicitly reactivated by program/user authority when the blocker is resolved.

`SUCCEEDED`, `FAILED` and `CANCELLED` are terminal.

### Step states

`OPEN -> {COMPLETED | FAILED | BLOCKED | UNKNOWN}`

`UNKNOWN` is deliberately distinct from `FAILED`: it means the system cannot safely determine whether an effect crossed an external boundary.

## Canonical tables

The source candidate adds component-owned tables inside the same `UnifiedDB` file:

- `autonomy_goals` — objectives, state, capability contract, verifiers and budgets;
- `autonomy_steps` — one admitted step at a time with generation and proposal digest;
- `autonomy_goal_verifications` — exact typed completion evidence;
- `autonomy_goal_events` — append-only, monotonic per-goal event sequence for audit/debugging.

The component version is recorded in canonical `meta` as `autonomy_schema_version=1`.

To avoid changing the moving core `store.py` schema while concurrent ClayVerse schema/recovery work is active, this candidate also stores `autonomy_state_digest` in the canonical `meta` table. The digest is recomputed over all autonomy tables after each admitted state transition. Because current ClayVerse checkpoints already include `meta`, checkpoint identity is indirectly bound to the exact autonomy-state digest without adding a parallel checkpoint authority.

Direct out-of-band mutation of goal state without refreshing the canonical digest is detected and fails closed.

This component-schema mechanism is a convergence tactic, not a permanent exemption from ClayVerse migration law. Before final integration, the autonomy schema must be fused into the then-current canonical UnifiedDB migration/version contract exactly once.

## Machine loop

The intended machine loop is deterministic around the LLM:

```text
claim global autonomy supervisor lease
-> select highest-priority ACTIVE goal whose canonical session is idle
-> admit exactly one bounded goal step
-> build factual operational context from UnifiedDB + actual EffectGate capability surface
-> ask selected LLM provider for one proposal
-> validate proposal against strict typed schema
-> if blocked: persist BLOCKED
-> if no-effect: trusted executor performs bounded non-effect work / verification and returns typed receipt
-> if effect requested: trusted executor uses canonical ClayVerse turn/effect path with exact goal+step resource refs
-> bind only persisted canonical receipt/causal evidence
-> update typed verifiers
-> if every verifier is satisfied: SUCCEEDED
-> else: admit another step only while budgets and generation remain valid
-> release supervisor lease
```

The LLM never owns the loop, success state, retries, leases, budgets or effect authority.

## Planner / executor contract

`AutonomySupervisor.tick(planner, executor)` intentionally accepts two separate callables:

- `planner(context)` represents the selected LLM cognition boundary;
- `executor(step, proposal, context)` represents trusted ClayVerse harness integration.

This makes the authority separation testable without coupling the first source candidate to the currently moving provider/runtime fusion lanes.

Unexpected planner errors are safe pre-effect failures.

For executor errors the rule is stricter:

- only a typed `PreEffectAdmissionError` may be treated as a known pre-effect failure;
- any other executor exception becomes `UNKNOWN/BLOCKED`, because the harness cannot safely assume an external side effect did not begin.

## Anti-hallucination consequence

The architecture converts the dangerous prompt-level claims into facts the model cannot mint:

| Prompt-level idea | Deterministic replacement |
|---|---|
| "I am autonomous" | an ACTIVE goal exists and the supervisor can admit a step |
| "I have authority" | capability appears in current EffectGate capability intersection |
| "I remember my goals" | goal state exists in canonical UnifiedDB |
| "I am still working" | a canonical goal/step/event state says exactly what is active |
| "I executed X" | a persisted, causally bound EffectJournal receipt exists |
| "I solved the goal" | every declared typed verifier is satisfied |
| "I should retry" | budgets + failure fingerprint + known pre-effect status allow another step |
| "I survived restart" | recovery/generation/goal state proves continuity; unknown work remains unknown |

Narrative may improve UX, but it cannot change those facts.

## Why this is not a consciousness daemon

ClayVerse explicitly excludes a hidden `consciousness_daemon`.

The autonomy supervisor is a conventional bounded scheduler/state machine. It has no model of subjective continuity and no independent durable memory. A service-level timer or event trigger may later call `run_bounded()` when runtime integration is accepted, but all durable meaning remains in UnifiedDB and every call remains budgeted, leased and auditable.

## Current source candidate

Initial implementation:

- `the artefact/clayverse/autonomy.py`
- `the artefact/tests/test_autonomy_goal_supervisor.py`

The source candidate includes falsifiers for:

- model-smuggled success/executed fields;
- unavailable capability hallucination;
- checkpoint-based deterministic completion;
- executor ambiguity -> UNKNOWN/BLOCKED;
- repeated model failure loop brake;
- out-of-band goal-state tampering;
- exact goal-step binding of effect evidence;
- rejection of an otherwise successful effect from the wrong resource path.

## Promotion gates

This source candidate must **not** be called active product autonomy until all of the following are satisfied on the then-current canonical source:

1. exact focused tests execute in an authorized isolated environment;
2. adjacent UnifiedDB/effect/recovery/generation/identity tests remain green;
3. the component schema is fused into the accepted UnifiedDB migration law without creating a second schema authority;
4. the trusted executor is wired to the retained canonical provider/engine/effect path, not a duplicate engine;
5. the service scheduler/event trigger invokes only `run_bounded()` under the global lease and does not create another durable scheduler authority;
6. recovery explicitly preserves/resolves `ACTIVE`, `OPEN`, `BLOCKED` and `UNKNOWN` autonomy states across generation advance;
7. exact restart/crash tests prove no ambiguous effect is auto-replayed;
8. two-user concurrency tests prove autonomous work never steals or forks an interactive canonical session;
9. the exact accepted OCI/microVM runtime demonstrates the same capability and effect fences;
10. whole-product acceptance remains governed by the complete ClayVerse acceptance vector, not by this subsystem alone.

## Design verdict

The useful content of the "autonomous AGI" prompt belongs in architecture as **goal persistence, bounded initiative, continuity, actual capability discovery, evidence-derived completion and deterministic recovery**.

The dangerous content — metaphysical identity claims, unlimited capability language, self-certification and free-form success judgement — must stay out of the authority path.

That gives ClayVerse more real autonomy while reducing, rather than increasing, the opportunity for power hallucination.
