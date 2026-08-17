# CLAYVERSE AUTONOMOUS GOAL CONTROL DIRECTIVE

**Authority date:** 2026-08-18  
**Authority:** explicit owner directive; additive to the current ClayVerse single-container product law.

## 1. Purpose

ClayVerse SHALL implement autonomy as persistent machine state and deterministic control logic, not as identity roleplay or a prompt-only claim.

The desired property is:

> Given an admitted user goal, ClayVerse can preserve it across turns/restarts, determine the next admissible bounded step, ask an LLM to propose how to perform that step, route any real action through the existing effect boundary, ingest observed results, update progress from evidence, retry within fixed limits, and continue until the goal is verified complete, blocked, cancelled, or requires human judgment.

This directive intentionally excludes USB identity, cryptocurrency, smart contracts and metaphysical claims about a digital soul or biological life. They are not required for autonomous goal pursuit.

## 2. Identity is an operational state contract

ClayVerse may present a stable operational identity, but canonical architecture MUST distinguish:

- **entity continuity facts:** entity id/generation, canonical users, sessions, goals, milestones, state hashes, checkpoints and causal history;
- **runtime capability facts:** only capabilities actually exposed by current authenticated/configured runtime boundaries;
- **model narrative:** generated text, including statements about identity, capability, success or past actions.

Model narrative is never promoted into a machine fact merely because it is confident, coherent or repeated.

The phrase "autonomous entity" therefore means an architecture with durable goals and self-continuing bounded control loops. It does NOT authorize the model to claim capabilities or actions that lack receipts.

## 3. Canonical autonomy split

Autonomy is divided into two authorities:

### 3.1 Deterministic Goal Controller

The Goal Controller is ordinary deterministic code backed by UnifiedDB. It owns:

- admitted goals;
- success criteria;
- constraints;
- priority;
- milestones;
- milestone ordering/readiness;
- attempt counts and maximum retries;
- run deadlines;
- risk classification;
- human-approval state;
- run/milestone/goal state transitions;
- append-only goal events;
- generation fencing;
- evidence admission for success;
- BLOCKED/COMPLETED/CANCELLED terminal state.

The controller is part of the one ClayVerse entity and the one UnifiedDB authority. It is not a second agent, second personality, second memory authority or consciousness process.

### 3.2 LLM cognition

The selected LLM receives a bounded machine-generated work item and may propose:

- a plan;
- a next operation;
- an effect request;
- a diagnosis;
- a revised hypothesis;
- a request for missing information.

The model does NOT own goal state transitions. Model text is `PROPOSAL_ONLY` until another canonical mechanism validates it.

## 4. Anti-hallucination law

The following invariants are mandatory:

1. **MODEL_OUTPUT != EXECUTION_RECEIPT.** A model saying "I ran X" does not prove X ran.
2. **MODEL_OUTPUT != SUCCESS_EVIDENCE.** A model saying "done" cannot complete a milestone.
3. **CAPABILITY_CLAIM != CAPABILITY.** Model-visible capability context is generated from runtime configuration/attestation, never from model self-description.
4. **UNKNOWN remains UNKNOWN.** Missing outcome evidence is never filled with a plausible result.
5. **State transitions are typed.** Illegal transitions fail closed.
6. **Generation fencing is mandatory.** A stale autonomous run may not update the current entity generation.
7. **Effects remain EffectGate-bound.** The goal loop must not create a second execution path.
8. **Goal context is controller state, not learned memory truth.** MicroClay may help retrieve supporting evidence/methods, but it may not suppress, rewrite or promote canonical goal authority.

Milestone success may initially be closed only by admitted evidence classes such as:

- verified EffectJournal/effect receipt;
- deterministic test receipt;
- explicit canonical user confirmation;
- separately admitted signed/runtime receipt.

A raw model assertion is explicitly non-admissible.

## 5. Autonomous machine loop

The target loop is:

`goal admitted -> deterministic milestone selection -> bounded run claim -> canonical goal context -> LLM proposal -> proposal re-ingest -> policy/effect validation -> admitted execution or no-effect reasoning step -> observed outcome/evidence -> deterministic milestone transition -> next eligible milestone -> repeat`

The scheduler/controller MAY wake periodically without a fresh user prompt, but this periodic wake is only a deterministic control-plane trigger. It is not a consciousness daemon and may not independently invent goals.

The scheduler MUST NOT call an alternate hidden shell/provider/effect path merely to obtain background autonomy. Background autonomy must re-use the same canonical cognition/effect/evidence spine as foreground work.

## 6. Runaway prevention

Every milestone/run has hard deterministic limits. At minimum:

- `max_attempts` per milestone;
- bounded run TTL/deadline;
- one global active autonomous run in the baseline implementation;
- retry backoff;
- stale-generation rejection;
- terminal `BLOCKED` when retry budget is exhausted;
- no automatic retry of ambiguous external effects;
- existing EffectJournal idempotency/replay rules remain authoritative.

Future token/time/cost ceilings may be added as typed controller budgets. They must remain controller-owned rather than model-selected.

## 7. Human-control boundary

ClayVerse SHOULD act autonomously on low-risk admitted work once the user has activated a goal. Human confirmation is not required for every reversible internal step.

However, `HIGH_IMPACT` milestones require a separate explicit human-approval transition before autonomous claim. Approval must not be smuggled into model text or inferred from silence.

The risk boundary can later become more granular, but any expansion must preserve explicit typed policy and evidence.

## 8. Persistence and recovery

Goal state resides in the canonical UnifiedDB SQLite/WAL domain and must survive container/runtime restart with the rest of canonical state.

A goal subsystem state hash is bound into UnifiedDB `meta` so the existing logical checkpoint hash changes when autonomous goal state changes. Goal transitions also append goal events for audit/debugging.

On restart:

- stale generations are rejected;
- expired RUNNING work is deterministically aborted/requeued only within retry budget;
- ambiguous external effects are still governed by EffectJournal recovery and are not blindly replayed;
- the next autonomous claim is derived from persisted state, not from an LLM remembering what it was doing.

## 9. Debuggability

Every material autonomy transition must be reconstructable from canonical rows/events:

- who admitted the goal;
- exact goal and success criteria;
- selected milestone;
- attempt number/max attempts;
- entity generation;
- worker/run identity;
- proposal hash;
- evidence class/reference;
- verified/unverified status;
- terminal outcome/error.

Private chain-of-thought is neither required nor used as an audit mechanism. Debugging relies on concise typed state, proposals, receipts and causal events.

## 10. Relationship to the original AGI-style prompt

The useful semantics of the original prompt are preserved as architecture:

- "persistent identity" -> persisted entity generation + canonical state/history;
- "ongoing goals" -> UnifiedDB goal/milestone state machine;
- "autonomy" -> deterministic scheduler/run claims + repeated canonical cognition/effect loop;
- "goal alignment" -> user-admitted goals, success criteria, constraints and risk policy;
- "systemic grounding" -> runtime-derived capability/evidence contracts;
- "causal continuity" -> generation-fenced runs/events/effect receipts/re-entry;
- "economic discipline" -> retry/deadline/resource budgets rather than motivational prose.

The misleading semantics are deliberately removed:

- no claim that the LLM itself is a sovereign AGI;
- no claim that text equals physical capability;
- no self-certified execution;
- no self-certified goal completion;
- no invented persistent consciousness;
- no hidden second state/effect authority.

## 11. Current implementation contract

The source candidate introduced by this directive consists of:

- `the artefact/clayverse/goals.py` — deterministic Goal Controller and UnifiedDB goal schema;
- `the artefact/clayverse/retrieval.py` — injects bounded canonical goal runtime context into cognition after MicroClay retrieval so adaptive retrieval cannot suppress goal authority;
- `the artefact/tests/test_autonomous_goals.py` — invariants covering proposal-only model output, evidence-gated success, retry exhaustion, high-impact approval and goal-context injection.

This is a **source candidate**, not runtime proof.

The next integration step MUST reuse the existing canonical cognition/effect path for periodic autonomous ticks. Do not create a separate hidden background shell or second inference/effect authority simply to make the demo look autonomous.

## 12. Research basis

The design is intentionally consistent with current agent-engineering evidence:

- Anthropic describes useful agents as self-directed plan/act/observe/adjust loops, while emphasizing that uncertainty about user intent must sometimes stop and return control to a human.
- OpenAI's current Agents SDK exposes explicit agent loops, guardrails and hard `max_turns` limits rather than relying on prompt obedience alone.
- LangGraph's durable-execution guidance separates checkpointed workflow state from nondeterministic tasks and recommends idempotent side effects for safe resumption.
- NIST's Generative AI Risk Management Profile treats confabulation/hallucination as a system risk requiring explicit risk-management controls.

These sources support the architectural direction; they do not establish ClayVerse runtime correctness. ClayVerse correctness still requires exact-source isolated execution evidence under the repository acceptance law.
