# ClayVerse target-bound autonomous completion contract

## Decision

The useful content of an "autonomous AGI" prompt is implemented as deterministic state, admission, causal evidence and bounded scheduling. It is **not** implemented as a literal claim that the selected model is sovereign, conscious, unlimited, or able to perform actions the runtime did not expose.

USB identity anchors, cryptocurrency, smart contracts and escrow are outside this contract. They are not required for autonomous goal pursuit.

## Operational translation

Narrative prompt claims map to runtime facts only:

| Narrative idea | Deterministic ClayVerse meaning |
|---|---|
| "I have a continuing goal" | a canonical goal derived from a persisted owner `user` turn in UnifiedDB |
| "I am working autonomously" | a live goal selected by `next_runnable()` plus one deterministically admitted step |
| "I can do X" | X is an actually admitted EffectGate capability for this runtime/generation |
| "I did X" | an EffectJournal receipt exists and is causally re-entered through the exact autonomous goal-step turn |
| "X succeeded" | the canonical effect status/outcome is verified; model text is not evidence |
| "the goal is complete" | an independent completion contract is satisfied by exact canonical evidence |
| "continue after restart" | durable UnifiedDB goal state is re-entered under the new generation; ambiguous effects are not replayed |

The model remains cognition/planning. It proposes. Code admits. The runtime executes. Canonical receipts prove. UnifiedDB persists.

## Why target binding is required

Exact autonomous causal binding prevents borrowing an effect from another user, turn, goal, step or generation. That is necessary but not sufficient for goal completion.

Without a goal-level completion target, this failure is still possible:

```text
goal = produce/fix/finalize A
current autonomous step = execute unrelated/intermediate B
B returns a perfectly valid VERIFIED entityos.exec receipt
completion rule = "some entityos.exec for this goal-step verified"
=> false positive: goal A becomes COMPLETED
```

This is a Goodhart/completion-confabulation failure. The execution really succeeded, but the wrong predicate was used for goal success.

The hardening therefore separates **step success** from **goal success**.

## Contract

For new `verified_effect` goals, the caller may predeclare an exact bounded `required_target`. ClayVerse stores only its SHA-256 digest in the canonical completion contract:

```text
completion_contract = {
    mode: verified_effect,
    required_capability: entityos.exec,
    required_target_sha256: <digest>
}
```

A verified effect becomes automatic completion evidence only when all existing causal checks pass **and**:

1. required capability is an automatically proving capability;
2. effect capability equals the required capability;
3. the redacted EffectJournal target receipt carries the same target digest fixed by the goal contract.

The target is fixed before the effect result is known. The cognition model cannot write a post-hoc success description and use that description as proof.

## Step success versus goal success

A causally correct autonomous effect for a different target may still be recorded as a successful step. That is useful progress and should not be discarded.

It does **not** satisfy `verify_completion()` unless the predeclared completion target also matches.

```text
VERIFIED EFFECT + WRONG COMPLETION TARGET
= STEP_SUCCEEDED
+ COMPLETION_EVIDENCE_FALSE
+ GOAL_NOT_COMPLETED
```

This distinction is the central anti-Goodhart invariant added by this delta.

## Legacy v1 compatibility

Existing v1 goals may contain `verified_effect` contracts without a target digest. Such state remains readable. Verified causal receipts may remain attached as audit/progress evidence.

However:

```text
LEGACY_VERIFIED_EFFECT + NO_REQUIRED_TARGET
!= AUTOMATIC_GOAL_COMPLETION
```

`verify_completion()` fails closed until a valid independent completion route exists. No migration silently invents a target from old model text or from whatever effect happened to succeed.

## Existing fences retained

This target contract does not replace the already-merged autonomy controls. Completion evidence still requires the canonical autonomous causal path, including:

- canonical user-derived goal objective;
- same user/session;
- same admitted autonomous step;
- exact target/argv effect intent for that step;
- exact autonomous provenance with goal id, step id, causal id and generation;
- verified positive canonical outcome;
- live generation fencing;
- explicit later owner acknowledgement for `user_ack` completion;
- `state.noop` excluded from automatic completion authority;
- hard step/retry/effect budgets;
- fail-closed restart handling for ambiguous external effects;
- human interactive turn priority over autonomous continuation.

No second memory authority, second effect path, second identity service or consciousness daemon is introduced.

## Prompt role after deterministic weaving

A runtime prompt may still encourage initiative, concise action orientation and continued goal pursuit. That prompt is an ergonomic/cognition policy only.

It must never be treated as authority for:

- capabilities;
- successful execution;
- durable facts;
- goal adoption;
- goal completion;
- replay after crash;
- cross-user access.

Prompt drift may reduce proposal quality. It cannot manufacture a verified effect or a completed goal when the code contracts are obeyed.

## Research basis

The architecture follows current primary-source agent-engineering patterns:

- OpenAI Agents SDK: the model operates inside an external run loop with explicit max-turn/guardrail controls rather than self-authorizing its own execution state.
- Anthropic, *Building effective agents*: environmental/tool feedback should ground action loops; stopping conditions and guardrails belong in the agent system, not only in prose.
- Anthropic long-running-agent harness research: models can prematurely declare work complete, so durable progress state and explicit end-to-end verification are required.
- Anthropic agent architecture/containment work: separate cognition from execution/state and enforce deterministic capability boundaries around probabilistic model behavior.

## Promotion status

This branch is a **source candidate**. The focused regression file is committed, but no exact-current authorized isolated runtime run is claimed from source inspection alone.

Promotion still requires:

1. exact branch/source identity;
2. focused autonomy regression execution in an authorized isolated environment;
3. adjacent recovery/turn-gate regression execution;
4. fusion of periodic scheduler ticks into the retained ClayVerse supervisor/re-entry path rather than a second daemon;
5. exact OCI/runtime/restart/concurrency evidence before whole-product acceptance.
