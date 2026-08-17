#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

# ClayVerse direct VPS KVM lab.
# Host responsibility is lifecycle/orchestration only. Untrusted product/test code
# executes as root INSIDE a fresh KVM guest and never on the VPS host.

usage() {
  cat <<'USAGE'
Usage:
  clayverse-vps-kvm-lab.sh \
    --base-image /path/lab-base.qcow2 --base-sha256 HEX \
    --source /path/source.tar.gz --source-sha256 HEX --source-revision GIT_SHA \
    --command-file /path/guest-command.sh \
    [--egress-host api.example.com ...] \
    [--secret-stdin] \
    [--out /path/receipt.json] [--export-log /path/command.log]

Safety defaults:
  * KVM is mandatory; TCG fallback is forbidden.
  * launcher must be a dedicated non-root, non-privileged account.
  * QEMU user networking uses restrict=on.
  * only loopback host->guest SSH is open.
  * optional egress hosts are fixed HTTPS-only guestfwd tunnels to globally
    routable IPs resolved before launch; private/link-local/metadata targets fail.
  * no host bind mounts, 9p, virtiofs, Docker socket, TAP, QMP, VNC or SPICE.
  * the overlay, seed image and ephemeral SSH key are destroyed after the run.
USAGE
}

die() { printf 'CLAY_VPS_KVM_LAB_FAIL:%s\n' "$*" >&2; exit 70; }
need() { command -v "$1" >/dev/null 2>&1 || die "missing_command:$1"; }
sha256_file() { sha256sum -- "$1" | awk '{print $1}'; }

BASE_IMAGE=''
BASE_SHA=''
SOURCE=''
SOURCE_SHA=''
SOURCE_REVISION=''
COMMAND_FILE=''
SECRET_STDIN=0
OUT=''
EXPORT_LOG=''
RAM_MIB="${CLAY_LAB_RAM_MIB:-8192}"
VCPUS="${CLAY_LAB_VCPUS:-4}"
MAX_SECONDS="${CLAY_LAB_MAX_SECONDS:-3600}"
MAX_BASE_BYTES="${CLAY_LAB_MAX_BASE_BYTES:-34359738368}"
MAX_FILE_BYTES="${CLAY_LAB_MAX_FILE_BYTES:-17179869184}"
HOST_NOFILE="${CLAY_LAB_HOST_NOFILE:-512}"
HOST_NPROC="${CLAY_LAB_HOST_NPROC:-256}"
WORK_ROOT="${CLAY_LAB_WORK_ROOT:-$HOME/.local/state/clayverse-vps-lab}"
EGRESS_HOSTS=()

while (($#)); do
  case "$1" in
    --base-image) BASE_IMAGE=${2:?}; shift 2 ;;
    --base-sha256) BASE_SHA=${2:?}; shift 2 ;;
    --source) SOURCE=${2:?}; shift 2 ;;
    --source-sha256) SOURCE_SHA=${2:?}; shift 2 ;;
    --source-revision) SOURCE_REVISION=${2:?}; shift 2 ;;
    --command-file) COMMAND_FILE=${2:?}; shift 2 ;;
    --secret-stdin) SECRET_STDIN=1; shift ;;
    --out) OUT=${2:?}; shift 2 ;;
    --export-log) EXPORT_LOG=${2:?}; shift 2 ;;
    --egress-host) EGRESS_HOSTS+=("${2:?}"); shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown_arg:$1" ;;
  esac
done

[[ -n "$BASE_IMAGE" && -n "$BASE_SHA" && -n "$SOURCE" && -n "$SOURCE_SHA" && -n "$SOURCE_REVISION" && -n "$COMMAND_FILE" ]] || { usage >&2; die required_args; }
[[ "$BASE_SHA" =~ ^[0-9a-fA-F]{64}$ ]] || die bad_base_sha256
[[ "$SOURCE_SHA" =~ ^[0-9a-fA-F]{64}$ ]] || die bad_source_sha256
[[ "$SOURCE_REVISION" =~ ^[0-9a-fA-F]{40}$ ]] || die bad_source_revision
[[ "$RAM_MIB" =~ ^[0-9]+$ ]] && ((RAM_MIB >= 1024 && RAM_MIB <= 32768)) || die bad_ram_mib
[[ "$VCPUS" =~ ^[0-9]+$ ]] && ((VCPUS >= 1 && VCPUS <= 8)) || die bad_vcpus
[[ "$MAX_SECONDS" =~ ^[0-9]+$ ]] && ((MAX_SECONDS >= 60 && MAX_SECONDS <= 14400)) || die bad_max_seconds
[[ "$MAX_FILE_BYTES" =~ ^[0-9]+$ ]] && ((MAX_FILE_BYTES >= 1073741824 && MAX_FILE_BYTES <= 34359738368)) || die bad_file_limit
[[ "$HOST_NOFILE" =~ ^[0-9]+$ ]] && ((HOST_NOFILE >= 64 && HOST_NOFILE <= 4096)) || die bad_nofile_limit
[[ "$HOST_NPROC" =~ ^[0-9]+$ ]] && ((HOST_NPROC >= 64 && HOST_NPROC <= 1024)) || die bad_nproc_limit

# Hard host-side trust boundary.
(( EUID != 0 )) || die launcher_must_not_be_root
for g in $(id -nG); do
  case "$g" in
    sudo|wheel|adm|docker|lxd|libvirt|libvirt-qemu|disk|root)
      die "launcher_in_privileged_group:$g" ;;
  esac
done
if command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1; then
  die launcher_has_passwordless_sudo
fi

for c in qemu-system-x86_64 qemu-img cloud-localds ssh scp ssh-keygen sha256sum python3 timeout setsid prlimit nice; do need "$c"; done

# The executable and trusted base must be immutable to the untrusted-runtime account;
# otherwise a VM escape could persist into a later host-side invocation.
SCRIPT_REAL=$(python3 - "${BASH_SOURCE[0]}" <<'PY2'
import os, sys
print(os.path.realpath(sys.argv[1]))
PY2
)
[[ ! -w "$SCRIPT_REAL" ]] || die launcher_script_writable_by_lab_user
[[ ! -w "$(dirname -- "$SCRIPT_REAL")" ]] || die launcher_directory_writable_by_lab_user
[[ ! -w "$BASE_IMAGE" ]] || die base_image_writable_by_lab_user
BASE_DIR=$(python3 - "$BASE_IMAGE" <<'PY3'
import os, sys
print(os.path.dirname(os.path.realpath(sys.argv[1])))
PY3
)
[[ ! -w "$BASE_DIR" ]] || die base_directory_writable_by_lab_user
for c in qemu-system-x86_64 qemu-img cloud-localds ssh scp ssh-keygen python3 timeout setsid prlimit nice; do
  bin=$(command -v "$c")
  [[ ! -w "$bin" ]] || die "trusted_binary_writable:$bin"
done

[[ -c /dev/kvm && -r /dev/kvm && -w /dev/kvm ]] || die kvm_device_not_rw
qemu-system-x86_64 -accel help 2>&1 | grep -Eq '(^|[[:space:]])kvm($|[[:space:]])' || die qemu_kvm_accel_unavailable

for f in "$BASE_IMAGE" "$SOURCE" "$COMMAND_FILE"; do
  [[ -f "$f" && ! -L "$f" ]] || die "not_regular_file:$f"
done

[[ "$(sha256_file "$BASE_IMAGE")" == "${BASE_SHA,,}" ]] || die base_sha256_mismatch
[[ "$(sha256_file "$SOURCE")" == "${SOURCE_SHA,,}" ]] || die source_sha256_mismatch

python3 - "$BASE_IMAGE" "$MAX_BASE_BYTES" <<'PY' || exit $?
import json, subprocess, sys
p=sys.argv[1]; cap=int(sys.argv[2])
try:
    data=json.loads(subprocess.check_output(['qemu-img','info','--output=json',p], text=True))
except Exception as exc:
    raise SystemExit('CLAY_VPS_KVM_LAB_FAIL:qemu_img_info:'+str(exc))
if data.get('format') != 'qcow2':
    raise SystemExit('CLAY_VPS_KVM_LAB_FAIL:base_not_qcow2')
size=int(data.get('virtual-size') or 0)
if size <= 0 or size > cap:
    raise SystemExit(f'CLAY_VPS_KVM_LAB_FAIL:base_virtual_size:{size}')
PY

mkdir -p -- "$WORK_ROOT"
chmod 700 -- "$WORK_ROOT"
[[ -d "$WORK_ROOT" && -O "$WORK_ROOT" ]] || die unsafe_work_root
run_id="$(date -u +%Y%m%dT%H%M%SZ)-$$-$RANDOM"
work="$WORK_ROOT/$run_id"
mkdir -m 700 -- "$work"
OVERLAY="$work/overlay.qcow2"
SEED="$work/seed.img"
KEY="$work/id_ed25519"
USER_DATA="$work/user-data"
META_DATA="$work/meta-data"
HOSTS_FILE="$work/guest-hosts"
GUEST_RECEIPT="$work/guest-receipt.json"
GUEST_LOG="$work/command.log"
SECRET_TMP="$work/secrets.env"
SERIAL_LOG="$work/serial.log"
QEMU_SUPERVISOR_PID=''

cleanup() {
  set +e
  if [[ -n "$QEMU_SUPERVISOR_PID" ]] && kill -0 "$QEMU_SUPERVISOR_PID" 2>/dev/null; then
    kill -TERM -- "-$QEMU_SUPERVISOR_PID" 2>/dev/null || kill -TERM "$QEMU_SUPERVISOR_PID" 2>/dev/null || true
    sleep 1
    kill -KILL -- "-$QEMU_SUPERVISOR_PID" 2>/dev/null || true
  fi
  rm -rf -- "$work"
}
trap cleanup EXIT INT TERM HUP

# Secrets may be piped by a trusted caller. They exist on the host only before
# untrusted product code starts, are never put in argv/env, and are deleted
# immediately after transfer into the guest.
if ((SECRET_STDIN == 1)); then
  cat >"$SECRET_TMP"
  chmod 600 "$SECRET_TMP"
  [[ -s "$SECRET_TMP" ]] || die empty_secret_stdin
fi

ssh-keygen -q -t ed25519 -N '' -f "$KEY"
pubkey=$(<"$KEY.pub")
cat >"$USER_DATA" <<EOF_USER
#cloud-config
users:
  - default
  - name: claylab
    groups: [sudo]
    sudo: ['ALL=(ALL) NOPASSWD:ALL']
    shell: /bin/bash
    ssh_authorized_keys:
      - $pubkey
ssh_pwauth: false
disable_root: true
package_update: false
package_upgrade: false
runcmd:
  - [sh, -c, 'mkdir -p /opt/clay /run/clay-result && chmod 700 /opt/clay /run/clay-result']
EOF_USER
printf 'instance-id: %s\nlocal-hostname: claylab\n' "$run_id" >"$META_DATA"

# Resolve optional HTTPS-only egress BEFORE guest launch. We pass the resolved
# public IP to QEMU so DNS rebinding cannot redirect a guestfwd tunnel to the VPS.
NETDEV="user,id=net0,restrict=on,ipv6=off"
map_index=100
: >"$HOSTS_FILE"
for host in "${EGRESS_HOSTS[@]}"; do
  [[ "$host" =~ ^[A-Za-z0-9.-]+$ ]] || die "bad_egress_hostname:$host"
  ip=$(python3 - "$host" <<'PY'
import ipaddress, socket, sys
host=sys.argv[1]
ips=[]
for fam,_,_,_,sa in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM):
    if fam != socket.AF_INET: continue
    ip=ipaddress.ip_address(sa[0])
    if ip.is_global: ips.append(str(ip))
if not ips: raise SystemExit(2)
print(sorted(set(ips))[0])
PY
  ) || die "egress_has_no_global_ipv4:$host"
  synthetic="10.0.2.$map_index"
  ((map_index++))
  ((map_index < 240)) || die too_many_egress_hosts
  printf '%s %s\n' "$synthetic" "$host" >>"$HOSTS_FILE"
  NETDEV+=",guestfwd=tcp:${synthetic}:443-tcp:${ip}:443"
done

# Find a loopback-only host port for the one management path (host -> guest SSH).
SSH_PORT=$(python3 - <<'PY'
import socket
s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1]); s.close()
PY
)
NETDEV+=",hostfwd=tcp:127.0.0.1:${SSH_PORT}-:22"

cloud-localds "$SEED" "$USER_DATA" "$META_DATA" >/dev/null
qemu-img create -q -f qcow2 -F qcow2 -b "$BASE_IMAGE" "$OVERLAY"
chmod 600 "$OVERLAY" "$SEED" "$KEY"

QEMU_VERSION=$(qemu-system-x86_64 --version | head -n1)
HOST_KERNEL=$(uname -r)
SOURCE_ACTUAL=$(sha256_file "$SOURCE")
COMMAND_SHA=$(sha256_file "$COMMAND_FILE")
BASE_ACTUAL=$(sha256_file "$BASE_IMAGE")

# No TCG fallback. No monitor. No host mounts. Seccomp tightens the QEMU process.
setsid timeout --signal=TERM --kill-after=5s "$MAX_SECONDS" \
  nice -n 10 prlimit --core=0 --fsize="$MAX_FILE_BYTES" --nofile="$HOST_NOFILE" --nproc="$HOST_NPROC" -- \
  qemu-system-x86_64 \
    -machine q35,accel=kvm \
    -cpu host \
    -smp "$VCPUS" \
    -m "$RAM_MIB" \
    -nodefaults \
    -no-user-config \
    -drive "file=$OVERLAY,if=virtio,format=qcow2,cache=none" \
    -drive "file=$SEED,format=raw,media=cdrom,readonly=on" \
    -device virtio-net-pci,netdev=net0 \
    -netdev "$NETDEV" \
    -serial "file:$SERIAL_LOG" \
    -display none \
    -monitor none \
    -no-reboot \
    -sandbox on,obsolete=deny,elevateprivileges=deny,spawn=deny,resourcecontrol=deny \
    </dev/null >/dev/null 2>&1 &
QEMU_SUPERVISOR_PID=$!

SSH=(ssh -i "$KEY" -p "$SSH_PORT" -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=3 claylab@127.0.0.1)
SCP=(scp -q -i "$KEY" -P "$SSH_PORT" -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null)

ready=0
for _ in $(seq 1 90); do
  if "${SSH[@]}" 'cloud-init status --wait >/dev/null 2>&1; true' >/dev/null 2>&1; then ready=1; break; fi
  kill -0 "$QEMU_SUPERVISOR_PID" 2>/dev/null || break
  sleep 2
done
((ready == 1)) || die guest_ssh_not_ready

"${SCP[@]}" -- "$SOURCE" "claylab@127.0.0.1:/tmp/clay-source.tar.gz"
"${SCP[@]}" -- "$COMMAND_FILE" "claylab@127.0.0.1:/tmp/clay-command.sh"
"${SCP[@]}" -- "$HOSTS_FILE" "claylab@127.0.0.1:/tmp/clay-hosts"
if ((SECRET_STDIN == 1)); then
  "${SCP[@]}" -- "$SECRET_TMP" "claylab@127.0.0.1:/tmp/clay-secrets.env"
  rm -f -- "$SECRET_TMP"
fi

"${SSH[@]}" 'sudo -n bash -s' <<'GUEST_SETUP'
set -Eeuo pipefail
umask 077
rm -rf /opt/clay/source
mkdir -p /opt/clay/source /run/clay-result
# All archive handling is inside the disposable guest.
tar -xzf /tmp/clay-source.tar.gz -C /opt/clay/source
install -m 0700 -o root -g root /tmp/clay-command.sh /opt/clay/command.sh
if [ -s /tmp/clay-hosts ]; then cat /tmp/clay-hosts >> /etc/hosts; fi
if [ -f /tmp/clay-secrets.env ]; then
  install -m 0600 -o root -g root /tmp/clay-secrets.env /run/clay-secrets.env
  rm -f /tmp/clay-secrets.env
fi
rm -f /tmp/clay-source.tar.gz /tmp/clay-command.sh /tmp/clay-hosts
GUEST_SETUP

set +e
"${SSH[@]}" 'sudo -n bash -s' <<'GUEST_RUN'
set -Eeuo pipefail
umask 077
export CLAY_LAB_RECEIPT_DIR=/run/clay-result
if [ -f /run/clay-secrets.env ]; then
  set -a
  # shellcheck disable=SC1091
  . /run/clay-secrets.env
  set +a
fi
set +e
bash /opt/clay/command.sh > /run/clay-result/command.log 2>&1
rc=$?
set -e
printf '%s\n' "$rc" > /run/clay-result/exit-code
sha256sum /run/clay-result/command.log | awk '{print $1}' > /run/clay-result/command-log.sha256
if [ -f /run/clay-secrets.env ]; then rm -f /run/clay-secrets.env; fi
python3 - "$rc" > /run/clay-result/guest.json <<'PY'
import json, pathlib, platform, subprocess, sys
rc=int(sys.argv[1])
def cmd(args):
    try: return subprocess.check_output(args,text=True,stderr=subprocess.STDOUT,timeout=10).strip()
    except Exception as exc: return 'UNAVAILABLE:'+type(exc).__name__
p=pathlib.Path('/run/clay-result')
image_digest=(p/'image-digest.txt').read_text().strip() if (p/'image-digest.txt').exists() else None
payload={
  'schema':'ClayVerseVpsKvmGuestResult/v1',
  'guest_kernel':platform.release(),
  'guest_machine_id':pathlib.Path('/etc/machine-id').read_text().strip() if pathlib.Path('/etc/machine-id').exists() else None,
  'command_exit_code':rc,
  'command_log_sha256':(p/'command-log.sha256').read_text().strip(),
  'image_digest':image_digest,
  'docker_version':cmd(['docker','version','--format','{{.Server.Version}}']) if pathlib.Path('/usr/bin/docker').exists() else 'UNAVAILABLE',
  'kvm_guest':True,
  'root_inside_guest':True,
}
print(json.dumps(payload,sort_keys=True))
PY
exit "$rc"
GUEST_RUN
guest_rc=$?
set -e

# Best effort evidence export; test may intentionally damage SSH/guest state.
"${SCP[@]}" "claylab@127.0.0.1:/run/clay-result/guest.json" "$GUEST_RECEIPT" >/dev/null 2>&1 || true
if [[ -n "$EXPORT_LOG" ]]; then
  mkdir -p -- "$(dirname -- "$EXPORT_LOG")"
  "${SCP[@]}" "claylab@127.0.0.1:/run/clay-result/command.log" "$GUEST_LOG" >/dev/null 2>&1 || true
  if [[ -f "$GUEST_LOG" ]]; then install -m 600 "$GUEST_LOG" "$EXPORT_LOG"; fi
fi
"${SSH[@]}" 'sudo -n poweroff' >/dev/null 2>&1 || true

# Guest teardown is enforced by cleanup even if graceful shutdown fails.
sleep 2
if kill -0 "$QEMU_SUPERVISOR_PID" 2>/dev/null; then
  kill -TERM -- "-$QEMU_SUPERVISOR_PID" 2>/dev/null || true
fi

[[ -n "$OUT" ]] || OUT="$PWD/clayverse-vps-kvm-${run_id}.json"
mkdir -p -- "$(dirname -- "$OUT")"
python3 - "$OUT" "$GUEST_RECEIPT" "$run_id" "$BASE_ACTUAL" "$SOURCE_ACTUAL" "$SOURCE_REVISION" "$COMMAND_SHA" "$guest_rc" "$QEMU_VERSION" "$HOST_KERNEL" "$RAM_MIB" "$VCPUS" "$MAX_SECONDS" "$MAX_FILE_BYTES" "$HOST_NOFILE" "$HOST_NPROC" "${#EGRESS_HOSTS[@]}" <<'PY'
import json, pathlib, sys
(out,guest_file,run_id,base_sha,source_sha,source_revision,command_sha,rc,qemu_version,host_kernel,ram,vcpus,max_seconds,max_file_bytes,host_nofile,host_nproc,egress_count)=sys.argv[1:]
guest=None
p=pathlib.Path(guest_file)
if p.exists():
    try: guest=json.loads(p.read_text())
    except Exception: guest={'receipt_parse_error':True}
payload={
  'schema':'ClayVerseVpsKvmLabReceipt/v1',
  'run_id':run_id,
  'base_image_sha256':base_sha,
  'source_tar_sha256':source_sha,
  'source_revision':source_revision,
  'command_sha256':command_sha,
  'command_exit_code':int(rc),
  'qemu_version':qemu_version,
  'host_kernel':host_kernel,
  'acceleration':'kvm',
  'tcg_fallback':False,
  'guest_ram_mib':int(ram),
  'guest_vcpus':int(vcpus),
  'max_runtime_seconds':int(max_seconds),
  'host_file_limit_bytes':int(max_file_bytes),
  'host_nofile_limit':int(host_nofile),
  'host_nproc_limit':int(host_nproc),
  'network_policy':'restrict=on + loopback hostfwd + explicit HTTPS guestfwd only',
  'egress_host_count':int(egress_count),
  'host_product_code_executed':False,
  'github_actions_required':False,
  'github_runner_required':False,
  'guest_receipt':guest,
}
pathlib.Path(out).write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
PY
chmod 600 "$OUT"
printf 'CLAY_VPS_KVM_LAB_RECEIPT=%s\n' "$OUT"
printf 'CLAY_VPS_KVM_LAB_EXIT=%s\n' "$guest_rc"
exit "$guest_rc"
