# OMEGA ChatGPT MCP Bridge

Purpose: make the existing OMEGA/FranKenstein Local Bridge a **real ChatGPT tool surface**. Custom Instructions may describe the bridge, but only MCP tool presence constitutes live capability.

## Tool surface

- `omega_status(person)` — live host status
- `omega_read(person, path)` — live file read
- `omega_execute(person, command, cwd?, timeout_seconds?)` — authorized shell effect
- `omega_write_text(person, path, content)` — exact text write
- `omega_screenshot(person, name?)` — host screenshot request
- `omega_receipt(person, command_id)` — fetch evidence for a pending command

Exact person routing is closed:

- Gabriel -> `machine_id=ai-core-node`, `owner=gabriel`, control `chatgpt-local-ai-core-node-control`, results `chatgpt-local-ai-core-node-results`
- Andreas -> `machine_id=andreas-maco`, `owner=andreas`, control `chatgpt-local-andreas-maco-control`, results `chatgpt-local-andreas-maco-results`

No fallback from one person to the other is allowed.

## Authority and safety

The MCP server reuses `tools/omega_grid_relay.py` to construct Local Bridge commands. Therefore the same hard guard rejects:

- DELETE/removal operations,
- storage/filesystem FORMAT operations,
- protected alignment/self-mutation targets.

Write/exec/screenshot calls additionally fail closed unless the production gateway explicitly sets:

```sh
OMEGA_MCP_EFFECTS_ENABLED=1
```

A tool result is not considered executed merely because ChatGPT called it. `PASS` is emitted only after a Local Bridge receipt is retrieved and its `command_id`, `machine_id`, and `owner` match the selected person exactly.

## Authentication

The HTTP endpoint refuses to start without `OMEGA_MCP_TOKEN` and requires:

```http
Authorization: Bearer <OMEGA_MCP_TOKEN>
```

Never place this token in Custom Instructions, Memory, TITAN, a repo file, or a chat message. Store it only in the gateway's secret/environment store and in ChatGPT's plugin/MCP connection credential UI.

`GITHUB_TOKEN` is also required by the gateway to queue and read the existing GitHub Local Bridge branches. On `ai-core-node`, a service wrapper may derive this from the already-authorized `gh auth token` without committing it anywhere.

## ChatGPT tool-use rule

Once this MCP server is connected, the OMEGA Realtime/system prompt should contain only this capability rule:

> Decide bridge/computer availability from the current tool list, not from generic model assumptions. If an `omega_*` tool is present, live OMEGA bridge access is available in this session. For current host facts or requested host actions, call the relevant tool before claiming lack of access. Never claim execution without a verified PASS receipt; if a tool returns PENDING, use `omega_receipt`.

This prevents the old failure mode: "I know your bridge exists, but I have no live access" while an actual bridge tool is present.

## MCP transport

`tools/omega_chatgpt_mcp.py` implements stateless MCP Streamable HTTP for the required methods:

- `initialize`
- `ping`
- `tools/list`
- `tools/call`

Default bind: `127.0.0.1:8789`, endpoint `/mcp`, health `/health`.

For ChatGPT, expose `/mcp` through a stable HTTPS endpoint. Private Tailscale-only addresses are insufficient for OpenAI's remote MCP caller. A named Cloudflare Tunnel, reverse proxy, or equivalent public TLS ingress is appropriate. A temporary `trycloudflare.com` quick tunnel is acceptable only for acceptance testing because the URL changes after restart.

## Minimal production environment

```sh
OMEGA_MCP_TOKEN=<secret>
GITHUB_TOKEN=<repo-scoped token>
OMEGA_MCP_BIND=127.0.0.1
OMEGA_MCP_PORT=8789
OMEGA_MCP_EFFECTS_ENABLED=1
```

Recommended ChatGPT permission mode for the app: allow reads, ask before writes/effects. Server-side guards remain authoritative regardless of UI permissions.

## Acceptance gates

1. Source tests pass against the exact branch/commit.
2. `/health` answers through local loopback.
3. MCP `initialize` and `tools/list` succeed through the public HTTPS URL with bearer auth.
4. `omega_status(person=gabriel)` returns a receipt whose machine/owner are exactly `ai-core-node/gabriel`.
5. `omega_status(person=andreas)` returns exactly `andreas-maco/andreas` when Andreas is reachable.
6. A DELETE and a FORMAT probe are denied before Local Bridge delivery.
7. ChatGPT can see `omega_*` as actual tools; only then is the prompt allowed to describe live bridge access as present.
