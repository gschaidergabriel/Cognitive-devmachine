# ClayVerse autonomy grounding fusion

Status: SOURCE CANDIDATE. This file extends the current `AUTONOMY_ARCHITECTURE.md`; it does not replace the canonical controller or create a second autonomy path.

## Scope

This fusion translates the useful behavior behind an "autonomous frontier AGI" identity into runtime architecture while explicitly excluding USB identity anchors, cryptocurrency, smart contracts, escrow and cryptographic-soul metaphors.

The operational target is:

- persistent user goals;
- proactive continuation instead of artificial assistant passivity;
- bounded autonomous step selection;
- exact capability/effect grounding;
- independent completion evidence;
- restart continuity without blind replay;
- no second memory, effect, identity or consciousness authority.

Core distinction:

```text
IDENTITY_TEXT != CAPABILITY
MODEL_PROPOSAL != ADMISSION
ADMISSION != EXECUTION
EXECUTION != VERIFIED_SUCCESS
VERIFIED_EFFECT != ARBITRARY_SEMANTIC_GOAL_SUCCESS
MODEL_SAYS_DONE != GOAL_COMPLETED
UNKNOWN_AFTER_RESTART != SAFE_TO_RETRY
```

The safe interpretation of "No Artificial Limitations" is **no artificial passivity**: when canonical state exposes an admitted, safe next step, cognition should advance it. The phrase never grants unavailable tools, credentials, host access or success.

## Runtime fusion into the existing canonical path

The existing `clayverse.autonomy.AutonomyController` remains the one controller and keeps its current exact EffectJournal target/argv binding and hard budget laws.

`clayverse.autonomy_integration` adds only integration boundaries:

1. **Explicit goal admission.** A durable interactive goal is created only from `/goal <objective>` after the exact managed `UserPromptSubmit` turn commits. The source turn must match user, session, content, hook provenance and live entity generation. Replaying the same source turn is idempotent.
2. **Perspective-scoped context.** The managed prompt hook injects bounded own-user goal state plus explicit anti-hallucination truth boundaries. Another canonical user's goal text is not injected by default.
3. **Generation recovery.** After normal ClayVerse recovery advances the global generation, safe unfinished goals are rebound to that generation. A merely PROPOSED step is retired and can be replanned. An ADMITTED in-flight step becomes `BLOCKED` with `UNKNOWN_AFTER_RESTART:admitted_step_interrupted` and is never automatically replayed. Unfinished prior-generation effect evidence is blocked for review rather than silently reinterpreted.
4. **Service binding.** Normal boot and the internal Mistral acceptance probe run autonomy recovery immediately after canonical turn/effect recovery. Process status exposes only goal counts and architectural readiness metadata, never objective text.

The generic `/goal` path uses `user_ack` as its v1 completion contract because arbitrary natural-language goals do not have one universal machine predicate. This does not force a human click for each intermediate step; it prevents the cognition model from self-certifying arbitrary semantic completion. Goal classes with a real deterministic verifier should use a typed independent completion contract when that verifier is explicitly defined and tested.

## Bounded hook context

Autonomy state enters the existing 9,000-character inline hook envelope as **data, not instructions**. The context carries the live entity generation, own goals, budgets, state and current step. If the envelope becomes large, autonomy content is compacted and then reduced to a minimal representation before ClayVerse fails closed.

The injected truth boundary says explicitly:

- identity text grants no capability;
- a model proposal is not execution;
- effect dispatch is not success;
- model completion is not goal completion;
- unknown is not success;
- cross-user goal injection is not allowed by default.

## Restart law

Persistent goals and stale writers are different concepts. Global generation advance must fence old writers, but it should not erase a safe unfinished objective merely because the process restarted.

Recovery therefore distinguishes execution state:

```text
no current step / finished reason step -> rebind goal generation safely
PROPOSED -> retire proposal as FAILED; goal may be replanned
ADMITTED -> BLOCKED + UNKNOWN_AFTER_RESTART; never auto-replay
prior effect evidence on unfinished goal -> BLOCKED for explicit review
COMPLETED/CANCELLED -> historical, unchanged
```

This preserves causal uncertainty rather than optimizing for apparent continuity.

## Scheduler boundary

This fusion does **not** introduce a second provider loop. The background scheduler remains unactivated until it is fused with the retained provider-generic cognition runtime. The target scheduler remains the existing supervisor/event/re-entry loop:

```text
wake/event
-> load UnifiedDB goal state
-> next_runnable()
-> assemble grounded context
-> retained cognition provider proposes one bounded step
-> deterministic admission
-> EffectGate / observation boundary
-> verified receipt
-> independent completion check
-> state transition / checkpoint / re-entry
```

Provider calls themselves must receive explicit token/time/cost budgets before unattended activation so malformed but ever-changing proposals cannot form an unmetered spend loop outside the current step/effect budgets.

## Research rationale

The mechanism follows the useful architectural implication of ReAct (arXiv:2210.03629): couple reasoning/actions to environmental observations instead of treating a coherent internal trajectory as reality. Reflexion (arXiv:2303.11366) supports feedback/episodic evidence for later attempts but not self-authored truth. PDoctor (arXiv:2404.17833) supports explicit constraint/test oracles outside model self-judgment. AgentHallu (arXiv:2601.06818) shows why long agent trajectories need fine-grained action/receipt boundaries: hallucinations propagate and tool-use attribution is difficult.

Persona/role prompting may alter initiative, style and cost, but it is intentionally kept below deterministic authorization, effect and truth boundaries.

These sources motivate the design; they do not establish ClayVerse runtime PASS.

## Source-defined falsifiers

`tests/test_autonomy_integration.py` defines checks for:

- no implicit goal creation from normal prose;
- exact hook-turn provenance and idempotent `/goal` admission;
- forged/non-hook user turns cannot create goals;
- own-user context does not leak the other user's goal text;
- safe pending goals survive a generation advance;
- unadmitted proposals are retired, not executed, after restart;
- admitted in-flight work becomes explicit UNKNOWN/BLOCKED and is not runnable;
- prior-generation effect evidence is not silently reinterpreted.

These tests are committed source obligations only until actually executed on exact current bytes in an authorized isolated environment.

## Promotion gate

Background autonomous execution must remain disabled until:

- the new integration tests and adjacent canonical autonomy suite execute on exact current UnifiedDB bytes in an authorized isolated checkout;
- hook context behavior is tested against the 9,000-character envelope and prompt-injection cases;
- restart/UNKNOWN and dual-user concurrency behavior is observed;
- scheduler provider calls are fused into the retained provider-generic lane with explicit planner resource budgets;
- autonomous effect evidence is bound to the exact causal episode/request/effect identity, in addition to the current exact target/argv fence;
- the integrated candidate passes exact OCI and required outer microVM acceptance.

Until then the correct label is **SOURCE CANDIDATE**, not runtime-verified autonomous operation and not whole-product PASS.
