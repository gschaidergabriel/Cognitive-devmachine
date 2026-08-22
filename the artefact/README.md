# the artefact — ClayVerse single-container candidate

`the artefact/` is the canonical product workspace for ClayVerse in `gschaidergabriel/clay-global-research-entity/main`.

ClayVerse remains **IN_PROGRESS**. Source coherence, commits, PRs, workflow definitions, deployment READY states and component evidence never imply whole-product PASS.

## Product target

The release target is **one immutable OCI/Docker-compatible ClayVerse image** implementing one persistent central entity with:

- UnifiedDB as sole durable world/state/memory/data/wiki/goal authority;
- Gabriel and Andreas as equal-rights perspectives into the same entity/global generation;
- Clerk-authenticated browser -> WebSocket PTY -> user-bound persistent tmux;
- normal interactive Claude Code as runtime cognition, not durable identity/memory;
- provider-generic bounded API inference as an inference-only alternate path;
- MicroClay adaptive retrieval/accessibility inside the same entity, never truth authority;
- ClayGraph/Hyperposition/Needle/workspace as derived/bounded cognitive coordination structures;
- deterministic autonomous goal pursuit from canonical user goals;
- one explicit TurnLifecycle causal spine;
- one EffectGate/EffectJournal action authority;
- complete accepted EntityOS as internal execution/security/runtime substrate in the final image;
- recoverable persistent state without blind external-effect replay.

Final whole-product acceptance additionally requires the **same exact accepted OCI digest** to execute behind an independent VM/microVM guest-kernel boundary. Direct host-kernel OCI execution is development/supporting evidence only.

There is no second `consciousness_daemon`, `autonomy_daemon`, memory ledger, effect path, identity service or hidden execution brain.

## Canonical machine loop

```text
INGRESS
-> authenticate/normalize/canonicalize in UnifiedDB
-> retrieve bounded current world/state
-> selected cognition proposes reasoning/action
-> model output re-enters ClayVerse as proposal
-> deterministic policy/authority validation
-> exact TurnLifecycle / EffectGate / EntityOS when admitted
-> stdout/stderr/effect outcome
-> EffectJournal + causal re-entry
-> memory/retrieval/goal-state update
-> repeat or EGRESS
```

Model output never self-authorizes execution.

## Deterministic autonomy

Autonomy is an architecture property, not an AGI roleplay claim.

```text
CLAIM != EVIDENCE
PROPOSAL != ADMISSION
ADMISSION != EXECUTION
TOOL_DISPATCH != SUCCESS
MODEL_COMPLETION != GOAL_COMPLETION
UNKNOWN != SUCCESS
UNKNOWN != FAILURE
```

Durable goals originate only from canonical owner `user` turns. The model may propose a next step but cannot silently rewrite the durable objective, mint a capability, declare a tool dispatch successful or mark its own goal complete.

The canonical controller is `clayverse/autonomy.py`. Goal state lives inside UnifiedDB under the existing transaction/WAL/checkpoint authority. Hard limits bound steps, retries and effects.

### Autonomous turn identity

Autonomous work reuses TurnLifecycle and carries exact provenance:

```text
source = clayverse-autonomy:goal-step
goal_id
step_id
turn_id
episode_id
causal_id
entity/session generation
```

Autonomy may not preempt a live human turn. A human may preempt autonomous work.

### Effect safety: two fences

**Before dispatch:** an active autonomous turn may not use generic `request_effect`. It must use `request_autonomy_effect(goal_id, step_id)`. Capability/target/argv are loaded from the already-admitted canonical step; the caller cannot resupply a different intent.

**After outcome:** the controller accepts effect evidence only when exact owner/session/generation, capability, redacted target/argv receipts, workspace episode, observation turn, causal id and autonomous goal/step provenance all match. An identical successful effect from another causal episode is not reusable as proof.

`state.noop` may exercise the effect spine but is non-rewarding and cannot automatically prove real-world goal completion. Automatic verified-effect completion is restricted to independently meaningful admitted capabilities such as `entityos.exec`.

### Human-preemption re-entry

Human priority must not leave an invisible `ADMITTED` autonomy zombie.

The managed prompt hook captures the exact autonomous predecessor before human admission. After canonical preemption:

- no emitted effect -> controller records a normal step failure/retry within existing budget;
- final effect -> exact `record_effect_result` causal re-entry, never replay;
- `PENDING` effect -> hard fence; preemption/reconciliation does not pretend the outcome is known;
- exhausted retry budget -> explicit `BLOCKED` rather than silent deadlock or invented success.

### Recovery

Generation change fences stale writers. Recovery does not blindly replay admitted effects or silently rebind old evidence into a new generation. Ambiguous effects remain blocked/unknown; interrupted no-effect work may be requeued under bounded policy.

### Context

The managed prompt path injects only a bounded, user-scoped autonomy projection marked as data, not instructions, with no truth/effect/completion authority. Autonomy does not widen cross-user retrieval.

See `AUTONOMY_ARCHITECTURE.md` and `AUTONOMOUS_TURN_GATE.md` for the current source contract.

## UnifiedDB / retrieval / learning laws

- UnifiedDB owns durable truth/state/memory/goal/effect/retrieval-learning records.
- ClayGraph is rebuildable projection only.
- MicroClay changes accessibility/routing, never semantic truth, rights or EffectGate policy.
- Adaptive retrieval starts SHADOW; ACTIVE promotion requires held-out/replay evidence and rollback-safe gating.
- Normal model completion is not automatic reward.
- Explicit corrections/misses and verified causal outcomes require typed provenance and idempotent receipts.
- Meta-learning is a required subsystem for reusable methods, but `FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT`.

## Runtime cognition/provider law

Claude Code remains the preferred terminal-native cognition path inside the managed PTY/tmux continuum. Built-in tools/Bash and competing side-memory are disabled by product policy; admitted state/effects come through ClayVerse boundaries.

Token/API providers are inference-only. Provider switching must preserve the same UnifiedDB entity/session/generation and may never create a second state/effect/identity authority. Provider credentials are transient secrets and never become UnifiedDB memory, snapshots, receipts, logs or model-visible context.

## Effect / EntityOS law

Real/state-changing actions use the one explicit EffectGate/EffectJournal path. Generic host `process.exec` remains forbidden.

EntityOS is mandatory inside the final accepted image as the complete accepted internal execution/security/runtime substrate, but it is not the product endpoint. Execution remains gated by exact embedded artifact identity and admitted policy/evidence.

Unknown or ambiguous external outcomes remain unknown. No crash/restart/preemption path may blindly replay an effect merely to preserve continuity.

## Recovery / isolation law

ClayVerse uses one global entity generation across both permanent user sessions. Restart/recovery fences stale writers, reconciles incomplete causal work, rebuilds derived graph state and preserves EffectJournal uncertainty.

The accepted runtime must use read-only image/root semantics with only declared tmpfs/persistent write surfaces. Whole-product PASS requires the exact accepted image behind an independent VM/microVM guest kernel and adversarial recovery/recreation evidence.

## Evidence ladder

```text
SOURCE_INSPECTED
-> STATIC_CONTRACT_PASS
-> FOCUSED_TEST_PASS
-> ADJACENT_REGRESSION_PASS
-> COMPONENT_RUNTIME_PASS
-> MULTICOMPONENT_INTEGRATION_PASS
-> EXACT_OCI_COMPONENT_PASS
-> EXACT_MICROVM_COMPONENT_PASS
-> WHOLE_CLAYVERSE_PASS
```

A higher class is never inferred from a lower one.

## Current autonomy evidence — 2026-08-18 03:05 +07:00

Current `main` has converged multiple non-duplicate autonomy hardenings, including explicit goal adoption, bounded goal context, non-preempting autonomous TurnLifecycle, exact causal effect evidence, pre-dispatch stored-intent enforcement, recovery hardening and human-preemption re-entry.

This GO cycle specifically closed:

1. **pre-execution intent drift** — autonomous turns cannot use generic effect dispatch; the dedicated path executes only the stored admitted intent;
2. **human-preemption ADMITTED-zombie state** — preempted steps are causally reconciled to retry/block/final-effect re-entry rather than silently remaining unrunnable.

Focused regressions now cover wrong goal/step identities, generic-effect denial before dispatch, stored-intent execution, human-turn compatibility, prompt-text impersonation, no-effect human preemption, final-effect preemption without replay, pending-effect fencing and zero-retry explicit blocking.

Two exact-head GitHub-hosted autonomy-guard attempts reached a job object but failed before runner assignment or any visible step:

- run `32066747923`, job `95500527451`;
- run `32067358388`, job `95502469614`.

Both reported `runner_id=0` and `steps=[]`. They provide **zero pytest/runtime credit** and are classified as runner/control-plane admission failures, not ClayVerse semantic test failures.

The private GitHub zipball connector returned no archive bytes, so no unauthenticated or fabricated exact-checkout execution was claimed. VPS/self-hosted/production testing was not used.

## Current frontier

Highest-information next gates are:

1. obtain an actually-started authorized isolated exact-checkout run of the focused autonomy + adjacent lifecycle/recovery suite;
2. fuse a real supervisor wake/pulse onto `next_runnable()` without creating a second daemon or allowing autonomy to preempt human turns;
3. prove effect ambiguity/recovery/preemption under real packaged runtime faults;
4. continue through exact OCI build/digest/start/readiness, Clerk/PTTY/Claude lifecycle, dual-user concurrency and the same-image microVM acceptance vector.

Detailed historical cycle evidence belongs in `the artefact/receipts/` and Git history rather than being duplicated indefinitely in this living README.

## GO delta — 2026-08-21 21:29 +07:00

Current canonical `main` was refreshed at `2b7360bb2682131dfb0121c25c1c03e808033df0` before this bounded repair lane was created.

Adversarial source review found a provenance/authority gap in the autonomous terminal one-shot transport: `consume_dispatch_prompt()` returned `None` not only for ordinary human text but also for malformed, wrong, expired, missing or already-consumed values inside the reserved `__CLAY_AUTONOMY_DISPATCH__:` namespace. The managed `UserPromptSubmit` hook interprets `None` as normal human input. A synthetic autonomy marker could therefore be canonically admitted with human-hook provenance and contaminate the later human-roundtrip attestation used to permit detached autonomy.

The bounded candidate now treats that prefix as a reserved transport namespace:

- ordinary non-prefixed text still follows the normal human path;
- malformed reserved prompts fail closed;
- missing/replayed dispatch leases fail closed;
- wrong nonce fails closed without consuming the valid lease;
- expired leases fail closed;
- existing generation, goal/step and one-shot deletion fences are retained.

Candidate source blobs:

- `clayverse/autonomy_dispatch.py`: `935ed3bec81a634e923fdcbae02667a0adbae9c8`;
- `tests/test_autonomy_dispatch.py`: `f02eb02a726ee42613971cd38998b8a01e187705`.

Evidence class is **SOURCE_CANDIDATE** until exact isolated execution runs the focused dispatch tests plus terminal-hook/autonomy-pulse adjacency. No OCI/microVM/runtime PASS is inferred.

The exact `go` unusual-experiment slot remains `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`: the available trigger identity is minute-precision only and has no immutable shared request/turn id, so zero unusual experiments were executed.

### Updated frontier

1. execute the exact candidate dispatch suite in an authorized isolated full checkout;
2. prove an expired/replayed/malformed synthetic terminal marker cannot create a canonical human turn and cannot satisfy `AutonomyPulse._has_human_roundtrip_after`;
3. after that bounded authority repair is accepted, continue the still-open exact OCI/private-source credential gate and same-digest Firecracker/microVM whole-product vector.
