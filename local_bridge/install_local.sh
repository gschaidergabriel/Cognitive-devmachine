#!/usr/bin/env bash
set -Eeuo pipefail

REPO='gschaidergabriel/clay-global-research-entity'
CONTROL_BRANCH='chatgpt-local-control'
RESULTS_BRANCH='chatgpt-local-results'
BASE="$HOME/.local/share/clay-local-bridge"
KEY="$BASE/keys/id_ed25519"
KNOWN="$BASE/keys/known_hosts"

if [[ ${EUID:-$(id -u)} -eq 0 ]]; then
  echo 'Run this as your normal desktop user, not root.' >&2
  exit 2
fi

echo '=== CLAY LOCAL DEVELOPMENT BRIDGE ==='
echo "user=$USER home=$HOME"

need=()
for x in git ssh-keygen ssh-keyscan python3 tmux; do command -v "$x" >/dev/null 2>&1 || need+=("$x"); done
if ((${#need[@]})); then
  echo "Installing missing development prerequisites: ${need[*]}"
  sudo apt-get update
  sudo apt-get install -y git openssh-client python3 tmux
fi

mkdir -p "$BASE/keys" "$BASE/state" "$BASE/jobs" "$BASE/bin" "$HOME/.config/systemd/user"
chmod 700 "$BASE/keys"
if [[ ! -s "$KEY" ]]; then
  ssh-keygen -q -t ed25519 -N '' -f "$KEY" -C "clay-chatgpt-local-bridge-$(hostname)"
fi
ssh-keyscan github.com > "$KNOWN" 2>/dev/null
chmod 600 "$KEY" "$KNOWN"
chmod 644 "$KEY.pub"

GIT_SSH="ssh -i $KEY -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$KNOWN"
export GIT_SSH_COMMAND="$GIT_SSH"

# If the dedicated key is not registered yet, reuse the user's existing authenticated gh session
# only to register this one deploy key. The daemon itself never needs a GitHub token.
if ! git ls-remote "git@github.com:${REPO}.git" HEAD >/dev/null 2>&1; then
  echo 'Dedicated local bridge key is not registered yet.'
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    echo 'Registering dedicated write-enabled Deploy Key with existing GitHub CLI session...'
    gh repo deploy-key add "$KEY.pub" --repo "$REPO" --title "clay-chatgpt-local-bridge-$(hostname)" --allow-write >/dev/null 2>&1 || \
      gh api --method POST "repos/$REPO/keys" -f title="clay-chatgpt-local-bridge-$(hostname)" -f key="$(cat "$KEY.pub")" -F read_only=false >/dev/null
  else
    echo
    echo 'A one-time GitHub authorization is needed. The public key is:'
    cat "$KEY.pub"
    echo
    echo "Add it to $REPO -> Settings -> Deploy keys -> Allow write access, then rerun this installer."
    exit 20
  fi
fi

git ls-remote "git@github.com:${REPO}.git" HEAD >/dev/null
echo 'DEPLOY_KEY_PASS'

clone_branch() {
  local dir="$1" branch="$2"
  if [[ ! -d "$dir/.git" ]]; then
    rm -rf "$dir"
    git clone --filter=blob:none --single-branch --branch "$branch" "git@github.com:${REPO}.git" "$dir"
  else
    git -C "$dir" remote set-url origin "git@github.com:${REPO}.git"
    git -C "$dir" fetch origin "$branch" --prune
    git -C "$dir" checkout -B "$branch" "origin/$branch"
    git -C "$dir" reset --hard "origin/$branch"
  fi
}

clone_branch "$BASE/control-mirror" "$CONTROL_BRANCH"
clone_branch "$BASE/results-mirror" "$RESULTS_BRANCH"
install -m 755 "$BASE/control-mirror/local_bridge/daemon.py" "$BASE/bin/daemon.py"

git -C "$BASE/results-mirror" config user.name 'Clay Local Bridge'
git -C "$BASE/results-mirror" config user.email 'clay-local-bridge@localhost'
git -C "$BASE/control-mirror" config user.name 'Clay Local Bridge'
git -C "$BASE/control-mirror" config user.email 'clay-local-bridge@localhost'

cat > "$HOME/.config/systemd/user/clay-local-bridge.service" <<EOF
[Unit]
Description=Clay ChatGPT local development bridge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Environment="HOME=$HOME"
Environment="GIT_SSH_COMMAND=$GIT_SSH"
ExecStart=/usr/bin/python3 $BASE/bin/daemon.py
WorkingDirectory=$HOME
Restart=always
RestartSec=2
Nice=5

[Install]
WantedBy=default.target
EOF

# Make the user service survive logout/reboot. This is the only system-level configuration.
sudo loginctl enable-linger "$USER" >/dev/null 2>&1 || true
systemctl --user daemon-reload
systemctl --user enable --now clay-local-bridge.service
sleep 2
systemctl --user is-active clay-local-bridge.service | grep -qx active

# Local terminal/persistent-session proof.
tmux new-session -d -s clay-local-selftest 'printf CLAY_LOCAL_TMUX_OK; sleep 3'
sleep 1
tmux capture-pane -p -t clay-local-selftest | grep -q CLAY_LOCAL_TMUX_OK
tmux kill-session -t clay-local-selftest >/dev/null 2>&1 || true

# Wait for the daemon to publish LIVE.json through the dedicated result branch.
echo 'Waiting for local LIVE.json...'
OK=0
for _ in $(seq 1 30); do
  sleep 2
  git -C "$BASE/results-mirror" fetch origin "$RESULTS_BRANCH" >/dev/null 2>&1 || true
  if git -C "$BASE/results-mirror" show "origin/${RESULTS_BRANCH}:local_bridge/results/LIVE.json" > "$BASE/state/LIVE.json" 2>/dev/null; then
    OK=1; break
  fi
done
if [[ "$OK" != 1 ]]; then
  echo 'ERROR: daemon is active but LIVE.json did not arrive.' >&2
  systemctl --user --no-pager -l status clay-local-bridge.service || true
  journalctl --user -u clay-local-bridge.service -n 120 --no-pager || true
  exit 50
fi

cat "$BASE/state/LIVE.json" | head -c 5000 || true
echo
echo 'SELFTEST_PASS'
echo 'CHATGPT_LOCAL_BRIDGE_READY'
echo
echo 'From now on ChatGPT can use chatgpt-local-control/chatgpt-local-results as an asynchronous local development terminal.'
