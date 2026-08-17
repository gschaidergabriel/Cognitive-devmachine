# GO receipt — EntityOS attested snapshot v2 — 2026-08-17

## Scope

User-triggered `go` macro-cycle. Product endpoint remains the exact one-file `EntityOS` Clay Computer. Current work was bounded to PR #787 (`clay/go-entityos-attestation-recomposed-20260817`) and the missing product gate: an actual one-file freeze from a Git-free exact source snapshot using external `EntityOSSourceSnapshotAttestation/v2`.

## Canonical identities observed

- Research main at join: `68de25fddabe6502a39627d79921d8c2120bc143`.
- Product main: `6012d2cf4125e65d3a0c2df8d3b37119ae4f7b47`.
- PR #787 head after repair: `580fe7ac84b2d3930a4a944a6e32ddc51be47f33`.
- No PR #787 promotion/merge is justified by this receipt.

## Executable evidence observed in Vercel Sandbox

### Historical/current-lane regression anchor on `e5b800f1238762b4e4b7ee0c950674579e7037e2`

A build-internal isolated Vercel Sandbox actually ran the inherited Batch-5 matrix under `DENY_ALL` and reported `GO_SANDBOX_MATRIX_VERIFIED`. The one-file artifact was byte-reproducible and relocation/self-test/no-host-Python gates passed. However the actual build receipt remained `source_provenance=GIT_CLEAN_HEAD` with `source_archive_sha256=null`. Therefore this run does **not** establish the unique PR #787 Git-free attested-snapshot product claim.

### `b2ac19b0ed77b1af129e0b538ecd944dfb7563c2`

An isolated Vercel Sandbox started and bound the exact source head/tree/archive. It failed in `derive_external_v2_attestation_from_exact_git_authority` with a Python `SyntaxError: unterminated string literal`. The sandbox stopped successfully. No unusual experiment step executed.

Outcome: negative evidence; no product PASS.

### `8afc19e3f8053104c4a453ebae03956c72256955`

An isolated Vercel Sandbox started, verified the raw Git-tree archive, external attestation digest, pinned toolchain, and switched test networking to `DENY_ALL`. It then failed in `attested_snapshot_v2_exact_entityos_double_build` before the registered unusual intervention. Final summary included:

- `ok=false`
- `status=GO_SANDBOX_MATRIX_FAILED`
- `new_unusual_experiment_count=0`
- `global_unusual_experiment_accounting=PENDING_1_OF_1_THIS_GO`
- `stopped=true`

Outcome: the current GO unusual-experiment slot was not consumed by this run.

### `3c0b024fc538ad393fbb1f64ffae6ba79a5f2b51`

Independent subsequent exact-head Vercel execution reproduced the same boundary: toolchain/setup passed, `attested_snapshot_v2_exact_entityos_double_build` failed before the unusual intervention, sandbox stopped, and `new_unusual_experiment_count=0` remained.

Outcome: failure is reproducible at the attested-snapshot build boundary; no product PASS and no experiment slot consumed.

## Source-level mechanism hypothesis and repair

Inspection found a cross-language canonical-order mismatch:

- `entityos/build_canonical_onefile.py` requires attestation entries to equal Python lexicographic ordering by path and fails closed with `ENTITYOS_SOURCE_ATTESTATION_FILES_NOT_SORTED` otherwise.
- `stage-go-source.mjs` had sorted paths with locale-sensitive `a.path.localeCompare(b.path, 'en')`.

PR #787 head `580fe7ac84b2d3930a4a944a6e32ddc51be47f33` replaces that locale-sensitive ordering with UTF-8 byte ordering via `Buffer.compare(Buffer.from(path, 'utf8'), ...)`, which is deterministic and intended to match the builder's ordering contract for admitted valid UTF-8 paths.

This is a source-supported repair hypothesis, **not executable proof**.

## Current exact-head blocker

GitHub/Vercel status for `580fe7ac84b2d3930a4a944a6e32ddc51be47f33` reported Vercel failure target `upgradeToPro=build-rate-limit`. No isolated Vercel Sandbox was started for that exact repaired head. Under the current execution law, this means the repair remains UNVERIFIED/BLOCKED rather than PASS or FAIL.

Do not substitute Vercel READY, source inspection, local execution, VPS execution, or historical receipts for the missing exact-head Sandbox run.

## Current GO experiment accounting

Observed started Sandbox executions in this receipt reached **zero** unusual-experiment steps. The one registered new intervention remains:

`ATTESTED_SNAPSHOT_CONTENT_TAMPER_FAIL_CLOSED`

When an authorized exact-head build-internal Vercel Sandbox can start, execute this intervention exactly once. All Git-free double-build, cross-provenance byte comparison, self-test/pathless/relocation gates, inherited Batch-5 checks, and later reruns are acceptance/regression controls, not additional unusual experiments.

## Next executable gate

On the exact current PR #787 head (or a newer descendant after re-refresh), once Vercel build capacity permits an actual build-internal Sandbox start:

1. bind exact source head/tree/raw archive/external v2 attestation;
2. perform the Git-free attested `EntityOS` double build;
3. require receipt `source_provenance=ATTESTED_SNAPSHOT_V2` and non-null exact archive digest;
4. execute the single registered content-tamper fail-closed intervention exactly once if still unconsumed;
5. reconstruct sanitized exact Git provenance and run inherited Batch-5 regressions;
6. require byte identity between attested-snapshot and Git-clean `EntityOS` artifacts;
7. require self-test, no-host-Python, relocation, `DENY_ALL`, exact digest, and successful Sandbox stop;
8. only then adjudicate PR #787 promotion.

## Acceptance statement

`EntityOS` whole-machine acceptance remains false/in progress. This receipt narrows the active provenance blocker and preserves two exact Sandbox failures plus the Vercel rate-limit blocker without converting any of them into a synthetic PASS.
