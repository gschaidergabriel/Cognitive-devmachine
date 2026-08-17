# the artefact — ClayVerse single-container candidate

Canonical product workspace for the ClayVerse endpoint: **one immutable OCI/Docker-compatible ClayVerse image**, finally executed inside a dedicated VM/microVM isolation envelope.

## Living cycle status

Refresh this file in every product-convergent cycle. Detailed evidence belongs in receipts/history; this file carries current product reality.

### Product contract

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- Product artifact: **one exact immutable ClayVerse OCI image digest**.
- Final deployment topology: **Host → KVM/equivalent → VM/microVM guest kernel → OCI runtime → exact ClayVerse image → sealed ClayVerse continuum**.
- Final acceptance requires the independent guest-kernel boundary. Direct host-kernel OCI execution may provide bounded development evidence but cannot receive `WHOLE_CLAYVERSE_PASS`.
- Preferred outer runtime line: **Kata Containers / runtime-rs** (or an equivalent OCI-compatible VM/microVM runtime proving the same invariants).
- UnifiedDB is the sole durable canonical state/world/memory authority; ClayGraph is derived/rebuildable.
- Final image MUST contain complete accepted EntityOS, managed Linux PTY/tmux, Claude Code terminal runtime, GLM token/API client boundary, hooks/retrieval, EffectGate/EffectJournal and ClayVerse supervision.
- Root filesystem is read-only. Runtime mutation is limited to declared RAM/tmpfs; durable mutation is limited to explicit persistent volumes such as `/var/lib/clayverse` and admitted workspace storage.
- No host filesystem, host shell, host PID namespace, mutable host binaries or hidden companion cognition/state service is part of ClayVerse authority.

### Canonical machine loop

`INGRESS -> UnifiedDB canonicalize/record -> retrieval/context -> selected LLM -> response re-ingested into ClayVerse -> policy/authority validation -> EntityOS -> managed Linux PTY/tmux execution -> stdout/stderr/exit/effect receipt -> UnifiedDB causal re-entry -> repeat -> EGRESS`

The LLM never self-authorizes execution. Model output always comes back into ClayVerse first.

### LLM provider law

- **Claude Code:** interactive terminal-native path inside the managed ClayVerse PTY/tmux environment; authenticated directly through its terminal login flow. No hidden Claude API-token replacement for the primary path.
- **GLM:** token/API inference only. Its token is secret, never source/UnifiedDB/snapshot/receipt/log content. GLM receives no PTY, filesystem, EntityOS or effect authority.
- Switching Claude/GLM never forks the entity or state; the same UnifiedDB causal turn/session/generation continues.

### Shock-absorber / self-healing law

The nested isolation boundary is the stability shock absorber:

1. **Tier 1:** if invariants remain trustworthy, restart/fence only failed EntityOS/LLM-client/PTY/tmux components from immutable image bytes, reconcile the last valid logical snapshot and resume after readiness attestation.
2. **Tier 2:** if invariants are uncertain, discard/recreate the full ClayVerse workload/microVM from the exact accepted image digest, recover UnifiedDB/WAL/known-good logical snapshot/EffectJournal, mint a new generation and reopen ingress only after complete readiness.

Known-good logical snapshots bind at least UnifiedDB checkpoint identity, global/session generations, EntityOS/config/policy hashes, causal queue position, EffectJournal state and required runtime identities.

Ambiguous external effects are never blindly replayed after crash/recreation. They become `UNKNOWN_AFTER_CRASH`/equivalent unless explicit idempotence plus durable EffectJournal evidence proves replay safe.

### Concrete outer deployment profile

Deployment authority:

- `deployment/MICROVM_DEPLOYMENT_CONTRACT.md`
- `deployment/clayverse-kata-statefulset.template.yaml`
- `research_entity/global/CLAYVERSE_MICROVM_OUTER_ENVELOPE_DIRECTIVE.md`

The supplied Kubernetes template selects `runtimeClassName: kata-qemu-runtime-rs`, runs exactly one ClayVerse replica, disables host PID/IPC/network authority, disables automatic ServiceAccount-token mounting, drops capabilities, enforces a read-only root filesystem, uses memory-backed `/tmp` and `/run`, and persists only declared ClayVerse state/workspace volumes.

The installed RuntimeClass and target hardware virtualization support must be verified on the actual deployment platform before final acceptance. Provider-specific configuration may vary, but the VM/microVM invariants may not.

### Retained convergence lanes

- **#611** tmux idempotent-reapply lane — exact final in-image runtime remains its promotion discriminator.
- **#622** Python hash-lock generator — source candidate/unexecuted; no canonical accepted `requirements.lock.txt` yet.
- **#623** auth/identity/readiness/reauth drift lane — bounded source/mechanism candidate; not exact final runtime evidence.
- **#602** managed native-Claude process attestation — downstream of exact terminal/runtime acceptance.
- **#625** tokenless development/baseline packaging — useful lower-layer lane; EntityOS omission is development-only and can never be final acceptance.
- **#810** retained Vercel Sandbox controller evidence — historical/bounded execution bridge, not the final deployment architecture.

### Testing law

Continue maximum independent testing under `TESTING_STRATEGY.md`. In addition to existing source/unit/negative/adversarial/restart/concurrency/fuzz/reproducibility/integration testing, final MicroVM acceptance must prove:

- exact ClayVerse image digest equality outside/inside the microVM;
- an independent guest-kernel boundary rather than host-kernel execution;
- read-only root and denial of undeclared writes/host mounts;
- only declared persistent volumes survive full appliance replacement;
- Tier-1 EntityOS/internal recovery;
- Tier-2 full microVM/workload replacement from the same image digest;
- UnifiedDB/WAL/snapshot recovery under a new generation;
- stale pre-crash result rejection;
- no blind effect replay around crash/acknowledgement boundaries;
- Claude Code direct terminal login/runtime continuity;
- GLM token secrecy and inference-only authority.

### Current execution boundary

The architecture and deployable Kata profile are now canonical source. **Actual Kata/microVM execution has not yet been observed for the exact final ClayVerse image**, so no VM-isolation runtime credit or whole-product PASS is claimed.

Vercel/Sandbox and other direct-container execution may continue to provide lower-layer development evidence. The final release discriminator is now stronger: the completed exact image must also pass inside the mandatory VM/microVM outer envelope.

### Final exact acceptance sequence

`fresh canonical source -> reproducible exact OCI image/digest -> complete EntityOS + UnifiedDB sealed continuum -> read-only root + declared volumes -> deploy SAME digest through Kata/equivalent microVM -> verify guest-kernel isolation -> ingress/egress -> managed PTY/tmux -> Claude terminal login and/or GLM token inference -> cognition/re-ingest/execute/result loop -> EffectGate/EffectJournal -> Tier-1 recovery -> destroy/recreate full microVM/workload -> WAL/snapshot recovery/new generation/no replay -> Clerk/WebSocket PTY -> dual-user concurrency -> WHOLE_CLAYVERSE_PASS`.

### Latest cycle delta

**2026-08-17 21:17 +07:00 — architecture strengthened: the outer VM/microVM envelope is now mandatory for final ClayVerse acceptance, not an optional future hardening.**

- new global directive: `research_entity/global/CLAYVERSE_MICROVM_OUTER_ENVELOPE_DIRECTIVE.md`;
- new deployment contract: `the artefact/deployment/MICROVM_DEPLOYMENT_CONTRACT.md`;
- new concrete Kata StatefulSet template: `the artefact/deployment/clayverse-kata-statefulset.template.yaml`;
- new static deployment-contract regression: `the artefact/tests/test_microvm_deployment_contract.py`;
- the product artifact remains one ClayVerse OCI image; the MicroVM is an execution envelope, not a second product/entity;
- Claude Code remains direct terminal-login; GLM remains token/API inference-only;
- no actual final MicroVM runtime test has been executed in this architecture cycle, therefore acceptance remains `IN_PROGRESS`.

## Verification

Architecture/source convergence is concrete, but **whole-product PASS is not claimed**. Final acceptance requires the exact same accepted ClayVerse image to pass both the internal appliance contract and the outer independent guest-kernel MicroVM contract.