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
- `deployment/clayverse-kata-annotation-admission-policy.yaml`
- `research_entity/global/CLAYVERSE_MICROVM_OUTER_ENVELOPE_DIRECTIVE.md`

The supplied Kubernetes template selects `runtimeClassName: kata-qemu-runtime-rs`, runs exactly one ClayVerse replica, disables host PID/IPC/network authority, disables automatic ServiceAccount-token mounting, drops capabilities, enforces a read-only root filesystem, uses memory-backed `/tmp` and `/run`, and persists only declared ClayVerse state/workspace volumes.

The same template also selects the ClayVerse pod with an explicit **default-deny `NetworkPolicy` for both ingress and egress**. It is intentionally network-nonfunctional until a separate deployment-specific reviewed allow policy is supplied. `hostNetwork: false` alone is not treated as network isolation. Final acceptance must bind the exact allow-policy bytes/identity, prove the chosen CNI actually enforces NetworkPolicy, enumerate the complete additive set of policies selecting the ClayVerse pod, and show that only admitted flows open while tested non-admitted flows remain denied.

The reference Kata admission fence is deliberately stricter than the workload template: a `ValidatingAdmissionPolicy` with `failurePolicy: Fail` plus a `Deny` binding rejects every Pod CREATE/UPDATE carrying an `io.katacontainers.*` annotation. The reference binding intentionally has no Pod `objectSelector`, because a Pod-label selector is an opt-in scope and is not an acceptable security boundary. On a shared cluster, any narrowing must use a separately reviewed and receipt-bound namespace boundary whose labels/RBAC are themselves attested. A required Kata annotation may be admitted only by explicit replacement policy bytes for the exact reviewed key/value; template absence alone never proves the effective admitted Pod is safe.

Readiness and liveness are intentionally distinct: `/readyz` is the full runtime admission gate, while `/healthz` is the narrower liveness surface. A recoverable readiness loss must stop traffic without automatically being treated as a dead appliance.

Tier-2 is also explicitly stronger than an in-place application-container restart: final recovery must replace the whole Kata Pod sandbox/VM, prove a new Pod UID plus new sandbox/VM identity, reattach only declared persistent volumes, advance the canonical generation and re-attest readiness before ingress returns. Until an external fail-closed deployment mechanism proves that full-sandbox replacement, the reference Kubernetes/Kata profile is `TIER2_REPLACEMENT_BLOCKED` for final acceptance.

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
- the exact ValidatingAdmissionPolicy + Binding are installed, reject an injected unreviewed `io.katacontainers.*` annotation, and cannot be bypassed through a Pod-label selector;
- Tier-1 EntityOS/internal recovery;
- Tier-2 full Pod-sandbox/microVM replacement from the same image digest, with new Pod plus sandbox/VM identity rather than an in-place container restart;
- UnifiedDB/WAL/snapshot recovery under a new generation;
- stale pre-crash result rejection;
- no blind effect replay around crash/acknowledgement boundaries;
- Claude Code direct terminal login/runtime continuity and process-environment secret isolation;
- GLM token secrecy and inference-only authority.

### Current execution boundary

The architecture and fail-closed Kata deployment profile are canonical source, but **actual Kata/microVM execution and CNI NetworkPolicy enforcement have not yet been observed for the exact final ClayVerse image**, so no VM-isolation/network-policy runtime credit or whole-product PASS is claimed.

The current MicroVM source slice has now been independently reconstructed from the exact Git blobs and executed together in an isolated non-production container: contract `794b209bc8ff14cbaf898b31557daac075977818`, template `629f7bbb7627e997839597edd499ce008c569a0f`, and focused test `283b269042e056e7adca227e84ae31a055f898da` all matched GitHub under `git hash-object`, and `pytest -q tests/test_microvm_deployment_contract.py` passed **10/10**. This exact-current source-slice result includes default-deny networking, separate `/healthz` versus `/readyz`, full Pod/Kata-sandbox Tier-2 semantics, rolling-release Kata security and runtime-annotation contract fences. It is bounded source/mechanism evidence only — not an OCI build, Kubernetes runtime, CNI enforcement, live Kata guest-kernel attestation or Tier-2 recovery execution.

The new admission-policy lane has a narrower evidence class: its exact branch YAML was parsed successfully and its policy/binding structure was checked locally, while the CEL form is grounded in the upstream CEL map-key `all()` semantics. No Kubernetes API-server admission execution has yet been observed for these new bytes, so this remains a source/mechanism candidate rather than admission-runtime proof.

The Claude terminal source starts the interactive process from `env -i`; the current source also carries an explicit regression fence against forwarding provider/auth/orchestration secret variables. Its byte-exact source/compile evidence remains bounded source-contract hardening until full exact-current-main pytest/live Claude-process attestation executes.

Vercel/Sandbox and other direct-container execution may continue to provide lower-layer development evidence. The retained Vercel #810 bridge has already proven Sandbox creation, but the exact private-source/OCI batch remains blocked before source staging by the missing host-side sensitive `GITHUB_READ_TOKEN`; that credential must never be committed or forwarded into the Sandbox. The connected Vercel tool surface available to this organ exposes inspection/documentation but no environment-secret mutation or direct Sandbox lifecycle mutation, so this prerequisite cannot be closed safely from this worker.

### Final exact acceptance sequence

`fresh canonical source -> reproducible exact OCI image/digest -> complete EntityOS + UnifiedDB sealed continuum -> read-only root + declared volumes -> deploy SAME digest through Kata/equivalent microVM -> verify guest-kernel isolation + current-supported Kata/runtime configuration -> install/prove fail-closed Kata annotation admission fence -> verify default-deny network enforcement -> bind/test explicit admitted network allow policy -> ingress/egress -> managed PTY/tmux -> Claude terminal login and process-env attestation and/or GLM token inference -> cognition/re-ingest/execute/result loop -> EffectGate/EffectJournal -> Tier-1 recovery -> destroy/recreate full Pod sandbox/microVM -> prove new sandbox identity -> WAL/snapshot recovery/new generation/no replay -> Clerk/WebSocket PTY -> dual-user concurrency -> WHOLE_CLAYVERSE_PASS`.

### Latest cycle delta

**GO 2026-08-17 22:59 +07:00 — fail-closed Kata runtime-annotation admission fence added as a bounded source candidate.**

- current `main` was refreshed through the fast-moving MicroVM lanes before write; the retained branch was created from the then-current `main` lineage observed through PR #632 base `608eafe5f154d0dbc3ddb4e9a2a8df3342cdd3d6`;
- added `deployment/clayverse-kata-annotation-admission-policy.yaml`: Kubernetes `admissionregistration.k8s.io/v1` ValidatingAdmissionPolicy + Binding, Pod CREATE/UPDATE, `failurePolicy: Fail`, `validationActions: Deny`, CEL rejection of every `io.katacontainers.*` annotation;
- adversarial review rejected the first draft's `objectSelector: app=clayverse` as label-bypassable and removed it before promotion/receipt; the baseline binding now applies to every Pod matched by the policy, with any shared-cluster namespace narrowing explicitly owner/review/receipt bound;
- added `tests/test_microvm_kata_annotation_admission_policy.py` to fence the fail-closed policy shape, the absence of a Pod-label selector, lack of preapproved Kata annotations in the reference workload, and the existing contract requirement for post-mutation admission enforcement;
- exact branch policy YAML parsed and structural assertions passed in an isolated non-production container; no API-server/Kata runtime credit is claimed;
- current upstream Kubernetes docs confirm unset binding `matchResources` validates all resources matched by the policy, `Deny` rejects failed validations, and `failurePolicy: Fail` rejects evaluation errors; CEL map comprehensions iterate map keys, supporting the prefix fence;
- no unusual experiment was executed: coordination is `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT` for the minute-precision trigger identity;
- exact final OCI/Kubernetes/Kata admission runtime remains blocked downstream; the retained Vercel source-staging prerequisite is still the missing host-side Preview `GITHUB_READ_TOKEN`, which must not enter the Sandbox.

## Verification

Architecture/source convergence is concrete, but **whole-product PASS is not claimed**. Final acceptance requires the exact same accepted ClayVerse image to pass both the internal appliance contract and the outer independent guest-kernel MicroVM contract, including actual current-supported Kata runtime/configuration, admission-policy enforcement, full-sandbox Tier-2 replacement, enforced ingress/egress policy and live process-environment attestation.
