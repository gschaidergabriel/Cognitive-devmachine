#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/.local/lib/omega-chatgpt-mcp"
STATE="$HOME/.local/state/omega-chatgpt-mcp"
CFG="$HOME/.config/omega"
ENV_FILE="$CFG/omega-mcp.env"
UNIT_DIR="$HOME/.config/systemd/user"
UNIT="$UNIT_DIR/omega-chatgpt-mcp.service"
ADAPTER_UNIT="$UNIT_DIR/omega-local-effect-adapter.service"
PORT="${OMEGA_MCP_PORT:-8789}"
UID_NUM="$(id -u)"
LOCAL_SOCKET="/run/user/${UID_NUM}/omega-local-effect.sock"

mkdir -p "$DEST" "$STATE" "$CFG" "$UNIT_DIR"
install -m 0755 "$HERE/omega_chatgpt_mcp.py" "$DEST/omega_chatgpt_mcp.py"
install -m 0755 "$HERE/omega_chatgpt_mcp_fallback.py" "$DEST/omega_chatgpt_mcp_fallback.py"
install -m 0755 "$HERE/omega_local_effect_adapter.py" "$DEST/omega_local_effect_adapter.py"
install -m 0644 "$HERE/omega_grid_relay.py" "$DEST/omega_grid_relay.py"

if [[ ! -s "$ENV_FILE" ]]; then
  umask 077
  TOKEN="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
)"
  LOCAL_TOKEN="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
)"
  cat >"$ENV_FILE" <<EOF
OMEGA_MCP_TOKEN=$TOKEN
OMEGA_MCP_BIND=127.0.0.1
OMEGA_MCP_PORT=$PORT
OMEGA_MCP_EFFECTS_ENABLED=1
OMEGA_MCP_WAIT_SECONDS=12
OMEGA_MCP_GATEWAY_MACHINE_ID=ai-core-node
OMEGA_MCP_GATEWAY_OWNER=gabriel
OMEGA_MCP_DIRECT_GABRIEL_URL=http://127.0.0.1:8765
OMEGA_MCP_LOCAL_FALLBACK_ENABLED=1
OMEGA_LOCAL_EFFECT_SOCKET=$LOCAL_SOCKET
OMEGA_LOCAL_EFFECT_DB=$STATE/local-effect.sqlite3
OMEGA_LOCAL_BRIDGE_ENGINE=$HOME/.claude/star/local_bridge_daemon.py
OMEGA_LOCAL_EFFECT_TOKEN=$LOCAL_TOKEN
EOF
else
  chmod 0600 "$ENV_FILE"
  ensure_kv() {
    local key="$1" value="$2"
    if ! grep -q "^${key}=" "$ENV_FILE"; then
      printf '%s=%s\n' "$key" "$value" >>"$ENV_FILE"
    fi
  }
  ensure_kv OMEGA_MCP_GATEWAY_MACHINE_ID ai-core-node
  ensure_kv OMEGA_MCP_GATEWAY_OWNER gabriel
  ensure_kv OMEGA_MCP_DIRECT_GABRIEL_URL http://127.0.0.1:8765
  ensure_kv OMEGA_MCP_LOCAL_FALLBACK_ENABLED 1
  ensure_kv OMEGA_LOCAL_EFFECT_SOCKET "$LOCAL_SOCKET"
  ensure_kv OMEGA_LOCAL_EFFECT_DB "$STATE/local-effect.sqlite3"
  ensure_kv OMEGA_LOCAL_BRIDGE_ENGINE "$HOME/.claude/star/local_bridge_daemon.py"
  if ! grep -q '^OMEGA_LOCAL_EFFECT_TOKEN=' "$ENV_FILE"; then
    LOCAL_TOKEN="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
)"
    printf 'OMEGA_LOCAL_EFFECT_TOKEN=%s\n' "$LOCAL_TOKEN" >>"$ENV_FILE"
  fi
fi
chmod 0600 "$ENV_FILE"

cat >"$DEST/run.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
# GitHub is a recovery/remote plane, not a process-start dependency anymore.
if [[ -z "${GITHUB_TOKEN:-}" ]] && command -v gh >/dev/null 2>&1; then
  GITHUB_TOKEN="$(gh auth token 2>/dev/null || true)"
  export GITHUB_TOKEN
fi
exec python3 "$HOME/.local/lib/omega-chatgpt-mcp/omega_chatgpt_mcp_fallback.py"
EOF
chmod 0755 "$DEST/run.sh"

cat >"$DEST/run-local-adapter.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec python3 "$HOME/.local/lib/omega-chatgpt-mcp/omega_local_effect_adapter.py"
EOF
chmod 0755 "$DEST/run-local-adapter.sh"

cat >"$ADAPTER_UNIT" <<EOF
[Unit]
Description=OMEGA local Unix effect fallback adapter (ai-core-node only)
After=network-online.target frankenstein-local-bridge.service
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=%h/.config/omega/omega-mcp.env
ExecStart=%h/.local/lib/omega-chatgpt-mcp/run-local-adapter.sh
Restart=on-failure
RestartSec=2
NoNewPrivileges=yes
UMask=0077

[Install]
WantedBy=default.target
EOF

cat >"$UNIT" <<EOF
[Unit]
Description=OMEGA ChatGPT MCP Bridge Gateway with verified transport fallback
After=network-online.target omega-local-effect-adapter.service frankenstein-chatgpt-client.service
Wants=network-online.target omega-local-effect-adapter.service

[Service]
Type=simple
EnvironmentFile=%h/.config/omega/omega-mcp.env
# Reuse the existing typed host-broker token in memory; never copy or print it.
EnvironmentFile=-%h/.config/frankenstein/chatgpt-client.env
ExecStart=%h/.local/lib/omega-chatgpt-mcp/run.sh
Restart=on-failure
RestartSec=3
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=%h/.config/omega %h/.local/lib/omega-chatgpt-mcp

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now omega-local-effect-adapter.service
systemctl --user enable --now omega-chatgpt-mcp.service
# `enable --now` does not replace an already-running process after an upgrade.
# Restart explicitly so deployed bytes and running bytes cannot drift.
systemctl --user restart omega-local-effect-adapter.service
systemctl --user restart omega-chatgpt-mcp.service
sleep 0.5
systemctl --user is-active --quiet omega-local-effect-adapter.service
systemctl --user is-active --quiet omega-chatgpt-mcp.service

# Never print either bearer token.
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
python3 - <<PY
import json,os,socket,urllib.request
with urllib.request.urlopen("http://127.0.0.1:${PORT}/health", timeout=3) as r:
    health=json.loads(r.read().decode())
assert health.get("ok") is True, health
s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.settimeout(2); s.connect(os.environ["OMEGA_LOCAL_EFFECT_SOCKET"])
req={"schema":"OMEGA_LOCAL_EFFECT/v1","token":os.environ["OMEGA_LOCAL_EFFECT_TOKEN"],"kind":"health"}
s.sendall(json.dumps(req,separators=(",",":")).encode()+b"\n")
local=json.loads(s.recv(65536).split(b"\n",1)[0].decode()); s.close()
assert local.get("ok") is True, local
print(json.dumps({"mcp_service":"active","local_adapter":"active","mcp_health":health,"local_identity":{"machine_id":local.get("machine_id"),"owner":local.get("owner")}},separators=(",",":")))
PY