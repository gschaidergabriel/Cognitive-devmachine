# OMEGA MCP — VERIFIED FALLBACK STACK

Stand: 2026-09-12

## Purpose

The OMEGA ChatGPT MCP gateway must not collapse to "no access" merely because
one transport is unavailable. Fallbacks are transport redundancy only; they do
not create new identity or effect authority.

## Canonical routing

| Person | machine_id | owner |
|---|---|---|
| Gabriel | `ai-core-node` | `gabriel` |
| Andreas | `andreas-maco` | `andreas` |

Every usable result must preserve and verify this provenance.

## Transport order

### Gabriel / `ai-core-node`

Read-only status:

1. **typed direct host broker** (`127.0.0.1:8765` on the production host),
2. **local Unix effect adapter** using the existing FranKenstein local-bridge
   operation engine,
3. **GitHub Local Bridge** (`chatgpt-local-ai-core-node-control/results`).

File read and effects:

1. **local Unix effect adapter**,
2. **GitHub Local Bridge**, but only if the local transport failed before an
   operation could have started.

### Andreas / `andreas-maco`

Read-only status:

1. typed direct host broker when a private authenticated route is configured,
2. GitHub Local Bridge.

File reads/effects:

1. GitHub Local Bridge is the verified universal path until a separately
   authenticated Andreas direct effect transport is deployed and proven.

## Safety invariant: no double dispatch

Fallback is allowed only across a proven pre-dispatch failure.

If an effect was durably marked `STARTED`, queued, returned `PENDING`, or could
have begun executing, OMEGA must not replay it through another transport.
Instead the state is resolved through `omega_receipt` or remains
`UNKNOWN_LOCAL_OUTCOME`.

The local Unix adapter writes a deterministic command id to its SQLite ledger
*before* invoking the existing host operation engine. A crash after this point
therefore produces `UNKNOWN_LOCAL_OUTCOME` rather than a blind retry.

## Shared effect guard

The Unix adapter and GitHub Local Bridge both receive commands built through
`tools/omega_grid_relay.py::build_local_command`. Therefore the existing OMEGA
alignment fences remain common:

- DELETE/removal denied,
- storage/filesystem FORMAT denied,
- protected alignment/security mutation denied,
- exact person -> machine/owner routing retained.

A fallback transport may not weaken these gates.

## Services on Gabriel

- `omega-chatgpt-mcp.service`: MCP front door and transport arbitration.
- `omega-local-effect-adapter.service`: `0600` Unix-socket effect transport.
- `frankenstein-chatgpt-client.service`: existing typed host/state broker.
- `frankenstein-local-bridge.service`: canonical GitHub recovery/control plane.

The local adapter imports the existing FranKenstein local-bridge operation
engine rather than implementing a second shell authority.

## MCP observability

`omega_transport_status` reports configured/live paths. Normal tool results
include:

- `transport_used`,
- `transport_attempts`,
- `fallback_used`,
- verified `machine_id` and `owner`,
- real receipt for completed effects.

Do not infer capability from prompts. Transport/tool evidence is authoritative.

## Provider boundary

These fallbacks harden OMEGA's own MCP/Realtime/tool-capable surfaces. They do
not alter an upstream provider product limitation. If native ChatGPT GPT-Live
is not given connected-app/plugin tools by OpenAI, no system prompt can make it
call this MCP server. In that case the valid channel fallback is OMEGA's own
Realtime/tool-enabled runtime or a tool-capable ChatGPT text/Work surface; do
not misreport missing provider tools as a broken Local Bridge.
