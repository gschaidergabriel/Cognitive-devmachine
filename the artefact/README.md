# the artefact — ClayVerse single-container candidate

Canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

Refresh this file in every product-convergent cycle. Detailed evidence belongs in receipts/history; this file carries the current product state.

### Product contract

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- Final runtime model: **sealed VM-like sandbox/appliance with explicit ingress and egress**.
- UnifiedDB is the sole durable canonical cognition/state/world/memory authority; ClayGraph is derived/rebuildable.
- The final accepted image MUST contain the complete accepted EntityOS execution/security/runtime substrate. EntityOS may be omitted only from explicitly classified development/baseline builds that can never receive whole-product PASS.
- Canonical internal loop: `INGRESS -> UnifiedDB -> retrieval/context -> Claude cognition -> proposed intent/command re-ingest -> policy/authority validation -> EntityOS/managed Linux PTY/tmux execution -> stdout/stderr/result/effect receipt -> UnifiedDB causal re-entry -> repeat -> EGRESS`.
- Claude/LLM output never bypasses ClayVerse directly into execution; it returns as proposed action/data first.
- Managed terminal control is mandatory inside the boundary. Unmediated generic host `process.exec` remains forbidden; admitted execution goes through the ClayVerse/EntityOS security/effect contract.
- Gabriel and Andreas are equal-rights perspectives into one central entity/global generation.
- Build/test/runtime validation remains authorized isolated-sandbox-only. VPS/self-hosted/production testing and Together are forbidden.

### Shock-absorber / automatic recovery law

The internal container boundary is deliberately a **stability shock absorber**. Internal failures should remain inside the ClayVerse machine continuum instead of making outside systems part of the runtime or state authority.

ClayVerse must maintain known-good logical machine snapshots binding at least:

- consistent UnifiedDB checkpoint/backup identity;
- global and canonical session generations;
- EntityOS binary/config/policy hashes;
- active causal turn/episode and resumable queue position;
- EffectJournal status for confirmed/pending/unknown effects;
- managed runtime identities required to reconstruct readiness.

On EntityOS or other critical internal runtime crash/wedge, the supervisor must automatically freeze new ingress/nonessential egress, fence the old generation, reconstruct from the last accepted snapshot, advance generation, re-attest UnifiedDB/EntityOS/terminal/Claude readiness and resume only through causal re-entry.

Ambiguous outside effects MUST NOT be blindly replayed after rollback. They become `UNKNOWN_AFTER_CRASH`/equivalent unless an explicitly idempotent contract plus durable EffectJournal evidence proves replay safe.

CRIU/filesystem/RAM snapshots may later optimize recovery, but they never replace the logical UnifiedDB/EffectJournal consistency contract.

### Retained convergence lanes

- **#611** tmux idempotent-reapply lane — exact in-image tmux remains its promotion discriminator.
- **#622** Python hash-lock generator — source candidate/unexecuted; no canonical accepted `requirements.lock.txt` yet.
- **#623** auth/identity/readiness/reauth drift lane — bounded source/mechanism candidate; not exact OCI/runtime evidence.
- **#602** managed native-Claude process attestation — downstream of exact in-image #611.
- **#625** tokenless baseline packaging — useful development/baseline lane. Its ability to omit EntityOS applies only to non-final builds; final ClayVerse acceptance requires complete accepted EntityOS in the same sealed continuum.
- Dr.-Unterweger **#810** remains historical/retained controller evidence; its cross-private-repo credential path is not the preferred baseline route.

### Testing policy

Missing direct Vercel Git-project linkage is not a development blocker. Continue maximum independent tests under `the artefact/TESTING_STRATEGY.md`.

Crash/recovery testing is now mandatory and includes EntityOS crash idle/active, terminal child crash, crash before/after effect emission and acknowledgement, interrupted UnifiedDB write, stale pre-crash result rejection, corrupt newest snapshot fallback, crash during recovery, no blind effect replay, ingress freeze during inconsistent state, and rejection of stale auth/session/generation resurrection.

### Current execution boundary

The final exact OCI/Sandbox gate remains deferred because the canonical Research repo is not directly connected to an executable Vercel project through the available connector surface. This does not stop source/product convergence or lower-layer testing.

### Final exact acceptance sequence

`fresh canonical source -> reproducible exact image/digest -> complete accepted EntityOS + UnifiedDB sealed continuum -> resolved dependency identities -> ingress/egress boundary -> managed Linux PTY/tmux -> Claude cognition/re-ingest/execute/result loop -> EffectGate/EffectJournal -> automatic known-good snapshot crash recovery -> Clerk/WebSocket PTY -> managed hooks -> persistence/restart/recovery -> dual-user concurrency/global-generation -> whole-product acceptance`.

Whole-product PASS requires this exact closure. Source inspection, static tests, mocks, component runtime PASS, deployment READY, Sandbox creation or historical evidence do not imply ClayVerse PASS.

### Latest cycle delta

**2026-08-17 21:07 +07:00 — architecture contract changed: final ClayVerse is explicitly a sealed VM-like ingress/process/egress machine continuum with complete EntityOS, direct managed Linux terminal control and automatic known-good snapshot recovery.**

- owner directive commit introduced the sealed machine-continuum law and made final accepted EntityOS mandatory;
- snapshot recovery is a product requirement, not an optional reliability enhancement;
- recovery advances/fences generations and never blindly replays ambiguous external effects;
- `TESTING_STRATEGY.md` now requires an adversarial crash/recovery matrix;
- receipt: `the artefact/receipts/2026-08-17_ARCH_2107_SEALED_CONTINUUM_SNAPSHOT_RECOVERY_GPT56SOL.json`;
- no whole-product PASS claimed and no final OCI runtime evidence added in this architecture-only update.

## Verification

Authorized bounded component evidence exists, but **whole-product PASS is not claimed**. Current work must now converge implementation toward the sealed continuum and its automatic snapshot recovery contract while maximizing all independently executable tests.
