#!/usr/bin/env bash
set -euo pipefail

# Bootstrap a repository-scoped GitHub Actions self-hosted runner on the already
# owner-registered Andreas Ubuntu target. This script never weakens ClayCode acceptance:
# it only restores the physical execution transport required by the existing target gate.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="gschaidergabriel/clay-global-research-entity"
REPO_URL="https://github.com/${REPO}"
REGISTRATION="${HOME}/.config/claycode/andreas_target_registration.json"
RUNNER_ROOT="${HOME}/.local/share/claycode-github-runner"
STATE_ROOT="${HOME}/.local/state/claycode"
STATE_FILE="${STATE_ROOT}/andreas_self_hosted_runner_bootstrap.json"
SERVICE_DIR="${HOME}/.config/systemd/user"
SERVICE_FILE="${SERVICE_DIR}/claycode-github-runner.service"

mkdir -p "${STATE_ROOT}"

emit_state() {
  local status="$1"
  local detail="${2:-}"
  python3 - "${STATE_FILE}" "${status}" "${detail}" <<'PY'
import json, os, platform, socket, sys
from datetime import datetime, timezone
from pathlib import Path
path=Path(sys.argv[1]); status=sys.argv[2]; detail=sys.argv[3]
payload={
  "schema_version":"1.0",
  "status":status,
  "detail":detail,
  "host":socket.gethostname(),
  "platform":platform.platform(),
  "python":platform.python_version(),
  "created_at":datetime.now(timezone.utc).isoformat(),
  "repo":"gschaidergabriel/clay-global-research-entity",
  "authority_invariant":"model output != execution authority",
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

command -v python3 >/dev/null || fail "python3_missing"
command -v gh >/dev/null || fail "github_cli_missing"
command -v curl >/dev/null || fail "curl_missing"
command -v tar >/dev/null || fail "tar_missing"
command -v systemctl >/dev/null || fail "systemd_missing"

# Hard identity boundary: this script is useless on any other host.
python3 tools/claycode_target_host_identity.py verify --registration "${REGISTRATION}" --json \
  > "${STATE_ROOT}/target_identity_verify.json" \
  || fail "registered_andreas_target_identity_not_verified"

python3 - "${STATE_ROOT}/target_identity_verify.json" <<'PY' || exit 3
import json, sys
p=json.load(open(sys.argv[1],encoding='utf-8'))
assert p.get('verified') is True, p
assert p.get('target_host') == 'ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM', p
PY

[[ "$(uname -s)" == "Linux" ]] || fail "not_linux"
[[ "$(uname -m)" == "x86_64" ]] || fail "not_x86_64"
if [[ -f /.dockerenv ]]; then fail "container_not_physical_target"; fi
if grep -Eqi '(docker|containerd|kubepods|lxc)' /proc/1/cgroup 2>/dev/null; then fail "container_cgroup_detected"; fi
if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  source /etc/os-release
  [[ "${ID:-}" == "ubuntu" ]] || fail "not_ubuntu"
else
  fail "os_release_missing"
fi

gh auth status >/dev/null 2>&1 || fail "gh_not_authenticated"

# Ask GitHub which runner release is current at execution time; do not freeze a stale
# version in the repository.
TAG="$(gh api repos/actions/runner/releases/latest --jq .tag_name 2>/dev/null)" \
  || fail "cannot_resolve_latest_actions_runner"
[[ "${TAG}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "unexpected_runner_tag_${TAG}"
VERSION="${TAG#v}"
ARCHIVE="actions-runner-linux-x64-${VERSION}.tar.gz"
URL="https://github.com/actions/runner/releases/download/${TAG}/${ARCHIVE}"

# Generate a short-lived repository registration token only after local identity and gh
# authentication are verified.
TOKEN="$(gh api --method POST "repos/${REPO}/actions/runners/registration-token" --jq .token 2>/dev/null)" \
  || fail "cannot_create_runner_registration_token"
[[ -n "${TOKEN}" ]] || fail "empty_runner_registration_token"

mkdir -p "${RUNNER_ROOT}"
cd "${RUNNER_ROOT}"

# If this exact runner is already configured, do not destroy working state. Restart it
# and validate online state below.
if [[ ! -f .runner ]]; then
  curl --fail --location --retry 4 --retry-delay 2 --output "${ARCHIVE}.tmp" "${URL}" \
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

mkdir -p "${SERVICE_DIR}"
cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=ClayCode GitHub Actions self-hosted runner
After=network-online.target
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

# Give the listener a bounded startup window.
for _ in $(seq 1 30); do
  if systemctl --user is-active --quiet claycode-github-runner.service; then
    break
  fi
  sleep 1
done
systemctl --user is-active --quiet claycode-github-runner.service || fail "runner_service_not_active"

# Verify GitHub sees an online runner with default Linux/X64 labels plus our scoped labels.
ONLINE_JSON="$(gh api "repos/${REPO}/actions/runners" 2>/dev/null)" || fail "cannot_list_repository_runners"
python3 - "${ONLINE_JSON}" <<'PY' || exit 4
import json, socket, sys
payload=json.loads(sys.argv[1])
rows=payload.get('runners') or []
expected_prefix='andreas-claycode-'
matched=[]
for row in rows:
    name=str(row.get('name') or '')
    labels={str(x.get('name') or '').lower() for x in row.get('labels') or []}
    if name.startswith(expected_prefix) and row.get('status')=='online' and {'self-hosted','linux','x64','andreas','claycode','target'}.issubset(labels):
        matched.append({'name':name,'status':row.get('status'),'busy':row.get('busy'),'labels':sorted(labels)})
assert matched, {'error':'no_online_matching_runner','runners':rows}
print(json.dumps({'online_matching_runners':matched},sort_keys=True))
PY

emit_state "PASS" "runner_online_and_waiting_for_queued_jobs"
trap - EXIT

echo "CLAYCODE_RUNNER_BOOTSTRAP_PASS"
echo "state=${STATE_FILE}"
echo "service=claycode-github-runner.service"
