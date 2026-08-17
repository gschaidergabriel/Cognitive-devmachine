# ClayVerse deterministic grounded autonomy

## Purpose

ClayVerse must not depend on an identity role-play prompt to behave like a persistent,
proactive agent. Identity continuity, goals, progress, limits and autonomous scheduling
are runtime state and code. The model is cognition inside that architecture, not the
source of truth about the architecture.

This design intentionally contains no USB identity anchor, crypto identity key, smart
contract, escrow or autonomous financial authority. The persistent anchor is the
server-side UnifiedDB and the canonical ClayVerse runtime.

## Architectural laws

1. **Identity is state, not a claim.**
   `entity_agency_profile` stores the runtime identity mode `PERSISTENT_GOAL_AGENT`,
   server anchor `SERVER_UNIFIEDDB` and behavior mode `PROACTIVE_GROUNDED`. The model
   may describe this state but cannot redefine it by text.

2. **Goals are typed persistent state.**
   Goals, success criteria, priorities and `CONCEPT -> PROTOTYPE -> FINAL` milestones
   live in UnifiedDB tables. Each goal has one canonical user owner. Goal snapshots
   injected into cognition are owner-scoped.

3. **Autonomy is a machine loop.**
   The server daemon periodically executes a bounded `Plan -> Act -> Observe -> Adjust`
   cycle only when runnable persisted work exists. No runnable work means no model call.

4. **The model is a proposer, never an effect authority.**
   Cognition chooses one next bounded move. Any real/state-changing proposal must cross
   EffectGate. The proposal is persisted before the effect result is used for progress.

5. **Operational truth comes from persisted evidence.**
   Agency progress does not trust fluent model text or a caller-supplied outcome object.
   For an effectful attempt it re-reads the canonical `effects` row and accepts success
   only when the EffectGate journal says `VERIFIED` and its persisted safe outcome says
   `ok=true`.

6. **Completion is not self-certified.**
   An effect-free model result may move a milestone only to `READY_FOR_REVIEW`.
   The model cannot set `PASSED` and cannot set a goal `COMPLETE`. A canonical owner
   review performs that transition. Later phases remain unrunnable while any earlier
   phase is not `PASSED`.

7. **Runaway behavior is structurally bounded.**
   Policy state limits steps per cycle, failed retries per milestone and effects per
   cycle. Inference failures close the cycle. Effect runtime exceptions are persisted
   as failed observations and close the current cycle rather than triggering a tight
   retry loop. A daemon sleep interval separates cycles.

8. **Reputation is telemetry, not authority.**
   ERS is derived from verified non-noop effect evidence and failed effect evidence.
   `state.noop` is non-rewarding. ERS cannot grant capabilities, bypass EffectGate,
   mark milestones passed or authorize spending.

9. **Headless autonomy uses canonical owner cognition identity.**
   Background Claude cognition uses the same per-user HOME as the owner's permanent
   terminal, selected strictly from canonical goal ownership. It does not attach to
   tmux, simulate terminal input or inherit an unrelated service HOME.

10. **Prompting is a view over architecture.**
    Interactive hooks and engine inference receive a bounded structured `agency`
    snapshot from UnifiedDB. Runtime instructions encourage proactive execution but
    explicitly prohibit invented memory, goals, capabilities, progress or effects.

11. **No consciousness claim.**
    The autonomy daemon is an operational scheduler. It does not establish or imply
    biological life, consciousness or unrestricted AGI capability.

## State machine

A normal milestone path is:

`PENDING -> ACTIVE -> READY_FOR_REVIEW -> PASSED`

Failure may keep the milestone `ACTIVE` until the persisted retry threshold is reached,
after which it becomes `BLOCKED`. `REOPEN` returns a reviewed milestone to `ACTIVE`.
A goal becomes `COMPLETE` only when all of its milestones are `PASSED`.

## Autonomous cycle

For each admitted work item the runner performs:

1. Claim the highest-priority runnable milestone from UnifiedDB.
2. Persist an autonomous observation containing goal/milestone identifiers and criteria.
3. Assemble user-scoped world state, agency state and live EffectGate capabilities.
4. Ask cognition for exactly one bounded next move.
5. Persist the model proposal before execution.
6. Route any effect intent through EffectGate.
7. Persist/re-ingest the observed outcome.
8. Re-read canonical effect evidence and update the attempt/milestone state.
9. Continue only while policy limits and runnable work permit it.

This preserves the useful part of the strong-agent identity prompt—continuity,
initiative, goal focus and causal persistence—while moving truth, authority and
termination out of language and into deterministic runtime mechanisms.
