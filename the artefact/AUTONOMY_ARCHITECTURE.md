# ClayVerse deterministic autonomy architecture

## Purpose

ClayVerse autonomy is **persistent goal state plus a deterministic bounded control loop**, not a personality trick and not a literal assertion that whichever language model is currently selected is AGI, conscious, sovereign, continuously awake, or able to perform actions outside the admitted runtime.

The useful behavior is operational: preserve owner goals, select unfinished work, let cognition propose bounded steps, admit only typed actions, observe the environment through canonical receipts, retry inside hard budgets, and mark completion only from evidence whose authority is independent of the model's own prose.

## Core law

**Operational autonomy is a state-machine property, not a model self-description.**

```text
CLAIM != EVIDENCE
PROPOSAL != ADMISSION
ADMISSION != EXECUTION
TOOL_DISPATCH != SUCCESS
MODEL_SAYS_DONE != GOAL_COMPLETED
UNKNOWN != SUCCESS
UNKNOWN != FAILURE
FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT
```

Calling the cognition model "frontier AGI", "autonomous", "sovereign" or an "organism" may influence initiative/style, but it grants zero permissions and creates zero facts.

## Authority split

ClayVerse deliberately separates four authorities:

1. **Goal authority** — canonical owner input plus deterministic Goal/Autonomy state.
2. **Cognition authority** — the selected LLM may propose reasoning and a next step.
3. **Effect authority** — EffectGate/EffectJournal decide and record real actions.
4. **Completion authority** — the autonomy controller evaluates an admitted success contract against canonical external evidence or a later explicit owner acknowledgement.

This separation is the anti-hallucination spine. A stronger model can improve proposals without gaining the power to manufacture goal truth.

## One canonical state authority

- one persistent ClayVerse entity;
- UnifiedDB = sole durable canonical state/memory authority;
- selected LLM = replaceable cognition interface, not durable identity;
- ClayGraph = rebuildable projection only;
- EffectGate/EffectJournal = real-action authority;
- no second `consciousness_daemon`, goal database, memory ledger, effect path or identity service.

The controller is `clayverse/autonomy.py`. Autonomy state is stored as canonical JSON under UnifiedDB `meta`; the v2 state includes a fixed operational identity record:

```text
entity_name = ClayVerse
operating_mode = HIGH_AGENCY_GROUNDED
model_authority = PROPOSAL_ONLY
completion_authority = EXTERNAL_EVIDENCE_OR_OWNER_ACK
```

This identity state is an operating contract, not a metaphysical claim. A persisted state whose identity contract is altered fails validation rather than silently redefining the entity.

The earlier v1 autonomy state was source-candidate evidence only and has no accepted product-runtime credit. Before any persistence-bearing runtime promotion, v1/v2 migration or explicit fail-closed replacement must be tested so two autonomy states can never become competing authorities.

## User alignment as code

A durable top-level goal can only be adopted by `create_goal_from_turn(...)` from an existing canonical UnifiedDB turn that belongs to the same canonical user/session and has role `user`.

The goal objective is copied **verbatim** from that stored turn. The planner does not provide or rewrite the objective. This prevents cognition, retrieval or summarization from silently broadening the owner's durable goal.

Stored goal state includes:

- goal id, user/session and global generation;
- canonical source turn id and verbatim objective;
- priority and status;
- typed completion contract;
- hard step/retry/effect budgets;
- current proposed/admitted step;
- independently verified effect evidence ids or explicit owner acknowledgement;
- timestamps and block reason.

Future generated subgoals may exist only as bounded planning artifacts under an already-admitted owner goal; they must not silently become new top-level owner authority.

## State machine

Goal states:

```text
ACTIVE | WAITING | VERIFYING | BLOCKED | COMPLETED | CANCELLED
```

Typical lifecycle:

```text
canonical owner turn
-> adopt goal at live generation
-> ACTIVE
-> claim goal lease
-> cognition proposes one bounded step
-> PROPOSED
-> deterministic admission
-> ADMITTED
-> canonical observed result
   -> SUCCEEDED -> ACTIVE/VERIFYING
   -> FAILED -> bounded retry or BLOCKED
-> independent completion verification
-> COMPLETED | next bounded step | BLOCKED
-> release lease
```

A stale-generation goal or worker is not runnable. `COMPLETED` and `CANCELLED` are terminal.

Step classes remain deliberately small: `reason`, `effect`, `wait`, and `complete_candidate`. A `complete_candidate` is only a hypothesis and can never mark the goal complete by itself.

## Effects: no new execution path

Autonomy adds no execution bypass. Intermediate effect proposals remain limited to the already admitted `state.noop` and `entityos.exec` shapes; generic `process.exec` is rejected.

The real path remains:

```text
step proposal
-> deterministic autonomy admission
-> canonical turn/workspace
-> EffectGate
-> EffectJournal
-> VERIFIED | DENIED | FAILED | UNKNOWN outcome
-> causal re-entry
-> autonomy evidence evaluation
```

A model sentence such as "the command succeeded" is never effect evidence.

## Completion contracts

### `verified_effect`

Automatic completion is intentionally narrower than generic effect success. It requires an **exact pre-admitted success target** and currently accepts only `entityos.exec`, never `state.noop`.

Completion evidence must satisfy all of these at evaluation time:

- effect belongs to the same canonical goal owner;
- effect workspace belongs to the same canonical session;
- goal, session and effect use the same live global generation;
- effect happened after goal adoption;
- capability is exactly the completion capability;
- redacted target SHA-256 equals the goal's pre-admitted completion-target SHA-256;
- EffectJournal status is `VERIFIED`;
- redacted outcome contains `ok == true`;
- a causal episode exists and is marked re-entered.

A successfully executed **different** action is therefore not completion evidence. A synthetic DB row without the canonical workspace/causal spine is not completion evidence. `PENDING`, `DENIED`, `FAILED`, stale, malformed and `UNKNOWN_AFTER_RESTART` are not success.

This first predicate is deliberately conservative. Broader goals whose success cannot be represented by an exact external validator/effect must not be auto-completed from model confidence.

### `user_ack`

Human-confirmed completion requires an actual later persisted `user` turn from the same owner/session. The original goal-source turn cannot acknowledge itself, another user cannot acknowledge it, and an assistant/model turn cannot acknowledge its own work.

New completion modes may be added only after their independent evidence source and falsifiers are defined.

## Runaway-agent containment

Every goal carries hard `max_steps`, `max_retries_per_step`, and `max_effects`. Global maxima bound goal count, state size, objective/step text and effect shapes. `max_effects=0` still permits pure reasoning steps while deterministically denying effect steps.

Budget exhaustion is code, not a prompt suggestion. The model cannot talk the controller into another attempt. This contains the classic loop:

```text
failure -> model changes something -> failure -> model changes something -> ...
```

A generation-bound lease (`autonomy-goal:<goal_id>`) is the scheduler claim primitive. Parallel wake workers must acquire it before driving a goal; a second worker fails to claim the same live goal until the exact lease is released or safely expires.

Before unattended autonomy is enabled, typed wall-clock/inference/token/effect-cost budgets should be added in addition to the existing step/retry/effect bounds.

## Scheduler, not consciousness daemon

`next_runnable()` remains a read-only scheduling view; `claim_next()` is the concurrency-safe worker claim primitive. Continuous work must be driven by the **existing ClayVerse supervisor/event/re-entry loop**, not a second durable mind process:

```text
wake/event/re-entry
-> load canonical autonomy state
-> claim next goal lease
-> assemble canonical world + goal state
-> ask selected cognition provider for one proposal
-> deterministic admission
-> EffectGate if needed
-> persist observed result
-> evaluate completion contract
-> requeue / wait / block / complete
-> checkpoint and re-enter
-> release exact goal claim
```

A trigger may be user input, verified effect result, timer, dependency event or recovery. The trigger is not authority; UnifiedDB state is.

For the normal interactive Claude Code lane, a future bounded continuation may use the managed `Stop` hook, but only with the documented active-stop recursion guard and the same Goal Kernel budgets. Browser disconnect/persistent tmux may preserve an already-running session; an offline provider supervisor may resume admitted work later. Both paths must re-enter the same state/effect authority and must not fork identity.

## Anti-hallucination fences

1. **Goal provenance** — durable objective comes from a canonical owner user turn.
2. **Persisted operational identity** — high agency is state, not an LLM belief claim.
3. **Generation fencing** — restart/global-generation advance invalidates stale work.
4. **Goal leases** — duplicate workers do not own the same runnable goal concurrently.
5. **Canonical JSON** — duplicate keys and non-finite values fail closed.
6. **Capability allowlist** — planner text cannot invent execution rights.
7. **Exact completion binding** — capability alone is insufficient; target/session/causal identity must match.
8. **No-op exclusion** — `state.noop` can never prove an external goal completed.
9. **Completion separation** — model completion hypotheses require independent evidence.
10. **Hard budgets** — no unbounded autonomous repair loop.
11. **Unknown preservation** — unresolved effects/dependencies remain unknown/blocked.
12. **UnifiedDB only** — no hidden model-side autonomy memory.
13. **Identity grants no privilege** — "I am AGI" has no authority effect.

## Runtime cognition contract

`runtime_CLAUDE.md` reinforces these code laws instead of pretending to enforce them. It asks cognition to be proactive and goal-directed, avoid passive boilerplate when a canonical safe next step exists, use only injected canonical state, distinguish proposal/admission/execution/verification, and never claim completion without canonical evidence.

Prompt drift may degrade proposal quality or style. It must not be able to manufacture effect truth, extend budgets, create top-level goals, or set `COMPLETED`.

## Research basis

Primary-source findings motivating this design:

- Anthropic, *Building effective agents*: agent loops should stay simple/composable, use environment feedback and explicit stopping/guardrail conditions rather than adding complexity without measured value — `https://www.anthropic.com/research/building-effective-agents`.
- Anthropic Claude Code hooks documentation: lifecycle hooks provide deterministic control around tool/Stop events; Stop continuations must use the active-stop recursion guard rather than recursively trapping the session — `https://docs.anthropic.com/en/docs/claude-code/hooks`.
- Park & Choi (2026), *When Do Agent Loops Mistake Stagnation for Progress?* (`arXiv:2607.25152`): long-running agents that judge their own work can accept apparent progress while external outcomes stagnate/regress; out-of-band/world-state grounding is structurally important when success lives outside the transcript.
- Ray & Goyal (2026), *Structured Feedback Improves Repair in an LLM Agent Loop* (`arXiv:2607.14167`): a code-controlled loop with external validators controlling acceptance, budgets and traces materially improves bounded repair behavior.
- Hou et al. (2026), *When Agents Do Not Stop* (`arXiv:2607.01641`): ineffective bounds can produce infinite agentic loops that amplify model/tool calls, cost, context and repeated side effects.

These sources motivate the architecture. They do not prove ClayVerse's implementation. Exact source-bound isolated execution remains the empirical authority for product behavior.

## Current implementation/evidence boundary

Current source candidate adds:

- canonical autonomy state inside UnifiedDB;
- persisted `HIGH_AGENCY_GROUNDED` identity contract;
- user-turn-bound top-level goal adoption;
- priority scheduler view plus generation-bound goal lease claims;
- deterministic proposal/admission states;
- step/retry/effect budgets;
- generation fencing;
- capability allowlist;
- exact target/session/causal verified-effect completion;
- explicit later-owner acknowledgement completion;
- malformed/duplicate/non-finite state rejection;
- anti-self-authorization runtime cognition contract.

The committed tests exercise model-self-completion rejection, no-op completion rejection, exact-target mismatch, real TurnLifecycle -> EffectGate -> EffectJournal -> causal receipt completion, synthetic receipt rejection, owner acknowledgement timing, budget bounds, stale generations, duplicate worker claims and checkpoint participation.

The GitHub-hosted PR identity-guard job observed for this fusion lane failed before any step executed (`steps: []`). That is execution-admission failure, **not** a test failure and not runtime credit.

Before promotion/default-on autonomy:

- run the committed focused + adjacent UnifiedDB/effect/recovery tests against exact current branch bytes in an authorized isolated executor;
- settle explicit v1->v2 state migration/fail-closed replacement before any persistence-bearing runtime upgrade;
- inject autonomy context through the existing bounded lifecycle/context path;
- fuse scheduler ticks/Stop continuation/provider resume into the existing supervisor/re-entry path;
- add wall-clock/inference/token/effect-cost budgets;
- adversarially test restart/UNKNOWN effects, duplicate wake, lease expiry/ABA, cancellation during reasoning, two-user concurrency, prompt injection and context-budget behavior;
- carry the integrated implementation through exact OCI and required microVM/runtime acceptance.

This remains **SOURCE CANDIDATE / MECHANISM DESIGNED**, not whole-product PASS.
