# ClayVerse direct VPS KVM lab

Purpose: run hard ClayVerse tests on a real VPS without making GitHub Actions/runners the execution control plane and without executing untrusted ClayVerse/test payload on the VPS host.

## Trust boundary

The VPS host is orchestration only. The test payload runs as root **inside a fresh hardware-virtualized KVM guest**.

Hard requirements:

- KVM is mandatory. There is **no TCG fallback** for this lane.
- The host launcher is a dedicated `claylab` Unix account with no `sudo`, `wheel`, `adm`, `docker`, `lxd`, `libvirt`, `disk`, or root-equivalent group membership. `kvm` is the only privileged device group admitted.
- The QEMU executable, launcher script, and trusted base qcow2 are immutable to `claylab` so a guest escape cannot persist by rewriting the next host-side launcher/base.
- QEMU runs unprivileged and with seccomp `-sandbox on,obsolete=deny,elevateprivileges=deny,spawn=deny,resourcecontrol=deny`.
- Every run creates a new qcow2 overlay and cloud-init seed, a new guest instance identity, and a new ephemeral SSH key.
- No host Docker socket, bind mount, 9p, virtiofs, TAP bridge, QMP/HMP monitor, VNC, SPICE, SSH agent forwarding, or host credential is exposed to the guest.
- Default guest networking is QEMU user networking with `restrict=on`. The only default forwarding rule is loopback-only host -> guest SSH.
- Optional provider/build egress is explicit HTTPS-only `guestfwd`. The launcher resolves the requested hostname before boot, rejects non-global IPv4 targets, passes the fixed public IP to QEMU, and writes a synthetic guest `/etc/hosts` mapping.
- The guest is destroyed after the run regardless of success. Test command output stays in the guest by default; only a bounded receipt is exported unless protected log export is explicitly requested.
- Source is copied into the guest as data and unpacked there. It is never executed on the VPS host.

This cannot make VM-escape risk mathematically zero. It deliberately narrows that residual risk to the KVM/QEMU virtualization boundary and runs QEMU with a dedicated least-privilege account and seccomp confinement.

## GitHub independence

`clayverse-vps-kvm-lab.sh` is a normal host CLI. It does **not** require GitHub Actions or a GitHub runner.

GitHub remains useful for canonical source identity and durable receipts, but execution can be driven directly over an authorized VPS control channel. Existing self-hosted-runner workflows are optional probes/bootstrap aids only; they are not an acceptance dependency for this lane.

A run consumes:

1. a root-owned, read-only trusted qcow2 lab base and its SHA-256;
2. a source tarball plus SHA-256 and exact source revision;
3. a guest command file plus its SHA-256-bound receipt;
4. zero or more explicitly admitted HTTPS egress hostnames.

The source tarball may be produced from an exact Git commit, but no GitHub-hosted runner participates in the run.

## Host install

Run once as VPS administrator:

```bash
sudo ./install-host.sh ./clayverse-vps-kvm-lab.sh /path/to/trusted-lab-base.qcow2 <BASE_SHA256>
```

This installs the runtime launcher root-owned at:

```text
/usr/local/libexec/clayverse-vps-lab/clayverse-vps-kvm-lab.sh
```

and creates the dedicated `claylab` account and directories under `/var/lib/clayverse-vps-lab/`.

The lab base must already contain the guest tooling needed by the selected tests, for example Docker/BuildKit when the exact OCI build is part of the batch. Keeping that base immutable to `claylab` prevents untrusted test code from persisting into later runs.

## Direct run

Example offline destructive/regression run:

```bash
sudo -u claylab /usr/local/libexec/clayverse-vps-lab/clayverse-vps-kvm-lab.sh \
  --base-image /var/lib/clayverse-vps-lab/base/lab-base.qcow2 \
  --base-sha256 <BASE_SHA256> \
  --source /var/lib/clayverse-vps-lab/inbox/clayverse-source.tar.gz \
  --source-sha256 <SOURCE_TAR_SHA256> \
  --source-revision <EXACT_40_HEX_GIT_SHA> \
  --command-file /var/lib/clayverse-vps-lab/inbox/run-exact-batch.sh \
  --out /var/lib/clayverse-vps-lab/out/exact-batch.json
```

Example with fixed provider egress:

```bash
... \
  --egress-host api.mistral.ai
```

For a provider test, a trusted caller may pipe a one-run environment file through `--secret-stdin`; the secret is transferred before test code starts and is not part of the command line or receipt.

`restrict=on` remains enabled. Explicit forwarding rules are the only network escape hatches. Add only the concrete domains required by a batch.

## Guest contract

The command file executes as guest root with:

```text
/opt/clay/source/            exact staged source
CLAY_LAB_RECEIPT_DIR=/run/clay-result
```

If an exact OCI image is built, the batch should write its immutable digest to:

```text
/run/clay-result/image-digest.txt
```

The outer receipt binds at least:

- base image SHA-256;
- source tar SHA-256 and exact source revision;
- guest-command SHA-256;
- QEMU version;
- host kernel observation;
- `acceleration=kvm` and `tcg_fallback=false`;
- guest kernel / machine identity when recoverable;
- command exit code and log digest;
- optional OCI digest;
- network mode / admitted egress count;
- explicit `github_actions_required=false` and `github_runner_required=false`.

## Hard-test freedom

Inside the guest, the test command is intentionally allowed to be root and may crash processes, corrupt its disposable filesystem, exhaust its bounded guest resources, reboot, kill SSH, fuzz ClayVerse, destroy/recreate containers, and run Tier-1/Tier-2 recovery experiments. The host watchdog still owns teardown.

The freedom stops at the VM boundary. There is no permission to attack the VPS host, other tenants, arbitrary Internet targets, or bypass the explicit egress profile.

## Acceptance use

This lane can become the preferred exact-runtime path when the VPS actually exposes usable `/dev/kvm` and the direct host installer/launcher has been executed there. A source-only harness commit is not runtime evidence. TCG-only boot evidence is not accepted as the secure sandbox boundary for untrusted ClayVerse testing.
