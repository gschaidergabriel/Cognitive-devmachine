# GO — EntityOS attested snapshot v2 verified on exact 92b62956; experiment slot consumed

Date: 2026-08-17
Program: CLAYVERSE_CLAY_MACHINE_ONLY / CLAY_MACHINE
Product boundary: exactly one executable `EntityOS`
Trigger: `go`
Execution surface: isolated Vercel build-internal Sandboxes only

## Exact executable evidence

Vercel deployment `dpl_7CZDVst5XGJp67fKs1EeT9KNwiwg` was Git-bound to product PR #787 exact source head:

`92b629566452d8f45fd208fba943b823ddd37e8c`

with exact source tree:

`14f8196483f3579be4724f4bba7dad3ded146b20`

The deployment actually started isolated Vercel Sandboxes. The empirical evidence is scoped to that exact head/tree and must not be generalized to later branch heads without a new exact-head run.

### Ordinary full-pytest gate

Observed summary `ClayVercelFullPytest/v2`:
- `ok=true`
- `status=FULL_PYTEST_SANDBOX_VERIFIED`
- exact Git identity `PASS`
- dependency closure `PASS`
- full pytest `PASS_ZERO_SKIPS`
- network policy during pytest `DENY_ALL`
- unusual experiment count `0`
- sandbox stopped `true`

### Canonical attested v7 gate

Observed summary `ClayVercelBuildBatch/v7`:
- `ok=true`
- `status=GO_SANDBOX_ATTESTED_SNAPSHOT_V2_VERIFIED`
- raw Git tree source provenance `PASS`
- `ATTESTED_SNAPSHOT_V2` provenance `PASS`
- exact source archive digest bound
- exact external attestation digest bound
- attested twin build `BYTE_IDENTICAL`
- attested runtime gates `PASS`
- attested relocation `BYTE_IDENTICAL`
- sanitized Git provenance `PASS`
- shallow-safe Git bundle `PASS`
- ClayVM Bytes v2 epoch fence `PASS`
- inherited Batch-5 regression matrix `PASS`
- one-file EntityOS `PASS` at this admitted artifact gate
- no-host-Python path `PASS`
- relocation copy/rename artifact and runtime output identical
- attested-vs-Git-clean EntityOS artifact `BYTE_IDENTICAL`
- sandbox stopped `true`

Exact observed EntityOS SHA-256:

`a68eb0cc2ac343d88421c9173e0d877f0f758b0ebd2e5918fd3e7a3c154b0c00`

Observed size: `9176080` bytes.

Observed source archive SHA-256:

`f574017f5fb5bd71dfb0f0b148b4e1b0c8521e7ab039b32e4f5696d81c3f100c`

Observed external attestation SHA-256:

`df47de56074cd8c2ff80168850d59d18a1c445c5782e2858f6a7d7e78284f84a`

## Exactly one unusual experiment — consumed

The preregistered experiment `ATTESTED_SNAPSHOT_CONTENT_TAMPER_FAIL_CLOSED` actually executed once in the v7 Sandbox and returned:

`PASS_FAIL_CLOSED_CONTENT_TAMPER`

The v7 summary reports:
- `new_unusual_experiment_count=1`
- `global_unusual_experiment_accounting=CONSUMED_1_OF_1_THIS_GO`

Therefore the one unusual-experiment slot for this user-triggered `go` macro-cycle is **consumed**.

Any later exact-head validation in this same macro-cycle MUST NOT mint another unusual experiment. If the same tamper intervention is repeated, it may be treated only as an explicitly labelled regression rerun with `new_unusual_experiment_count=0` and prior-evidence accounting. A later runner that again labels it as a fresh `1_of_1` experiment would violate the global GO accounting law even if the technical behavior remains fail-closed.

## Duplicate invocation observation

After the successful result markers existed, the same Vercel deployment invoked the build command again. The ordinary full-pytest runner and v7 runner both reused their completed result markers, reporting `SKIPPED_ALREADY_FINISHED_THIS_DEPLOYMENT`; no second Sandbox or unusual experiment was started. This is positive evidence for completed-result deduplication only.

A separate source-review gap remains for the v7 **pending concurrent owner** path: on head `92b62956...`, if a claim marker exists but no result marker exists yet, the runner logs `DUPLICATE_BUILD_INVOCATION_SKIPPED_CONCURRENT_OWNER` and exits 0. That fail-open pending-owner path is not exercised/proved safe by the completed-result observation and should still be hardened to nonzero/fail-closed or equivalent owner-result synchronization.

## Current-head drift boundary

During the 92b Sandbox run, PR #787 advanced to descendant head observed as:

`e4921d8c66c3fc34f68e056b710487026d9a4d03`

That descendant adds an exact installed Python distribution lock verifier. It is **not** covered by the 92b executable evidence until an exact-head Vercel Sandbox validates the descendant. Because the global unusual experiment is already consumed, descendant validation must use regression-only experiment accounting.

## Acceptance boundary

This evidence materially promotes the `ATTESTED_SNAPSHOT_V2` one-file artifact/provenance lane for exact head 92b62956. It does **not** establish whole EntityOS / whole Clay Computer acceptance: broader accepted baseline gates and the current canonical product head still remain outside this exact bounded artifact claim, and product `main` has not been promoted by this receipt.

Outcome: `EXACT_92B_ATTESTED_ENTITYOS_GATE_VERIFIED / GO_EXPERIMENT_CONSUMED_1_OF_1 / CURRENT_DESCENDANT_REQUIRES_REGRESSION_ONLY_REVALIDATION`.
