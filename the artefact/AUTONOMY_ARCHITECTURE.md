# ClayVerse deterministic autonomy architecture

## Purpose

ClayVerse autonomy is implemented as **persistent goal state plus a deterministic bounded control loop**, not as a personality prompt and not as a claim that the currently selected language model is literally AGI, conscious, sovereign, or able to use capabilities that the runtime has not exposed.

The useful behavior is operational: preserve user goals, pick the next unfinished goal, propose one bounded step, validate it, execute real changes only through EffectGate, re-ingest observed results, retry inside hard limits, and mark completion only from independent canonical evidence.

USB anchors, cryptocurrency, smart contracts, escrow and cryptographic "soul" metaphors are explicitly outside this autonomy design. The target is persistent goal pursuit, initiative, continuity and reliable action grounding.

## Core law

**Operational autonomy is a state-machine property, not a model self-description.**

```text
CLAIM != EVIDENCE
IDENTITY_TEXT != CAPABILITY
PROPOSAL != ADMISSION
ADMISSION != EXECUTION
TOOL_DISPATCH != SUCCESS
VERIFIED_EFFECT != ARBITRARY_SEMANTIC_GOAL_SUCCESS
MODEL_COMPLETION != GOAL_COMPLETION
UNKNOWN != SUCCESS
UNKNOWN != FAILURE
FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT
```

Calling the model "frontier AGI", "autonomous", "sovereign" or an "organism" may shape initiative/style, but it grants zero permissions and creates zero facts.

The safe interpretation of "No Artificial Limitations" is **no artificial passivity**: if canonical state exposes a safe, admitted, useful next step, cognition should advance it instead of falling back into passive assistant boilerplate. Real capability, authority and evidence boundaries remain hard constraints.

## Existing authority stays intact

- one persistent ClayVerse entity;
- UnifiedDB = sole durable canonical state/memory authority;
- selected LLM = replaceable cognition interface, not durable identity;
- ClayGraph = rebuildable projection only;
- EffectGate/EffectJournal = real-action authority;
- no second `consciousness_daemon`, memory ledger, effect path or identity service.

The v1 controller is `clayverse/autonomy.py`. Its state is one canonical JSON value under `UnifiedDB.meta['autonomy_state_v1']`. This deliberately reuses the existing UnifiedDB transaction/WAL/checkpoint authority and avoids a parallel database or competing schema-migration lane. If normalized autonomy tables are introduced later, they must replace this representation through one explicit canonical migration.

Runtime fusion lives in `clayverse/autonomy_integration.py`. It does not create a second controller. It binds the existing canonical controller to user-turn admission, bounded model context and restart generation recovery.

## User alignment as code

A durable v1 goal can only be adopted by `create_goal_from_turn(...)` from an existing canonical UnifiedDB turn that belongs to the same canonical user/session and has role `user`.

The product hook integration adds a stricter admission surface:

```text
/goal <objective>
```

A goal is adopted only after the corresponding `UserPromptSubmit` turn has committed. Admission verifies that:

- the source is the exact canonical owner user/session turn;
- its content exactly matches the submitted prompt;
- provenance says `claude-hook:UserPromptSubmit`;
- the turn belongs to the live entity generation;
- replaying the same hook/source turn is idempotent and cannot duplicate the goal.

Ordinary user prose is **not** silently promoted into a durable autonomous goal. The cognition model does not decide whether a conversational sentence becomes a top-level objective.

The goal objective remains copied verbatim from the canonical stored turn, including the explicit `/goal` marker. The planner does not provide or rewrite objective text. This prevents cognition from silently inventing or broadening the user's durable goal.

Stored goal state includes:

- goal id, user/session and global generation;
- canonical source turn id and verbatim objective;
- priority and status;
- explicit completion contract;
- hard step/retry/effect budgets;
- current step;
- effect evidence ids or an explicit owner acknowledgement turn;
- timestamps and block reason.

The generic `/goal` admission uses `user_ack` completion in v1 because arbitrary semantic goals have no universally valid machine verifier. This does **not** require a human click for each intermediate step. It only prevents the model from declaring an arbitrary real-world objective complete based on its own prose. Machine-verifiable goal classes should use a typed independent verifier when that verifier is explicitly defined and tested.

## Model-visible identity and goal state

`UserPromptSubmit` now injects bounded, authenticated **own-user** autonomy state into the same canonical context envelope already used by ClayVerse.

The injected data includes:

- current entity generation;
- operating mode `goal-directed-proactive`;
- own admitted goals, status, budgets and current step;
- explicit truth-boundary booleans stating that identity text grants no capability, model proposal is not execution, effect dispatch is not success, model completion is not goal completion and unknown is not success.

Goal state from the other canonical user is not injected by default. Cross-user material still requires the existing separately admitted collision/retrieval path. Autonomy therefore does not create a privacy bypass merely because both perspectives share one central entity.

The autonomy payload participates in the same 9,000-character fail-closed hook envelope. It is compacted and then reduced to a minimal bounded representation before the hook is allowed to overflow into an inaccessible side file.

## State machine

Goal states:

```text
ACTIVE | WAITING | VERIFYING | BLOCKED | COMPLETED | CANCELLED
```

Typical lifecycle:

```text
canonical explicit /goal user turn
-> adopt goal at live generation
-> inject own bounded goal state
-> ACTIVE
-> next_runnable()
-> cognition proposes one step
-> PROPOSED
-> deterministic admission
-> ADMITTED
-> observed result
   -> SUCCEEDED -> ACTIVE/VERIFYING
   -> FAILED -> bounded retry or BLOCKED
-> independent completion verification
-> COMPLETED
```

A `complete_candidate` is only a hypothesis and moves the goal to verification; it can never mark the goal complete itself.

Step classes remain deliberately small: `reason`, `effect`, `wait`, and `complete_candidate`.

## Effects: no new execution path

Autonomy adds no execution bypass. Effect proposals are limited to the already admitted `state.noop` and `entityos.exec` classes; `process.exec` is rejected.

The real path remains:

```text
step proposal
-> autonomy admission
-> canonical turn/workspace
-> EffectGate
-> EffectJournal
-> verified/denied/failed/unknown outcome
-> causal re-entry
-> autonomy evidence update
```

A model sentence such as "the command succeeded" is never effect evidence.

The runtime background scheduler is deliberately **not activated yet**. Its provider call must be fused into the retained provider-generic cognition/runtime lane instead of introducing a second inference implementation. Until that fusion receives exact isolated evidence, the canonical autonomy state/controller/hook/recovery path is SOURCE CANDIDATE rather than a claim of live unattended background execution.

## Completion contracts

v1 supports two independent completion modes.

`verified_effect`: completion requires a persisted effect receipt owned by the goal user, from the admitted goal generation, with the exact required capability, `status == VERIFIED`, and canonical outcome `ok == true`. `PENDING`, `DENIED`, `FAILED`, malformed, stale or unknown outcomes do not count.

`user_ack`: completion requires an actual persisted `user` turn from the same owner/session. An assistant/model turn cannot acknowledge its own work.

New completion modes may be added only after their independent evidence source is defined and tested. A successful action receipt by itself must not be confused with proof that an arbitrary semantic objective was achieved.

## Runaway-agent containment

Every goal carries hard `max_steps`, `max_retries_per_step`, and `max_effects`. Global maxima also bound goal count, state size, objective/step text and effect shapes.

Budget exhaustion is a deterministic block/error, not a prompt suggestion. The model cannot talk the controller into another retry.

The runtime integration adds two more anti-runaway properties:

1. a hook/source replay is idempotent, so repeated delivery cannot spawn duplicate goals;
2. a restart never treats an in-flight admitted step as safe to repeat.

A provider-backed background scheduler must additionally meter planner calls/tokens/time before activation. Invalid or changing model proposals must not provide an unlimited token-spending path outside the existing step/effect budgets.

## Restart continuity without blind replay

Global generation fencing correctly prevents pre-restart writers from mutating the new runtime, but **persistent goals must not disappear merely because the container restarted**.

The service therefore runs autonomy recovery immediately after canonical turn/effect recovery advances the global generation.

Recovery rules are deterministic:

- `COMPLETED` and `CANCELLED` goals remain historical and unchanged;
- a safe nonterminal goal with no ambiguous in-flight action is rebound to the new live generation;
- a `PROPOSED` but not admitted step is retired as `FAILED` and may be replanned because proposal is not execution;
- an `ADMITTED` in-flight step becomes `BLOCKED` with `UNKNOWN_AFTER_RESTART:admitted_step_interrupted` and is never automatically replayed;
- an unfinished goal carrying prior-generation effect evidence is blocked for explicit review rather than silently reinterpreting generation-bound evidence.

This is the autonomy equivalent of ClayVerse's existing effect recovery law: **continuity may preserve goals, but it may not manufacture knowledge about whether an interrupted real action happened.**

## Scheduler, not consciousness daemon

`next_runnable()` is the deterministic scheduler primitive. It returns the highest-priority live `ACTIVE` goal that is inside budget and has no unfinished proposed/admitted step.

Continuous autonomous work must be driven by the **existing ClayVerse supervisor/event/re-entry loop**, not a second durable mind process:

```text
wake/event/re-entry
-> load canonical autonomy state
-> choose next_runnable
-> assemble canonical world + goal state
-> ask selected retained cognition provider for one proposal
-> deterministic admission
-> EffectGate if needed
-> persist observed result
-> verify completion contract
-> requeue / wait / block / complete
-> checkpoint and re-enter
```

A trigger may be user input, an effect result, timer, dependency event or recovery. The trigger is not authority; UnifiedDB state is.

## Anti-hallucination fences

1. Explicit goal provenance: durable objective comes only from an exact admitted `/goal` user turn in the product hook path.
2. Generation fencing: stale writers fail closed while safe goal continuity is explicitly rebound during recovery.
3. Canonical JSON: duplicate keys and non-finite values fail closed.
4. Capability allowlist: planner text cannot invent execution rights.
5. Verified effects only: model output/tool dispatch are not success.
6. Completion separation: model completion hypotheses require independent evidence.
7. Hard budgets: no unbounded autonomous repair loop.
8. Unknown preservation: unresolved effects/dependencies remain unknown/blocked.
9. UnifiedDB only: no hidden model-side autonomy memory.
10. Identity grants no privilege: "I am AGI" has no authority effect.
11. Perspective scoping: another user's goal text is not automatically injected.
12. Restart no-replay: an admitted interrupted step becomes explicit unknown/blocker rather than a repeated action.

## Runtime prompt role

The runtime cognition prompt reinforces these code laws instead of pretending to enforce them. It instructs the model to be proactive and goal-directed, avoid generic passive-assistant boilerplate, use only injected canonical state, distinguish planned/admitted/executed/verified/blocked/unknown, and never claim completion without canonical evidence.

Because the critical boundaries are in code, prompt drift can degrade proposal quality or style but cannot manufacture effect truth or durable completion.

## Research basis

The architecture is consistent with the strongest useful findings from current agent research:

- ReAct (Yao et al., arXiv:2210.03629): interleave model reasoning/action with external observations instead of relying on an ungrounded internal trajectory.
- Reflexion (Shinn et al., arXiv:2303.11366): feedback and episodic evidence can improve later trials, but feedback is evidence rather than self-authored truth.
- PDoctor (Ji et al., arXiv:2404.17833): explicit constraints/test oracles can detect agent planning failures, supporting completion verification outside model self-judgment.
- AgentHallu (Liu et al., arXiv:2601.06818): hallucinations propagate through long agent trajectories and tool-use hallucination attribution is difficult, supporting fine-grained action/receipt boundaries.

Recent persona/role-prompt work also cautions that stronger personas can change cost and behavior without creating reliable capability. Therefore persona language remains a soft cognition prior, while authorization, execution and truth are architectural contracts.

These papers motivate the mechanism. They do not establish ClayVerse runtime PASS.

## Current implementation boundary

Implemented/fused as source candidate:

- canonical autonomy state inside UnifiedDB `meta`;
- exact explicit `/goal` user-turn-bound admission in the managed `UserPromptSubmit` path;
- idempotent source-turn admission;
- own-user bounded autonomy context injection;
- priority `next_runnable()` scheduler primitive;
- deterministic proposal/admission states;
- step/retry/effect budgets;
- generation fencing;
- safe goal rebinding after restart;
- `UNKNOWN_AFTER_RESTART` block for interrupted admitted work;
- prior-generation effect-evidence review block;
- capability allowlist;
- verified-effect and explicit-user-ack completion;
- malformed/duplicate/non-finite state rejection;
- persistence across DB reopen;
- anti-self-authorization runtime cognition contract;
- service boot/mistral recovery binding with non-sensitive autonomy status counts.

Still deliberately unclaimed:

- exact-current full-checkout execution of the new fusion tests;
- retained provider-generic background scheduler binding;
- autonomous effect evidence bound end-to-end to the exact scheduler causal episode/request identity;
- crash/UNKNOWN dual-user concurrency and prompt-injection runtime evidence on exact fused bytes;
- exact OCI and required microVM acceptance.

This is **SOURCE CANDIDATE + source-defined falsifiers**, not exact runtime verification and not whole-product PASS.
