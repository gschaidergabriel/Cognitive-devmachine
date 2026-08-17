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
- `deployment/clayverse-kata-admission-policy.template.yaml`
- `research_entity/global/CLAYVERSE_MICROVM_OUTER_ENVELOPE_DIRECTIVE.md`

The supplied Kubernetes workload template selects `runtimeClassName: kata-qemu-runtime-rs`, runs exactly one ClayVerse replica, disables host PID/IPC/network authority, disables automatic ServiceAccount-token mounting, drops capabilities, enforces a read-only root filesystem, uses memory-backed `/tmp` and `/run`, and persists only declared ClayVerse state/workspace volumes.

The same workload template also selects the ClayVerse pod with an explicit **default-deny `NetworkPolicy` for both ingress and egress**. It is intentionally network-nonfunctional until a separate deployment-specific reviewed allow policy is supplied. `hostNetwork: false` alone is not treated as network isolation. Final acceptance must bind the exact allow-policy bytes/identity, prove the chosen CNI actually enforces NetworkPolicy, enumerate the complete additive set of policies selecting the ClayVerse pod, and show that only admitted flows open while tested non-admitted flows remain denied.

The Kata admission template adds a separate fail-closed Kubernetes `ValidatingAdmissionPolicy` + `ValidatingAdmissionPolicyBinding`. For ClayVerse Pod CREATE/UPDATE it denies the entire unreviewed `io.katacontainers.*` workload-annotation namespace, checks both the incoming object and `oldObject` so label removal cannot authorize annotation injection in the same update, uses `failurePolicy: Fail`, and binds failures to `Deny`. This is a source security floor only: final acceptance must prove the API server admits the exact policy, inspect the final Pod after all mutating admission, and exercise negative requests on the real target.

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
- the exact Kata admission policy is present with fail-closed `Deny`, rejects unreviewed `io.katacontainers.*` annotations after mutation, and cannot be bypassed by same-update ClayVerse-label removal;
- Tier-1 EntityOS/internal recovery;
- Tier-2 full microVM/workload replacement from the same image digest;
- UnifiedDB/WAL/snapshot recovery under a new generation;
- stale pre-crash result rejection;
- no blind effect replay around crash/acknowledgement boundaries;
- Claude Code direct terminal login/runtime continuity and process-environment secret isolation;
- GLM token secrecy and inference-only authority.

### Current execution boundary

The architecture and fail-closed Kata deployment profile are canonical source. **Actual Kubernetes admission, Kata/microVM execution and CNI NetworkPolicy enforcement have not yet been observed for the exact final ClayVerse image**, so no admission/VM-isolation/network-policy runtime credit or whole-product PASS is claimed.

The current default-deny network source contract has been independently reconstructed from the exact current Git blobs and exercised in an isolated non-production environment. That bounded source/mechanism evidence does not establish Kubernetes/Kata/CNI runtime behavior.

This cycle closes a separate source gap in the runtime-annotation boundary. Exact branch blobs `c54e5706dd6f74f9d09290af476aafab6e91c8ce` (admission policy) and `7d5565654a467d207fec6a75245d9630f5fc154a` (regression) were reconstructed byte-for-byte; focused pytest passed **4/4**, PyYAML loaded exactly `ValidatingAdmissionPolicy` + `ValidatingAdmissionPolicyBinding`, and Python compile passed. No API-server CEL compilation or live admission request executed, so this remains source/mechanism evidence only.

The Claude terminal source already starts the interactive process from `env -i`; the preceding cycle added an explicit source regression fence against forwarding current provider/auth/orchestration secret variables. Full exact-current-main pytest/live Claude process attestation remains unexecuted.

Vercel/Sandbox and other direct-container execution may continue to provide lower-layer development evidence. A direct re-read of retained PR #810 deployment `dpl_DSKkEM6GK2pWmrYXwsguRcu1Ryp8` confirms real Firecracker Sandbox creation and clean stop, but the exact private-source/OCI batch still fails closed before private source staging with `PRIVATE_SOURCE_STAGE_BLOCKED:GITHUB_READ_TOKEN_MISSING`; source-runtime and OCI-runtime credit remain zero and the credential must never be committed or forwarded into the Sandbox.

### Final exact acceptance sequence

`fresh canonical source -> reproducible exact OCI image/digest -> complete EntityOS + UnifiedDB sealed continuum -> read-only root + declared volumes -> deploy SAME digest through Kata/equivalent microVM -> verify guest-kernel isolation -> apply/prove Kata annotation admission fence -> verify default-deny network enforcement -> bind/test explicit admitted network allow policy -> ingress/egress -> managed PTY/tmux -> Claude terminal login and process-env attestation and/or GLM token inference -> cognition/re-ingest/execute/result loop -> EffectGate/EffectJournal -> Tier-1 recovery -> destroy/recreate full microVM/workload -> WAL/snapshot recovery/new generation/no replay -> Clerk/WebSocket PTY -> dual-user concurrency -> WHOLE_CLAYVERSE_PASS`.

### Latest cycle delta

**2026-08-17 22:59 +07:00 — fail-closed Kata workload-annotation admission fence added.**

- live source review found that the MicroVM contract already requires rejecting unreviewed `io.katacontainers.*` runtime-mutating annotations, but the deployment path had no executable admission-policy artifact; template absence alone was explicitly insufficient;
- current upstream Kata security evidence gives the gap product relevance: the July 2026 runtime-rs advisories include an arbitrary config-path/host-RCE class and an ungated host-path bind-mount annotation class, both patched in 4.0.0;
- added `deployment/clayverse-kata-admission-policy.template.yaml` with Kubernetes v1 `ValidatingAdmissionPolicy` + binding, `failurePolicy: Fail`, CREATE/UPDATE Pod scope, old/new ClayVerse identity fence and `validationActions: Deny`;
- added `tests/test_kata_annotation_admission_policy.py` to fence policy/binding identity, fail-closed action, update label-removal coverage, whole-prefix rejection and absence of a second runtime/state authority;
- exact written blobs: policy `c54e5706dd6f74f9d09290af476aafab6e91c8ce`; test `7d5565654a467d207fec6a75245d9630f5fc154a`;
- bounded isolated verification: exact Git blob match **2/2**, focused pytest **4/4 PASS**, semantic YAML probe **PASS**, Python compile **PASS**;
- strongest counterhypothesis remains open: static source tests do not prove Kubernetes API-server CEL compilation, admission ordering/effective post-mutation Pod state, installed Kata identity, CNI enforcement or actual guest-kernel isolation;
- retained #810 execution path was rechecked and remains credential-blocked before source staging by host-side `GITHUB_READ_TOKEN`; source/OCI runtime credit remains zero;
- GO unusual experiment: `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`; zero unusual experiments executed because this trigger exposes no shared immutable request/turn id with the precision required by the atomic lease protocol.

## Verification

Architecture/source convergence is concrete, but **whole-product PASS is not claimed**. Final acceptance requires the exact same accepted ClayVerse image to pass both the internal appliance contract and the outer independent guest-kernel MicroVM contract, including live admission enforcement, ingress/egress enforcement and process-environment attestation.
