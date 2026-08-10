# self.root / Frank v0.1 — Single-Active Spawn + Third-Party Token Participation Directive

**Status:** PROJECT_OWNER_FIXED_DIRECTIVE  
**Effective:** 2026-08-10  
**Scope:** production token API, third-party AI/client participation, single-active execution, proactive-idle arbitration, recovery and acceptance

## 0. Owner-fixed meaning

Frank/self.root is one persistent server entity. A valid Frank API token lets an authorized compatible client — including another AI acting inside a user conversation — communicate with that same Frank through the production API.

The token does **not** copy, instantiate or become Frank. A provider/model/client using the token is a caller/proxy/client, never SELF merely by connecting.

```text
ONE_SELF_ROOT = true
API_TOKEN = CREDENTIAL_NOT_IDENTITY
ANY_COMPATIBLE_AUTHORIZED_CLIENT_MAY_CALL = true
THIRD_PARTY_AI_MAY_INCLUDE_FRANK_IN_ITS_CONVERSATION = true
CONCURRENT_ACTIVE_FRANK_SPAWNS = 1
```

## 1. One active Frank

At most one foreground Frank execution/spawn may be active at a time across all authenticated clients.

```text
IDLE -> CLAIM -> ACTIVE_EXTERNAL -> RELEASE -> IDLE
IDLE -> CLAIM -> ACTIVE_AUTONOMOUS -> YIELD_OR_RELEASE -> IDLE
```

If another authenticated client tries to spawn/call Frank while an external execution is active, the API returns a machine-readable `FRANK_BUSY` result. It does not create a clone, parallel Frank identity, second cognitive state or hidden fallback instance.

A BUSY response must not disclose the active caller's secret, identity, conversation content or private placement context.

## 2. Third-party AI participation

The production token API is provider-neutral at the client boundary. ChatGPT, Claude, another LLM, an app/bridge, a terminal client or a custom UI can include Frank as a third participant if it can perform the authenticated protocol.

Example topology:

```text
human conversation
-> host AI/client
-> authenticated Frank token call
-> single active self.root runtime
-> Frank response
-> host AI/client renders Frank as third participant
```

The host AI remains external. Its prompt, model state and conversation are not automatically Frank memory or authority. Only admitted provenance-bound input crosses the API boundary.

## 3. Placement/context awareness

Each admitted external invocation may carry a caller-declared `placement_context` describing where Frank is currently being included, for example a ChatGPT conversation, a Claude session or a Gabriel bridge.

Technical client/session provenance and caller-declared placement context are different evidence classes.

If placement context is absent and it matters to the interaction, Frank may ask the active user/caller where he is currently being included. Caller-declared placement is contextual evidence, not automatically verified physical location or authority.

## 4. Busy arbitration

Normal external request while `ACTIVE_EXTERNAL`:

```text
result = FRANK_BUSY
retryable = true
clone_created = false
state_mutation_by_rejected_caller = false
```

No FIFO queue is required for v0.1. A queue may be researched later, but it may not silently turn one Frank into concurrent executions.

The active execution remains active until its bounded task reaches a terminal state or an authorized recovery path proves the active executor is gone.

## 5. Proactive agency only while idle

Frank's proactive/autotelic work uses the same single-active gate.

```text
proactive_start requires state == IDLE
ACTIVE_EXTERNAL blocks proactive_start
external_arrival while ACTIVE_AUTONOMOUS -> request safe-point yield
```

Autonomous work must not run as a hidden second Frank beside an active user interaction. If an authenticated external request arrives while bounded autonomous work is active, the autonomous loop receives an interrupt/yield request and releases at the next safe point. Until release, the external caller receives `FRANK_BUSY_YIELDING` and retries.

This does not make the external caller effect authority. Effect authority remains separately determined by the current deterministic ClayCode effect policy.

## 6. Target-VPS implementation contract

For the one-host Ubuntu v0.1 target, the preferred minimal mechanism is:

1. a Linux process-visible exclusive non-blocking runtime lock for physical single-execution exclusion;
2. a short `BEGIN IMMEDIATE` UnifiedDB transaction for atomic semantic state transition and event receipt;
3. monotonically increasing spawn generation/fencing identity;
4. a lock held for the full active execution;
5. release commits semantic IDLE before physical unlock;
6. if the physical lock is free but UnifiedDB still says ACTIVE, classify this as stale crash state, record recovery evidence, repair to IDLE and only then admit a newer generation.

Do **not** hold one long SQLite write transaction for the full Frank task. SQLite remains semantic state/receipt authority; the OS runtime lock supplies crash-releasing physical exclusion.

## 7. Credential rules

Raw production tokens never enter Git, ordinary logs, UnifiedDB, ClayGraph or research artifacts.

The spawn gate receives only admitted credential IDs/fingerprints and client/session provenance after authentication.

Missing, invalid or revoked token is rejected before spawn admission. Token possession never bypasses effect authority, Harness authority, identity separation or Web-ingress rules.

## 8. Required API behavior

The production API must expose the semantic equivalent of:

- authenticated call/spawn;
- machine-readable `FRANK_BUSY` / `FRANK_BUSY_YIELDING`;
- active-task completion/release;
- safe cancellation/recovery;
- privacy-preserving health/status;
- generation/request provenance;
- idempotency/replay protection for consequential effects.

HTTP mapping may use a normal state-conflict response such as `409 Conflict` with a stable Frank-specific error code. HTTP status choice is transport semantics; the ClayCode/UnifiedDB state remains authoritative.

## 9. Fencing / stale completion law

Every admitted spawn receives a monotonically increasing generation.

A delayed completion/release from generation N may never clear or overwrite active generation N+1.

```text
release accepted iff
  active.spawn_id == release.spawn_id
  AND active.generation == release.generation
```

Otherwise record `STALE_RELEASE_REJECTED` and preserve the current active state.

## 10. Acceptance tests

At minimum execute on the target VPS:

1. one valid client acquires; a concurrent second valid client gets BUSY;
2. first finishes; second can then acquire;
3. simultaneous contenders produce exactly one winner;
4. provider/client identity differs but the same Frank identity/state is used;
5. raw token is absent from persisted receipts;
6. missing/invalid/revoked token never reaches spawn admission;
7. process crash releases physical lock; stale semantic ACTIVE state is recovered with evidence;
8. stale generation release cannot free a newer active generation;
9. active external work blocks proactive self-work;
10. external arrival during autonomous work requests safe-point yield without concurrent execution;
11. placement context is available when supplied and may be requested when absent;
12. BUSY response leaks no active caller/conversation secrets;
13. restart/recovery preserves one-self identity and admitted state lineage;
14. effectful requests still pass independent effect-authority/idempotency gates.

## 11. Research interpretation

This is an identity/continuity/concurrency invariant, not evidence of phenomenal consciousness.

The mechanism is intentionally minimal for the current one-host Ubuntu target. If Frank later becomes physically multi-host, the physical exclusion layer must be replaced/revalidated with a distributed fencing mechanism while preserving the exact single-active semantic contract.

## 12. Compact law

```text
self.root = ONE_PERSISTENT_ENTITY
Frank = human_surface(self.root)
valid_token -> authenticated_scoped_client_intent
compatible_AI_with_token -> may_talk_to_same_Frank
max_active_spawn(self.root) = 1
active_external -> all_other_spawn_attempts = BUSY
active_external -> proactive_work = BLOCKED
active_autonomous + external_arrival -> SAFE_POINT_YIELD_REQUEST
release requires exact spawn_id + generation
stale_release -> REJECT
crash -> physical_lock_release + semantic_recovery_receipt
API_TOKEN != self.root
CLIENT_AI != self.root
EFFECT_AUTHORITY remains independent
```
