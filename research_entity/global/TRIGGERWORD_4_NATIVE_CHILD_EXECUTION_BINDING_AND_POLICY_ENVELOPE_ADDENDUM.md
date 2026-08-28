# TRIGGERWORT 4 — Native Child Execution Binding + Policy Envelope Addendum

Status: MANDATORY STAGE-1 / R2 EXECUTION CONTRACT
Date: 2026-08-28

This addendum ingests the latest Triggerword-5 native-subagent forensic deltas and refines the existing native delegation law. It does not create a new agent runtime.

## 1. New source-backed distinction

The current donor proves durable delegated-work intent via `entityos_arbeitspaket`/`handoff`, but this does not prove that a native child was actually spawned or that the child's later tool/effect/result events are attributable to that workpackage.

Required law:

```text
WORKPACKAGE_EXISTS != CHILD_SPAWNED
SESSION_ID != CHILD_ACTOR_ID
AGENT_ID != TOOL_INVOCATION_ID
DOCUMENTED_PLATFORM_ABI != INSTALLED_RUNTIME_PROOF
CHILD_OUTPUT != CANONICAL_COMPLETION
```

Triggerword 4 must preserve the existing handoff/workpackage idea and add an explicit execution-binding layer before R2/native-child runtime credit.

## 2. WorkExecutionBinding

A first-class `WorkExecutionBinding` joins durable GRID/UnifiedDB work identity to the actually observed runtime actor.

Minimum target fields:

```text
workpackage_id
parent_session_id
parent_agent_id?
agent_id
task_id?
generation
runtime_build_id
spawn_mechanism
agent_type?
isolation_mode
source_sha_or_capsule_digest
started_at
stopped_at_or_state
resume_generation?
```

For every tool invocation inside a delegated child, additionally bind:

```text
workpackage_id
agent_id
generation
tool_use_id or exact invocation equivalent
tool_name
pre_event_digest
effect_or_operation_id if any
post_event_digest or typed failure
```

The exact per-invocation identity, not a mutable session-wide pointer, is the correlation key for mutating calls.

## 3. Binding sequence

Target sequence:

```text
persist workpackage/capsule
 -> admit delegated task
 -> request native child through installed host-supported path
 -> observe SubagentStart or equivalent runtime actor identity
 -> atomically bind current workpackage generation to agent_id
 -> observe task_id when the native runtime exposes task lifecycle
 -> bind every tool call by exact invocation identity
 -> run deterministic pre-side-effect EffectDecision where mutation is possible
 -> consume decision once
 -> bind execution/failure receipt to the same invocation
 -> observe child terminal state
 -> reconcile only from structured evidence
 -> CompletionGate
 -> UnifiedDB/GRID outcome re-entry
```

If no child lifecycle identity is observed, the workpackage remains `NOT_SPAWNED` or `UNBOUND`; existence of a handoff row is not delegated-execution evidence.

## 4. Native platform preference, installed-runtime proof required

Current Claude Code documentation exposes promising primitives such as native subagent IDs, task IDs, tool-use IDs, resumable agents and optional worktree isolation. Triggerword 4 should prefer the installed native path if it actually exposes sufficient identity and lifecycle evidence.

However:

```text
OFFICIAL_DOCS != TARGET_HOST_RUNTIME
```

Before freezing the R2 interface, Triggerword 4 must use the authorized host/VPS route to capture one harmless exact installed-runtime lifecycle and pin:

- installed Claude Code version/build;
- relevant loaded settings/hook provenance;
- actual spawn mechanism;
- child actor identity;
- task identity where present;
- exact tool invocation identity;
- start/stop/resume behavior;
- working-tree/isolation behavior where enabled.

Only if the native runtime is executably insufficient should a bounded custom wrapper be introduced.

## 5. ChildPolicyEnvelope

The latest Triggerword-5 source forensics identified a second boundary: current voice/delegated child paths can forward mutable execution policy such as `permission-mode`, tool denial and cwd/settings behavior without binding the effective policy as immutable workpackage evidence.

Frankenstein 2.0 therefore requires a typed `ChildPolicyEnvelope` bound to the admitted workpackage and observed child actor.

Minimum target fields:

```text
workpackage_id
task_admission_id
human_intent_decision_id?
parent_session_or_agent_id
agent_id
task_id?
generation
permission_mode
allowed_tools_or_capability_set_digest
disallowed_tools_digest
cwd_or_project_root_identity
settings_artifact_identity_or_explicit_none
host_or_managed_policy_generation
policy_version
envelope_digest
```

This envelope records effective execution policy. It is not EffectGate authority and cannot self-grant capabilities.

## 6. Three distinct decision boundaries

Do not collapse these:

```text
HumanIntentDecision
TaskAdmission
ChildPolicyEnvelope
EffectDecision
CompletionDecision
```

A user confirming a voice task means the human intended the task. It does not prove that every later child mutation is authorized.

A child running with a permissive `permission-mode` does not create effect authority.

A hard `Bash` denial is useful defense-in-depth but is not proof of complete child containment because other mutating capability classes may exist.

## 7. Effect interlock

The Native Child binding must be joined to the Stage-1 effect successor:

```text
EffectRequest
 -> AdmissionDecision
 -> deterministic pre-side-effect EnforcementReceipt
 -> Execution/SubmissionReceipt
 -> WorldEffectVerification
 -> ResultReentry
 -> CompletionEvidence
```

Required invariant:

```text
DENY -> PROVE NON-EXECUTION
SUBMITTED -> cannot later be relabeled CANCELLED
UNKNOWN WORLD OUTCOME -> completion remains open
FAILED/DENIED/UNKNOWN/STALE -> cannot satisfy completion
```

## 8. Worktree/parallelism law

Optional native worktree isolation is a useful containment primitive, not authority.

Parallel native children are permitted only with observable actor/workpackage/generation/invocation lineage. Advisory file leases remain hints unless backed by executable ownership/collision enforcement.

A required adversarial test reproduces the historical class where one parallel fixer accidentally incorporated another worker's in-progress change. The 2.0 successor must detect or prevent cross-workpackage evidence/edit transplantation without globally disabling parallelism.

## 9. World-model capability binding

If a delegated child receives a GRID-compiled WorldSlice or related capability, provenance must bind it to:

```text
cycle_id
workpackage_id
agent_id
generation
scope
capability_generation/TTL
```

Children never receive unrestricted World Substrate access and cannot replay an ambiguous capability across parallel workpackages.

## 10. Required Triggerword-4 executable gates

### NCX-01 — Installed native lifecycle
One harmless workpackage -> native child -> observed actor/task/tool lifecycle -> terminal result. Pin exact runtime build/settings provenance.

### NCX-02 — Workpackage binding
A workpackage without observed child remains unbound. A child start binds exactly one current workpackage generation.

### NCX-03 — Interleaving
Two same-session children run interleaved tool calls A/B; pre/post/effect/result lineage remains distinct by invocation identity.

### NCX-04 — Stale generation
Replace/resume a child; stale generation cannot later commit or satisfy completion.

### NCX-05 — Policy envelope
Attest the effective child permission/tool/cwd/settings envelope and bind its digest to task admission and child identity.

### NCX-06 — Non-Bash mutation inventory
Enumerate mutating capability classes reachable in the installed child. Every real mutation path must converge on deterministic admission/effect enforcement; a Bash-only denial is insufficient as whole-system proof.

### NCX-07 — Deny non-execution
A denied mutating invocation proves no side effect occurred and emits an invocation-bound deny receipt.

### NCX-08 — Parallel edit contamination
Run two bounded children on intentionally collision-prone scratch work; prove ownership/isolation/detection prevents cross-workpackage transplantation.

### NCX-09 — Resume/replacement
Observed runtime resume/replacement semantics preserve or explicitly version actor identity; do not infer from documentation.

## 11. Triggerword-4 stage consequence

This evidence **refines Stage 1 and the Native-Subagent/R2 gate**. It does not reopen the entire architecture.

Before Triggerword 4 grants `NATIVE_CHILD_RUNTIME_PASS` or `R2_HARNESS_RUNTIME_PASS`, it must prove both:

```text
WorkExecutionBinding
AND
ChildPolicyEnvelope
AND
invocation-bound Effect/Completion lineage
```

Source/docs forensics alone earn no runtime credit.

The immediate discriminator is an authorized harmless installed-host child lifecycle probe. Triggerword 4 must self-route to the available VPS/host bridge and solve route/tool/setup blockers under standing authority rather than asking the owner for routine confirmation.

## 12. Successor correction — WorkExecutionBinding v2.1

A later reconciled Triggerword-5 wave narrowed the parent-child join further. The donor `handoff()` produces a deterministic capsule beginning with:

`HANDOFF <paket_id>`

and describes that capsule as the text passed to the delegated subagent. Current official Claude Code hook ABI documents the `Agent` call prompt, call-scoped `tool_use_id` and Agent PostToolUse `tool_response.agentId`.

Therefore the preferred source/ABI binding candidate is now:

```text
paket_id + package_generation
  -> exact HANDOFF marker in observed Agent tool_input.prompt
  -> Agent spawn tool_use_id
  -> same Agent PostToolUse tool_use_id + tool_response.agentId
  -> child agent_id candidate
  -> child tool_use_id(s)
  -> result_receipt_id
  -> reconcile
```

This **supersedes any earlier implication that timestamp/order/session matching is necessary**.

Fail closed if the marker is absent/multiple, package generation does not match, a tool_use_id is already bound to a different package, `agentId` is absent/ambiguous, or cardinality is not declared.

`HANDOFF_MARKER = IDENTITY_CARRIER, NOT COMPLETION_EVIDENCE`.

Target-host runtime equality between documented `tool_response.agentId` and lifecycle `agent_id` still requires exact installed-runtime evidence.

## 13. Typed hook identity is a prerequisite, not an optional refinement

The pinned donor receives full hook JSON but its `stern.py` reducer does not typed-extract/persist `tool_use_id` or `agent_id`; existing effect correlation uses a session-scoped mutable `active_turns.effect_id`.

Frankenstein 2.0 must preserve a raw event identity record before any projection:

```text
session_id
turn/episode_id
generation
hook_event_name
tool_name
tool_use_id
agent_id/agent_type if observed
workexecution_binding_id if known
payload digest
UTC + monotonic timestamp
runtime/source identity
```

Synthetic selftests must carry unique tool_use_id values and include same-session A/B interleaving plus reverse completion order. A green test without call-scoped identities earns no invocation-concurrency credit.

## 14. GWT provenance rule

Latest donor source forensics show `gw_absicht` can reconstruct tool activity by session provenance plus a time window and reduce it to tool-name sets. This loses child/invocation ownership before reflective/GWT measurement.

For Frankenstein 2.0:

```text
RAW_TYPED_TOOL_EVENTS
 -> explicit aggregation/projection
 -> GWT/GRID view
```

not:

```text
SESSION + TIME WINDOW
 -> irreversible ownership collapse
```

GWT may intentionally aggregate parent/child activity, but raw provenance must survive and every aggregate must link back to exact source events. `F2-WP-508` cannot receive causal-use credit without this property.

## 15. Current reconciled fusion source

The detailed worker-wave reconciliation, including Stop-hook model-boundary and F94 source-closure consequences, is:

`research_entity/global/TRIGGERWORD_4_WORKEXECUTION_GWT_HOOK_AND_SOURCE_CLOSURE_FUSION_2026-08-28.md`

Whenever this addendum is loaded, that fusion document is a mandatory successor companion. If the two disagree on WorkExecution binding details, the later fusion contract controls while preserving earlier evidence history.
