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

The same template also selects the ClayVerse pod with an explicit **default-deny `NetworkPolicy` for both ingress and egress**. It is intentionally network-nonfunctional until a separate deployment-specific reviewed allow policy is supplied. `hostNetwork: false` alone is not treated as network isolation. Final acceptance must bind the exact allow-policy bytes/identity, prove the chosen CNI actually enforces NetworkPolicy, enumerate the complete additive set of policies selecting the ClayVerse pod, and show that only admitted flows open while tested non-admitted flows remain denied.

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
- Tier-1 EntityOS/internal recovery;
- Tier-2 full microVM/workload replacement from the same image digest;
- UnifiedDB/WAL/snapshot recovery under a new generation;
- stale pre-crash result rejection;
- no blind effect replay around crash/acknowledgement boundaries;
- Claude Code direct terminal login/runtime continuity;
- GLM token secrecy and inference-only authority.

### Current execution boundary

The architecture and fail-closed Kata deployment profile are now canonical source. **Actual Kata/microVM execution and CNI NetworkPolicy enforcement have not yet been observed for the exact final ClayVerse image**, so no VM-isolation/network-policy runtime credit or whole-product PASS is claimed.

The current default-deny source contract has been independently reconstructed from the exact three current Git blobs and exercised in an isolated non-production environment: Git blob identities matched **3/3**, `tests/test_microvm_deployment_contract.py` passed **6/6**, and a PyYAML 6.0.3 semantic probe loaded exactly `Service`, `StatefulSet`, `NetworkPolicy` with `clayverse-default-deny`, `app: clayverse`, `Ingress` + `Egress`, and empty ingress/egress rule sets. This is bounded exact-file source/mechanism evidence only, not Kubernetes/Kata/CNI runtime evidence.

Vercel/Sandbox and other direct-container execution may continue to provide lower-layer development evidence. The retained Vercel #810 bridge has already proven Sandbox creation, but the exact private-source/OCI batch remains blocked before source staging by the missing host-side sensitive `GITHUB_READ_TOKEN`; that credential must never be committed or forwarded into the Sandbox. A fresh Vercel project check in this cycle found **zero new deployments since 2026-08-17 14:30 UTC**, so no newer credential-capable runtime evidence supersedes that blocker.

### Final exact acceptance sequence

`fresh canonical source -> reproducible exact OCI image/digest -> complete EntityOS + UnifiedDB sealed continuum -> read-only root + declared volumes -> deploy SAME digest through Kata/equivalent microVM -> verify guest-kernel isolation -> verify default-deny network enforcement -> bind/test explicit admitted network allow policy -> ingress/egress -> managed PTY/tmux -> Claude terminal login and/or GLM token inference -> cognition/re-ingest/execute/result loop -> EffectGate/EffectJournal -> Tier-1 recovery -> destroy/recreate full microVM/workload -> WAL/snapshot recovery/new generation/no replay -> Clerk/WebSocket PTY -> dual-user concurrency -> WHOLE_CLAYVERSE_PASS`.

### Latest cycle delta

**2026-08-17 22:57 +07:00 — current MicroVM network source re-bound after parallel fusion; OCI blocker rechecked.**

- a stale write attempt was correctly rejected with `409`; after refresh, parallel work had already closed the #623-discovered NetworkPolicy gap, so no duplicate implementation was created;
- exact current Git blobs independently reconstructed and matched: template `788492ef...`, MicroVM contract `2608f5ca...`, focused test `5c2f48f7...`;
- focused deterministic regression: **6/6 PASS** (`python -m pytest -q tests/test_microvm_deployment_contract.py`);
- semantic YAML probe: exactly `Service`, `StatefulSet`, one `NetworkPolicy`; deny policy selects `app=clayverse`, carries `Ingress` + `Egress`, and has exact empty ingress/egress rule sets;
- canonical manifest already binds the default-deny baseline, reviewed deployment-specific allow-policy requirement and final CNI enforcement gate;
- fresh #810/Vercel evidence check: zero new deployments since 14:30 UTC; retained deployment `dpl_DSKkEM6GK2pWmrYXwsguRcu1Ryp8` remains `Sandbox.create` PASS then `PRIVATE_SOURCE_STAGE_BLOCKED:GITHUB_READ_TOKEN_MISSING`, with source/OCI runtime credit zero;
- durable receipt: `receipts/2026-08-17_GO_2257_MICROVM_NETWORK_EXACT_RECHECK_AND_OCI_BLOCKER_GPT56SOL.json`;
- runtime credit remains **zero** for exact OCI, Kubernetes, Kata/microVM and CNI enforcement; source/mechanism evidence is not whole-product PASS;
- GO unusual experiment: `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`; zero unusual experiments executed because this trigger exposes no shared immutable request/turn id for the atomic lease.

## Verification

Architecture/source convergence is concrete, but **whole-product PASS is not claimed**. Final acceptance requires the exact same accepted ClayVerse image to pass both the internal appliance contract and the outer independent guest-kernel MicroVM contract, including actual enforcement of the accepted ingress/egress policy.
