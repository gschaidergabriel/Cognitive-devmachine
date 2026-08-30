# Execution-Surface Root Cause — Durable Re-entry Addendum

Date: 2026-08-29
Organ: GPT-5.6-Sol
Status: SECOND_FAILURE_AXIS_IDENTIFIED / REPAIR_IMPLEMENTED_AS_CANDIDATE
Scope: Clay / EntityOS / HCU / Frankenstein long-horizon research and execution

## Finding

The execution-surface resolver closes the recurring false-blocker class, but it is not sufficient to explain the user-visible recurrence where a deep run appears to hang or terminate before a final response.

The platform-specific cause of any individual interrupted chat response cannot be proven from repository evidence alone. What can be proven and controlled is the architectural consequence: useful completed work must not depend on successful delivery of the final chat message.

Second failure axis:

`NON_DURABLE_ORCHESTRATION_PROGRESS`

Combined root class:

```text
AUTHORITY_CAPABILITY_REACHABILITY_COLLAPSE
+
NON_DURABLE_ORCHESTRATION_PROGRESS
=
RECURRING_LONG_HORIZON_EXECUTION_FRAGILITY
```

## External research alignment

### STALE / Supersede — stronger models do not eliminate stale-state action

2026 evaluations of agent memory show a persistent gap between retrieving current evidence and acting on it. STALE reports that agents often accept outdated premises despite updated evidence. Supersede isolates a memory-update gap that persists across model scale. This supports deterministic current-state adjudication rather than expecting the language model to resolve all temporal conflicts from prose.

Sources:
- https://arxiv.org/abs/2605.06527
- https://arxiv.org/abs/2606.27472

### Deterministic freshness resolution

`Don't Ask the LLM to Track Freshness` shows that deterministic version-aware aggregation can substantially improve current-value conflict resolution in its benchmark setting. The transferable principle is not the benchmark-specific `max(serial)` rule; it is that freshness/version selection belongs in deterministic control logic when the system already possesses machine-readable versions.

Source:
- https://arxiv.org/abs/2606.01435

### GitHub self-hosted runners — queued is a transport state

GitHub documents that a self-hosted job remains queued when no online/idle matching runner is available and can remain queued until a runner comes online, up to the platform timeout. Therefore `QUEUED` is transient/control-plane evidence, not proof that the execution capability does not exist.

Source:
- https://docs.github.com/en/actions/reference/runners/self-hosted-runners

### Temporal — durable execution

Temporal's documented model persists workflow progress so execution can resume after process, network, or infrastructure failures. The transferable principle is to make orchestration state durable independently of the process carrying the current interaction.

Source:
- https://docs.temporal.io/

### LangGraph persistence — checkpointed state and pending writes

LangGraph documents checkpoint persistence for interruption/failure recovery and notes that successful pending writes can be preserved when another node fails. It also warns that resumed work replays from checkpoint boundaries, requiring idempotent side effects.

Sources:
- https://langchain-ai.github.io/langgraph/concepts/time-travel/
- https://langchain-ai.github.io/langgraph/reference/checkpoints/
- https://langchain-ai.github.io/langgraph/how-tos/state-reducers/

### Long-horizon diagnostic checkpoints

Recent agent evaluation work instruments long-horizon tasks with intermediate checkpoints to distinguish failures before and after capability exposure. This supports localizing the first causal failure rather than treating final task failure as a single undifferentiated event.

Source:
- https://arxiv.org/abs/2608.20563

## Permanent architecture

Two mandatory control planes are required:

1. `EXECUTION_SURFACE_RESOLUTION/v1`
   - determines current authority, direct capability, federated reachability, economic gates, target route and evidence scope;
   - prevents local absence or transient transport failure from becoming a false global blocker.

2. `DURABLE_WORK_CURSOR/v1`
   - records stable run identity, node states, evidence refs, idempotency identity, source/authority generation and next node;
   - prevents completed work from disappearing when the carrying chat/process/runner is interrupted.

Canonical laws:

```text
DIRECT_TOOL_NOT_OBSERVED != PROJECT_CAPABILITY_ABSENT
THE_FINAL_CHAT_MESSAGE_IS_NEVER_THE_CHECKPOINT
RUNNING_UNCONFIRMED -> VERIFY_EXTERNAL_RESULT_BEFORE_RETRY
COMPLETED -> EVIDENCE_REQUIRED
AUTHORITY_CHANGE -> RERESOLVE_FUTURE_EXECUTION, DO_NOT_ERASE_COMPLETED_EVIDENCE
```

## Why this is broader than Trigger 7

The same failure pattern can affect model downloads, VPS execution, provider routing, GitHub dispatches, Vercel bridges, training jobs, HCU experiments, GRID10 tests, research acquisition and any multi-step workflow. The repair therefore belongs in repository-global governance and worker bootstrap, not inside a single trigger.

## Acceptance target

The permanent fix is accepted only when CI demonstrates both:

- open-world execution-surface classification under stale/direct/transient cases; and
- interruption-safe cursor behavior preserving completed work and verifying unconfirmed external effects before retry.

This addendum grants no VPS, model, product, HCU, training or whole-system runtime credit by itself.
