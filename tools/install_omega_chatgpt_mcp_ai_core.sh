#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/.local/lib/omega-chatgpt-mcp"
CFG="$HOME/.config/omega"
ENV_FILE="$CFG/omega-mcp.env"
UNIT_DIR="$HOME/.config/systemd/user"
UNIT="$UNIT_DIR/omega-chatgpt-mcp.service"
PORT="${OMEGA_MCP_PORT:-8789}"

mkdir -p "$DEST" "$CFG" "$UNIT_DIR"
install -m 0755 "$HERE/omega_chatgpt_mcp.py" "$DEST/omega_chatgpt_mcp.py"
install -m 0644 "$HERE/omega_grid_relay.py" "$DEST/omega_grid_relay.py"

if [[ ! -s "$ENV_FILE" ]]; then
  umask 077
  TOKEN="$(python3 - <<'PY'
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
EOF
  chmod 0600 "$ENV_FILE"
else
  chmod 0600 "$ENV_FILE"
fi

cat >"$DEST/run.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  if ! command -v gh >/dev/null 2>&1; then
    echo "gh CLI missing and GITHUB_TOKEN unset" >&2
    exit 78
  fi
  GITHUB_TOKEN="$(gh auth token)"
  export GITHUB_TOKEN
fi
exec python3 "$HOME/.local/lib/omega-chatgpt-mcp/omega_chatgpt_mcp.py"
EOF
chmod 0755 "$DEST/run.sh"

cat >"$UNIT" <<EOF
[Unit]
Description=OMEGA ChatGPT MCP Bridge Gateway
After=network-online.target frankenstein-local-bridge.service
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=%h/.config/omega/omega-mcp.env
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
systemctl --user enable --now omega-chatgpt-mcp.service
sleep 0.4
systemctl --user is-active --quiet omega-chatgpt-mcp.service

# Never print OMEGA_MCP_TOKEN.  Health is deliberately non-secret.
python3 - <<PY
import json, urllib.request
with urllib.request.urlopen("http://127.0.0.1:${PORT}/health", timeout=3) as r:
    data=json.loads(r.read().decode())
assert data.get("ok") is True, data
print(json.dumps({"service":"omega-chatgpt-mcp.service","active":True,"health":data}, separators=(",",":")))
PY
