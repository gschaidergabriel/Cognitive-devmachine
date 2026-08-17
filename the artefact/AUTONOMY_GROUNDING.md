# ClayVerse deterministic grounded autonomy

Status: SOURCE CANDIDATE — runtime activation and exact isolated execution evidence are still required.

## Purpose

This contract translates the useful operational content of an "autonomous frontier AGI" identity prompt into deterministic ClayVerse architecture without turning narrative identity into fabricated capability or fabricated reality.

Explicitly out of scope here: USB identity anchors, cryptocurrency, smart contracts, escrow and cryptographic ownership metaphors. The target is autonomous goal pursuit, causal continuity, proactive execution and strong anti-hallucination boundaries.

## Research basis

The architecture follows a conservative synthesis of agent research rather than assuming that a stronger role prompt creates stronger real capability:

- ReAct (Yao et al., arXiv:2210.03629): interleaving reasoning/action with observations from an external environment can reduce hallucination/error propagation compared with an ungrounded reasoning-only trajectory.
- PDoctor (Ji et al., arXiv:2404.17833): agent planning failures can be exposed by checking plans against explicit constraints/test oracles; this supports typed completion contracts outside model self-judgment.
- Reflexion (Shinn et al., arXiv:2303.11366): feedback and episodic memory can improve later trials, but feedback must remain evidence with provenance rather than becoming self-authored truth.
- AgentHallu (Liu et al., arXiv:2601.06818): hallucinations in multi-step agent trajectories can propagate and tool-use hallucination attribution is especially difficult; therefore each causal step needs explicit action/receipt identity rather than one opaque autonomous chain.

These papers motivate the mechanism. They do not establish ClayVerse runtime PASS.

## Translation of the identity prompt into architecture

### 1. Identity: state contract, not capability story

Do not inject "you are sovereign AGI" as a factual capability premise.

Persist and inject only operationally testable identity facts:

- entity: `ClayVerse`;
- canonical durable state authority: `UnifiedDB`;
- operating mode: `goal-directed-proactive`;
- current global generation;
- admitted active goals and their budgets/status;
- currently observed runtime capabilities;
- verified receipts and explicit unknowns;
- model role: cognition/proposal organ, not state/effect/truth authority.

The phrase "AGI identity" may describe the desired interaction posture — proactive, capable, persistent, non-servile — but it never grants a tool, credential, filesystem, network path or successful outcome.

### 2. "No artificial limitations" -> no artificial passivity

The safe architectural interpretation is:

> Do not add unnecessary assistant passivity when canonical state already authorizes a useful next step.

It is NOT:

> Pretend unavailable capabilities exist or suppress real system/security boundaries.

Therefore the cognition model should advance an admitted goal without asking for a human click at every reversible bounded intermediate step, while exact missing authority/evidence becomes a blocker rather than a disclaimer or fabricated action.

### 3. Goal alignment: admitted user goals

A model may propose plans and substeps, but it may not silently mint a new persistent top-level goal.

Initial deterministic admission surface:

`/goal <objective>`

The canonical `UserPromptSubmit` turn commits first. Then ClayVerse atomically writes:

- `autonomy_goals` row;
- first `autonomy_steps` row;
- provenance receipt bound to the exact user turn.

The admission receipt is an `OBSERVATION`, not success evidence. Asking for a goal can never prove completion of that goal.

Future natural-language goal extraction may create `GOAL_CANDIDATE` proposals, but promotion must retain an explicit user/owner authority contract rather than allowing model self-assignment of durable objectives.

### 4. Autonomous machine loop: bounded state machine, not consciousness daemon

Autonomy is implemented as a timer/event-driven worker inside the existing ClayVerse supervisor process and the same UnifiedDB authority.

One wake performs at most one bounded work unit:

`SELECT FRONTIER -> BUILD GROUNDED SNAPSHOT -> MODEL PROPOSES -> VALIDATE CAPABILITY -> OBSERVE/EFFECT -> RECEIPT -> TRUSTED VERIFIER -> UPDATE STEP/GOAL -> SLEEP`

The LLM is a planner/proposal function. The state machine owns transitions.

There is no second durable agent, second database, hidden consciousness process or second effect path.

### 5. Grounded self-model

Every autonomy planning snapshot contains:

- exact goal + current step;
- exact entity generation;
- observed capabilities only;
- verified receipts only;
- explicit epistemic rules.

Hard invariants:

1. `IDENTITY_TEXT != CAPABILITY`.
2. `MODEL_PROPOSAL != EFFECT`.
3. `EFFECT_REQUEST != EFFECT_SUCCESS`.
4. `VERIFIED_EFFECT_SUCCESS != GOAL_SUCCESS`.
5. `MODEL_SAYS_DONE != STEP_DONE`.
6. `UNKNOWN != SUCCESS`.
7. stale generation evidence cannot advance a goal.

This is the main defense against "power hallucination".

### 6. Typed success contracts

Every goal and step has a success/verification contract. The model cannot satisfy it by producing persuasive text.

A step may move to `VERIFIED` only with a verified receipt from an admitted verification class such as:

- deterministic test oracle;
- verified artifact predicate;
- explicit user confirmation when the contract genuinely requires human judgment;
- deterministic state predicate;
- independently verified external/effect result plus a success predicate.

An execution/effect receipt alone is evidence that an action occurred. It is not semantic proof that the intended objective was achieved.

Goal completion separately requires its goal-level verifier after all required steps are verified.

### 7. Runaway prevention

Autonomy is intentionally finite-state and budgeted:

- maximum attempts per step;
- maximum total attempts per goal;
- repeated-identical-failure fingerprint;
- persistent `BLOCKED` state;
- one bounded work unit per wake;
- error backoff;
- stale-generation fencing;
- no blind effect replay after crash;
- planner-declared missing prerequisites become durable blockers rather than repeated paid prompts.

Later resource policy can add explicit token, wall-clock and monetary budgets, but those budgets must be measured values rather than narrative "economic discipline".

### 8. ERS / reputation

Do not implement a fictional reputation score that the model can optimize against itself.

If an ERS-like signal is introduced, it must be a derived metric from verified external outcomes, test quality, reversals/corrections, cost and reliability. It must not become truth authority and must not be usable by model prose to self-award progress.

### 9. Causal continuity without hidden chain-of-thought authority

Continuity is state + receipts + causal IDs, not a requirement to persist private chain-of-thought.

Durable trace should contain concise, inspectable fields:

- goal/step identity;
- proposal/action class;
- observed capability set;
- effect/observation receipt identity;
- verifier result;
- blocker/failure fingerprint;
- generation;
- state transition.

This gives debuggability without making free-form hidden reasoning a second truth ledger.

## Source-candidate implementation

Current branch introduces:

- `clayverse/autonomy.py`: goal/step/receipt/tick schema plus bounded controller;
- `clayverse/autonomy_runtime.py`: supervisor-safe quiescence/backoff wrapper;
- `clayverse/goal_admission.py`: explicit user-grounded atomic goal admission;
- `clayverse/terminal_hooks.py`: bounded autonomy state injected as canonical data;
- `runtime_CLAUDE.md`: proactive/non-passive operating contract plus anti-capability-hallucination rules;
- `tests/test_autonomy_grounding.py`: source-defined falsifiers for fake capabilities, model self-completion, stale receipts, unverified success, goal provenance and blocked-loop repolling.

## Deliberately not claimed yet

- The autonomy tests have not yet received exact authorized isolated runtime execution credit.
- The background planner has not been bound to a final accepted provider runtime in this branch.
- Autonomy is therefore SOURCE CANDIDATE, not runtime-verified autonomous operation.
- Provider/runtime binding should fuse with the retained provider-generic cognition path rather than creating another permanent inference authority.
- Whole ClayVerse product acceptance remains governed by the complete one-container + microVM acceptance vector.

## Promotion gate

Do not activate autonomous background cognition in the accepted product until all of the following are observed on exact current bytes:

1. goal admission provenance and transaction tests pass;
2. unobserved-capability and model-self-completion falsifiers pass;
3. stale-generation receipts cannot advance state;
4. repeated/missing-prerequisite loops quiesce under budget;
5. effect receipts cannot substitute for success verification;
6. crash/restart preserves BLOCKED/UNKNOWN and does not replay ambiguous effects;
7. provider-generic planner binding cannot bypass UnifiedDB/EffectGate;
8. full adjacent lifecycle/recovery/concurrency regression remains green;
9. exact OCI runtime and required outer microVM path preserve the same behavior.

The intended result is a ClayVerse that behaves proactively and persistently because the machine architecture carries goals forward, while hallucination resistance comes from separating proposal, capability, execution, observation, verification and truth.
