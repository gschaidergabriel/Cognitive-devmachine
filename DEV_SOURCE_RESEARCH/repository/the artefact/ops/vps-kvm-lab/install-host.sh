#!/usr/bin/env bash
set -Eeuo pipefail
umask 022

RUNNER_SOURCE=${1:-}
BASE_SOURCE=${2:-}
BASE_SHA=${3:-}
[[ $EUID -eq 0 ]] || { echo 'must run as root' >&2; exit 64; }
[[ -f "$RUNNER_SOURCE" ]] || { echo 'usage: install-host.sh RUNNER_SCRIPT [BASE_QCOW2 BASE_SHA256]' >&2; exit 64; }

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  qemu-system-x86 qemu-utils cloud-image-utils openssh-client python3 ca-certificates

if ! id claylab >/dev/null 2>&1; then
  useradd --create-home --home-dir /var/lib/clayverse-vps-lab/home --shell /bin/bash claylab
fi
passwd -l claylab >/dev/null 2>&1 || true
usermod -aG kvm claylab
for g in sudo wheel adm docker lxd libvirt libvirt-qemu disk root; do
  if getent group "$g" >/dev/null 2>&1; then gpasswd -d claylab "$g" >/dev/null 2>&1 || true; fi
done

install -d -o root -g root -m 0755 /usr/local/libexec/clayverse-vps-lab
install -o root -g root -m 0555 "$RUNNER_SOURCE" /usr/local/libexec/clayverse-vps-lab/clayverse-vps-kvm-lab.sh
install -d -o root -g root -m 0755 /var/lib/clayverse-vps-lab/base
install -d -o claylab -g claylab -m 0700 /var/lib/clayverse-vps-lab/inbox /var/lib/clayverse-vps-lab/out /var/lib/clayverse-vps-lab/home/.local/state

if [[ -n "$BASE_SOURCE" || -n "$BASE_SHA" ]]; then
  [[ -f "$BASE_SOURCE" && "$BASE_SHA" =~ ^[0-9a-fA-F]{64}$ ]] || { echo 'base image and sha256 must be supplied together' >&2; exit 65; }
  actual=$(sha256sum "$BASE_SOURCE" | awk '{print $1}')
  [[ "$actual" == "${BASE_SHA,,}" ]] || { echo 'base sha256 mismatch' >&2; exit 66; }
  fmt=$(qemu-img info --output=json "$BASE_SOURCE" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("format",""))')
  [[ "$fmt" == qcow2 ]] || { echo 'base image must be qcow2' >&2; exit 67; }
  install -o root -g root -m 0444 "$BASE_SOURCE" /var/lib/clayverse-vps-lab/base/lab-base.qcow2
  printf '%s  %s\n' "$actual" /var/lib/clayverse-vps-lab/base/lab-base.qcow2 > /var/lib/clayverse-vps-lab/base/lab-base.qcow2.sha256
  chmod 0444 /var/lib/clayverse-vps-lab/base/lab-base.qcow2.sha256
fi

cat <<'MSG'
ClayVerse VPS KVM lab host installed.
Runtime account: claylab (locked password, no sudo groups; kvm only).
Runner: /usr/local/libexec/clayverse-vps-lab/clayverse-vps-kvm-lab.sh
Base directory: /var/lib/clayverse-vps-lab/base (root-owned, immutable to claylab).
Inputs: /var/lib/clayverse-vps-lab/inbox
Receipts: /var/lib/clayverse-vps-lab/out

Re-login the claylab account after group changes. Do not add claylab to sudo/docker/libvirt/disk/lxd groups.
MSG
