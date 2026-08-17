# VPS-HOSTED DISPOSABLE GUEST TEST EXECUTION — OWNER DIRECTIVE

**Authority:** explicit owner instruction  
**Authority time:** 2026-08-18 02:05 +07:00  
**Status:** CURRENT

This directive supersedes every older Clay/ClayVerse rule that categorically forbids all VPS-hosted testing. It does **not** authorize direct testing on the VPS host. It authorizes a VPS only as a trusted orchestration substrate for a separately isolated disposable guest test environment.

The owner additionally requests that the actual test execution path be independent of GitHub Actions/GitHub-hosted/self-hosted runners where technically possible, so GitHub rate/control-plane limits do not gate runtime testing.

## 1. New execution law

Clay/ClayVerse tests, builds, experiments, fuzzing, crash testing and destructive validation MAY run from the real VPS only when **all code under test executes inside a freshly created disposable hardware-virtualized guest with its own guest kernel**.

The VPS host itself is never the test environment. Direct execution of product/test commands on the VPS host remains forbidden. Ordinary Docker/container isolation directly on the VPS host is not an acceptable substitute.

GitHub Actions or a self-hosted runner MAY bootstrap/orchestrate this path, but they are not required and are not the preferred steady-state execution control plane. A normal direct host CLI reached over an explicitly authorized VPS control channel is preferred. GitHub remains canonical source/coordination/receipt storage, not a runtime admission dependency.

## 2. Hard-test isolation law

For the owner-requested unrestricted/destructive test lane:

1. Hardware-virtualized KVM or another explicitly accepted hardware-backed VM/microVM guest is REQUIRED.
2. There is NO TCG/software-emulation fallback for untrusted, adversarial, destructive or full-freedom ClayVerse test payloads.
3. If `/dev/kvm` is missing or unusable, the hard-test lane is `BLOCKED_KVM_UNAVAILABLE` and must fail closed.
4. Full-system QEMU/TCG may be used only for bounded trusted bring-up/tooling smoke where the payload is not treated as hostile. Such a run receives no security-isolation credit, no unrestricted-sandbox credit and no final hardware-microVM acceptance credit.
5. Direct host-kernel OCI/Docker execution remains development evidence only and is not authorized as the unrestricted VPS test boundary.

## 3. Host safety boundary

The disposable KVM guest lane must fail closed unless these controls hold:

- the VMM runs as a dedicated unprivileged host identity wherever technically possible;
- the host identity has no sudo/root-equivalent, Docker, LXD, libvirt-management, raw-disk or unrelated administrative group membership; only the minimum KVM device access is admitted;
- the VMM executable, trusted launcher and trusted base image are not writable by the lab identity;
- VMM seccomp/sandboxing is enabled;
- no host filesystem share, bind mount, 9p/virtiofs share, host Docker/containerd socket, host PID/IPC namespace, SSH agent, host credential or mutable host library path is exposed to the guest;
- no passthrough of arbitrary host devices;
- no QEMU monitor/QMP/HMP control socket is exposed to the guest or test code;
- guest storage uses an immutable verified base plus a fresh per-run disposable overlay;
- source/test inputs are transferred as data and unpacked/executed only inside the guest; the guest does not receive repository credentials merely to fetch its own source;
- default networking is denied/restricted; host/private/loopback/link-local/metadata/control-plane targets remain inaccessible from the guest;
- any required provider egress is explicit, destination-bounded and receipt-bound;
- the guest receives no credential that permits a return path into the VPS host;
- provider secrets are one-run guest-scoped values, not image-layer state, and are excluded from receipts/logs;
- CPU, memory, process/file descriptors, wall-clock runtime and disk growth are bounded so guest/VMM failure cannot starve the host;
- every run has a hard watchdog and unconditional cleanup path;
- on completion/failure, guest process, overlay, transient media, sockets, ephemeral keys and secrets are destroyed.

This boundary reduces host risk but does not claim mathematically zero VM-escape risk. The residual trust boundary is the hardware virtualization/VMM/kernel stack and the VPS provider.

## 4. Freedom inside the guest

Inside the disposable KVM guest, tests may deliberately exercise hostile conditions against the ClayVerse test instance, including:

- root/admin execution inside the guest;
- killing or wedging ClayVerse/EntityOS/PTY/tmux processes;
- OOM/resource-pressure tests inside the guest limits;
- filesystem/state corruption of disposable guest data;
- kernel panic/reboot/power-loss simulation;
- repeated crash/recovery and stale-generation tests;
- container/OCI builds and destructive replacement tests;
- fuzzing of product-local parsers/protocols and guest-local network services;
- Tier-1/Tier-2 recovery and effect-journal failure injection.

Freedom inside the guest never expands authority over the VPS host, other tenants or arbitrary external systems.

## 5. Runner-independent direct lane

The preferred steady-state control path is:

```text
authorized direct VPS control channel
-> trusted root-installed host launcher
-> dedicated unprivileged claylab identity
-> fresh KVM guest + disposable overlay
-> exact source/payload transfer
-> destructive/full-freedom guest test
-> bounded receipt/log digest export
-> unconditional guest destruction
-> optional durable receipt commit to GitHub
```

No GitHub Actions job or GitHub runner is required for the actual test command to start or complete.

Canonical implementation candidate:

```text
the artefact/ops/vps-kvm-lab/
```

## 6. Current real-VPS compatibility rule

The known VPS characteristics must be re-probed at execution time. Nested/hardware KVM availability is an empirical gate, not an assumption.

If `/dev/kvm` is missing/unusable or the provider disables nested virtualization, do not fake KVM credit and do not downgrade unrestricted testing to TCG. Report the precise KVM admission blocker.

## 7. Evidence law

Every hard-lane receipt binds at minimum:

- host orchestration identity without exposing host secrets;
- executor type and explicit `acceleration=KVM`/equivalent;
- explicit `tcg_fallback=false`;
- exact source revision/tree and staged payload digest;
- guest/base-image digest;
- guest kernel/machine identity where observable;
- exact command/test contract digest;
- bounded resource limits and network mode;
- exit status plus bounded log digest;
- cleanup result;
- OCI image digest where an OCI image was built/tested;
- explicit `github_actions_required=false` and `github_runner_required=false` for the direct lane.

Host-side orchestration success is zero product-runtime credit unless the intended command actually executed inside the disposable guest.

## 8. ClayVerse final-pass boundary

This directive creates a high-intensity VPS-hosted test laboratory. It does not weaken the existing final-product law:

- the final accepted ClayVerse artifact remains one exact OCI/Docker-compatible image;
- the complete accepted EntityOS substrate remains mandatory inside it;
- final `WHOLE_CLAYVERSE_PASS` still requires the same exact accepted OCI digest behind the independently verified hardware-virtualized VM/microVM guest-kernel boundary defined by the current MicroVM outer-envelope directive.

A KVM lab run can earn exact bounded runtime evidence at the scope actually executed. Whole-product PASS still requires the complete admitted acceptance path.

## 9. Supersession

Where older files say `VPS testing is forbidden` or `self-hosted VPS test runners are forbidden`, read them under this newer rule:

**direct host testing remains forbidden; runner-independent VPS-hosted disposable KVM guest testing is authorized under the controls above.**
