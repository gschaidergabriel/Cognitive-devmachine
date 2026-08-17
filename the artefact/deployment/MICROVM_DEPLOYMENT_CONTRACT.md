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
6. **Controlled ingress/egress** — only declared network/transport/storage surfaces cross the microVM boundary. Host filesystem, host process namespace and host terminal are not ClayVerse runtime authorities.
7. **Terminal stays internal** — Linux PTY/tmux and EntityOS command execution run inside the ClayVerse image/guest boundary. No command is executed by an uncontrolled host shell path.
8. **LLM provider law preserved** — Claude Code is authenticated and operated directly through the managed internal terminal path. GLM is token/API inference only and receives no PTY, filesystem or EntityOS authority.
9. **Self-healing** — Tier-1 internal recovery reconstructs replaceable components from immutable image bytes. Tier-2 failure terminates the appliance and lets the VM/microVM/OCI supervisor create a clean runtime from the same accepted image digest before logical snapshot/WAL recovery.
10. **No blind external replay** — EffectJournal and generation fencing survive appliance recreation. Ambiguous effects become `UNKNOWN_AFTER_CRASH` rather than being automatically repeated.
11. **No hidden writable host dependency** — final ClayVerse functionality may not rely on mutable host binaries, host libraries, host home directories or undeclared host mounts.
12. **Attested boundary** — final acceptance records image digest, microVM runtime identity/version, guest kernel identity, host/guest isolation mode, mounted persistent volumes, network policy and successful recovery evidence.

## Runtime-class implementation profile

A Kubernetes/containerd deployment MAY use a sandboxed runtime class such as `kata`. If Kubernetes is used, the admitted ClayVerse workload MUST select the sandboxed RuntimeClass explicitly; silently falling back to the default host-kernel runtime is a final-acceptance failure.

Other platforms may provide the same property through a native microVM OCI runtime. Provider-specific configuration is deployment material, not a second ClayVerse artifact.

## Acceptance tests

Final whole-product acceptance MUST include at least:

- prove exact OCI digest equality before and inside the microVM runtime;
- prove guest kernel differs from and is isolated from host kernel execution context;
- prove root filesystem is read-only and undeclared writes fail;
- prove only declared persistent volumes survive full appliance replacement;
- prove host PID/filesystem/terminal surfaces are not directly reachable as ClayVerse authority;
- kill EntityOS and verify Tier-1 recovery;
- kill the full ClayVerse workload/microVM and verify Tier-2 reconstruction from the same image digest plus UnifiedDB/WAL/logical snapshot recovery;
- inject stale pre-crash results and verify generation fencing;
- crash around external-effect acknowledgement and prove no blind replay;
- verify Claude Code terminal login path survives/re-establishes according to its credential/session contract;
- verify GLM token remains secret and GLM retains inference-only authority.

A normal OCI-container PASS without the required VM/microVM outer envelope is supporting evidence only and cannot receive final `WHOLE_CLAYVERSE_PASS`.