# ChatGPT ↔ FranKenstein Unified Terminal/Harness Contract

Status: implementation contract / coordination branch, 2026-09-12

## Goal

The owner-facing system behaves as ONE FranKenstein across browser chat, terminal, voice and worker execution. These are surfaces/organs, not separate assistants and not separate memory authorities.

The existing FranKenstein mechanisms remain authoritative. This contract does NOT create a new sync system, a new semantic database, a second turn loop, a second worker authority or a second local-host bridge.

## Existing mechanisms to compose

- `stern.py` / UnifiedDB / existing hook + handoff + reconcile paths.
- Existing GRID10 / canonical turn/reentry integration.
- Existing ChatGPT bridge: `chatgpt_senden()` + `chatgpt_ernten()` and its browser/login/recovery/resource discipline.
- Existing worker harness: `~/.claude/star/harness_aider.py`, including handoff, scoped work, checkpoint, audit and reconcile.
- Existing real-host Local Bridge with per-machine control/results branches and exact `machine_id` + `owner` attribution.
- Existing two host subjects: `ai-core-node/gabriel` and `andreas-maco/andreas`.

## Hard invariant: one logical turn, one semantic admission

Every owner message receives one immutable `turn_id`. Browser, terminal and voice are ingress surfaces only.

```text
owner input
  -> canonical Frank ingress envelope
  -> existing context / GRID / handoff authorities
  -> ChatGPT organ and/or scoped workers
  -> admitted host effects through existing effect/bridge paths
  -> receipts
  -> canonical uptake/reentry
  -> response events
  -> browser / terminal / voice presentation
```

The same logical message MUST NOT be separately admitted once by a terminal database and again by a browser/ChatGPT database.

Minimum ingress envelope:

```json
{
  "schema": "FRANK_TURN/v1",
  "turn_id": "immutable unique id",
  "session_id": "surface session / attach id",
  "surface": "terminal|web|voice",
  "machine_id": "ai-core-node|andreas-maco|...",
  "owner": "gabriel|andreas|...",
  "text": "owner message",
  "created_at": "UTC timestamp"
}
```

Existing EntityIdentity / InstallationIdentity / StateRootIdentity / RuntimeEpoch remain the identity authorities. A surface session is not a new entity.

## No split brain / database law

"ChatGPT writes normally into FranKenstein's databases" means: ChatGPT uses the SAME admitted write APIs and turn/effect paths as FranKenstein. It MUST NOT own a ChatGPT-only semantic DB or a terminal-only semantic DB.

It does NOT mean blindly duplicating every SQL write into every physical SQLite file. Gabriel and Andreas remain distinct installations/host subjects. Byte-identical dual-write across two independent SQLite stores would create exactly the split-brain failure this integration is meant to eliminate.

Rules:

1. One logical fact has one canonical `turn_id` / event identity.
2. Write through the existing authoritative database API for the exact runtime/install scope.
3. If another host needs the fact, project/replicate it as the SAME logical event with provenance and an idempotent receipt; do not mint a second semantic fact.
4. Preserve `machine_id`, `owner`, runtime epoch and source receipt on every cross-host fact.
5. Unknown/partial remote outcome is reconciled, never blindly replayed as a new fact.
6. Local Bridge's per-machine idempotency DB is an effect ledger, not a second semantic memory authority.
7. Existing GRID/turn/outbox/event tables are reused where sufficient; do not add another sync ledger merely for this terminal feature.

## Terminal UX

Target command: `frank` (or a compatible alias from the existing FranKenstein Terminal launcher).

The terminal is a thin interactive surface over canonical Frank ingress. It is not "Claude in a Frankenstein-themed terminal" and not "an Aider shell".

Default presentation:

```text
FranKenstein  [ai-core-node · gabriel]  connected
frank › repariere das Kopfspringen des Avatars

  ◌ reading state
  ◉ worker avatar-motion        running
  ◉ worker visual-qa            running
  ✓ receipt ai-core-node/...    verified

frank › <final response>
```

High-value convenience commands:

- `/status` — entity/runtime/bridge state, concise by default.
- `/host auto|gabriel|andreas` — effect target selection; `auto` means current/local subject, never silent cross-host guessing.
- `/workers` — active scoped workers and their state.
- `/attach <turn_id|worker_id>` — reconnect after terminal close/reopen.
- `/cancel <worker_id>` — scoped cancellation, not whole-entity shutdown.
- `/receipt <id>` — exact effect/readback receipt.
- `/verbose on|off` — worker/event chatter without changing cognition.
- `/exit` — detach the surface; ongoing admitted work keeps its own lifecycle.

Terminal close/reopen MUST NOT mint a new EntityIdentity. It attaches to persistent state and may resume/inspect an existing nonterminal turn.

## ChatGPT organ adapter

The existing ChatGPT browser bridge is reused first; no duplicate Playwright/browser stack.

- `chatgpt_senden()` remains the send authority.
- `chatgpt_ernten()` remains the harvest authority.
- Existing lock, one-tab discipline, login checks, crash recovery and resource thresholds remain intact.
- Terminal UX may hide the internal send/harvest split by presenting an event stream, but it MUST NOT replace the proven internals with an uncontrolled blocking browser loop.
- Mapping from Frank `turn_id` to ChatGPT send/harvest/conversation evidence must be persisted through an existing admitted state/event path, not a shadow semantic store.
- If the ChatGPT bridge falls back to another model, model/provenance remains explicit. A fallback worker does not silently impersonate ChatGPT.

## Worker plane

`harness_aider.py` is reused as a worker executor behind FranKenstein, not as the identity presented to the owner.

A worker is ephemeral and scoped:

```text
worker.spawned
worker.running
worker.receipt
worker.done | worker.failed | worker.cancelled
```

Every worker packet carries at minimum:

- parent `turn_id`;
- unique `worker_id`;
- exact task/scope;
- target repo/branch/path or read-only scope;
- target `machine_id` + `owner` when host-bound;
- write/effect lease or explicit read-only class;
- provenance/model identity;
- result/reconcile receipt.

Workers may fan out only on disjoint mutation boundaries or as independent read-only/falsification work. They do not write canonical state directly around `stern.py`/GRID/effect gates.

## Host effect path

ChatGPT/worker intent that changes a real host goes through the already existing Local Bridge/effect authority. The bridge is a body/effect edge, not the semantic brain.

Every consumed Local Bridge receipt must match the requested target in BOTH fields:

```text
machine_id
owner
```

Branch name alone is not enough.

## Host safety / admission

Before local worker fan-out or expensive execution, use current host telemetry/admission. Unknown/red telemetry fails closed. Worker count is bounded by current resources, not by how many tasks can be imagined.

## Reliability requirements

- immutable/idempotent `turn_id`;
- worker idempotency + scoped leases;
- crash-safe reattach/resume;
- exact host attribution;
- no duplicate ChatGPT browser tabs/runtimes;
- no duplicate canonical turn loop;
- no duplicate productive watcher;
- explicit `UNKNOWN` for unverified effects;
- readback before promotion;
- cancellation is scoped and recorded;
- terminal renderer failure cannot falsify task outcome;
- surface disconnect cannot erase admitted work.

## Current integration gap observed 2026-09-12

On `ai-core-node`, existing owner-facing terminal wrappers currently launch Claude Code (`frank-terminal-hilfe`, `work-on-frank`) or Aider/free-pool work (`frank-harness-sichtbar`). The ChatGPT bridge and the real-host bridge exist separately. Therefore the missing product step is not another harness: it is a thin canonical terminal ingress/renderer that composes the existing ChatGPT organ + GRID/DB + worker harness + Local Bridge.

## Implementation order

1. Bind the exact existing canonical turn/DB admission function used by current hooks/GRID.
2. Add a thin `frank` interactive frontend over that ingress; no model call inside the UI layer.
3. Add ChatGPT-organ adapter calls to existing `chatgpt_senden` / `chatgpt_ernten`, keyed by `turn_id`.
4. Expose existing `harness_aider.py` jobs as child worker events keyed by parent `turn_id`.
5. Route host effects through current Local Bridge and feed verified receipts back into the same turn uptake/reentry path.
6. Change the existing FranKenstein Terminal launcher to enter this frontend; keep an explicit developer escape hatch for raw Claude/Aider rather than presenting them as FranKenstein itself.
7. Run one end-to-end discriminator: terminal input -> canonical DB/GRID admission -> ChatGPT -> one scoped worker -> real read-only host receipt -> uptake -> terminal final response -> close/reopen -> same turn visible.
8. Only after that pass, improve TUI polish/streaming/shortcuts.

## Acceptance test

A single terminal sentence on `ai-core-node` must be traceable end-to-end by ONE `turn_id` through:

- terminal ingress;
- canonical Frank state/GRID admission;
- ChatGPT organ dispatch/harvest evidence;
- optional worker handoff/reconcile;
- exact real-host receipt if tools/effects were used;
- canonical uptake/reentry;
- terminal response;
- reattach after terminal restart.

The test fails if any of these occur:

- a second semantic DB becomes authoritative;
- the same owner message is admitted twice under different logical identities;
- host provenance is lost;
- a worker bypasses the normal write/effect authority;
- a fallback model is presented as ChatGPT without provenance;
- terminal closure loses the turn;
- browser/terminal surfaces disagree because each maintained independent semantic history.
