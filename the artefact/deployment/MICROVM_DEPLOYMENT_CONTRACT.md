# ClayVerse MicroVM deployment contract

Status: **MANDATORY FOR FINAL ACCEPTANCE**

The released ClayVerse product remains exactly one OCI/Docker-compatible image. Final deployment MUST place that same immutable image inside a hardware-virtualized VM/microVM runtime envelope. No second ClayVerse build, second state authority or companion cognition service is introduced.

## Final topology

`HOST -> hardware virtualization (KVM or equivalent) -> VM/microVM guest kernel -> OCI runtime -> exact ClayVerse image digest -> sealed ClayVerse machine continuum`

The preferred implementation line is an OCI-compatible sandboxed runtime such as Kata Containers. An equivalent runtime is admissible only if it preserves the invariants below.

## Required invariants

1. **Same artifact identity** — the image executed inside the VM/microVM MUST have the exact accepted ClayVerse OCI digest. MicroVM deployment may not rebuild or mutate the image.
2. **Separate guest kernel** — ClayVerse userspace MUST run behind a VM/microVM guest-kernel boundary, not directly on the host kernel, for final acceptance.
3. **One entity only** — the VM/microVM is an outer isolation envelope, not a second ClayVerse instance. UnifiedDB inside the ClayVerse continuum remains the sole state/world/memory authority.
4. **Immutable runtime** — ClayVerse root filesystem is read-only. Runtime scratch is limited to declared tmpfs/RAM surfaces. Code, EntityOS, policies and runtime binaries are recreated from the accepted image on restart.
5. **Explicit persistent state** — only declared persistent volumes cross runtime replacement boundaries, primarily `/var/lib/clayverse` for UnifiedDB/WAL/checkpoints/EffectJournal and any separately admitted workspace volume.
6. **Controlled ingress/egress** — only declared network/transport/storage surfaces cross the microVM boundary. `hostNetwork: false` is necessary but is not sufficient network isolation for a Kubernetes workload. The baseline deployment profile MUST select the ClayVerse pod with an explicit default-deny `NetworkPolicy` for both ingress and egress. The admitted cluster network plugin/CNI MUST actually support and enforce Kubernetes `NetworkPolicy`; merely creating the object on a non-enforcing cluster earns zero network-isolation evidence. Functional network access is enabled only by separate deployment-specific reviewed allow policies whose exact bytes/identity are bound into acceptance evidence. Because matching NetworkPolicies combine additively, final acceptance MUST enumerate every policy selecting the ClayVerse pod and fail if any unreviewed broad allow path changes the effective union. Host filesystem, host process namespace and host terminal are not ClayVerse runtime authorities.
7. **Terminal stays internal** — Linux PTY/tmux and EntityOS command execution run inside the ClayVerse image/guest boundary. No command is executed by an uncontrolled host shell path.
8. **LLM provider law preserved** — Claude Code is authenticated and operated directly through the managed internal terminal path. GLM is token/API inference only and receives no PTY, filesystem or EntityOS authority.
9. **Self-healing** — Tier-1 internal recovery reconstructs replaceable components from immutable image bytes. Tier-2 failure terminates the appliance and lets the VM/microVM/OCI supervisor create a clean runtime from the same accepted image digest before logical snapshot/WAL recovery.
10. **No blind external replay** — EffectJournal and generation fencing survive appliance recreation. Ambiguous effects become `UNKNOWN_AFTER_CRASH` rather than being automatically repeated.
11. **No hidden writable host dependency** — final ClayVerse functionality may not rely on mutable host binaries, host libraries, host home directories or undeclared host mounts.
12. **Attested boundary** — final acceptance records image digest, microVM runtime identity/version, guest kernel identity, host/guest isolation mode, mounted persistent volumes, exact network-policy identity, network-plugin/CNI identity and successful recovery evidence.

## Tier-2 full-sandbox replacement gate

A **container restart inside an existing VM/microVM is not Tier 2** and MUST NOT be reported as full-appliance recovery.

For the canonical Kubernetes/Kata profile this distinction is security-critical:

- a StatefulSet Pod template uses Kubernetes' required `restartPolicy: Always` semantics, so a terminated ClayVerse application container can be restarted by kubelet without deleting the Pod;
- Kata maps the **Pod sandbox** to the VM. Recreating a container inside the same Pod therefore does not itself prove that the Kata VM/sandbox was discarded or that a fresh guest-kernel boundary was created.

Accordingly, the reference StatefulSet is only the workload/isolation profile. Final deployment MUST additionally bind an **external orchestration mechanism** that converts a ClayVerse fatal-invariant/Tier-2 signal into deletion/replacement of the entire Pod sandbox/VM. That mechanism is deployment infrastructure, not a second ClayVerse cognition/state authority and not a companion application container.

The Tier-2 mechanism MUST fail closed and prove all of the following before ingress reopens:

- the old Pod UID and old Kata sandbox/VM identity are terminal and cannot rejoin;
- a new Pod UID and new sandbox/VM identity are observed;
- the new workload executes the exact same accepted ClayVerse image digest;
- only the declared persistent state/workspace volumes are reattached;
- UnifiedDB/WAL/logical-snapshot/EffectJournal recovery completes under a newly advanced global generation;
- stale pre-crash results are rejected;
- ambiguous external effects remain `UNKNOWN_AFTER_CRASH`/equivalent and are not blindly replayed;
- readiness re-attests EntityOS, terminal/PTY/tmux, selected LLM boundary, canonical users/sessions, network policy and generation consistency.

A normal kubelet container restart in the same Pod/sandbox may contribute Tier-1/component evidence only. It cannot satisfy the Tier-2 or `WHOLE_CLAYVERSE_PASS` gate.

Until a target deployment proves the external full-sandbox replacement behavior, the Kubernetes/Kata profile is explicitly **TIER2_REPLACEMENT_BLOCKED** for final acceptance even if its static security fields are correct.

## Runtime-class implementation profile

A Kubernetes/containerd deployment MAY use a sandboxed runtime class such as `kata`. If Kubernetes is used, the admitted ClayVerse workload MUST select the sandboxed RuntimeClass explicitly; silently falling back to the default host-kernel runtime is a final-acceptance failure.

### Kata runtime-rs security floor

Any admitted deployment using Kata Containers `runtime-rs` MUST use a release containing the upstream fix for **GHSA-2gv2-cffp-j227 / CVE-2026-47243**. Upstream classifies `runtime-rs` versions `<= 3.30.0` as affected and `3.31.0` as the first patched release, so `runtime-rs <= 3.30.0` is explicitly forbidden for ClayVerse final acceptance.

The `3.31.0` floor is a historical minimum fence, not a permanent safety claim. Immediately before final acceptance, ClayVerse MUST refresh current Kata upstream security advisories and release state, bind the exact installed Kata/runtime-rs version and configuration, and reject any version/configuration then known to be affected by a guest-to-host isolation escape or another critical boundary failure. Acceptance evidence MUST record the Kata release/runtime identity, relevant runtime configuration (including shared-filesystem/virtiofs mode where applicable), guest-kernel identity and the security-advisory review timestamp/source identity. A version string alone is not microVM security evidence.

The repository deployment template is deliberately fail-closed on networking: its ClayVerse-selected `NetworkPolicy` contains both `Ingress` and `Egress` policy types with empty rule sets. That baseline is intentionally non-functional until an environment-specific allow policy is supplied. The allow policy MUST admit only the exact product-required paths (for example the authenticated web ingress and the narrowly admitted external inference/authentication dependencies), must not silently grant broad host/cluster authority, and MUST be captured and tested as part of the deployment receipt. A permissive implicit cluster default is not acceptance evidence.

A Kubernetes `NetworkPolicy` object is declarative intent, not proof of enforcement. Before final deployment the selected CNI/network plugin and version MUST be identified and shown to enforce NetworkPolicy on the admitted nodes/runtime. The default-deny baseline MUST be exercised on the real target before any allow policy is added. After explicit allow policies are applied, acceptance MUST inspect the complete additive set of policies selecting the ClayVerse pod and prove that required flows work while representative undeclared ingress and egress remain denied. If the network plugin ignores NetworkPolicy, or policy inventory/effective behavior is uncertain, ClayVerse networking is `BLOCKED`, not accepted.

Other platforms may provide the same property through a native microVM OCI runtime. Provider-specific configuration is deployment material, not a second ClayVerse artifact.

## Acceptance tests

Final whole-product acceptance MUST include at least:

- prove exact OCI digest equality before and inside the microVM runtime;
- prove guest kernel differs from and is isolated from host kernel execution context;
- prove root filesystem is read-only and undeclared writes fail;
- prove only declared persistent volumes survive full appliance replacement;
- prove host PID/filesystem/terminal surfaces are not directly reachable as ClayVerse authority;
- identify and attest the actual network plugin/CNI and prove it enforces Kubernetes NetworkPolicy on the admitted target;
- prove the baseline ClayVerse network policy denies ingress and egress before any allow policy is added, including an undeclared external egress probe;
- apply the exact reviewed deployment allow policies, enumerate the full additive set selecting the ClayVerse pod, prove only admitted flows open, and prove representative undeclared flows remain denied;
- prove the installed Kata/runtime-rs identity satisfies the current upstream security baseline, explicitly rejecting `runtime-rs <= 3.30.0`, and record a fresh upstream advisory review before acceptance;
- where virtiofs/shared-filesystem transport is enabled, attest the exact runtime configuration and demonstrate that the admitted patched runtime/configuration is the one actually executing the ClayVerse workload;
- kill EntityOS and verify Tier-1 recovery;
- kill the full ClayVerse workload/microVM and verify Tier-2 reconstruction from the same image digest plus UnifiedDB/WAL/logical snapshot recovery;
- prove Tier-2 replacement changes both Pod UID and Kata sandbox/VM identity rather than merely restarting the ClayVerse container in place;
- inject stale pre-crash results and verify generation fencing;
- crash around external-effect acknowledgement and prove no blind replay;
- verify Claude Code terminal login path survives/re-establishes according to its credential/session contract;
- verify GLM token remains secret and GLM retains inference-only authority.

A normal OCI-container PASS without the required VM/microVM outer envelope is supporting evidence only and cannot receive final `WHOLE_CLAYVERSE_PASS`.
