# EXECUTION SURFACE RESOLUTION PROTOCOL V1

Status: CURRENT PROTOCOL CANDIDATE
Scope: all Clay / EntityOS / HCU / Frankenstein workers, triggers, agents and execution decisions
Authority: this protocol grants no authority; it compiles current owner/supervisor authority, observed capabilities and known federated routes into a deterministic execution classification.

## 0. Purpose

Prevent the recurring failure class in which a worker infers a global execution blocker from a local missing tool, stale policy cache, transient transport failure, provider restriction, or incomplete current-state observation.

Canonical distinction:

```text
ATTENTION_SURFACE
!= NATIVE_INVOCATION_SURFACE
!= FEDERATED_REACHABILITY
!= EXECUTION_AUTHORITY
!= TARGET_HEALTH
!= ECONOMIC_PROVIDER_BOUNDARY
!= EVIDENCE_ADMISSION
```

A worker MUST resolve these planes separately.

## 1. Mandatory entry gate

Before any material execution attempt or any visible claim equivalent to `NO_EXECUTOR`, `NO_SHELL`, `VPS_UNAVAILABLE`, `SANDBOX_UNAVAILABLE`, `SELF_HOSTED_UNAVAILABLE`, `CANNOT_RUN`, or `BLOCKED_BY_TOOLING`, compile an `EXECUTION_SURFACE_RESOLUTION/v1` frame.

Required order:

```text
REQUESTED ACTION/CAPABILITIES
-> CURRENT OWNER AUTHORITY
-> CURRENT SUPERVISOR/PROGRAM POLICY WHERE RELEVANT
-> DIRECT SESSION CAPABILITY OBSERVATION
-> KNOWN FEDERATED ROUTE ENUMERATION
-> ROUTE HEALTH/REACHABILITY OBSERVATION OR PROBE PLAN
-> ECONOMIC/PROVIDER/EFFECT GATES
-> ROUTE CLASSIFICATION
-> PRE-USE REVALIDATION
-> EXECUTION
-> EXACT RECEIPT / EVIDENCE-SCOPE CLASSIFICATION
```

## 2. Open-world capability law

Direct tool visibility is not a closed-world inventory of project capability.

```text
DIRECT_TOOL_NOT_LISTED
=> DIRECT_CAPABILITY_NOT_OBSERVED_ON_THIS_SURFACE
!= PROJECT_CAPABILITY_ABSENT
```

If a registered indirect route may satisfy the request, the result is `DISCOVERY_REQUIRED` or `REACHABLE_VIA_BRIDGE`, not `CAPABILITY_ABSENT_PROVEN`.

## 3. Legal resolution states

Every requested capability must end in one of:

- `DIRECT_AVAILABLE` — directly callable on the current session surface and current authority permits the action.
- `REACHABLE_VIA_BRIDGE` — an admitted indirect route is currently observed reachable.
- `DISCOVERY_REQUIRED` — an admitted/known candidate route exists but current reachability is not freshly established.
- `TRANSIENTLY_UNREACHABLE` — a route probe failed or is queued/rate-limited/offline, but capability absence is not proven.
- `AUTHORITY_DENIED` — newest applicable authority explicitly forbids the action class.
- `ECONOMICALLY_DENIED` — compute route may exist but the concrete external provider/token/spend route is forbidden or unproven under current economic policy.
- `CAPABILITY_ABSENT_PROVEN` — all registered applicable routes at the same bound authority generation were exhaustively resolved and terminally lack the required capability; no unknown/unprobed route remains.

`NO_EXECUTOR` is deprecated as an unscoped conclusion. If retained in legacy output it must be accompanied by one of the states above and the exact route-resolution receipt.

## 4. Scope law for negative observations

Every negative observation MUST bind:

```text
surface_id
route_id (if any)
observation_time
observation_ttl_seconds
authority_identity / authority_generation
probe or discovery method
raw classification
scope
```

Examples:

```text
ssh binary absent in transient chat container
!= SSH bridge absent

GitHub workflow queued at T
!= self-hosted runner permanently absent

connector does not export sandbox.exec
!= repository-owned sandbox bridge absent

provider HARD_OFF
!= owner VPS compute forbidden
```

Historical negative receipts remain provenance. They expire as current planning facts when their TTL/currentness fence expires.

## 5. Authority resolution

This protocol does not define execution permission. Resolve authority from current canonical project pointers, beginning with `CLAY_EXECUTION_AUTHORITY.md` and the newest explicit owner direction, then current supervisor policy where it governs the requested plane.

A lower cache, historical receipt, file name containing `CURRENT`, or self-reported surface capability cannot override newer owner authority.

If authority is genuinely ambiguous after current-source resolution, fail closed as `AUTHORITY_DENIED_OR_UNRESOLVED` for the affected action only. Do not turn one authority ambiguity into a claim that the execution mechanism does not exist.

## 6. Federated route graph law

Known routes are stored in `governance/EXECUTION_SURFACE_REGISTRY_V1.json`.

The registry is a discovery map, not authority. Every route points to its authority and evidence sources.

A worker MUST traverse candidate routes that satisfy the requested capability before issuing a global absence claim.

Typical route shapes include:

```text
Chat session
-> GitHub connector
-> repository workflow/controller
-> self-hosted runner
-> clay-direct-dev

Configured bridge host
-> Clay Git/SSH bridge
-> clay-direct-dev

Chat/repo
-> preview/deployment controller
-> Vercel Sandbox orchestration
-> Sandbox microVM
```

Route existence is not route health. Route health is not target capability. Target execution is not evidence admission.

## 7. Provider/economic axis separation

External provider/token policy is independent of owner infrastructure reachability.

```text
FREE_ONLY_PROVIDER_POLICY != NO_VPS
PROVIDER_HARD_OFF != OWNER_COMPUTE_HARD_OFF
PAID_API_DENIED != LOCAL_MODEL_DENIED
```

Evaluate provider/economic constraints only for the provider/token/spend portion of a route.

## 8. Transport vs target/product failure

Transport/control-plane failures must remain transport-scoped:

- queue delay;
- runner offline;
- SSH client absent on caller;
- DNS failure;
- rate limit;
- connector missing method;
- authentication transport failure;
- bridge health unknown.

None of those proves a product scientific failure.

Likewise a successful bridge roundtrip proves reachability at that scope, not whole EntityOS/HCU/Frankenstein acceptance.

## 9. Generation / TOCTOU fence

Every resolution frame binds an `authority_generation` and `route_observation_generation` or timestamp.

Before an effectful, cost-bearing, promotion-bearing, or runtime-credit-bearing action, revalidate:

1. current owner authority identity still matches;
2. selected route has not exceeded its observation TTL;
3. exact source/artifact identity still matches the planned input;
4. economic/provider policy still admits the concrete lane;
5. no newer explicit owner instruction supersedes the frame.

Mismatch => discard the stale frame and resolve again.

## 10. Context compiler law

Workers should not depend on full historical prose to answer the execution question. Compile a compact SituationFrame containing:

```text
requested_capabilities
owner_authority_identity
policy_axes
observed_direct_capabilities
candidate_federated_routes
route health + TTL
selected route
blocker class if none
required revalidation
expected evidence scope
```

Place the compiled current frame in active attention. Historical receipts remain durable but need not remain in active context.

## 11. Self-healing behavior

If the preferred route is `TRANSIENTLY_UNREACHABLE` and current authority permits infrastructure repair:

1. inspect alternate registered routes;
2. inspect the existing bridge/runner repair path;
3. repair or re-enter the route if bounded and authorized;
4. re-probe;
5. only then classify the remaining blocker.

Do not create a competing product/state/effect authority to bypass a route failure.

## 12. Evidence receipt

Every material resolver result should be serializable as:

```json
{
  "schema": "EXECUTION_SURFACE_RESOLUTION/v1",
  "requested_capabilities": [],
  "authority_identity": "...",
  "authority_generation": "...",
  "direct_observations": {},
  "candidate_routes": [],
  "selected_route": null,
  "classification": "DISCOVERY_REQUIRED",
  "negative_observations": [],
  "revalidate_before_use": true,
  "evidence_scope": "ROUTING_ONLY"
}
```

A routing receipt cannot mint product/runtime/training/effect credit.

## 13. Acceptance tests

A conforming resolver MUST satisfy:

1. direct SSH absent + authorized known runner/bridge -> not `CAPABILITY_ABSENT_PROVEN`;
2. provider HARD_OFF + owner VPS allowed -> provider denied, VPS/local compute still eligible;
3. stale current-facing document conflicts with newer owner authority -> stale document cannot select policy;
4. queued/offline bridge -> `TRANSIENTLY_UNREACHABLE`;
5. known unprobed bridge -> `DISCOVERY_REQUIRED`;
6. explicit current owner denial -> `AUTHORITY_DENIED`;
7. authority generation changes before use -> re-resolution mandatory;
8. route exists but no exact runtime receipt -> routing/reachability credit only;
9. connector method absent + repository bridge known -> indirect route remains eligible;
10. all routes explicitly denied/absent at same fresh generation -> only then `CAPABILITY_ABSENT_PROVEN`.

## 14. Recurrence invariant

The permanent anti-recurrence rule is:

```text
LOCAL ABSENCE MUST NEVER BECOME GLOBAL ABSENCE WITHOUT EXHAUSTIVE CURRENT ROUTE RESOLUTION.
```

and:

```text
STALE CURRENT-FACING TEXT MUST NEVER OUTRANK A FRESH AUTHORITY POINTER.
```

## 15. Long-run durability binding

Execution-surface correctness and run durability are separate requirements. Any multi-step material run that can outlive one fragile interaction/tool/transport boundary MUST additionally apply `governance/DURABLE_WORK_REENTRY_PROTOCOL_V1.md` and persist a `DURABLE_WORK_CURSOR/v1` checkpoint through `tools/durable_work_cursor_v1.py` or an evidence-equivalent implementation.

Mandatory law:

```text
THE FINAL CHAT MESSAGE IS NEVER THE CHECKPOINT.
RUNNING_UNCONFIRMED -> VERIFY_EXTERNAL_RESULT_BEFORE_RETRY.
COMPLETED MATERIAL WORK -> DURABLE EVIDENCE BEFORE THE NEXT FAILURE-PRONE STEP.
```

A response-delivery failure or worker interruption may leave presentation incomplete while durable work is already complete. The next worker must re-enter the durable cursor, preserve completed evidence, revalidate authority/route freshness for future execution, verify unconfirmed external effects, and resume from the first incomplete node. It must not describe this as invisible background work and must not restart completed nodes merely because the previous visible response failed.
