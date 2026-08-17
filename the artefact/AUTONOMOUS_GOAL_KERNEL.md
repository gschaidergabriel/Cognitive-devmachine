# Autonomous Goal Kernel — deterministic high-agency architecture

**Status:** SOURCE CANDIDATE / NOT RUNTIME-ACCEPTED  
**Scope:** autonomous goal pursuit inside the one ClayVerse entity, without a second identity/state/effect authority.

## 1. Design translation

The useful part of an "AGI identity" prompt is not the literal claim that a model is a sovereign organism. The useful part is the intended behavior: persistent identity, durable goals, proactive continuation, causal continuity, economic/resource discipline and reduced passive-assistant drift.

ClayVerse implements those properties as **state + control logic + evidence gates** instead of asking a model to believe them.

Narrative statement -> deterministic mechanism:

- "persistent identity" -> typed `entity_profile` in canonical UnifiedDB;
- "ongoing historical state" -> UnifiedDB turns/memory/effects/checkpoints plus goal/cycle state;
- "aligned goals" -> top-level goals admitted only from persisted human user turns;
- "autonomy" -> bounded goal claims/cycles that can be driven repeatedly by the one ClayVerse runtime;
- "proactive maker role" -> `HIGH_AGENCY_GROUNDED` cognition contract plus explicit next-step cycles;
- "causal continuity" -> global generation, leases, causal/effect receipts and goal evidence;
- "economic discipline" -> hard cycle/failure budgets now; explicit token/time/effect budgets are the next typed extension;
- "completion" -> deterministic success contract, never model self-verdict.

No architecture depends on a claim that the model is conscious, alive, AGI, sovereign, continuously aware, or physically capable of actions absent from the admitted effect path.

## 2. Anti-hallucination authority split

Four authorities are deliberately separate:

1. **Goal authority:** canonical human input and Goal Kernel state.
2. **Cognition authority:** selected LLM may propose reasoning/next action.
3. **Effect authority:** EffectGate/EntityOS decides whether a proposed real action is admitted and records the result.
4. **Completion authority:** Goal Kernel evaluates typed canonical evidence against a pre-admitted success contract.

Core invariant:

`MODEL_SAYS_DONE != GOAL_COMPLETED`

For the first automatic contract:

`GOAL_COMPLETED := exact target-bound entityos.exec effect is VERIFIED + same user/session/global generation + positive redacted receipt + causal re-entry`

If that predicate cannot express the real success condition, the goal remains active/blocked or requires explicit human confirmation. ClayVerse does not substitute model confidence for missing world-state evidence.

## 3. Persistent state

`clayverse/autonomy.py` adds schema within the existing UnifiedDB connection:

- `entity_profile`: stable ClayVerse operational identity/mission/mode;
- `goals`: owner/session/source turn, exact objective, success contract, priority, status and hard budgets;
- `goal_cycles`: generation-fenced bounded attempts, proposal digest, effect/evidence and terminal state;
- `goal_confirmations`: explicit human completion evidence for goals without an automatic predicate;
- `meta.autonomy_state_hash`: digest of the autonomy tables folded into the existing canonical checkpoint payload.

This is not a second database. ClayGraph remains derived, and model/provider state remains non-canonical.

## 4. Goal admission

A top-level goal can be created only from an existing canonical `role=user` turn. The goal objective is copied exactly from the turn. This prevents a model, retriever, summarizer or background worker from silently inventing a new owner goal or rewriting its semantics.

Later product UX may provide a typed "run autonomously" control that binds the current user turn to a success contract/budget. Natural-language goal classification may propose a candidate, but promotion to top-level goal authority must remain tied to an explicit user action or an already-admitted deterministic policy.

Subgoals may eventually be generated as bounded planning artifacts under one owner goal, but they must not gain independent top-level authority.

## 5. Bounded autonomous cycle

Target control flow:

1. choose highest-priority runnable goal;
2. acquire `goal:<goal_id>` lease;
3. verify session generation equals global entity generation;
4. atomically increment `cycle_count` and persist a RUNNING goal cycle;
5. assemble canonical context and Goal Kernel snapshot;
6. selected LLM proposes one next step;
7. persist proposal digest/summary as `proposal`, never evidence;
8. if a real action is needed, send it through the existing canonical effect path;
9. re-ingest verified/denied/failed result;
10. evaluate the success contract from canonical evidence;
11. if satisfied -> `COMPLETED`;
12. if not satisfied and budget remains -> next cycle;
13. if cycle/failure budget is exhausted -> `BLOCKED`;
14. release claim/lease.

A wake mechanism may later drive this loop after browser disconnect, but it must call this same kernel and existing provider/effect boundaries. It may not create a hidden "second Clay" or separate consciousness/state daemon.

## 6. Stop / retry / runaway controls

Current source candidate already hard-codes:

- `max_cycles` per goal;
- `max_failures` per goal;
- per-goal lease TTL bounded to <= 300 seconds;
- global-generation fencing;
- exact success contract;
- terminal `BLOCKED` on budget exhaustion;
- no automatic completion from `state.noop`;
- no generic host `process.exec` path;
- no model route to mutate budgets/status through the kernel.

Next extension should add typed `max_elapsed_seconds`, `max_inference_calls`, `max_effects`, and monetary/token budgets before any default-on unattended scheduler is admitted.

## 7. Runtime integration sequence

Do not jump directly from this state kernel to an always-on free-running loop.

Promotion sequence:

### Phase A — state/evidence kernel (this candidate)

- schema/state identity;
- exact user-owned goals;
- leases/generation;
- hard cycle/failure budgets;
- proposal-is-not-evidence invariant;
- verified-effect/human confirmation completion.

### Phase B — interactive continuation

Use the managed Claude lifecycle to continue one admitted goal across bounded reasoning/effect cycles. Claude Code `Stop` can be used only with explicit loop guards and the documented active-stop recursion guard. The canonical turn/effect identity must remain intact.

### Phase C — unattended wake/resume

When the interactive model/session is absent, the one ClayVerse supervisor may select an admitted provider adapter and resume a runnable goal. Provider output remains proposal-only and must re-enter UnifiedDB before effects. The wake mechanism is orchestration, not identity or state authority.

### Phase D — recovery/concurrency acceptance

Prove restart, stale worker, duplicate wake, lease expiry, ambiguous effect, provider timeout, model stagnation, user pause/cancel, two-user concurrency and resource-budget behavior on exact accepted runtime bytes.

Only after these gates may unattended autonomy become default-on for admitted goals.

## 8. Research basis

The design follows a consistent result across current primary sources:

- Anthropic's agent guidance recommends simple composable agent loops with environmental feedback, explicit stop conditions and guardrails rather than unnecessary complexity: `https://www.anthropic.com/research/building-effective-agents`.
- Claude Code hooks provide deterministic lifecycle interception; Stop hooks explicitly require recursion/active-stop guards: `https://docs.anthropic.com/en/docs/claude-code/hooks`.
- Park & Choi (2026), *When Do Agent Loops Mistake Stagnation for Progress?*, reports a "progress mirage" when long-running agents grade themselves and shows that externally grounded/world-state verification is structurally different from stronger in-band self-judging: `https://arxiv.org/abs/2607.25152`.
- Ray & Goyal (2026), *Structured Feedback Improves Repair in an LLM Agent Loop*, uses a code-controlled loop where external validators control acceptance, budgets and traces: `https://arxiv.org/abs/2607.14167`.
- Hou et al. (2026), *When Agents Do Not Stop*, documents infinite agentic-loop failure paths that can amplify model/tool calls, cost, context growth and repeated side effects, motivating effective hard bounds: `https://arxiv.org/abs/2607.01641`.

These sources do not prove ClayVerse's implementation. They motivate the architecture. Product claims still require exact source-bound isolated execution.

## 9. Adversarial falsifiers

`tests/test_autonomous_goal_kernel.py` is designed to reject at least these failure worlds:

- assistant/system text mints a goal;
- model says "done" and completion follows without evidence;
- `state.noop` is treated as proof of external success;
- invented effect id completes a goal;
- stale global generation continues a claimed cycle;
- wrong user confirms another user's goal;
- cycle/failure budget exhaustion keeps retrying;
- autonomy state changes without affecting canonical checkpoint identity;
- an effect from the wrong target/session/generation satisfies an automatic contract.

Additional required integration falsifiers before activation:

- two workers claim the same goal after lease expiry/ABA;
- restart while a cycle is RUNNING;
- verified effect arrives after generation advance;
- model repeatedly proposes no-op/text-only progress;
- Stop-hook recursion/infinite continuation;
- provider timeout/partial response;
- user pauses/cancels while a worker is reasoning;
- effect becomes `UNKNOWN_AFTER_RESTART` and is not mistaken for success;
- goal completion depends on an external success signal that the contract cannot observe.

## 10. Current evidence boundary

This document and source branch establish an architecture/source candidate only. No claim is made that the new goal kernel has executed inside the exact accepted OCI/microVM product path. The current next discriminator is exact isolated execution of the new focused tests plus adjacent UnifiedDB/effect/recovery/concurrency regressions, followed by controlled integration with the managed Claude lifecycle/provider supervisor.
