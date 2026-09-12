# OMEGA — ChatGPT MCP Bridge live receipt

Date: 2026-09-12

## Canonical source

Research repository main source merge:

- PR: `#2175` — `[OMEGA] Expose FranKenstein Local Bridge as ChatGPT MCP tools`
- merge commit: `12fa3b4d0c8c73dcf8a205d8b282a30beebfafc0`

Implemented surface:

- `omega_status`
- `omega_read`
- `omega_execute`
- `omega_write_text`
- `omega_screenshot`
- `omega_receipt`

The gateway reuses `tools/omega_grid_relay.py` for exact person→organ routing and the canonical DELETE / storage-filesystem FORMAT / protected-alignment guards.

Exact routing remains:

- Gabriel -> `machine_id=ai-core-node`, `owner=gabriel`
- Andreas -> `machine_id=andreas-maco`, `owner=andreas`

No cross-person fallback is allowed.

## Real-host source and merge proof

On real host `ai-core-node`, owner `gabriel`, execution boundary `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`:

- exact final branch source test: `omega-mcp-final-source-test-ai-core-20260912a`
- result: `10 passed`, py_compile PASS, installer shell syntax PASS
- tested branch head: `2706e4e9da4bf8d199ce47eda8751fafda566384`

Current-main merge proof:

- `omega-mcp-mergeproof-ai-core-20260912a`
- result: `10 passed`
- canonical main observed: `12fa3b4d0c8c73dcf8a205d8b282a30beebfafc0`

## Production deployment

Deployment receipt:

`local_bridge/results/receipts/omega-mcp-deploy-ai-core-20260912a.json`

Verified:

- deployed exact canonical main `12fa3b4d0c8c73dcf8a205d8b282a30beebfafc0`
- `omega-chatgpt-mcp.service` active/running
- loopback health PASS
- service reports `auth_required=true`
- service reports `effects_enabled=true`
- generated MCP bearer secret is kept only in host secret/environment storage and was not emitted into receipts/chat

## MCP protocol end-to-end proof

Protocol stage 1:

`omega-mcp-e2e-stage1-ai-core-20260912a`

Verified through the running MCP HTTP endpoint:

- MCP server name = `omega-frankenstein-bridge`
- actual exposed tools include all six `omega_*` tools
- `omega_status(person=gabriel)` queued a concrete `CLAY_LOCAL_COMMAND/v1`
- queued command preserved exact `ai-core-node/gabriel` binding

Resulting Local Bridge command:

`omega-effect-chatgpt-mcp-gabriel-status-e2e-70614664df504cb4`

Real host receipt:

- status = PASS
- machine_id = `ai-core-node`
- owner = `gabriel`
- execution boundary = `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`

MCP receipt stage 2:

`omega-mcp-e2e-stage2-ai-core-20260912a`

Verified that `omega_receipt` read and validated the exact host receipt and returned PASS only after matching command_id + machine_id + owner.

## Real execution proof

`omega_execute(person=gabriel, command="printf OMEGA_MCP_EXEC_OK", cwd="/tmp")` was invoked through the running MCP endpoint.

Generated Local Bridge command:

`omega-effect-chatgpt-mcp-gabriel-exec-e2e-0d4f5cc510ee7cd9`

Real host receipt:

- op = exec
- status = PASS
- machine_id = `ai-core-node`
- owner = `gabriel`
- stdout = `OMEGA_MCP_EXEC_OK`
- execution boundary = `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`

Therefore the path is empirically closed:

`MCP tools/call -> OMEGA gateway -> GitHub Local Bridge -> real ai-core-node -> verified receipt`

This is no longer a prompt-only description of bridge capability.

## Critical OpenAI product boundary discovered during integration

As of 2026-09-12, current OpenAI documentation states that ChatGPT **GPT-Live-1 / Live Voice does not initially support connected apps or plugins**. Therefore native ChatGPT Live cannot currently invoke this MCP gateway even though the gateway itself is real and operational.

Additionally, full custom MCP with write/modify actions is currently documented for Business / Enterprise / Edu; Pro has a more limited custom-MCP path. The current native consumer plan must not be assumed to have full custom MCP write access.

Consequences:

1. Do NOT attempt to fix native GPT-Live bridge access by adding more Custom Instructions. Instructions cannot create a missing tool surface.
2. Do NOT tell native GPT-Live that an `omega_*` tool is available unless that surface actually exposes it.
3. The MCP gateway is valid for supported ChatGPT app/plugin surfaces and future Voice support, but is not presently a route into native GPT-Live.
4. For fully actionable realtime speech today, the canonical FranKenstein/OMEGA Realtime runtime remains the supported path because it already exposes real `frank_*` tools inside its own Realtime session.
5. Do not expose the local MCP service publicly merely to satisfy GPT-Live; current Live cannot consume it. Keep loopback/private unless a supported consumer requires remote ingress.

## Promotion state

- `MCP_SOURCE_MERGED=1`
- `MCP_SOURCE_REAL_HOST_TESTED=1`
- `MCP_PRODUCTION_SERVICE_ACTIVE=1`
- `MCP_PROTOCOL_TOOL_LIST_PROVEN=1`
- `MCP_STATUS_TO_REAL_HOST_RECEIPT_PROVEN=1`
- `MCP_EXEC_TO_REAL_HOST_RECEIPT_PROVEN=1`
- `NATIVE_GPT_LIVE_PLUGIN_SUPPORT=0` (OpenAI product boundary as documented on 2026-09-12)

Future work must preserve the distinction between **tool capability** and **prompt knowledge about capability**.
