# the artefact — ClayVerse single-container candidate

Canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

Refresh this file in every product-convergent cycle. Detailed evidence belongs in receipts/history; this file carries the current product state.

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
- **#625** tokenless baseline packaging — useful development/baseline lane. Its ability to omit EntityOS applies only to non-final builds; final ClayVerse acceptance requires complete accepted EntityOS in the same sealed continuum.
- Dr.-Unterweger **#810** remains historical/retained controller evidence; its cross-private-repo credential path is not the preferred baseline route.

### Testing policy

Missing direct Vercel Git-project linkage is not a development blocker. Continue maximum independent tests under `the artefact/TESTING_STRATEGY.md`.

Crash/recovery testing is mandatory: EntityOS crash idle/active, terminal child crash, crash before/after effect emission and acknowledgement, interrupted UnifiedDB write, stale pre-crash result rejection, corrupt newest snapshot fallback, crash during recovery, no blind effect replay, ingress freeze during inconsistent state, stale auth/session/generation rejection, read-only-root enforcement and undeclared-write denial.

### Current execution boundary

The final exact OCI/Sandbox gate remains deferred because the canonical Research repo is not directly connected to an executable Vercel project through the available connector surface. This does not stop source/product convergence or lower-layer testing.

### Final exact acceptance sequence

`fresh canonical source -> reproducible exact image/digest -> read-only rootfs + declared tmpfs/persistent write surfaces -> complete accepted EntityOS + UnifiedDB sealed continuum -> ingress/egress boundary -> managed Linux PTY/tmux -> Claude cognition/re-ingest/execute/result loop -> EffectGate/EffectJournal -> automatic tier-1 and tier-2 snapshot recovery -> Clerk/WebSocket PTY -> managed hooks -> persistence/restart/recovery -> dual-user concurrency/global-generation -> whole-product acceptance`.

Whole-product PASS requires this exact closure. Source inspection, static tests, mocks, component runtime PASS, deployment READY, Sandbox creation or historical evidence do not imply ClayVerse PASS.

### Latest cycle delta

**2026-08-17 21:07 +07:00 — the appliance paradigm was made explicit and hardened: immutable read-only runtime, persistent UnifiedDB state, direct managed PTY loop, complete EntityOS in the final image, and two-tier automatic self-healing from known-good logical snapshots.**

- owner directive: sealed VM-like ingress/process/egress continuum plus automatic snapshot recovery;
- immutable appliance refinement: read-only OCI rootfs, RAM/tmpfs for ephemeral mutation, explicit persistent data areas only;
- recovery refinement: Tier 1 internal component reconstruction and Tier 2 full container restart from immutable image;
- manifest updated to encode the same runtime/state/recovery laws;
- testing strategy requires the adversarial crash/recovery matrix;
- receipts:
  - `the artefact/receipts/2026-08-17_ARCH_2107_SEALED_CONTINUUM_SNAPSHOT_RECOVERY_GPT56SOL.json`
  - `the artefact/receipts/2026-08-17_ARCH_2107_IMMUTABLE_APPLIANCE_SELF_HEALING_GPT56SOL.json`
- no whole-product PASS claimed and no final OCI runtime evidence added in this architecture update.

## Verification

Authorized bounded component evidence exists, but **whole-product PASS is not claimed**. Current work must now converge implementation toward this immutable self-healing appliance contract while maximizing all independently executable tests.
