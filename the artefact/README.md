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
- The interactive Claude process starts from `env -i` with an explicit allowlist. Supervisor/auth/provider/build-orchestration secrets are not part of that process environment; the regression fence explicitly covers Anthropic/Claude API variables, `GLM_API_TOKEN`, Clerk runtime secrets and `GITHUB_READ_TOKEN`.

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

The supplied Kubernetes template selects `runtimeClassName: kata-qemu-runtime-rs`, runs exactly one ClayVerse replica, disables host PID/IPC/network authority, disables automatic ServiceAccount-token mounting, drops capabilities, enforces a read-only root filesystem, uses memory-backed `/tmp` and `/run`, and persists only declared ClayVerse state/workspace volumes. The current StatefulSet uses a separate headless governing Service while keeping the client-facing Service distinct, and binds PVC ownership through pod `fsGroup: 10001` / `OnRootMismatch` without introducing a privileged ownership-repair path; actual CSI behavior remains an executable gate.

EntityOS artifact identity is image-authoritative: the Docker build derives the expected digest from the tracked `entityos.lock.json`, requires the build argument to equal that lock and verifies the embedded bytes before sealing the image. The MicroVM deployment template therefore does **not** override `CLAYVERSE_ENTITYOS_SHA256` from a Secret or other deployment configuration; a deployment-time integrity value must not become a parallel artifact authority.

The same template also selects the ClayVerse pod with an explicit **default-deny `NetworkPolicy` for both ingress and egress**. It is intentionally network-nonfunctional until a separate deployment-specific reviewed allow policy is supplied. `hostNetwork: false` alone is not treated as network isolation. Final acceptance must bind the exact allow-policy bytes/identity, prove the chosen CNI actually enforces NetworkPolicy, enumerate the complete additive set of policies selecting the ClayVerse pod, and show that only admitted flows open while tested non-admitted flows remain denied.

Readiness and liveness are intentionally distinct: `/readyz` is the full runtime admission gate, while `/healthz` is the narrower liveness surface. A recoverable readiness loss must stop traffic without automatically being treated as a dead appliance.

Tier-2 is explicitly stronger than an in-place application-container restart: final recovery must replace the whole Kata Pod sandbox/VM, prove a new Pod UID plus new sandbox/VM identity, reattach only declared persistent volumes, advance the canonical generation and re-attest readiness before ingress returns. Until an external fail-closed deployment mechanism proves that full-sandbox replacement, the reference Kubernetes/Kata profile is `TIER2_REPLACEMENT_BLOCKED` for final acceptance.

Kata security is version-and-configuration bound, not a fixed historical number. Upstream operates a rolling-release security model in which only the current monthly release is supported. The 2026-08-17 refresh makes the old `3.31.0` historical floor insufficient for final acceptance: upstream `releases/latest` identifies `4.0.0`, while July advisories affecting releases through `3.32.0` are first patched in `4.0.0`. Final deployment therefore must resolve and use the then-current supported release, reject unsupported prior releases, bind exact runtime/hypervisor/shared-filesystem configuration, and reject unreviewed runtime-mutating `io.katacontainers.*` Pod annotations after admission mutation.

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
- baseline ClayVerse ingress+egress deny is actually enforced by the deployed CNI;
- the exact reviewed network allow policy opens only admitted paths while tested non-admitted flows remain denied;
- the installed Kata/runtime identity is the then-current upstream-supported release and the effective runtime configuration/Pod annotations match the reviewed acceptance set;
- Tier-1 EntityOS/internal recovery;
- Tier-2 full Pod-sandbox/microVM replacement from the same image digest, with new Pod plus sandbox/VM identity rather than an in-place container restart;
- UnifiedDB/WAL/snapshot recovery under a new generation;
- stale pre-crash result rejection;
- no blind effect replay around crash/acknowledgement boundaries;
- Claude Code direct terminal login/runtime continuity and process-environment secret isolation;
- GLM token secrecy and inference-only authority.

### Current execution boundary

The architecture and fail-closed Kata deployment profile are canonical source, but **actual Kata/microVM execution, CNI NetworkPolicy enforcement and Tier-2 full-sandbox replacement have not yet been observed for the exact final ClayVerse image**, so no VM-isolation/network-policy/Tier-2 runtime credit or whole-product PASS is claimed.

A prior stronger MicroVM source slice was independently reconstructed from exact Git blobs and executed together in an isolated non-production container: contract `2e03fb7074c7b88191df31f12627bf656fe6d84e`, template `73f4dcf80f78fcb4d78e144e281758c194aff6df`, focused test `f0360882a33660ac49c7b9eb24a93ad99324526d`, and manifest `9ac10e882b4f760935f3671f479eb064d8fa058d` matched GitHub exactly; `pytest -q tests/test_microvm_deployment_contract.py` passed **12/12 in 0.06s**. That result remains bounded to those recorded blobs and is no longer exact-current after the EntityOS deployment-authority hardening in this cycle. The new template/test blobs therefore have source-contract credit only until an exact bound rerun executes.

The Claude terminal source starts the interactive process from `env -i`; the current source also carries an explicit regression fence against forwarding provider/auth/orchestration secret variables. Its byte-exact source/compile evidence remains bounded source-contract hardening until full exact-current-main pytest/live Claude-process attestation executes.

Vercel/Sandbox and other direct-container execution may continue to provide lower-layer development evidence. The retained Vercel #810 bridge has already proven Sandbox creation, but the exact private-source/OCI batch remains blocked before source staging by the missing host-side sensitive `GITHUB_READ_TOKEN`; that credential must never be committed or forwarded into the Sandbox. The connected Vercel tool surface available to this organ exposes inspection/documentation but no environment-secret mutation or direct Sandbox lifecycle mutation, so this prerequisite cannot be closed safely from this worker.

### Final exact acceptance sequence

`fresh canonical source -> reproducible exact OCI image/digest -> complete EntityOS + UnifiedDB sealed continuum -> read-only root + declared volumes -> deploy SAME digest through Kata/equivalent microVM -> verify guest-kernel isolation + current-supported Kata/runtime configuration -> verify default-deny network enforcement -> bind/test explicit admitted network allow policy -> ingress/egress -> managed PTY/tmux -> Claude terminal login and process-env attestation and/or GLM token inference -> cognition/re-ingest/execute/result loop -> EffectGate/EffectJournal -> Tier-1 recovery -> destroy/recreate full Pod sandbox/microVM -> prove new sandbox identity -> WAL/snapshot recovery/new generation/no replay -> Clerk/WebSocket PTY -> dual-user concurrency -> WHOLE_CLAYVERSE_PASS`.

### Latest cycle delta

**2026-08-17 — EntityOS deployment digest authority collapsed back into the immutable image.**

- current `go` detected that the tracked `entityos.lock.json` declares itself the EntityOS artifact authority while the Kubernetes template separately injected `CLAYVERSE_ENTITYOS_SHA256` from a mutable Secret;
- Kubernetes primary documentation confirms Pod `env` / `envFrom` values override environment values defined in the container image, so the deployment Secret could replace the image-baked expected digest even though it could not replace the read-only embedded EntityOS bytes;
- canonical MicroVM template commit `a420a7e7342d29a2713d6eddabfa353997876b01` removes that deployment-time digest override and documents the image-authoritative boundary;
- canonical focused-test commit `e612abc14cd5c6546f094537d8cd8810e24ab6aa` adds a regression requiring the template to expose no `CLAYVERSE_ENTITYOS_SHA256` / `entityos-sha256` deployment knob while retaining Docker build binding to the tracked lock;
- this is source/contract hardening only; no new exact-current pytest, OCI, Kubernetes or Kata runtime credit is claimed for these new blobs;
- strongest executable OCI blocker remains host-side provisioning of the sensitive Vercel Preview `GITHUB_READ_TOKEN` for private Research/EntityOS staging; it must remain outside the Sandbox and cannot be provisioned through the connected Vercel surface available to this organ;
- runtime credit remains **zero** for exact final OCI, Kubernetes, Kata/microVM, CNI enforcement, CSI behavior and Tier-2 full-sandbox replacement;
- GO unusual experiment: `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`; zero unusual experiments executed because this trigger exposes no shared immutable request/turn id and only minute-precision immutable message time.

## Verification

Architecture/source convergence is concrete, but **whole-product PASS is not claimed**. Final acceptance requires the exact same accepted ClayVerse image to pass both the internal appliance contract and the outer independent guest-kernel MicroVM contract, including actual current-supported Kata runtime/configuration, full-sandbox Tier-2 replacement, enforced ingress/egress policy, live process-environment attestation and declared-volume recovery behavior.
