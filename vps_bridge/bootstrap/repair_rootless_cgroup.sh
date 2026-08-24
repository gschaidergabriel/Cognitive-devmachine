#!/usr/bin/env bash
set -Eeuo pipefail

BASE='/srv/claylab'
UIDC="$(id -u claylab)"

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo 'ERROR: run as root' >&2
  exit 2
fi

# We need an OCI runtime that supports rootless NoCgroups for the long-lived sandbox.
# runc built the image successfully but rejects --cgroups=disabled on this host, so install/pin crun.
apt-get update -y
apt-get install -y crun runc
CRUN_BIN="$(command -v crun || true)"
if [[ -z "$CRUN_BIN" ]]; then
  echo 'ERROR: crun unavailable after package install' >&2
  exit 3
fi

echo "OCI_RUNTIME=$CRUN_BIN"

mkdir -p "$BASE/.config/containers"
cat > "$BASE/.config/containers/containers.conf" <<EOF
[engine]
cgroup_manager = "cgroupfs"
events_logger = "file"
runtime = "crun"
EOF
chown -R claylab:claylab "$BASE/.config/containers"

as_clay() {
  runuser -u claylab -- env \
    HOME="$BASE" \
    XDG_RUNTIME_DIR="/run/user/$UIDC" \
    CONTAINERS_CONF="$BASE/.config/containers/containers.conf" \
    "$@"
}

cd "$BASE"

echo '== Rootless Podman diagnostics =='
as_clay podman info --debug | sed -n '1,220p' || true

echo '== Reusing/building sandbox image with crun + cgroupfs =='
as_clay podman rm -f clay-direct-dev >/dev/null 2>&1 || true

# Reuse the already-successful image if present; otherwise build with chroot isolation.
if ! as_clay podman image exists localhost/clay-direct-dev:ubuntu24; then
  as_clay podman --cgroup-manager=cgroupfs --runtime="$CRUN_BIN" build \
    --isolation=chroot \
    --pull=missing \
    -t localhost/clay-direct-dev:ubuntu24 \
    -f "$BASE/git-bridge/Containerfile" \
    "$BASE/git-bridge"
fi

as_clay podman --cgroup-manager=cgroupfs --runtime="$CRUN_BIN" run -d \
  --name clay-direct-dev \
  --cgroups=disabled \
  --pids-limit=4096 \
  -v "$BASE/workspace:/workspace:rw" \
  -v "$BASE/cache:/cache:rw" \
  -v "$BASE/artifacts:/artifacts:rw" \
  localhost/clay-direct-dev:ubuntu24

echo '== Sandbox proof =='
as_clay podman --cgroup-manager=cgroupfs --runtime="$CRUN_BIN" exec clay-direct-dev bash -lc \
  'set -e; id; touch /workspace/.bridge-rw-test; rm /workspace/.bridge-rw-test; curl -fsSI https://github.com >/dev/null; git --version; python3 --version; sqlite3 --version'

echo '== Starting bridge daemon =='
if as_clay systemctl --user daemon-reload >/dev/null 2>&1 && \
   as_clay systemctl --user enable --now clay-vps-git-bridge.service >/dev/null 2>&1 && \
   [[ "$(as_clay systemctl --user is-active clay-vps-git-bridge.service 2>/dev/null || true)" == 'active' ]]; then
  echo 'BRIDGE_START_MODE=systemd-user'
else
  echo 'BRIDGE_START_MODE=nohup-fallback'
  pkill -u claylab -f '/srv/claylab/git-bridge/bridge_daemon.py' >/dev/null 2>&1 || true
  as_clay bash -lc "cd '$BASE' && nohup /usr/bin/python3 '$BASE/git-bridge/bridge_daemon.py' >'$BASE/state/bridge-daemon.log' 2>&1 < /dev/null & echo \\$! >'$BASE/state/bridge-daemon.pid'"
  sleep 2
  kill -0 "$(cat "$BASE/state/bridge-daemon.pid")"
fi

echo '== Waiting for LIVE.json on results branch =='
OK=0
for _ in $(seq 1 30); do
  sleep 2
  as_clay git -C "$BASE/results-mirror" fetch origin chatgpt-vps-results >/dev/null 2>&1 || true
  if as_clay git -C "$BASE/results-mirror" show 'origin/chatgpt-vps-results:vps_bridge/results/LIVE.json' >/tmp/clay-live.json 2>/dev/null; then
    OK=1
    break
  fi
done

if [[ "$OK" != 1 ]]; then
  echo 'ERROR: LIVE.json not observed' >&2
  tail -n 120 "$BASE/state/bridge-daemon.log" 2>/dev/null || true
  as_clay systemctl --user --no-pager -l status clay-vps-git-bridge.service 2>/dev/null || true
  exit 50
fi

cat /tmp/clay-live.json | head -c 5000 || true
echo
echo 'SELFTEST_PASS'
echo 'CHATGPT_VPS_BRIDGE_READY'
