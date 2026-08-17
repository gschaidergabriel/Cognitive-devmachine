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
- The Kubernetes reference profile now starts from an explicit **default-deny ingress+egress NetworkPolicy**. Functional networking requires a separate reviewed deployment-specific allow policy. Final acceptance additionally MUST prove the selected CNI actually enforces NetworkPolicy and must separately fence/probe node-local, metadata-service and control-plane reachability; the policy object is not a substitute for the MicroVM guest-kernel boundary.

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

The supplied Kubernetes template selects `runtimeClassName: kata-qemu-runtime-rs`, runs exactly one ClayVerse replica, disables host PID/IPC/network authority, disables automatic ServiceAccount-token mounting, drops capabilities, enforces a read-only root filesystem, uses memory-backed `/tmp` and `/run`, persists only declared ClayVerse state/workspace volumes and now appends a ClayVerse-selected default-deny `networking.k8s.io/v1` NetworkPolicy for both ingress and egress.

That NetworkPolicy is intentionally a fail-closed baseline rather than a finished connectivity policy. The admitted deployment must provide a separate reviewed allow policy for only the exact required ingress/egress paths, prove the installed CNI enforces the policy, and separately test/fence node-local, metadata-service and control-plane paths that standard NetworkPolicy does not itself prove unreachable.

The installed RuntimeClass and target hardware virtualization support must be verified on the actual deployment platform before final acceptance. Provider-specific configuration may vary, but the VM/microVM invariants may not.

### Retained convergence lanes

- **#611** tmux idempotent-reapply lane — exact final in-image runtime remains its promotion discriminator.
- **#622** Python hash-lock generator — source candidate/unexecuted; no canonical accepted `requirements.lock.txt` yet.
- **#623** auth/identity/readiness/reauth drift lane — bounded source/mechanism candidate; not exact final runtime evidence. Its reported MicroVM network-policy gap is addressed by this retained current-main network-fusion lane, but #623 still needs fresh ancestry fusion before promotion.
- **#602** managed native-Claude process attestation — downstream of exact terminal/runtime acceptance.
- **#625** tokenless development/baseline packaging — useful lower-layer lane; EntityOS omission is development-only and can never be final acceptance.
- **#810** retained Vercel Sandbox controller evidence — historical/bounded execution bridge, not the final deployment architecture.

### Testing law

Continue maximum independent testing under `TESTING_STRATEGY.md`. In addition to existing source/unit/negative/adversarial/restart/concurrency/fuzz/reproducibility/integration testing, final MicroVM acceptance must prove:

- exact ClayVerse image digest equality outside/inside the microVM;
- an independent guest-kernel boundary rather than host-kernel execution;
- read-only root and denial of undeclared writes/host mounts;
- only declared persistent volumes survive full appliance replacement;
- the selected CNI really enforces the baseline NetworkPolicy;
- default-deny blocks policy-governed ingress/egress before a reviewed allow policy exists;
- the exact reviewed allow policy opens only admitted paths while tested non-admitted flows stay denied;
- node-local, metadata-service and control-plane paths are explicitly probed and fenced outside the assumptions of standard NetworkPolicy;
- Tier-1 EntityOS/internal recovery;
- Tier-2 full microVM/workload replacement from the same image digest;
- UnifiedDB/WAL/snapshot recovery under a new generation;
- stale pre-crash result rejection;
- no blind effect replay around crash/acknowledgement boundaries;
- Claude Code direct terminal login/runtime continuity;
- GLM token secrecy and inference-only authority.

### Current execution boundary

The architecture, Kata profile and source-level MicroVM network default-deny contract are concrete. The current network-fusion source blobs were rebound byte-for-byte in an authorized isolated non-production container and the focused static contract regression passed **6/6**. This is bounded exact-file source/mechanism evidence only.

**Actual Kubernetes CNI enforcement and Kata/microVM execution have not yet been observed for the exact final ClayVerse image**, so no VM-isolation/network-runtime credit or whole-product PASS is claimed.

Vercel/Sandbox and other direct-container execution may continue to provide lower-layer development evidence. The strongest refreshed Vercel observation still creates a disposable Firecracker Sandbox successfully but fails closed before private Research source staging because the sensitive host-side Preview `GITHUB_READ_TOKEN` is absent; source-runtime and OCI-runtime credit remain zero. Retrying that same blocked path without credential admission would add no product evidence.

### Final exact acceptance sequence

`fresh canonical source -> reproducible exact OCI image/digest -> complete EntityOS + UnifiedDB sealed continuum -> read-only root + declared volumes -> deploy SAME digest through Kata/equivalent microVM -> verify guest-kernel isolation -> verify CNI/default-deny + exact allow policy + node/metadata/control-plane fences -> ingress/egress -> managed PTY/tmux -> Claude terminal login and/or GLM token inference -> cognition/re-ingest/execute/result loop -> EffectGate/EffectJournal -> Tier-1 recovery -> destroy/recreate full microVM/workload -> WAL/snapshot recovery/new generation/no replay -> Clerk/WebSocket PTY -> dual-user concurrency -> WHOLE_CLAYVERSE_PASS`.

### Latest cycle delta

**2026-08-17 22:49 +07:00 — MicroVM network boundary strengthened from `hostNetwork: false` to an explicit fail-closed policy contract without overclaiming Kubernetes NetworkPolicy.**

- retained fresh-current-main lane: `gpt56sol/go-microvm-network-fusion-current-main-20260817-2249`;
- `clayverse-kata-statefulset.template.yaml` now contains one ClayVerse-selected `networking.k8s.io/v1` default-deny policy with both `Ingress` and `Egress`, `ingress: []`, `egress: []`, and an explicit `ClusterIP` Service baseline;
- `MICROVM_DEPLOYMENT_CONTRACT.md` now requires exact reviewed allow-policy identity, verified CNI enforcement, separate node-local/metadata/control-plane fencing, and records that NetworkPolicy is not a substitute for the mandatory guest-kernel boundary;
- focused regression now checks the default-deny source shape, forbids broad `0.0.0.0/0` / `::/0` source grants, and checks the CNI/node-local non-overclaim contract;
- exact Git blobs were independently rebound in an isolated container and the focused regression observed **6 passed in 0.06s**;
- Vercel admission remains empirically open, but the retained OCI controller remains blocked before private source staging by absent host-side `GITHUB_READ_TOKEN`; no source/OCI/Kata runtime credit is claimed;
- unusual experiment state: `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT` because this trigger exposes only minute-precision immutable message time and no shared immutable request/turn id;
- no VPS/self-hosted/production testing, Together API, secret exposure or paid/final training was used;
- whole-product acceptance remains **IN_PROGRESS**.

Previous architecture delta remains valid: the outer VM/microVM envelope is mandatory for final ClayVerse acceptance, not an optional future hardening.

## Verification

Architecture/source convergence is concrete, but **whole-product PASS is not claimed**. Final acceptance requires the exact same accepted ClayVerse image to pass both the internal appliance contract and the outer independent guest-kernel MicroVM contract, including measured network enforcement rather than policy-object presence alone.
