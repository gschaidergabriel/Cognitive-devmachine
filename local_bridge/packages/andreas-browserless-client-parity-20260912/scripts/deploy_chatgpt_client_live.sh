#!/usr/bin/env bash
set -euo pipefail

EXPECTED_USER="ai-core-node"
EXPECTED_HOST="ai-core-node-projekt-frankenstein"
DB="$HOME/.local/share/agentzero/unified.db"
LIVE_STAR="$HOME/.claude/star"
LIVE_STERN="$LIVE_STAR/stern.py"
DEST="$HOME/.local/lib/frankenstein"
SYSTEMD_DIR="$HOME/.config/systemd/user"
CFG_DIR="$HOME/.config/frankenstein"
ENVF="$CFG_DIR/chatgpt-client.env"
SERVICE="frankenstein-chatgpt-client.service"
PORT=8765

fail(){ echo "DEPLOY_FAIL:$*" >&2; exit 1; }

[[ "$(id -un)" == "$EXPECTED_USER" ]] || fail "unix_user=$(id -un)"
[[ "$(hostname)" == "$EXPECTED_HOST" ]] || fail "kernel_hostname=$(hostname)"
[[ -s "$DB" ]] || fail "canonical_db_missing=$DB"
[[ -s "$LIVE_STERN" ]] || fail "live_stern_missing=$LIVE_STERN"

VOICE_PID_BEFORE="$(systemctl --user show frankenstein-gespraechsmodus.service -p MainPID --value || true)"
VOICE_PID_BEFORE="${VOICE_PID_BEFORE:-0}"
echo "VOICE_PID_BEFORE=$VOICE_PID_BEFORE"

if ss -ltnH "sport = :$PORT" | grep -q .; then
  fail "port_${PORT}_already_in_use"
fi

mkdir -p "$CFG_DIR" "$SYSTEMD_DIR" "$DEST"
umask 077
TOKEN=""
if [[ -f "$ENVF" ]]; then
  TOKEN="$(sed -n 's/^FRANK_VOICE_BROKER_TOKEN=//p' "$ENVF" | head -n1 || true)"
fi
if [[ -z "$TOKEN" ]]; then
  TOKEN="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
)"
fi
TMP="$(mktemp "$CFG_DIR/.chatgpt-client.env.XXXXXX")"
cat >"$TMP" <<EOF
FRANK_VOICE_MACHINE_ID=ai-core-node
FRANK_VOICE_OWNER=gabriel
FRANK_VOICE_PERSON=gabriel
FRANK_VOICE_DB_PATH=$DB
FRANK_VOICE_BROKER_TOKEN=$TOKEN
FRANK_VOICE_BROKER_BIND=127.0.0.1
FRANK_VOICE_BROKER_PORT=$PORT
FRANK_CHATGPT_SESSION_TTL_S=1800
FRANK_CHATGPT_MAX_SESSIONS=16
FRANK_LIVE_STAR_DIR=$LIVE_STAR
EOF
chmod 600 "$TMP"
mv "$TMP" "$ENVF"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 -m py_compile \
  "$ROOT/scripts/voice_host_live_client.py" \
  "$ROOT/scripts/voice_host_agent.py" \
  "$ROOT/scripts/frankenstein_identity_assembly.py" \
  "$ROOT/scripts/f2wp1207_titan_mc.py"

rsync -a --delete --exclude '.git' --exclude '__pycache__' "$ROOT/" "$DEST/"
chmod +x "$DEST/scripts/voice_host_live_client.py" "$DEST/scripts/voice_host_agent.py"
cp "$DEST/scripts/systemd/frankenstein-chatgpt-client.service" "$SYSTEMD_DIR/$SERVICE"

systemctl --user daemon-reload
systemctl --user enable --now "$SERVICE" >/dev/null
systemctl --user is-active --quiet "$SERVICE" || {
  systemctl --user status --no-pager "$SERVICE" >&2 || true
  fail "client_service_not_active"
}
CLIENT_PID="$(systemctl --user show "$SERVICE" -p MainPID --value)"
echo "CLIENT_PID=$CLIENT_PID"

python3 - "$TOKEN" "$PORT" <<'PY'
import json, sys, time, urllib.request

token, port = sys.argv[1], int(sys.argv[2])
base = f"http://127.0.0.1:{port}"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def call(method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

health = call("GET", "/health")
assert health["ok"] is True
assert health["machine_id"] == "ai-core-node"
assert health["owner"] == "gabriel"
assert health["person"] == "gabriel"
assert health["persistent_client"] is True
print("HEALTH_OK")

sid = f"smoke-gabriel-{int(time.time())}"
opened = call("POST", "/v1/session/open", {"session_id": sid})
assert opened["session"]["identity_state"] == "IDENTITY_REQUIRED"
assert opened["session"]["selected_person"] is None
print("OPEN_OK")

selected = call("POST", "/v1/session/select", {"session_id": sid, "person": "gabriel"})
assert selected["session"]["identity_state"] == "BOUND"
print("SELECT_OK runtime_epoch_id=" + str(selected["session"].get("runtime_epoch_id")))

turn = call("POST", "/v1/session/turn-context", {
    "session_id": sid,
    "query": "Wer bist du und mit wem sprichst du gerade?",
    "char_budget": 1800,
})
assert turn["ok"] is True and turn["person"] == "gabriel"
assembly = turn.get("identity_active_assembly", "")
assert "FranKenstein" in assembly and "gabriel" in assembly.lower()
assert "titan_context" in turn and "state" in turn
print("TURN_CONTEXT_OK identity_bytes=%d titan_bytes=%d emergent_bytes=%d" % (
    len(assembly), len(turn.get("titan_context", "")), len(turn.get("emergent_context", ""))))

closed = call("POST", "/v1/session/close", {"session_id": sid, "reason": "smoke_complete"})
assert closed["ok"] is True and closed["closed"] is True
print("CLOSE_OK")
PY

VOICE_PID_AFTER="$(systemctl --user show frankenstein-gespraechsmodus.service -p MainPID --value || true)"
VOICE_PID_AFTER="${VOICE_PID_AFTER:-0}"
echo "VOICE_PID_AFTER=$VOICE_PID_AFTER"
[[ "$VOICE_PID_BEFORE" == "$VOICE_PID_AFTER" ]] || fail "conversation_service_restarted"

if pstree -ap "$CLIENT_PID" 2>/dev/null | grep -Eiq 'chrome|chromium'; then
  fail "client_spawned_browser_descendant"
fi

echo "NO_VOICE_RESTART=PASS"
echo "CLIENT_BROWSER_DESCENDANTS=0"
echo "DEPLOYMENT=PASS"
