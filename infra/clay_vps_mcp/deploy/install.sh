#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "run as root: sudo bash deploy/install.sh" >&2
  exit 1
fi

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR=/opt/clay-vps-mcp
ENV_FILE=/etc/clay-vps-mcp.env
STATE_DIR=/var/lib/clay-vps-mcp
WORK_DIR=/srv/clay-mcp/workspace

if ! id clay-mcp >/dev/null 2>&1; then
  useradd --system --home-dir "$STATE_DIR" --create-home --shell /usr/sbin/nologin clay-mcp
fi

install -d -m 0755 "$APP_DIR"
install -d -o clay-mcp -g clay-mcp -m 0700 "$STATE_DIR" "$WORK_DIR"
install -d -m 0755 /srv/models /opt/frank /opt/clay

# Copy source without deleting anything already on the VPS.
cp -a "$SRC_DIR/pyproject.toml" "$APP_DIR/pyproject.toml"
rm -rf "$APP_DIR/clay_vps_mcp.new"
cp -a "$SRC_DIR/clay_vps_mcp" "$APP_DIR/clay_vps_mcp.new"
if [[ -d "$APP_DIR/clay_vps_mcp" ]]; then
  backup="$STATE_DIR/install-backups/clay_vps_mcp-$(date -u +%Y%m%dT%H%M%SZ)"
  install -d -o clay-mcp -g clay-mcp -m 0700 "$(dirname "$backup")"
  cp -a "$APP_DIR/clay_vps_mcp" "$backup"
fi
mv -T "$APP_DIR/clay_vps_mcp.new" "$APP_DIR/clay_vps_mcp"

python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/python" -m pip install --upgrade pip
"$APP_DIR/.venv/bin/pip" install "$APP_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  token="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
)"
  cat >"$ENV_FILE" <<EOF
CLAY_MCP_BIND=127.0.0.1
CLAY_MCP_PORT=8765
CLAY_MCP_TOKEN=$token
CLAY_MCP_ALLOWED_HOSTS=127.0.0.1:*,localhost:*,[::1]:*
CLAY_MCP_ALLOWED_ORIGINS=http://127.0.0.1:*,http://localhost:*,http://[::1]:*
CLAY_MCP_FORWARDED_ALLOW_IPS=127.0.0.1
CLAY_MCP_ALLOWED_ROOTS=/srv/clay-mcp/workspace,/srv/models,/opt/frank,/opt/clay
CLAY_MCP_STATE_DIR=/var/lib/clay-vps-mcp
CLAY_MCP_MAX_TIMEOUT=7200
FRANK_API_BASE_URL=http://127.0.0.1:8080/
FRANK_API_TOKEN=
FRANK_API_TOKEN_HEADER=Authorization
FRANK_API_TOKEN_PREFIX=Bearer 
FRANK_API_HEALTH_PATH=/health
FRANK_API_ALLOWED_PATH_PREFIXES=/health,/status,/v1/models,/v1/chat,/v1/chat/completions,/chat,/message
EOF
  chmod 0600 "$ENV_FILE"
  chown root:root "$ENV_FILE"
  echo "Created $ENV_FILE. Add the existing FRANK_API_TOKEN before expecting Frank API calls to work."
else
  echo "Preserving existing $ENV_FILE unchanged."
fi

install -m 0644 "$SRC_DIR/deploy/clay-vps-mcp.service" /etc/systemd/system/clay-vps-mcp.service
systemctl daemon-reload
systemctl enable --now clay-vps-mcp.service
sleep 1
systemctl --no-pager --full status clay-vps-mcp.service || true
curl --fail --silent --show-error http://127.0.0.1:8765/healthz
printf '\nClay VPS MCP installed. Endpoint: http://127.0.0.1:8765/mcp\n'
