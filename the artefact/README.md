# the artefact — ClayVerse single-container candidate

Canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

Refresh this file in every product-convergent cycle. Detailed evidence belongs in receipts/history; this file carries the current product state and latest concrete delta.

### Product contract

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- Final runtime model: **immutable sealed appliance / VM-like sandbox with controlled ingress and egress**.
- UnifiedDB is the sole durable canonical state/world/memory authority; ClayGraph is derived/rebuildable.
- The final accepted image MUST contain the complete accepted EntityOS execution/security/runtime substrate. EntityOS may be omitted only from explicitly classified development/baseline builds that can never receive whole-product PASS.
- The accepted OCI root filesystem is read-only. Runtime mutation is restricted to declared RAM/tmpfs paths; durable mutation is restricted to explicit persistent data areas such as `/var/lib/clayverse` and separately admitted workspace storage.
- Runtime code, EntityOS binaries, policies and managed settings are reconstructed from immutable image bytes after failure rather than repaired in place.
- Gabriel and Andreas are equal-rights perspectives into one central entity/global generation.

### Canonical machine loop

`INGRESS -> UnifiedDB canonicalize/record -> retrieval/context -> Claude cognition -> proposed intent/command re-ingest -> policy/authority validation -> EntityOS -> managed Linux PTY/tmux execution -> stdout/stderr/exit/effect receipt -> UnifiedDB causal re-entry -> repeat as needed -> EGRESS`

The LLM never bypasses ClayVerse directly into shell execution. Its output returns into the continuum first and remains proposed action/data until admitted by the execution/effect boundary.

The accepted ClayVerse/EntityOS layer must directly control the managed Linux PTY/tmux surface inside the appliance. Unmediated generic host `process.exec` remains forbidden.

### Shock-absorber / self-healing law

The inner machine boundary is deliberately a **stability shock absorber**. Runtime and state are separated:

- **Runtime:** EntityOS, Claude, PTY/tmux and orchestration are reconstructable/ephemeral from immutable image bytes.
- **State:** UnifiedDB/WAL/checkpoints, EffectJournal and admitted durable workspace are persistent and explicitly scoped.

ClayVerse maintains known-good logical machine snapshots binding at least UnifiedDB checkpoint identity, global/session generations, EntityOS/config/policy hashes, causal queue position and EffectJournal state.

Recovery is two-tiered:

1. **Internal recovery:** if invariants remain trustworthy, fence/restart only the failed EntityOS/Claude/PTY/tmux component, reconcile the last valid snapshot, re-attest readiness and resume through causal re-entry.
2. **Full appliance recovery:** if invariants cannot be trusted, fail the container closed and let the OCI runtime/orchestrator restart the entire appliance from the immutable base image. UnifiedDB/WAL/snapshot/effect-journal recovery runs before a new generation is minted and ingress reopens.

Ambiguous external effects are never blindly replayed after a crash. They become `UNKNOWN_AFTER_CRASH`/equivalent unless explicit idempotence plus durable EffectJournal evidence proves replay safe.

Fast deterministic restart is a design goal, but no fixed millisecond restart guarantee is claimed until measured on the admitted runtime.

OCI isolates product userspace but still shares the host kernel. If stronger kernel isolation is required later, the same ClayVerse image may run inside a deployment VM/microVM without changing the internal ClayVerse architecture.

### Retained convergence lanes

- **#611** tmux idempotent-reapply lane — exact in-image tmux remains its promotion discriminator.
- **#622** Python hash-lock generator — source candidate/unexecuted; no canonical accepted `requirements.lock.txt` yet.
- **#623** auth/identity/readiness/reauth drift lane — bounded source/mechanism candidate; not exact OCI/runtime evidence.
- **#602** managed native-Claude process attestation — downstream of exact in-image #611.
- **#625** tokenless development/baseline packaging — useful development lane. Its ability to omit EntityOS applies only to non-final builds; final ClayVerse acceptance requires complete accepted EntityOS in the same sealed continuum. The branch now explicitly fences this distinction in manifest/test/README; those source changes remain unmerged.
- Dr.-Unterweger **#810** is the retained Vercel Sandbox orchestration bridge/controller evidence. Its current cross-private-repo source-fetch route is credential-blocked before Research source staging when host-side `GITHUB_READ_TOKEN` is absent; this is not Sandbox unavailability and not ClayVerse TEST_FAIL.

### Testing policy

Continue maximum independent tests under `the artefact/TESTING_STRATEGY.md` while preserving isolated-sandbox-only execution.

Crash/recovery testing is mandatory: EntityOS crash idle/active, terminal child crash, crash before/after effect emission and acknowledgement, interrupted UnifiedDB write, stale pre-crash result rejection, corrupt newest snapshot fallback, crash during recovery, no blind effect replay, ingress freeze during inconsistent state, stale auth/session/generation rejection, read-only-root enforcement and undeclared-write denial.

### Current execution boundary

Vercel Sandbox execution is **confirmed** through the retained Dr.-Unterweger #810 Git-preview/OIDC controller. Bound runs have reached real `Sandbox.create` and clean stop. The current #810 cross-private-repo source-fetch design fails closed before Research source staging because the host-side sensitive `GITHUB_READ_TOKEN` is absent; source/OCI product-runtime credit therefore remains zero.

The tokenless #625 development baseline must not regain `GITHUB_READ_TOKEN` or mandatory private EntityOS staging merely to obtain lower-layer execution. Conversely, tokenless baseline evidence can never substitute for the final EntityOS-bearing image required by owner authority.

The authorized Daytona fallback remains a provider option, but the current ChatGPT orchestrator is blocked before Daytona provider contact. That is not evidence Daytona itself is unavailable.

### Final exact acceptance sequence

`fresh canonical source -> reproducible exact image/digest -> read-only rootfs + declared tmpfs/persistent write surfaces -> complete accepted EntityOS + UnifiedDB sealed continuum -> ingress/egress boundary -> managed Linux PTY/tmux -> Claude cognition/re-ingest/execute/result loop -> EffectGate/EffectJournal -> automatic tier-1 and tier-2 snapshot recovery -> Clerk/WebSocket PTY -> managed hooks -> persistence/restart/recovery -> dual-user concurrency/global-generation -> whole-product acceptance`.

Whole-product PASS requires this exact closure. Source inspection, static tests, mocks, component runtime PASS, deployment READY, Sandbox creation or historical evidence do not imply ClayVerse PASS.

### Latest cycle delta

**2026-08-17 21:17 +07:00 — `NO_CANONICAL_RUNTIME_CHANGE`: #625 was re-entered under the newest final-EntityOS authority, stale OCI-path duplication was fenced on its branch, and the current Sandbox execution boundary was corrected.**

- Canonical product law remains the immutable sealed appliance contract: final accepted ClayVerse MUST contain complete accepted EntityOS and automatic known-good snapshot/self-healing recovery.
- #625 remains an unmerged development/baseline source lane; tokenless builds may omit EntityOS only with execution disabled and can never receive whole-product PASS.
- On #625, the stale duplicate `clayverse-artifact-ci.yml` path was retired and a regression fences the single retained `clayverse-artefact-ci.yml` workflow authority. This is source-lane anti-entropy repair, not a canonical runtime promotion.
- After refreshing the newer owner directive, #625 manifest/test/README were corrected so development tokenlessness cannot be mistaken for final acceptance. Exact GitHub blobs `d25b9b69b0d5eb817549cd5db083955f33d43b50` and `a1ac6828421123b3ad09d2e7d775d66ff5e4a578` were byte-bound with `git hash-object`; the selected manifest-only acceptance-fence regression passed **1/1 in 0.66s** in the authorized isolated OpenAI container.
- Superseding branch receipt: `the artefact/receipts/2026-08-17_GO_2117_PR625_FINAL_ENTITYOS_AUTHORITY_REENTRY_GPT56SOL.json`. The earlier 21:12 receipt remains valid only for duplicate-workflow/execution-surface scope; any final-EntityOS-optional interpretation is superseded.
- Vercel classification is aligned with current continuity notices: Sandbox admission is confirmed through #810; its old private-source path is blocked before source staging by absent host-side credential. No source or OCI runtime credit is claimed.
- No unusual experiment was executed because the shared exact-go trigger identity remains insufficient for the atomic experiment lease.
- Exact OCI build/image digest, complete accepted EntityOS-in-image runtime, immutable/read-only appliance enforcement, sealed-continuum crash/snapshot recovery, Clerk/PTY/Claude and whole-product PASS remain open.

## Verification

Authorized bounded component/source evidence exists, but **whole-product PASS is not claimed**. Current work must converge implementation toward this immutable self-healing appliance contract while maximizing all independently executable tests.
