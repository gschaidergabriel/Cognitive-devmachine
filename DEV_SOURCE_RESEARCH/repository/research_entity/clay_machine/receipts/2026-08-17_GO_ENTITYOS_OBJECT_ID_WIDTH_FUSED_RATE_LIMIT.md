# GO — EntityOS attestation object-id width fused; exact-head Vercel blocked

Date: 2026-08-17
Program: CLAYVERSE_CLAY_MACHINE_ONLY / CLAY_MACHINE
Product boundary: exactly one executable `EntityOS`
Trigger: `go`

## Current bounded product delta

Canonical product main remains `6012d2cf4125e65d3a0c2df8d3b37119ae4f7b47`.
Active product candidate is PR #787 branch `clay/go-entityos-attestation-recomposed-20260817` at observed head `16986218b1fdfa6fc3b36547ed33257bfd4f7588`.

This GO fused the fail-closed Git object-id width hardening requested by research work item `2026-08-17_ENTITYOS_ATTESTATION_OBJECT_ID_WIDTH_FAIL_CLOSED_WORKITEM.md`:

- `517b0511a9b65a324ce0d88e2022b440ae1725b8` changes `_normalized_object_id` from accepting every 40–64 hex width to accepting exactly 40 or exactly 64 hex characters.
- `16986218b1fdfa6fc3b36547ed33257bfd4f7588` adds deterministic positive controls for 40/64 and fail-closed controls for 41/48/63.

The same active PR already contains:
- exact external attestation byte SHA-256 binding in `SourceProvenance` and `EntityOSBuildReceipt/v1` at `fc8484008d7b99735321790b5a03ff609cdd0222`;
- canonical v7 receipt enforcement of exact source tree, archive SHA-256 and attestation SHA-256 at `9d829960c32ec88e0b48531328134a05a82f5483`;
- pre-experiment full-pytest gating and source-bound dependency closure.

## Executable evidence boundary

No exact-head Vercel Sandbox execution exists for `16986218b1fdfa6fc3b36547ed33257bfd4f7588`.
The GitHub Vercel status for this head is provider failure with build-rate-limit before Sandbox start. This is infrastructure blocking, not product PASS and not a Sandbox runtime FAIL.

The last relevant actually-started v7 Sandbox negative evidence remains the earlier exact candidate `fa9827d496602d7c5821b13103da665f7287b16c`: it reached the Git-free attested double-build step and failed before the reserved unusual experiment; Sandbox stop succeeded. Later sort/receipt/dependency/object-id repairs are therefore source deltas awaiting exact-head execution.

## GO unusual-experiment accounting

New unusual experiments executed by this delta: `0`.
The one shared GO unusual experiment remains reserved and unconsumed: `ATTESTED_SNAPSHOT_CONTENT_TAMPER_FAIL_CLOSED`.
Do not consume or duplicate it without an actually-started exact-head Vercel Sandbox execution.

## Next exact executable discriminator

When an authorized Vercel Git-bound build can actually start, refresh PR #787 head and run the existing coordinated build-internal sequence on that exact head. Promotion requires source-bound dependency preflight, ordinary full pytest with zero skips and zero unusual experiments, exact Git-free twin `EntityOS` builds with source tree/archive/attestation receipt binding, runtime/relocation/no-host-Python gates under `DENY_ALL`, exactly the one preregistered content-tamper fail-closed experiment, inherited Batch-5 regressions with zero new unusual experiments, attested-vs-Git-clean byte identity, and successful Sandbox stop.

Outcome: SOURCE_HARDENING_FUSED / EXECUTABLE_ACCEPTANCE_BLOCKED_BY_VERCEL_RATE_LIMIT.
Whole EntityOS / whole Clay Computer acceptance remains false.
