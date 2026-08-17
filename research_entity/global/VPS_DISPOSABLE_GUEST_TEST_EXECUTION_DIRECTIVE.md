# VPS-HOSTED DISPOSABLE GUEST TEST EXECUTION — OWNER DIRECTIVE

**Authority:** explicit owner instruction  
**Authority time:** 2026-08-18 01:58 +07:00  
**Status:** CURRENT

This directive supersedes every older Clay/ClayVerse rule that categorically forbids all VPS-hosted testing. It does **not** authorize direct testing on the VPS host. It authorizes a VPS only as a trusted orchestration substrate for a separately isolated disposable guest test environment.

## 1. New execution law

Clay/ClayVerse tests, builds, experiments, fuzzing, crash testing and destructive validation MAY run from the real VPS only when **all code under test executes inside a freshly created disposable guest with its own guest kernel or an equivalently strong independently isolated sandbox**.

The VPS host itself is never the test environment.

Direct execution of product/test commands on the VPS host remains forbidden.

A self-hosted runner on the VPS is allowed only as an orchestrator that stages immutable inputs, creates the isolated guest, starts/stops it, captures bounded evidence and destroys the guest. The runner must never execute the ClayVerse product test command on the host.

## 2. Preferred isolation order

1. Hardware-virtualized KVM/microVM guest when `/dev/kvm` is genuinely exposed and usable.
2. If nested hardware virtualization is unavailable, a full-system QEMU/TCG guest with an independent guest kernel is allowed for development/runtime testing, provided the host-hardening rules below are met.
3. Ordinary Docker/container isolation directly on the VPS host is **not** an acceptable substitute for this directive.

QEMU/TCG evidence is valid only for the exact guest-scoped test that actually executed. It does not satisfy the separate final ClayVerse requirement for the accepted OCI digest to execute behind a hardware-virtualized VM/microVM guest-kernel boundary.

## 3. Host safety boundary

The disposable guest lane must fail closed unless these controls hold:

- QEMU/Firecracker/VMM runs as a dedicated unprivileged host identity wherever technically possible.
- VMM seccomp/sandboxing is enabled; Firecracker uses `jailer` or an equivalently restrictive launcher when Firecracker is used.
- No host filesystem share, bind mount, 9p/virtiofs share, host Docker/containerd socket, host PID namespace, host IPC namespace or host mutable library path is exposed to the guest.
- No passthrough of arbitrary host devices.
- No QEMU monitor/QMP/HMP control socket is exposed to the guest or test code.
- Guest boot/root storage uses an immutable verified base plus a per-run disposable overlay or equivalent disposable disk.
- Source/test inputs are transferred as immutable read-only payloads or another bounded one-way staging mechanism; the guest never receives repository credentials merely to fetch its own source.
- Guest output is captured through a bounded serial/virtio output channel or another non-authoritative receipt channel; guest-controlled paths are not mounted directly as trusted host filesystems.
- Default network mode is `NONE`/default-deny.
- If a test explicitly requires egress, the host boundary must deny the VPS host, RFC1918/private ranges, loopback, link-local, metadata-service/control-plane endpoints and all non-admitted destinations. Broad Internet scanning or using the guest as an attack relay is not authorized.
- The guest receives no SSH key or credential that permits a return path into the VPS host.
- Secrets required for an admitted provider test are one-shot guest-scoped values, never image-layer state, and are excluded from receipts/logs.
- CPU, memory, process count, runtime duration and disk growth are bounded with cgroups/resource controls so guest failure cannot starve the host.
- Every run has a hard timeout and unconditional cleanup path.
- On completion or failure, the guest process, disposable overlay, transient payload media, sockets and namespaces are destroyed.

## 4. Freedom inside the guest

Inside the disposable guest, tests may deliberately exercise hostile conditions against the ClayVerse test instance, including:

- root/admin execution inside the guest;
- killing or wedging ClayVerse/EntityOS/PTY/tmux processes;
- OOM/resource-pressure tests within the guest limits;
- filesystem and state corruption of disposable guest data;
- kernel panic/reboot/power-loss simulation;
- repeated crash/recovery and stale-generation tests;
- container/OCI builds and destructive replacement tests;
- fuzzing of product-local parsers/protocols and guest-local network services;
- Tier-1/Tier-2 recovery and effect-journal failure injection.

Freedom inside the guest never expands authority over the VPS host or external systems.

## 5. Current real-VPS compatibility rule

The currently known VPS is Ubuntu 24.04 LTS with approximately 16 GB RAM and no swap. Nested KVM availability must be probed empirically before any KVM/microVM claim.

If `/dev/kvm` is missing/unusable or the provider disables nested virtualization, the lane must not fake KVM credit. It may use the hardened QEMU/TCG independent-kernel lane for development/runtime evidence and must label that evidence `VPS_QEMU_TCG_GUEST`, not final hardware-microVM acceptance.

## 6. Evidence law

Every receipt from this lane binds at minimum:

- host orchestration identity without exposing host secrets;
- executor type (`KVM`, `FIRECRACKER`, `QEMU_TCG`, or other explicitly reviewed type);
- exact source SHA/tree and exact staged payload digest;
- guest image/base digest;
- guest kernel identity;
- command/test contract;
- bounded resource limits and network mode;
- exit status plus bounded log digest;
- cleanup result;
- OCI image digest where an OCI image was built/tested.

Host-side orchestration success is zero product-runtime credit unless the intended command actually executed inside the disposable guest.

## 7. ClayVerse final-pass boundary

This directive creates a high-intensity VPS-hosted **test laboratory**. It does not weaken the existing final-product law:

- the final accepted ClayVerse artifact remains one exact OCI/Docker-compatible image;
- the complete accepted EntityOS substrate remains mandatory inside it;
- final `WHOLE_CLAYVERSE_PASS` still requires the same exact accepted OCI digest behind the independently verified hardware-virtualized VM/microVM guest-kernel boundary defined by the current MicroVM outer-envelope directive.

A QEMU/TCG run can find bugs and earn bounded isolated runtime evidence, but cannot by itself close that final hardware-virtualization gate.

## 8. Supersession

Where older files say `VPS testing is forbidden` or `self-hosted VPS test runners are forbidden`, read them under this newer rule:

**direct host testing remains forbidden; VPS-hosted disposable independent-guest testing is authorized under the controls above.**
