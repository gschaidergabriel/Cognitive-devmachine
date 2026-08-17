# ClayVerse integrated candidate architecture

Canonical runtime path:

`Clerk subject -> IdentityRouter -> permanent user session -> observation turn -> WorldAssembler -> ClayGraph projection -> bounded Hyperposition alternatives -> GWT workspace episode -> inference adapter (Claude Code boundary) -> intent -> capability/effect gate -> EntityOS/process boundary -> verified outcome -> causal re-entry -> UnifiedDB -> rebuilt ClayGraph`

## Invariants implemented in this candidate

- One SQLite/WAL UnifiedDB is the canonical state authority.
- Gabriel and Andreas are equal-rights perspectives into one database/entity.
- Each session preserves its newest 20 turns at full fidelity.
- Older history degrades in generations down to a two-word minimum trace.
- Destructive compression promotes only explicitly typed durable lines (`FACT:`, `DECISION:`, `TASK:`, `COMMITMENT:`, `PREFERENCE:`) without an inference extractor, so unknown meaning fails closed.
- Cross-session retrieval is collision-triggered by explicit shared resource references, not routinely injected.
- ClayGraph is derived and can be deleted/rebuilt from UnifiedDB.
- Workspace alternatives remain explicit until the inference boundary selects one.
- Effects are capability gated; process execution requires explicit argv and uses `shell=False`.
- Resource leases use generation+nonce fencing to reject stale/ABA writers.
- Outcomes are hashed and causally re-entered into canonical state.
- Container state is externalized at `/var/lib/clayverse`.
- Container runs as non-root with all Linux capabilities dropped in the supplied Compose profile.

## Deliberately unclaimed / still external

- Real Clerk JWT verification and key rotation.
- Browser terminal transport and xterm/ttyd adapter.
- Actual installed/authenticated Claude Code CLI and its two permanent PTYs.
- Strongest EntityOS binary/ClayCode runtime integration rather than the current typed process boundary.
- Production PostgreSQL/multi-process contention qualification if SQLite no longer meets scale requirements.
- VPS deployment and migration from Frank donor state.

Those boundaries are explicit so the candidate cannot be mistaken for whole-system PASS.
