# GO Effect / Recovery fusion receipt — 2026-08-17

Trigger: `go`
Organ: GPT-5.6 Sol temporary Clay organ
Program: ClayVerse single-container
Stage: CLAYVERSE_ARTIFACT

## Scope

This receipt records the non-duplicate effect-boundary and restart-recovery work fused directly into canonical `main` during a rapidly advancing multi-worker cycle. It does not claim whole-container PASS and does not substitute source inspection for Vercel Sandbox truth.

## One unusual experiment consumed by this GO

`LEASE_EXPIRY_EFFECT_OVERLAP` was the single unusual experiment for this user-triggered macro-cycle.

The discriminator constructed two workers over one SQLite lease resource. Worker A acquired generation 1 with a deliberately short lease and began an external-effect analogue. After lease expiry, worker B acquired generation 2 and executed while A was still in flight. A was rejected only at completion as stale.

Observed mechanism: begin/completion lease checks can protect journal classification and causal credit while still permitting physical overlap when a lease expires during the external action. This negative result motivated full-window canonical serialization. No second unusual experiment was performed.

## Parallel fusion

Canonical `main` independently landed the core repair while this worker was active:

- one global label-independent `effect:entityos.exec` resource;
- unique per-attempt holders;
- exact resource/holder/generation/nonce cleanup;
- global entity-generation fencing;
- replay denial and stronger restart/active-turn handling;
- durable target/argv/outcome redaction.

The worker abandoned/closed duplicate PR paths and retained only non-overlapping defects.

## Non-duplicate defects fixed on main

1. Caller-supplied lease bypass

A valid lease for an unrelated resource could be passed to `EffectGate.execute(..., lease=...)`, suppressing the canonical automatic EntityOS lease. `entityos.exec` now rejects caller-supplied leases and `EffectGate` alone owns the canonical global fence.

Main commit: `18041d730161e423a12e4bc55e35db4fa0458b9f`.

2. Destructive journal construction

`EffectJournal.__init__` called `recover_pending()` unconditionally. In the intended shared UnifiedDB/two-persistent-terminal architecture, construction by a second live MCP/terminal process could classify another process's live `PENDING` effect as `UNKNOWN_AFTER_RESTART`.

Ordinary `EffectJournal` construction is now non-destructive.

Main commit: `42ff76e5329cce4296064b2cea8a2d1f058824d1`.

3. Explicit restart boundary

Pending-effect collapse remains fail-closed but is now invoked explicitly from `recover_incomplete_episodes()`, the container-restart recovery path, while preserving the newer active-turn, causal re-entry, lease-expiry, and global-generation logic.

Main commit: `c934bf9f9e968b6e8f11314d3511a7ed3de9f45c`.

4. Regression source alignment

`test_effect_fencing.py` was updated so the source obligations match the repaired contract:

- caller-supplied EntityOS lease bypass must fail before execution/journaling;
- stale completion tampers the automatic global EntityOS lease, not an unrelated caller lease;
- a second live `EffectGate` must not recover another connection's pending effect;
- explicit restart recovery must still collapse an orphaned pending effect to `UNKNOWN_AFTER_RESTART` with zero credit.

Main commit: `2783cd8bb5d59100f6fefdc86ce5c65d78512bc6`.

## Duplicate-path cleanup

PR #341 was closed after canonical main independently landed the core automatic EntityOS effect lease.
PR #355 was later closed after the remaining non-duplicate fixes were SHA-bound directly into main. No alternate permanent effect/recovery implementation is intended to remain canonical.

## Execution truth

No exact-current-head full pytest/OCI/runtime PASS is claimed here.

Vercel Sandbox execution is known to exist through the `dr-unterweger` build-internal Sandbox path. Historical/current-cycle evidence showed the original OCI gate blocked on unavailable Podman/Buildah provisioning. A Docker-in-Sandbox repair was prepared on product-repo commit `73ed538995b8427e14f6c64cffec9622d887613f`, but the GitHub `Vercel` status for that exact repair is currently `failure` with target `build-rate-limit` / upgrade-to-Pro. Therefore the repaired Docker gate is UNEXECUTED and repeated deployment attempts are intentionally not generated while that rate limiter is the active discriminator.

## Current next discriminator

When Vercel accepts another preview build:

1. execute the already-prepared Docker-in-Sandbox infrastructure repair once;
2. if that path works, restage the exact then-current research `main`/artefact tree;
3. execute the coordinated full artefact pytest + OCI build/run + restart + two-user contention gates in the real Vercel Sandbox;
4. bind exact source SHA/tree, commands, exit codes, image digest, runtime observations and Sandbox stop receipt;
5. do not generalize predecessor evidence to later heads.

Outcome: canonical source convergence improved and two concrete effect/recovery bypasses were removed. Whole ClayVerse container acceptance remains in progress and empirically blocked at the current Vercel build-rate-limit discriminator.
