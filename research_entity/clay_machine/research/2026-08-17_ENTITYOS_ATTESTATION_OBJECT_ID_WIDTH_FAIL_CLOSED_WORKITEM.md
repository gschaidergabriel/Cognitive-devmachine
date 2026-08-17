# EntityOS attestation object-id width — fail-closed work item

Date: 2026-08-17
Program: CLAYVERSE_CLAY_MACHINE_ONLY / CLAY_MACHINE
Product boundary: one executable `EntityOS`
Trigger context: `go`
Execution classification: SOURCE-INSPECTION WORK ITEM ONLY — not Vercel Sandbox evidence and not a new unusual experiment.

## Observed anchor

At product PR #787 head `4f09d74878b939d554af61b65e3f3b4c274a927d`, `entityos/build_canonical_onefile.py::_normalized_object_id` validates object identifiers with:

`[0-9a-f]{40,64}`

The same helper is used for the attested `source_head` and `source_tree` fields in `EntityOSSourceSnapshotAttestation/v2`.

That expression admits every hexadecimal length from 40 through 64 inclusive. It therefore accepts 41–63 hexadecimal characters even though this attestation surface names Git object identities and the currently admitted identities are fixed-width Git object IDs (40 hex for SHA-1 repositories or 64 hex for SHA-256 repositories).

The current Vercel staging lane derives the attestation from actual Git objects and separately binds the source manifest, so this finding is **not** evidence that the presently staged #787 path is exploitable. The narrower gap is that the canonical Git-free builder itself does not fail closed on unsupported intermediate object-id widths when the external attestation is its authority.

## Counterhypothesis / boundary

A broad 40–64 syntax could be intentional future-proofing for another digest family. No such intermediate-width object-id semantics are currently declared for `source_head` or `source_tree`, and silently admitting an undefined width conflicts with the active fail-closed provenance law. If future formats are admitted, they should be schema/version explicit rather than accepted by an interval regex.

## Smallest canonical hardening

1. Change generic Git object-id validation from a 40–64 interval to exactly 40 **or** exactly 64 hexadecimal characters, e.g. `(?:[0-9a-f]{40}|[0-9a-f]{64})`.
2. Add deterministic regressions that reject representative 41-, 48-, and 63-hex values for attested `source_head` and `source_tree`.
3. Preserve positive controls for exact 40-hex identities and, at the helper/schema boundary, exact 64-hex identities.
4. Keep the external attestation schema/version as the authority for any future identifier-family expansion; do not silently widen the regex.
5. When fused into the canonical product lane, require the existing exact-head isolated full-pytest gate and attested EntityOS Vercel Sandbox sequence before promotion.

## Experiment accounting

This is ordinary provenance hardening derived from source inspection. It consumes **zero** unusual experiments. The shared `go` unusual-experiment slot remains reserved for `ATTESTED_SNAPSHOT_CONTENT_TAMPER_FAIL_CLOSED` on PR #787 and must not be duplicated.

## Coordination

Do not open a competing permanent EntityOS builder/attestation implementation while PR #787 owns the canonical lane. Fuse this width fence into that lane (or its refreshed successor) after live overlap refresh.

Outcome: RETAIN as fail-closed provenance hardening work item; no EntityOS PASS claim.
