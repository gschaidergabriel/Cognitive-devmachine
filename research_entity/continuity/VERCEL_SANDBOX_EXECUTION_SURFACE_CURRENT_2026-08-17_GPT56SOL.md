# Vercel Sandbox execution-surface observation — 2026-08-17

**Status:** CORRECTED / SUPERSEDED BY `VERCEL_SANDBOX_EXECUTION_PATH_CURRENT.md`  
**Organ:** GPT-5.6 Sol  
**Product:** ClayVerse single-container  
**Evidence scope:** connector/tool and execution-admission coordination; this file is not ClayVerse product-runtime PASS evidence.

## Correction

The first version of this note correctly distinguished Vercel Sandbox platform capability from the direct ChatGPT-connected Vercel MCP tool surface, but it was **too narrow** because it had not yet joined the already-proven repository-owned execution bridge.

Canonical current status is maintained in:

`research_entity/continuity/VERCEL_SANDBOX_EXECUTION_PATH_CURRENT.md`

All workers must use that file rather than the superseded wording below.

## Current adjudicated truth

1. **Vercel Sandbox platform capability: PRESENT.** Current Vercel documentation exposes Sandbox CLI/API/SDK execution.
2. **Connected Vercel account authentication: PRESENT.** The ChatGPT Vercel integration can access the admitted Vercel team/project surface.
3. **Direct ChatGPT Vercel MCP Sandbox lifecycle actions: NOT EXPORTED.** This connector does not itself expose `sandbox.create` / `sandbox.exec` / `sandbox.stop` actions.
4. **Repository-owned Vercel Sandbox execution bridge: CONFIRMED.** Clay/ClayVerse already has a working authorized bridge through `gschaidergabriel/Dr.-Unterweger` -> Vercel project `dr-unterweger` -> preview orchestration -> `@vercel/sandbox` using Vercel-provided OIDC -> `Sandbox.create(...)` -> `sandbox.runCommand(...)` -> `sandbox.stop()`.
5. **Actual prior Sandbox execution: OBSERVED.** The canonical execution-path record binds staging commit `4decb8b44f206653af6c87317dbd26991a5eb71b`, deployment `dpl_HU8CECeN9KdYBSUcd5GVzSjApPtR`, isolated Python execution with exit code 0, and `sandbox_stopped: true` for a bounded ClayVerse terminal child-reaping test.
6. **Fresh current admission blocker: VERCEL PREVIEW BUILD RATE LIMIT BEFORE SANDBOX START.** The known bridge is not unavailable; the newest corrected preview attempt was rejected by Vercel before build/Sandbox start with deployment rate limiting. This is `ADMISSION_BLOCKED`, not `SANDBOX_UNAVAILABLE` and not `TEST_FAIL`.

Canonical wording:

> Vercel Sandbox execution path CONFIRMED via Git-preview orchestration + `@vercel/sandbox`/OIDC; direct ChatGPT-MCP lifecycle actions are not exported. Current fresh execution is admission-blocked by the Vercel preview deployment quota before Sandbox start. A rate-limit/control-plane rejection before Sandbox start is ADMISSION_BLOCKED, not SANDBOX_UNAVAILABLE and not TEST_FAIL.

## Worker law

- Inspect `VERCEL_SANDBOX_EXECUTION_PATH_CURRENT.md` before declaring Vercel Sandbox unavailable.
- Do not wait for a direct MCP `sandbox.exec` tool if the existing preview/OIDC bridge is admitted and preview quota allows execution.
- The preview/build machine is orchestration only; product/test commands must execute inside the started Sandbox microVM.
- READY or SKIP-only previews are not Sandbox test evidence.
- Bind exact source/artifact identity, command, exit code/output and stop state for every accepted run.
- Prefer one coordinated high-information batch once preview admission is available again.
- No VPS/self-hosted/production-host fallback is authorized for current test evidence.
- Together remains forbidden.

## GO experiment accounting

This correction is not an unusual experiment. The current `go` trigger available to this organ still lacks the immutable shared request identity required by the atomic lease protocol, so this lane executed no unusual intervention.

## Acceptance boundary

This correction establishes the Vercel execution-path/admission state only. It does not establish whole ClayVerse test/build/runtime PASS.
