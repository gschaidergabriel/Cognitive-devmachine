#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "run as root: sudo bash deploy/install.sh" >&2
  exit 1
fi

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ROOT=/opt/clay-vps-mcp
RELEASES_DIR="$APP_ROOT/releases"
ENV_FILE=/etc/clay-vps-mcp.env
STATE_DIR=/var/lib/clay-vps-mcp
WORK_DIR=/srv/clay-mcp/workspace
HISTORY_DIR=/srv/clay-history
TELEMETRY_DIR=/srv/frank-telemetry
UDB_BACKUP_DIR=/srv/unifieddb-backups
STAMP="$(date -u +%Y%m%dT%H%M%SZ)-$$"
RELEASE_DIR="$RELEASES_DIR/$STAMP"

if ! id clay-mcp >/dev/null 2>&1; then
  useradd --system --home-dir "$STATE_DIR" --create-home --shell /usr/sbin/nologin clay-mcp
fi

install -d -m 0755 "$APP_ROOT" "$RELEASES_DIR"
install -d -o clay-mcp -g clay-mcp -m 0700 "$STATE_DIR" "$WORK_DIR" "$HISTORY_DIR" "$TELEMETRY_DIR" "$UDB_BACKUP_DIR"
install -d -m 0755 /srv/models /opt/frank /opt/clay
install -d -m 0755 "$RELEASE_DIR"

# Append-only release: never delete or overwrite a prior MCP release.
cp -a "$SRC_DIR/pyproject.toml" "$RELEASE_DIR/pyproject.toml"
cp -a "$SRC_DIR/clay_vps_mcp" "$RELEASE_DIR/clay_vps_mcp"
cp -a "$SRC_DIR/deploy" "$RELEASE_DIR/deploy"

python3 -m venv "$RELEASE_DIR/.venv"
"$RELEASE_DIR/.venv/bin/python" -m pip install --upgrade pip
"$RELEASE_DIR/.venv/bin/pip" install "$RELEASE_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  mcp_token="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
)"
  telemetry_token="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
)"
  cat >"$ENV_FILE" <<EOF
CLAY_MCP_BIND=127.0.0.1
CLAY_MCP_PORT=8765
CLAY_MCP_TOKEN=$mcp_token
CLAY_MCP_ALLOWED_HOSTS=127.0.0.1:*,localhost:*,[::1]:*
CLAY_MCP_ALLOWED_ORIGINS=http://127.0.0.1:*,http://localhost:*,http://[::1]:*
CLAY_MCP_FORWARDED_ALLOW_IPS=127.0.0.1
CLAY_MCP_ALLOWED_ROOTS=/srv/clay-mcp/workspace,/srv/models,/opt/frank,/opt/clay
CLAY_MCP_STATE_DIR=/var/lib/clay-vps-mcp
CLAY_MCP_MAX_TIMEOUT=7200
CLAY_HISTORY_REPO=/srv/clay-history
CLAY_HISTORY_POLL_SECONDS=1.0
FRANK_TELEMETRY_BIND=127.0.0.1
FRANK_TELEMETRY_PORT=8766
FRANK_TELEMETRY_INGEST_TOKEN=$telemetry_token
FRANK_TELEMETRY_DIR=/srv/frank-telemetry
FRANK_TELEMETRY_DB=/srv/frank-telemetry/frank_telemetry.sqlite3
FRANK_TELEMETRY_TOTAL_BUDGET_BYTES=10737418240
FRANK_TELEMETRY_MAIN_BUDGET_BYTES=9663676416
FRANK_TELEMETRY_WAL_LIMIT_BYTES=268435456
FRANK_TELEMETRY_PRESSURE_FRACTION=0.85
FRANK_TELEMETRY_CLEANUP_TARGET_FRACTION=0.72
FRANK_UNIFIEDDB_BACKUP_ROOT=/srv/unifieddb-backups
FRANK_UNIFIEDDB_BACKUP_BUDGET_BYTES=53687091200
FRANK_UNIFIEDDB_PATHS=
FRANK_UNIFIEDDB_DISCOVERY_ROOTS=/opt/frank,/srv/clay-mcp/workspace
FRANK_UNIFIEDDB_DISCOVERY_PATTERNS=*unified*.db,*unified*.sqlite,*unified*.sqlite3
FRANK_API_BASE_URL=http://127.0.0.1:8080/
FRANK_API_TOKEN=
FRANK_API_TOKEN_HEADER=Authorization
FRANK_API_TOKEN_PREFIX=Bearer 
FRANK_API_HEALTH_PATH=/health
FRANK_API_ALLOWED_PATH_PREFIXES=/health,/status,/v1/models,/v1/chat,/v1/chat/completions,/chat,/message
EOF
  chmod 0600 "$ENV_FILE"
  chown root:root "$ENV_FILE"
  echo "Created $ENV_FILE. Add FRANK_API_TOKEN when Frank's persistent API is ready."
else
  echo "Preserving existing $ENV_FILE unchanged. Add new variables manually if upgrading an older install."
fi

# Atomic symlink switch; all old releases remain intact for rollback.
ln -s "$RELEASE_DIR" "$APP_ROOT/current.next"
mv -Tf "$APP_ROOT/current.next" "$APP_ROOT/current"

for unit in clay-vps-mcp.service clay-vps-history.service frank-telemetry.service unifieddb-backup.service unifieddb-backup.timer; do
  install -m 0644 "$SRC_DIR/deploy/$unit" "/etc/systemd/system/$unit"
done
systemctl daemon-reload
systemctl enable clay-vps-mcp.service clay-vps-history.service frank-telemetry.service unifieddb-backup.timer
systemctl restart clay-vps-mcp.service
systemctl restart clay-vps-history.service
systemctl restart frank-telemetry.service
systemctl restart unifieddb-backup.timer
sleep 1

curl --fail --silent --show-error http://127.0.0.1:8765/healthz
printf '\n'
curl --fail --silent --show-error http://127.0.0.1:8766/healthz
printf '\nClay VPS stack installed.\nMCP: http://127.0.0.1:8765/mcp\nTelemetry ingest: http://127.0.0.1:8766/v1/events\nHistory: %s\nTelemetry DB: %s\nUnifiedDB backups: %s\nRelease: %s\n' "$HISTORY_DIR" "$TELEMETRY_DIR/frank_telemetry.sqlite3" "$UDB_BACKUP_DIR" "$RELEASE_DIR"
