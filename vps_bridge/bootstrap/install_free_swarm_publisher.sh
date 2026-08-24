#!/usr/bin/env bash
set -Eeuo pipefail

# Host-side narrowly scoped publisher. It executes no research workload on the
# host; it only reads sandbox artifact mounts, regenerates dashboard files in a
# dedicated checkout, and pushes those derived metrics to main.
[[ ${EUID:-$(id -u)} -eq 0 ]] || { echo 'root required for one-time service install' >&2; exit 2; }

BASE=/srv/claylab
USER_NAME=claylab
REPO=gschaidergabriel/clay-global-research-entity
KEY="$BASE/.ssh/chatgpt_vps_ed25519"
KNOWN="$BASE/.ssh/known_hosts"
PUB="$BASE/free-swarm-publisher"
ART="$BASE/artifacts/clay-entityos-swarm"
BIN="$BASE/bin/clay-free-swarm-publisher"
STATE="$BASE/state/free-swarm-publisher"
UNIT_DIR="$BASE/.config/systemd/user"
RUNTIME="/run/user/$(id -u "$USER_NAME")"

install -d -o "$USER_NAME" -g "$USER_NAME" "$BASE/bin" "$STATE" "$UNIT_DIR" "$ART"

as_clay() {
  runuser -u "$USER_NAME" -- env HOME="$BASE" XDG_RUNTIME_DIR="$RUNTIME" \
    GIT_SSH_COMMAND="ssh -i $KEY -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$KNOWN" \
    bash -lc "cd '$BASE'; $*"
}

if [[ ! -d "$PUB/.git" ]]; then
  as_clay "git clone git@github.com:$REPO.git '$PUB'"
else
  as_clay "git -C '$PUB' fetch origin main --prune"
fi
as_clay "git -C '$PUB' config user.name 'Clay Free Swarm Metrics'"
as_clay "git -C '$PUB' config user.email 'clay-free-swarm@localhost'"

cat > "$BIN" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
BASE=/srv/claylab
PUB="$BASE/free-swarm-publisher"
ART="$BASE/artifacts/clay-entityos-swarm"
KEY="$BASE/.ssh/chatgpt_vps_ed25519"
KNOWN="$BASE/.ssh/known_hosts"
LOCK="$BASE/state/free-swarm-publisher/lock"
INTERVAL="${CLAY_FREE_SWARM_PUBLISH_SECONDS:-900}"
exec 9>"$LOCK"
flock -n 9 || exit 0
export GIT_SSH_COMMAND="ssh -i $KEY -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$KNOWN"

render_all() {
  [[ ! -f "$PUB/free swarm/merge_forge_evaluations.py" ]] || python3 "$PUB/free swarm/merge_forge_evaluations.py" --repo "$PUB" --artifacts "$ART" >/dev/null
  python3 "$PUB/free swarm/evaluate.py" --repo "$PUB" --artifacts "$ART" >/dev/null
  [[ ! -f "$PUB/free swarm/update_distillery_readme.py" ]] || python3 "$PUB/free swarm/update_distillery_readme.py" --repo "$PUB" --artifacts "$ART" >/dev/null
  [[ ! -f "$PUB/free swarm/update_forge_readme.py" ]] || python3 "$PUB/free swarm/update_forge_readme.py" --repo "$PUB" --artifacts "$ART" >/dev/null
  # Root mirror: make the complete detailed dashboard visible immediately in the
  # repository root instead of requiring users to discover the nested folder.
  cp "$PUB/free swarm/README.md" "$PUB/000_FREE_SWARM_LIVE_DASHBOARD.md"
}

stage_all() {
  git -C "$PUB" add -- "000_FREE_SWARM_LIVE_DASHBOARD.md" "free swarm/README.md" "free swarm/LIVE_METRICS.json" "free swarm/architecture_delta_evaluations.jsonl"
  [[ ! -f "$PUB/free swarm/DISTILLERY_LIVE.json" ]] || git -C "$PUB" add -- "free swarm/DISTILLERY_LIVE.json"
  [[ ! -f "$PUB/free swarm/FORGE_LIVE.json" ]] || git -C "$PUB" add -- "free swarm/FORGE_LIVE.json"
  [[ ! -f "$PUB/free swarm/SYSTEM_ANALYSIS_LIVE.json" ]] || git -C "$PUB" add -- "free swarm/SYSTEM_ANALYSIS_LIVE.json"
}

refresh_once() {
  git -C "$PUB" fetch origin main --prune
  git -C "$PUB" checkout -B main origin/main
  git -C "$PUB" reset --hard origin/main
  render_all
  stage_all
  git -C "$PUB" diff --cached --quiet && return 0
  git -C "$PUB" commit -m "metrics: autonomous Free Swarm + distillery + forge + root dashboard refresh"
  if ! git -C "$PUB" push origin HEAD:main; then
    git -C "$PUB" fetch origin main --prune
    git -C "$PUB" reset --hard origin/main
    render_all
    stage_all
    git -C "$PUB" diff --cached --quiet && return 0
    git -C "$PUB" commit -m "metrics: autonomous Free Swarm + distillery + forge + root dashboard refresh"
    git -C "$PUB" push origin HEAD:main
  fi
}

while true; do
  refresh_once || true
  sleep "$INTERVAL"
done
EOF
chmod 0755 "$BIN"
chown "$USER_NAME:$USER_NAME" "$BIN"

cat > "$UNIT_DIR/clay-free-swarm-publisher.service" <<EOF
[Unit]
Description=Clay Free Swarm autonomous metrics publisher
After=network-online.target

[Service]
Type=simple
ExecStart=$BIN
Restart=always
RestartSec=20
Environment=CLAY_FREE_SWARM_PUBLISH_SECONDS=900

[Install]
WantedBy=default.target
EOF
chown -R "$USER_NAME:$USER_NAME" "$UNIT_DIR"
loginctl enable-linger "$USER_NAME" >/dev/null 2>&1 || true
install -d -m 0700 -o "$USER_NAME" -g "$USER_NAME" "$RUNTIME"

if runuser -u "$USER_NAME" -- env HOME="$BASE" XDG_RUNTIME_DIR="$RUNTIME" systemctl --user daemon-reload >/dev/null 2>&1; then
  runuser -u "$USER_NAME" -- env HOME="$BASE" XDG_RUNTIME_DIR="$RUNTIME" systemctl --user enable --now clay-free-swarm-publisher.service
  sleep 3
  runuser -u "$USER_NAME" -- env HOME="$BASE" XDG_RUNTIME_DIR="$RUNTIME" systemctl --user --no-pager --full status clay-free-swarm-publisher.service | head -40 || true
  echo FREE_SWARM_PUBLISHER_MODE=systemd-user
else
  pkill -u "$USER_NAME" -f '/srv/claylab/bin/clay-free-swarm-publisher' 2>/dev/null || true
  as_clay "nohup '$BIN' >'$STATE/publisher.log' 2>&1 </dev/null & echo \$! >'$STATE/publisher.pid'"
  sleep 3
  as_clay "kill -0 \$(cat '$STATE/publisher.pid')"
  echo FREE_SWARM_PUBLISHER_MODE=nohup
fi

echo FREE_SWARM_PUBLISHER_READY
