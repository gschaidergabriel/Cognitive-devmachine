# the artefact — ClayVerse single-container candidate

Canonical product workspace for ClayVerse: **one exact immutable OCI/Docker-compatible ClayVerse image**, finally executed inside an independent VM/microVM guest-kernel isolation envelope.

## Living cycle status

Refresh this file in every product-convergent cycle. Detailed evidence belongs in receipts/history; this file carries current product reality plus the concrete latest-cycle delta.

### Current product contract

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- UnifiedDB is the sole durable canonical state/world/memory authority; ClayGraph is derived/rebuildable; MicroClay controls retrieval/accessibility only.
- Gabriel and Andreas are equal-rights perspectives into one central entity/global generation.
- Final image MUST contain complete accepted EntityOS, managed Linux PTY/tmux, Claude Code terminal runtime, GLM token/API client boundary, managed hooks/retrieval, EffectGate/EffectJournal and ClayVerse supervision.
- EntityOS-free #625 builds are development baselines only and can never receive whole-product PASS.
- Final deployment/acceptance additionally requires the same accepted OCI image digest inside an independent VM/microVM guest-kernel boundary. The microVM is an execution envelope, not a second product/entity/state authority.
- Root filesystem is read-only; only declared tmpfs and persistent ClayVerse state/workspace volumes may mutate.
- Ambiguous external effects after crash/recovery remain unknown unless durable idempotence/effect-journal evidence proves replay safe.
- VPS/self-hosted/production testing and Together remain forbidden for current evidence work.

### Retained convergence lanes

- **#625** — tokenless EntityOS-free development/baseline packaging plus EntityOS-bearing final-candidate path. Development baseline is useful for lower-layer testing; final acceptance still requires complete accepted EntityOS.
- **#622** — Python 3.13 hash-lock generator source candidate. The declared pip-tools bootstrap is hash-bound/offline-install oriented; no accepted canonical `requirements.lock.txt` yet.
- **#623** — this retained auth/identity/readiness/reauth drift-hardening lane. Source candidate only; DRAFT/unmerged.
- **#611** — retained tmux idempotent-reapply lane; exact final in-image runtime remains its promotion discriminator.
- **#602** — downstream managed native-Claude process attestation.
- **#810** — retained Vercel Sandbox controller evidence only; not final deployment architecture and not a reason to reintroduce a mandatory private-read token into the development baseline.

### #623 identity/restart law after this cycle

`IdentityRouter.resolve()` was already read/validate-only at request time. This cycle found a separate startup/restart gap: `IdentityRouter.__init__()` still called `ensure_session()` for both canonical users before normalizing persisted session state. Therefore an otherwise persisted UnifiedDB with a deleted canonical permanent session could silently recreate that session on restart and hide durable-state loss.

The retained #623 lane now separates **pristine bootstrap** from **persisted-state validation**:

- if the identity state is genuinely empty, bootstrap exactly Gabriel/Andreas and their exact permanent sessions;
- if canonical users already exist, startup does not create missing sessions; it only validates/normalizes the persisted session contract;
- a deleted persisted canonical session therefore fails closed and remains deleted as evidence of drift;
- if users are empty but session rows already exist, startup fails before bootstrapping users, preserving the corrupted state for recovery/audit;
- existing noncanonical session IDs, duplicate sessions, terminal drift, generation drift and equal-rights/user drift remain fail-closed under the retained #623 checks.

### Evidence from this cycle

- New source commits on #623: `c1c4290bc22e1163b4e0efa6a804a445e1277012`, `df61ca8805ad960113c3b140a493b5f7af483fe9`, `4ead235be191878e9e64ebdf3c5c8f4b09190d9e`.
- Added durable regressions for missing persisted session without repair, exact clean-bootstrap sessions, and the users-empty/sessions-present corruption boundary.
- Isolated SQLite mechanism falsifier: **4/4 PASS** — pristine bootstrap succeeds; deleted canonical session fails and stays missing; noncanonical session ID fails; orphan persisted session blocks bootstrap without mutation.
- Receipt: `the artefact/receipts/2026-08-17_GO_2124_PR623_IDENTITY_BOOT_FAIL_CLOSED_GPT56SOL.json` (receipt wording correction commit `a8e19b35e69d27318ddc7432ce2bfccdf4dc16c0`).
- GitHub Actions job/run details remain inaccessible to this connector (`403`), and the local isolated surface has no Docker/tmux. Therefore this is **MECHANISM_SUPPORTED / SOURCE CANDIDATE**, not exact PR-head pytest, OCI, real Clerk/browser PTY or whole-product evidence.

### Coordination refresh

At the latest observed refresh:

- #623 head before this README write had advanced beyond the semantic commits through receipt/documentation commits; rebind again before execution.
- #625 head observed: `606f1297da915efb2581f9e013b6c54586874d21`; its current owner-authority fence explicitly says EntityOS-free is development-only.
- #622 API head observed: `3b47c65dfbf97e15c50f9c49272d73a082f2bfcf`; its semantic workflow head is moving under evidence/documentation commits and remains unexecuted.
- #623 PR base observed `main` SHA: `79cdde5232e7047e2dabcd5e51a95da173e13bec`. Direct commit-list/head APIs returned `403`, so this README does not generalize that value beyond the PR-base observation.
- current `main/the artefact/README.md` and the current product directive were refreshed directly and already contain the stronger mandatory final EntityOS + VM/microVM envelope law.

### Unusual-experiment accounting

This exact user-triggered `go` still has no safely shared immutable request/turn identity for the required global unusual-experiment lease. **Zero unusual experiments** were executed. Deterministic corruption/regression falsifiers are ordinary adversarial validation and do not consume an unusual-experiment slot.

### Next executable discriminators

Continue independent evidence now, but do not promote until exact runtime gates are observed:

`fresh exact retained-lane fusion -> exact reproducible OCI image/digest with complete accepted EntityOS -> dependency hash-lock closure -> in-image tmux/Claude/EntityOS -> identity/restart regressions including missing-session no-repair -> real Clerk auth-first WebSocket PTY + reauth -> managed hooks/effects -> Tier-1 internal recovery -> same digest inside Kata/equivalent microVM -> Tier-2 full workload replacement -> UnifiedDB/WAL/snapshot/new-generation recovery -> stale-result/no-replay falsifiers -> dual-user concurrency -> WHOLE_CLAYVERSE_PASS`.

## Latest cycle delta

**2026-08-17 21:24 +07:00 — #623 startup identity bootstrap now fails closed on missing persisted canonical sessions instead of silently recreating them; canonical `main` product acceptance remains IN_PROGRESS.**

The cycle also refreshed against the newer owner law: EntityOS omission is development-only, and final ClayVerse acceptance now includes an independent VM/microVM guest-kernel envelope around the exact same OCI image digest. No claim from this #623 source lane is upgraded to final runtime evidence.

## Verification

Current evidence is bounded source/component evidence only. No exact final OCI image, accepted image digest, packaged Clerk/PTY/tmux/Claude runtime, complete EntityOS continuum, microVM execution or whole-product PASS has been observed in this lane.
