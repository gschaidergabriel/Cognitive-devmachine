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
  git-lfs rsync procps

if ! id "$USER_NAME" >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash "$USER_NAME"
fi

# Ensure rootless user-namespace ranges exist. New Ubuntu users normally get these
# automatically; only add a private range if the system did not create one.
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

# Acquire an already-authorized local GitHub CLI token without printing it.
TOKEN="${GH_TOKEN:-}"
if [[ -z "$TOKEN" ]] && command -v gh >/dev/null 2>&1; then
  TOKEN="$(gh auth token 2>/dev/null || true)"
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

# Git identity for host-side result commits and task branches.
sudo -u "$USER_NAME" -H git config --global user.name "Clay VPS Bridge"
sudo -u "$USER_NAME" -H git config --global user.email "clay-vps-bridge@localhost"
sudo -u "$USER_NAME" -H git config --global init.defaultBranch main
sudo -u "$USER_NAME" -H git config --global credential.helper '!gh auth git-credential'

# Clone/update the control checkout with the token present only in host process env.
set -a
source /etc/clay-gpt/bridge.env
set +a
if [[ ! -d "$ROOT/control/.git" ]]; then
  rm -rf "$ROOT/control"
  sudo -u "$USER_NAME" -H env GH_TOKEN="$GH_TOKEN" \
    git clone --branch "$CONTROL_BRANCH" --single-branch "$REPO_URL" "$ROOT/control"
else
  sudo -u "$USER_NAME" -H env GH_TOKEN="$GH_TOKEN" \
    git -C "$ROOT/control" fetch origin "$CONTROL_BRANCH"
  sudo -u "$USER_NAME" -H env GH_TOKEN="$GH_TOKEN" \
    git -C "$ROOT/control" checkout "$CONTROL_BRANCH"
  sudo -u "$USER_NAME" -H env GH_TOKEN="$GH_TOKEN" \
    git -C "$ROOT/control" reset --hard "origin/$CONTROL_BRANCH"
fi

# Separate canonical clone. Task containers never receive the token; only host git does.
if [[ ! -d "$ROOT/repo/.git" ]]; then
  rm -rf "$ROOT/repo"
  sudo -u "$USER_NAME" -H env GH_TOKEN="$GH_TOKEN" \
    git clone "$REPO_URL" "$ROOT/repo"
else
  sudo -u "$USER_NAME" -H env GH_TOKEN="$GH_TOKEN" \
    git -C "$ROOT/repo" fetch origin --prune
fi

chmod 0755 "$ROOT/control/vps_bridge/bin/webfetch" "$ROOT/control/vps_bridge/bin/hffetch"
chmod 0755 "$ROOT/control/vps_bridge/bridge_runner.py"

# Rootless Podman requires a runtime dir owned by claybot. systemd creates it below.
USER_UID="$(id -u "$USER_NAME")"

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
NoNewPrivileges=true
PrivateTmp=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now "$SERVICE"

# Give first image build time to start, then show exact state.
sleep 3
systemctl --no-pager --full status "$SERVICE" || true

if ! systemctl is-active --quiet "$SERVICE"; then
  echo "BRIDGE_SERVICE_FAILED" >&2
  journalctl -u "$SERVICE" -n 120 --no-pager >&2 || true
  exit 20
fi

cat <<EOF
BRIDGE_INSTALLED
service=${SERVICE}
root=${ROOT}
control_branch=${CONTROL_BRANCH}
selftest_inbox=vps_bridge/inbox/SELFTEST_BOOTSTRAP.json
selftest_expected_outbox=vps_bridge/outbox/SELFTEST_BOOTSTRAP.json

The first Podman image build can take several minutes. Watch with:
  sudo journalctl -u ${SERVICE} -f
EOF
