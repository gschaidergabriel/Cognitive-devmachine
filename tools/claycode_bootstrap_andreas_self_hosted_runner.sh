#!/usr/bin/env bash
set -euo pipefail

# Bootstrap a repository-scoped GitHub Actions self-hosted runner on the already
# owner-registered Andreas Ubuntu target. This restores execution transport only; it
# never relaxes ClayCode target/release evidence gates.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="gschaidergabriel/clay-global-research-entity"
REPO_URL="https://github.com/${REPO}"
REGISTRATION="${HOME}/.config/claycode/andreas_target_registration.json"
RUNNER_ROOT="${HOME}/.local/share/claycode-github-runner"
STATE_ROOT="${HOME}/.local/state/claycode"
STATE_FILE="${STATE_ROOT}/andreas_self_hosted_runner_bootstrap.json"
SERVICE_DIR="${HOME}/.config/systemd/user"
SERVICE_FILE="${SERVICE_DIR}/claycode-github-runner.service"
DOWNLOADS_FILE="${STATE_ROOT}/github_runner_downloads.json"

mkdir -p "${STATE_ROOT}"

emit_state() {
  local status="$1"
  local detail="${2:-}"
  python3 - "${STATE_FILE}" "${status}" "${detail}" <<'PY'
import json, platform, socket, sys
from datetime import datetime, timezone
from pathlib import Path
path=Path(sys.argv[1]); status=sys.argv[2]; detail=sys.argv[3]
payload={
  "schema_version":"1.1",
  "status":status,
  "detail":detail,
  "host":socket.gethostname(),
  "platform":platform.platform(),
  "python":platform.python_version(),
  "created_at":datetime.now(timezone.utc).isoformat(),
  "repo":"gschaidergabriel/clay-global-research-entity",
  "authority_invariant":"model output != execution authority",
  "runner_source_policy":"repository-specific GitHub Actions runner downloads API",
  "desktop_policy":"real Tk mapped-window preflight before starting listener",
}
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY
}

fail() {
  emit_state "FAIL" "$*"
  echo "CLAYCODE_RUNNER_BOOTSTRAP_FAIL: $*" >&2
  exit 2
}

trap 'rc=$?; if [[ $rc -ne 0 ]]; then emit_state "FAIL" "unexpected_exit_${rc}"; fi' EXIT

cd "${ROOT}"

for cmd in python3 gh curl tar systemctl; do
  command -v "$cmd" >/dev/null || fail "${cmd}_missing"
done

# Hard owner-machine boundary.
python3 tools/claycode_target_host_identity.py verify --registration "${REGISTRATION}" --json \
  > "${STATE_ROOT}/target_identity_verify.json" \
  || fail "registered_andreas_target_identity_not_verified"
python3 - "${STATE_ROOT}/target_identity_verify.json" <<'PY' || fail "registered_target_payload_invalid"
import json, sys
p=json.load(open(sys.argv[1],encoding='utf-8'))
assert p.get('verified') is True, p
assert p.get('target_host') == 'ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM', p
PY

[[ "$(uname -s)" == "Linux" ]] || fail "not_linux"
[[ "$(uname -m)" == "x86_64" ]] || fail "not_x86_64"
[[ ! -f /.dockerenv ]] || fail "container_not_physical_target"
if grep -Eqi '(docker|containerd|kubepods|lxc)' /proc/1/cgroup 2>/dev/null; then fail "container_cgroup_detected"; fi
if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  source /etc/os-release
  [[ "${ID:-}" == "ubuntu" ]] || fail "not_ubuntu"
else
  fail "os_release_missing"
fi

gh auth status >/dev/null 2>&1 || fail "gh_not_authenticated"

# Use GitHub's repository-specific downloads endpoint, rather than assuming the globally
# newest actions/runner release has already reached this repository's progressive rollout.
gh api "repos/${REPO}/actions/runners/downloads" > "${DOWNLOADS_FILE}" \
  || fail "cannot_list_repository_runner_downloads"
readarray -t RUNNER_META < <(python3 - "${DOWNLOADS_FILE}" <<'PY'
import json,re,sys
rows=json.load(open(sys.argv[1],encoding='utf-8'))
match=[r for r in rows if r.get('os')=='linux' and r.get('architecture')=='x64']
assert len(match)==1, match
r=match[0]; url=str(r.get('download_url') or ''); filename=str(r.get('filename') or '')
assert re.fullmatch(r'actions-runner-linux-x64-[0-9]+\.[0-9]+\.[0-9]+\.tar\.gz',filename), filename
assert url.startswith('https://github.com/actions/runner/releases/download/'), url
assert url.endswith('/'+filename), (url,filename)
print(url); print(filename)
PY
)
[[ "${#RUNNER_META[@]}" -eq 2 ]] || fail "runner_download_metadata_invalid"
DOWNLOAD_URL="${RUNNER_META[0]}"
ARCHIVE="${RUNNER_META[1]}"

# The registration token is short-lived and is requested only after host identity and
# local GitHub authentication have both passed.
TOKEN="$(gh api --method POST "repos/${REPO}/actions/runners/registration-token" --jq .token 2>/dev/null)" \
  || fail "cannot_create_runner_registration_token"
[[ -n "${TOKEN}" ]] || fail "empty_runner_registration_token"

mkdir -p "${RUNNER_ROOT}"
cd "${RUNNER_ROOT}"

if [[ ! -f .runner ]]; then
  curl --fail --location --retry 4 --retry-delay 2 --output "${ARCHIVE}.tmp" "${DOWNLOAD_URL}" \
    || fail "runner_download_failed"
  mv "${ARCHIVE}.tmp" "${ARCHIVE}"
  tar xzf "${ARCHIVE}" || fail "runner_extract_failed"
  rm -f "${ARCHIVE}"

  RUNNER_NAME="andreas-claycode-$(hostname | tr -cs 'A-Za-z0-9._-' '-')"
  ./config.sh \
    --unattended \
    --url "${REPO_URL}" \
    --token "${TOKEN}" \
    --name "${RUNNER_NAME}" \
    --labels "andreas,claycode,target" \
    --work "_work" \
    --replace \
    || fail "runner_config_failed"
fi

# APP-05 is a *real desktop* gate. Import the active graphical-session variables into the
# user systemd manager before launching the listener. If the shell lacks them, recover
# any already-known values from the user manager. Then prove Tk can actually map a window.
env_keys=()
for key in DISPLAY WAYLAND_DISPLAY XAUTHORITY DBUS_SESSION_BUS_ADDRESS XDG_RUNTIME_DIR; do
  if [[ -n "${!key:-}" ]]; then env_keys+=("$key"); fi
done
if [[ "${#env_keys[@]}" -gt 0 ]]; then
  systemctl --user import-environment "${env_keys[@]}" || fail "desktop_environment_import_failed"
fi
while IFS='=' read -r key value; do
  case "$key" in
    DISPLAY|WAYLAND_DISPLAY|XAUTHORITY|DBUS_SESSION_BUS_ADDRESS|XDG_RUNTIME_DIR)
      if [[ -z "${!key:-}" && -n "$value" ]]; then export "$key=$value"; fi
      ;;
  esac
done < <(systemctl --user show-environment)

python3 - <<'PY' || fail "real_desktop_tk_preflight_failed"
import json, os
if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
    raise SystemExit('NO_GRAPHICAL_SESSION_ENV')
try:
    import tkinter as tk
except Exception as exc:
    raise SystemExit('TKINTER_UNAVAILABLE:'+type(exc).__name__)
root=tk.Tk(); root.title('ClayCode runner desktop preflight'); root.geometry('240x80+20+20')
root.update_idletasks(); root.update(); mapped=bool(root.winfo_ismapped()); screen=root.winfo_screen(); root.destroy()
assert mapped, 'WINDOW_NOT_MAPPED'
print(json.dumps({'desktop_preflight':True,'screen':screen,'display':bool(os.environ.get('DISPLAY')),'wayland':bool(os.environ.get('WAYLAND_DISPLAY'))}))
PY

mkdir -p "${SERVICE_DIR}"
cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=ClayCode GitHub Actions self-hosted runner
After=network-online.target graphical-session.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${RUNNER_ROOT}
ExecStart=${RUNNER_ROOT}/runsvc.sh
Restart=always
RestartSec=5
KillSignal=SIGINT
TimeoutStopSec=30

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload || fail "systemd_user_daemon_reload_failed"
systemctl --user enable --now claycode-github-runner.service || fail "systemd_user_service_start_failed"

for _ in $(seq 1 30); do
  systemctl --user is-active --quiet claycode-github-runner.service && break
  sleep 1
done
systemctl --user is-active --quiet claycode-github-runner.service || fail "runner_service_not_active"

ONLINE_JSON="$(gh api "repos/${REPO}/actions/runners" 2>/dev/null)" || fail "cannot_list_repository_runners"
python3 - "${ONLINE_JSON}" <<'PY' || fail "no_online_matching_runner"
import json,sys
payload=json.loads(sys.argv[1]); rows=payload.get('runners') or []; matched=[]
for row in rows:
    name=str(row.get('name') or '')
    labels={str(x.get('name') or '').lower() for x in row.get('labels') or []}
    if name.startswith('andreas-claycode-') and row.get('status')=='online' and {'self-hosted','linux','x64','andreas','claycode','target'}.issubset(labels):
        matched.append({'id':row.get('id'),'name':name,'status':row.get('status'),'busy':row.get('busy'),'version':row.get('version'),'labels':sorted(labels)})
assert matched, {'error':'no_online_matching_runner','runners':rows}
print(json.dumps({'online_matching_runners':matched},sort_keys=True))
PY

emit_state "PASS" "runner_online_with_real_desktop_preflight_and_waiting_for_queued_jobs"
trap - EXIT

echo "CLAYCODE_RUNNER_BOOTSTRAP_PASS"
echo "state=${STATE_FILE}"
echo "service=claycode-github-runner.service"
