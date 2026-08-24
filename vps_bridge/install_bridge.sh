#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "RUN_AS_ROOT: sudo bash install_bridge.sh" >&2
  exit 2
fi

REPO_URL="https://github.com/gschaidergabriel/clay-global-research-entity.git"
CONTROL_BRANCH="gpt56sol/vps-chatgpt-bridge-20260824"
ROOT="/srv/clay-gpt"
USER_NAME="claybot"
SERVICE="clay-gpt-bridge.service"

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates curl git gh jq python3 podman uidmap slirp4netns fuse-overlayfs \
  git-lfs rsync procps util-linux

if ! id "$USER_NAME" >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash "$USER_NAME"
fi

if ! grep -q "^${USER_NAME}:" /etc/subuid; then
  usermod --add-subuids 200000-265535 "$USER_NAME"
fi
if ! grep -q "^${USER_NAME}:" /etc/subgid; then
  usermod --add-subgids 200000-265535 "$USER_NAME"
fi

install -d -o "$USER_NAME" -g "$USER_NAME" -m 0750 \
  "$ROOT" "$ROOT/control" "$ROOT/repo" "$ROOT/worktrees" "$ROOT/cache" \
  "$ROOT/models" "$ROOT/tools" "$ROOT/logs" "$ROOT/state"
install -d -o root -g "$USER_NAME" -m 0750 /etc/clay-gpt

run_claybot() {
  runuser -u "$USER_NAME" -- env HOME="/home/$USER_NAME" "$@"
}

TOKEN="${GH_TOKEN:-}"
if [[ -z "$TOKEN" ]]; then
  TOKEN="$(gh auth token 2>/dev/null || true)"
fi
if [[ -z "$TOKEN" && -n "${SUDO_USER:-}" && "${SUDO_USER}" != root ]]; then
  TOKEN="$(runuser -u "$SUDO_USER" -- gh auth token 2>/dev/null || true)"
fi
if [[ -z "$TOKEN" ]]; then
  cat >&2 <<'EOF'
GITHUB_AUTH_REQUIRED
Authenticate once on this VPS with:
  gh auth login
Then rerun:
  sudo bash install_bridge.sh
The token must never be pasted into chat or committed.
EOF
  exit 10
fi

umask 027
cat > /etc/clay-gpt/bridge.env <<EOF
GH_TOKEN=${TOKEN}
CLAY_BRIDGE_ROOT=${ROOT}
CLAY_CONTROL_BRANCH=${CONTROL_BRANCH}
CLAY_REPOSITORY=${REPO_URL}
CLAY_SANDBOX_IMAGE=localhost/clay-gpt-dev:ubuntu24
CLAY_POLL_SECONDS=20
EOF
chown root:"$USER_NAME" /etc/clay-gpt/bridge.env
chmod 0640 /etc/clay-gpt/bridge.env
unset TOKEN

run_claybot git config --global user.name "Clay VPS Bridge"
run_claybot git config --global user.email "clay-vps-bridge@localhost"
run_claybot git config --global init.defaultBranch main
run_claybot git config --global credential.helper '!gh auth git-credential'

set -a
source /etc/clay-gpt/bridge.env
set +a

if [[ ! -d "$ROOT/control/.git" ]]; then
  rm -rf "$ROOT/control"
  run_claybot env GH_TOKEN="$GH_TOKEN" \
    git clone --branch "$CONTROL_BRANCH" --single-branch "$REPO_URL" "$ROOT/control"
else
  run_claybot env GH_TOKEN="$GH_TOKEN" git -C "$ROOT/control" fetch origin "$CONTROL_BRANCH"
  run_claybot env GH_TOKEN="$GH_TOKEN" git -C "$ROOT/control" checkout "$CONTROL_BRANCH"
  run_claybot env GH_TOKEN="$GH_TOKEN" git -C "$ROOT/control" reset --hard "origin/$CONTROL_BRANCH"
fi

if [[ ! -d "$ROOT/repo/.git" ]]; then
  rm -rf "$ROOT/repo"
  run_claybot env GH_TOKEN="$GH_TOKEN" git clone "$REPO_URL" "$ROOT/repo"
else
  run_claybot env GH_TOKEN="$GH_TOKEN" git -C "$ROOT/repo" fetch origin --prune
fi

chmod 0755 "$ROOT/control/vps_bridge/bin/webfetch" "$ROOT/control/vps_bridge/bin/hffetch"
chmod 0755 "$ROOT/control/vps_bridge/bridge_runner.py"

cat > "/etc/systemd/system/$SERVICE" <<EOF
[Unit]
Description=Clay ChatGPT pull-only VPS sandbox bridge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${USER_NAME}
Group=${USER_NAME}
Environment=HOME=/home/${USER_NAME}
Environment=XDG_RUNTIME_DIR=/run/clay-gpt
EnvironmentFile=/etc/clay-gpt/bridge.env
RuntimeDirectory=clay-gpt
RuntimeDirectoryMode=0700
WorkingDirectory=${ROOT}/control/vps_bridge
ExecStart=/usr/bin/python3 ${ROOT}/control/vps_bridge/bridge_runner.py
Restart=always
RestartSec=5
TimeoutStopSec=30
PrivateTmp=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now "$SERVICE"
sleep 3

if ! systemctl is-active --quiet "$SERVICE"; then
  echo "BRIDGE_SERVICE_FAILED" >&2
  journalctl -u "$SERVICE" -n 160 --no-pager >&2 || true
  exit 20
fi

cat <<EOF
BRIDGE_INSTALLED
service=${SERVICE}
root=${ROOT}
control_branch=${CONTROL_BRANCH}
selftest_inbox=vps_bridge/inbox/SELFTEST_BOOTSTRAP.json
selftest_expected_outbox=vps_bridge/outbox/SELFTEST_BOOTSTRAP.json

The first rootless Podman image build can take several minutes. Watch with:
  sudo journalctl -u ${SERVICE} -f
EOF
