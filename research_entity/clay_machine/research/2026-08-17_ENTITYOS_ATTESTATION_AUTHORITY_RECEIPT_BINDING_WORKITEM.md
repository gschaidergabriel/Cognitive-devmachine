# EntityOS attestation-authority receipt binding — bounded work item

Date: 2026-08-17
Program: CLAYVERSE_CLAY_MACHINE_ONLY / CLAY_MACHINE
Product boundary: one executable `EntityOS`
Trigger context: `go`
Execution classification: SOURCE-INSPECTION WORK ITEM ONLY — not Vercel Sandbox evidence and not a new unusual experiment.

## Observed anchor

In the active PR #787 ancestry after the `EntityOSSourceSnapshotAttestation/v2` implementation, the canonical builder verifies the external attestation schema, expected source head, declared source tree/hash syntax, transport, and the complete snapshot file set/mode/SHA-256 contents. The resulting `SourceProvenance` and `EntityOSBuildReceipt/v1` carry `source_provenance`, `source_tree`, and `source_archive_sha256`.

The receipt does not currently bind the SHA-256 digest of the exact external attestation document that authorized the Git-free snapshot. `source_tree` and `archive_sha256` are authority metadata read from that attestation; the builder does not independently derive either Git object identity or archive digest from the unpacked snapshot alone.

## Counterhypothesis / boundary

This is not evidence that the current attestation path is exploitable. Treating the external attestation as the authority may be intentional. The gap is narrower: durable replay/provenance cannot identify the exact authority document from the build receipt alone.

## Proposed smallest canonical hardening

1. Extend `SourceProvenance` with `source_attestation_sha256: str | None`.
2. In `ATTESTED_SNAPSHOT_V2` mode, hash the exact external attestation bytes after successful validation and carry the digest into provenance.
3. Add `source_attestation_sha256` to `EntityOSBuildReceipt/v1` (null for Git-clean mode unless schema evolution requires otherwise).
4. In the build-internal Vercel lane, compare that receipt digest with the independently staged/manifest-bound attestation digest before accepting the artifact.
5. Add deterministic unit regressions for exact digest binding and substituted-attestation mismatch.

## Promotion rule

Do not implement or test this as a second unusual intervention in the current 2026-08-17 `go`. The only reserved unusual experiment remains `ATTESTED_SNAPSHOT_CONTENT_TAMPER_FAIL_CLOSED`. This work item is ordinary provenance hardening/regression work and may be fused after or alongside the current exact-head acceptance blocker without multiplying runtime semantics.

Outcome: RETAIN as hardening work item; no EntityOS PASS claim.