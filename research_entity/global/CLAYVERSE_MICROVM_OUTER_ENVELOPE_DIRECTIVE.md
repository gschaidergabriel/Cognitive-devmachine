# CLAYVERSE MICROVM OUTER ENVELOPE DIRECTIVE

**Authority date:** 2026-08-17  
**Authority:** newest explicit owner directive. This directive supersedes any older ClayVerse text that describes VM/microVM outer isolation as optional for final deployment.

## Final deployment law

The final accepted ClayVerse system MUST execute the **same accepted ClayVerse OCI image** inside a hardware-virtualized VM/microVM isolation envelope.

Canonical topology:

`HOST -> KVM/equivalent hardware virtualization -> VM/microVM guest kernel -> OCI/container runtime -> exact accepted ClayVerse image digest -> sealed ClayVerse continuum`

The preferred runtime family is an OCI-compatible sandboxed runtime such as Kata Containers. An equivalent implementation may replace Kata only if it proves the same isolation and identity invariants.

## Non-negotiable invariants

- The ClayVerse OCI image remains the single product artifact. The microVM does not create a second ClayVerse build or second state authority.
- Final acceptance requires an independent guest-kernel boundary. Running the image directly on the host kernel may be used for bounded development evidence but cannot receive `WHOLE_CLAYVERSE_PASS`.
- The exact image digest accepted before deployment MUST be the image digest executed inside the microVM. No provider-side rebuild or mutation is admitted.
- The ClayVerse root filesystem remains read-only. Only declared tmpfs/RAM and persistent volumes are writable.
- UnifiedDB remains the sole canonical state/world/memory authority. Persistent state survives appliance replacement only through declared scoped volumes/checkpoints/WAL/snapshots.
- Complete accepted EntityOS, managed PTY/tmux/Linux terminal, Claude Code terminal runtime, GLM token/API boundary, EffectGate/EffectJournal and ClayVerse supervision remain inside the same ClayVerse image/guest boundary.
- Claude Code is authenticated through its direct managed terminal login path. GLM is token/API inference only and receives no terminal/filesystem/EntityOS authority.
- Host PID namespace, host filesystem, host shell and host mutable libraries are not part of ClayVerse execution authority.
- Ingress/egress remains explicit and policy-controlled across both the microVM and ClayVerse boundaries.
- Tier-1 recovery recreates failed internal components from immutable image bytes. Tier-2 recovery discards/recreates the full microVM/workload from the exact accepted image digest, then restores logical ClayVerse state from UnifiedDB/WAL/known-good snapshot under a new generation.
- External effects are never blindly replayed after crash/recreation; ambiguous completion becomes `UNKNOWN_AFTER_CRASH` unless durable idempotence evidence proves replay safe.

## Final acceptance requirement

Final `WHOLE_CLAYVERSE_PASS` therefore requires evidence for **both** nested boundaries:

1. the internal sealed ClayVerse appliance contract; and
2. the outer independent guest-kernel VM/microVM contract.

The implementation/deployment contract is `the artefact/deployment/MICROVM_DEPLOYMENT_CONTRACT.md`.

Any newer implementation or documentation that treats direct host-kernel OCI execution as sufficient for final ClayVerse acceptance violates this directive.