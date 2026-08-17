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

The supplied Kubernetes template selects `runtimeClassName: kata-qemu-runtime-rs`, runs exactly one ClayVerse replica, disables host PID/IPC/network authority, disables automatic ServiceAccount-token mounting, drops capabilities, enforces a read-only root filesystem, uses memory-backed `/tmp` and `/run`, and persists only declared ClayVerse state/workspace volumes.

The same template also selects the ClayVerse pod with an explicit **default-deny `NetworkPolicy` for both ingress and egress**. It is intentionally network-nonfunctional until a separate deployment-specific reviewed allow policy is supplied. `hostNetwork: false` alone is not treated as network isolation. Final acceptance must bind the exact allow-policy bytes/identity, prove the chosen CNI actually enforces NetworkPolicy, enumerate the complete additive set of policies selecting the ClayVerse pod, and show that only admitted flows open while tested non-admitted flows remain denied.

Readiness and liveness are intentionally distinct: `/readyz` is the full runtime admission gate, while `/healthz` is the narrower liveness surface. A recoverable readiness loss must stop traffic without automatically being treated as a dead appliance.

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
- Claude Code direct terminal login/runtime continuity and process-environment secret isolation;
- GLM token secrecy and inference-only authority.

### Current execution boundary

The architecture and fail-closed Kata deployment profile are now canonical source. **Actual Kata/microVM execution and CNI NetworkPolicy enforcement have not yet been observed for the exact final ClayVerse image**, so no VM-isolation/network-policy runtime credit or whole-product PASS is claimed.

The now-current MicroVM source contract has been independently reconstructed from the exact three Git blobs and exercised in an authorized isolated non-production environment: Git blob identities matched **3/3** — contract `57db5224db000fc246445d68938b218ed8e4ff14`, template `b075755d24fcd3dbd203b02f67eeff8a5a8c571b`, focused test `a03de2e8fe1473c7e019dce66710bc04d244aa75` — and `tests/test_microvm_deployment_contract.py` passed **7/7**. The current set covers the mandatory guest-kernel envelope, immutable/runtime-state boundaries, default-deny ingress+egress, CNI enforcement obligations, `/readyz` readiness versus `/healthz` liveness, and bounded provider credential shape. This is bounded exact-file source/mechanism evidence only, not Kubernetes/Kata/CNI runtime evidence.

The Claude terminal source already starts the interactive process from `env -i`; the current source also carries an explicit regression fence against forwarding provider/auth/orchestration secret variables. Its byte-exact source/compile evidence remains bounded source-contract hardening until full exact-current-main pytest/live Claude-process attestation executes.

Vercel/Sandbox and other direct-container execution may continue to provide lower-layer development evidence. The retained Vercel #810 bridge has already proven Sandbox creation, but the exact private-source/OCI batch remains blocked before source staging by the missing host-side sensitive `GITHUB_READ_TOKEN`; that credential must never be committed or forwarded into the Sandbox. The connected Vercel tool surface available to this organ exposes inspection/documentation but no environment-secret mutation or direct Sandbox lifecycle mutation, so this prerequisite cannot be closed safely from this worker.

### Final exact acceptance sequence

`fresh canonical source -> reproducible exact OCI image/digest -> complete EntityOS + UnifiedDB sealed continuum -> read-only root + declared volumes -> deploy SAME digest through Kata/equivalent microVM -> verify guest-kernel isolation -> verify default-deny network enforcement -> bind/test explicit admitted network allow policy -> ingress/egress -> managed PTY/tmux -> Claude terminal login and process-env attestation and/or GLM token inference -> cognition/re-ingest/execute/result loop -> EffectGate/EffectJournal -> Tier-1 recovery -> destroy/recreate full microVM/workload -> WAL/snapshot recovery/new generation/no replay -> Clerk/WebSocket PTY -> dual-user concurrency -> WHOLE_CLAYVERSE_PASS`.

### Latest cycle delta

**2026-08-17 22:59 +07:00 — live-fused MicroVM contract independently replicated at current 7/7; execution blocker revalidated.**

- parallel live fusion had already closed the MicroVM default-deny NetworkPolicy gap and the liveness/readiness probe separation, so no duplicate implementation was created;
- independent exact reconstruction matched all three current Git blobs: contract `57db5224db000fc246445d68938b218ed8e4ff14`, template `b075755d24fcd3dbd203b02f67eeff8a5a8c571b`, focused test `a03de2e8fe1473c7e019dce66710bc04d244aa75`;
- focused deterministic regression: **7/7 PASS** (`python -m pytest -q tests/test_microvm_deployment_contract.py`);
- the parallel terminal secret-environment fence is retained: interactive Claude launches from the existing `env -i` allowlist and the new regression explicitly rejects provider/auth/orchestration secret forwarding; no second provider/security authority was introduced;
- retained #810 controller remains Draft at `78d92753d9442c66c3ffcff127c31faa98ffd622`; strongest bounded execution remains real `Sandbox.create` followed by fail-closed `PRIVATE_SOURCE_STAGE_BLOCKED:GITHUB_READ_TOKEN_MISSING`, with source/OCI runtime credit zero;
- the connected Vercel surface exposes no secret/environment mutation path, so safe host-side credential provisioning remains the exact admission blocker rather than another retry/controller fork;
- durable receipt: `receipts/2026-08-17_GO_2250_MICROVM_CURRENT_7OF7_INDEPENDENT_REPLICATION_GPT56SOL.json`; existing terminal/network receipts remain preserved;
- runtime credit remains **zero** for exact OCI, Kubernetes, Kata/microVM and CNI enforcement; source/mechanism evidence is not whole-product PASS;
- GO unusual experiment: `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`; zero unusual experiments executed because this trigger exposes no shared immutable request/turn id for the atomic lease.

## Verification

Architecture/source convergence is concrete, but **whole-product PASS is not claimed**. Final acceptance requires the exact same accepted ClayVerse image to pass both the internal appliance contract and the outer independent guest-kernel MicroVM contract, including actual enforcement of the accepted ingress/egress policy and live process-environment attestation.
