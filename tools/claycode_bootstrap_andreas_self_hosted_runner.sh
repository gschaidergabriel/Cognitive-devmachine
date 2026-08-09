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
DESKTOP_PREFLIGHT_FILE="${STATE_ROOT}/desktop_preflight.json"
RUNNER_LABEL_PATCH_FILE="${STATE_ROOT}/runner_label_patch.json"
FAILED_DETAIL_WRITTEN=0

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
  "schema_version":"1.3",
  "status":status,
  "detail":detail,
  "host":socket.gethostname(),
  "platform":platform.platform(),
  "python":platform.python_version(),
  "created_at":datetime.now(timezone.utc).isoformat(),
  "repo":"gschaidergabriel/clay-global-research-entity",
  "authority_invariant":"model output != execution authority",
  "runner_source_policy":"repository-specific GitHub Actions runner downloads API only when fresh registration is required",
  "runner_label_policy":"exact local runner may receive only missing scoped custom labels through repository runner-label REST API after local identity verification",
  "desktop_policy":"real Tk mapped-window preflight plus runner-service environment verification",
}
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY
}

fail() {
  FAILED_DETAIL_WRITTEN=1
  emit_state "FAIL" "$*"
  echo "CLAYCODE_RUNNER_BOOTSTRAP_FAIL: $*" >&2
  exit 2
}

trap 'rc=$?; if [[ $rc -ne 0 && ${FAILED_DETAIL_WRITTEN:-0} -ne 1 ]]; then emit_state "FAIL" "unexpected_exit_${rc}"; fi' EXIT

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

mkdir -p "${RUNNER_ROOT}"
cd "${RUNNER_ROOT}"

# A working existing repository runner does not need a new registration token. Requiring
# repo-admin registration permission on every restart creates an avoidable transport
# blocker. The stronger exact-runner online/label check below still proves repository
# scope before success is reported.
if [[ ! -f .runner ]]; then
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

  # The registration token is short-lived and is requested only for fresh registration,
  # after host identity and local GitHub authentication have both passed.
  TOKEN="$(gh api --method POST "repos/${REPO}/actions/runners/registration-token" --jq .token 2>/dev/null)" \
    || fail "cannot_create_runner_registration_token"
  [[ -n "${TOKEN}" ]] || fail "empty_runner_registration_token"

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

[[ -f .runner ]] || fail "runner_registration_state_missing"
[[ -x ./runsvc.sh ]] || fail "runner_service_entrypoint_missing"

# Bind subsequent repository runner API operations to the exact locally configured runner.
# This prevents a similarly named remote runner from satisfying or receiving mutations.
readarray -t LOCAL_RUNNER_META < <(python3 - "${RUNNER_ROOT}/.runner" <<'PY'
import json,re,sys
p=json.load(open(sys.argv[1],encoding='utf-8'))
rid=p.get('agentId'); name=str(p.get('agentName') or '')
assert isinstance(rid,int) and rid > 0, p
assert re.fullmatch(r'andreas-claycode-[A-Za-z0-9._-]+',name), name
print(rid); print(name)
PY
) || fail "local_runner_metadata_invalid"
[[ "${#LOCAL_RUNNER_META[@]}" -eq 2 ]] || fail "local_runner_metadata_invalid"
RUNNER_ID="${LOCAL_RUNNER_META[0]}"
RUNNER_NAME="${LOCAL_RUNNER_META[1]}"

# APP-05 is a *real desktop* gate. Import the active graphical-session variables into the
# user systemd manager before launching/restarting the listener. If the shell lacks them,
# recover any already-known values from the user manager. Then prove Tk can actually map
# a window. Restarting the service is mandatory: enable --now alone does not refresh the
# environment of an already-running listener.
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

python3 - "${DESKTOP_PREFLIGHT_FILE}" <<'PY' || fail "real_desktop_tk_preflight_failed"
import json, os, sys
from pathlib import Path
if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
    raise SystemExit('NO_GRAPHICAL_SESSION_ENV')
try:
    import tkinter as tk
except Exception as exc:
    raise SystemExit('TKINTER_UNAVAILABLE:'+type(exc).__name__)
root=tk.Tk(); root.title('ClayCode runner desktop preflight'); root.geometry('240x80+20+20')
root.update_idletasks(); root.update(); mapped=bool(root.winfo_ismapped()); screen=root.winfo_screen(); root.destroy()
assert mapped, 'WINDOW_NOT_MAPPED'
payload={
    'desktop_preflight':True,
    'screen':screen,
    'display':os.environ.get('DISPLAY'),
    'wayland_display':os.environ.get('WAYLAND_DISPLAY'),
    'xdg_runtime_dir':os.environ.get('XDG_RUNTIME_DIR'),
}
Path(sys.argv[1]).write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(payload,sort_keys=True))
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
systemctl --user enable claycode-github-runner.service >/dev/null || fail "systemd_user_service_enable_failed"
systemctl --user restart claycode-github-runner.service || fail "systemd_user_service_restart_failed"

for _ in $(seq 1 30); do
  systemctl --user is-active --quiet claycode-github-runner.service && break
  sleep 1
done
systemctl --user is-active --quiet claycode-github-runner.service || fail "runner_service_not_active"

# Verify the restarted listener inherited a real graphical environment. This closes the
# subtle failure mode where bootstrap preflight passes in the launching shell but an old
# already-running systemd listener remains headless and later fails APP-05.
MAIN_PID="$(systemctl --user show --property MainPID --value claycode-github-runner.service)"
[[ "${MAIN_PID}" =~ ^[1-9][0-9]*$ ]] || fail "runner_service_mainpid_invalid"
python3 - "${MAIN_PID}" <<'PY' || fail "runner_service_desktop_environment_missing"
import sys
pid=sys.argv[1]
raw=open(f'/proc/{pid}/environ','rb').read().split(b'\0')
env={}
for item in raw:
    if b'=' in item:
        k,v=item.split(b'=',1)
        env[k.decode(errors='replace')]=v.decode(errors='replace')
assert env.get('DISPLAY') or env.get('WAYLAND_DISPLAY'), {
    'error':'RUNNER_LISTENER_HEADLESS',
    'has_display':bool(env.get('DISPLAY')),
    'has_wayland_display':bool(env.get('WAYLAND_DISPLAY')),
    'has_xdg_runtime_dir':bool(env.get('XDG_RUNTIME_DIR')),
}
print('RUNNER_LISTENER_DESKTOP_ENV=PASS')
PY

# Existing local runner state may predate the scoped workflow labels. GitHub's supported
# repair path for an already configured self-hosted runner is its runner-label REST API,
# not re-running config.sh. Only missing project custom labels may be added here; default
# or unknown missing labels fail closed instead of being mutated.
ONLINE_JSON="$(gh api "repos/${REPO}/actions/runners" 2>/dev/null)" || fail "cannot_list_repository_runners"
MISSING_LABELS="$(python3 - "${ONLINE_JSON}" "${RUNNER_ID}" "${RUNNER_NAME}" <<'PY'
import json,sys
payload=json.loads(sys.argv[1]); rid=int(sys.argv[2]); expected_name=sys.argv[3]
rows=payload.get('runners') or []
matched=[r for r in rows if r.get('id')==rid and str(r.get('name') or '')==expected_name]
assert len(matched)==1, {'error':'exact_local_runner_not_found','id':rid,'name':expected_name,'runners':rows}
r=matched[0]
assert r.get('status')=='online', {'error':'exact_local_runner_not_online','runner':r}
labels={str(x.get('name') or '').lower() for x in r.get('labels') or []}
required={'self-hosted','linux','x64','andreas','claycode','target'}
print(','.join(sorted(required-labels)))
PY
)" || fail "exact_local_runner_not_online"

if [[ -n "${MISSING_LABELS}" ]]; then
  python3 - "${MISSING_LABELS}" <<'PY' > "${RUNNER_LABEL_PATCH_FILE}" || fail "runner_label_patch_payload_invalid"
import json,sys
allowed={'andreas','claycode','target'}
missing={x for x in sys.argv[1].split(',') if x}
assert missing <= allowed, {'refusing_to_mutate_default_or_unknown_labels':sorted(missing)}
print(json.dumps({'labels':sorted(missing)}))
PY
  gh api --method POST \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "repos/${REPO}/actions/runners/${RUNNER_ID}/labels" \
    --input "${RUNNER_LABEL_PATCH_FILE}" >/dev/null \
    || fail "cannot_add_required_runner_labels"
fi

ONLINE_JSON="$(gh api "repos/${REPO}/actions/runners" 2>/dev/null)" || fail "cannot_list_repository_runners_after_label_repair"
python3 - "${ONLINE_JSON}" "${RUNNER_ID}" "${RUNNER_NAME}" <<'PY' || fail "no_online_matching_runner"
import json,sys
payload=json.loads(sys.argv[1]); rid=int(sys.argv[2]); expected_name=sys.argv[3]
rows=payload.get('runners') or []
matched=[]
for row in rows:
    labels={str(x.get('name') or '').lower() for x in row.get('labels') or []}
    if row.get('id')==rid and str(row.get('name') or '')==expected_name and row.get('status')=='online' and {'self-hosted','linux','x64','andreas','claycode','target'}.issubset(labels):
        matched.append({'id':row.get('id'),'name':row.get('name'),'status':row.get('status'),'busy':row.get('busy'),'version':row.get('version'),'labels':sorted(labels)})
assert len(matched)==1, {'error':'no_exact_online_matching_runner','id':rid,'name':expected_name,'runners':rows}
print(json.dumps({'online_matching_runners':matched},sort_keys=True))
PY

emit_state "PASS" "runner_online_with_scoped_labels_real_desktop_preflight_and_service_environment_verified"
trap - EXIT

echo "CLAYCODE_RUNNER_BOOTSTRAP_PASS"
echo "state=${STATE_FILE}"
echo "service=claycode-github-runner.service"
