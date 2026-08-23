# JSPACE/GWT RUNTIME SOURCE ADMISSION v1

Status: SOURCE COMPOSITION GATE / RUNTIME UNVERIFIED
Scope: exact-source admission for `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1`.

## Problem closed

The canonical boot-binding validator proves structural coherence and cross-binds the bundled cognition manifest, source lock, model/tokenizer/runtime/lens/J-Space/GWT identities and authority claims. Its `source.main_sha` and `source.tree_sha` fields were previously validated only as non-placeholder SHA-1-shaped values.

A receipt could therefore carry internally consistent but externally false source commit/tree values and still pass the structural validator. The downstream UCF ancestry chain compared its cycle source to those same receipt values, so agreement between two self-declared fields did not prove the checkout that actually contained the validator and admitted source objects.

That is a provenance false-green class, not a J-Space semantic failure.

## Canonical composition

`validate_jspace_gwt_runtime_admission_v1.py` does not replace or fork the canonical boot validator. It composes it:

```text
JSPACE_GWT_BOOT_BINDING_RECEIPT/v1
    -> canonical validate_jspace_gwt_boot_binding_v1.py
    -> canonical manifest/source-lock cross-binding
    -> live Git checkout measurement
         git rev-parse --show-toplevel
         git rev-parse --verify HEAD
         git rev-parse --verify HEAD^{tree}
         git status --porcelain=v1 --untracked-files=all
    -> exact receipt source HEAD/tree equality
    -> clean-checkout requirement
    -> JSPACE_GWT_RUNTIME_ADMISSION/v1
```

The runtime-admission wrapper derives the repository root from the committed validator's own location. It does not accept an arbitrary caller-selected repository as source authority. The admitted bundled manifest and source-lock paths must also resolve inside that same checkout.

## Fail-closed laws

```claycode
r4.discriminate(
  require(runtime_admission_reuses_canonical_boot_validator),
  require(source_root == git_toplevel_containing_runtime_admission_validator),
  require(manifest_path within source_root),
  require(source_lock_path within source_root),
  require(receipt.source.dirty == false),
  require(git_status_clean == true),
  require(receipt.source.main_sha == git_HEAD),
  require(receipt.source.tree_sha == git_HEAD_tree)
)
```

Typed failures include:

- `SOURCE_ROOT_NOT_GIT_TOPLEVEL`;
- `SOURCE_RECEIPT_DIRTY_NOT_RUNTIME_ADMISSIBLE`;
- `SOURCE_CHECKOUT_DIRTY`;
- `SOURCE_HEAD_MISMATCH`;
- `SOURCE_TREE_MISMATCH`;
- `BUNDLED_MANIFEST_OUTSIDE_SOURCE_ROOT`;
- `SOURCE_LOCK_OUTSIDE_SOURCE_ROOT`;
- Git command/unavailability failures.

A dirty boot receipt may still exist as diagnostic evidence under the structural contract, but it cannot receive this exact runtime-source admission. This prevents an unverifiable dirty-diff digest from becoming execution authority.

## Invocation

Structural validation remains useful for source/unit regressions:

```text
python validate_jspace_gwt_boot_binding_v1.py RECEIPT.json BUNDLED_MANIFEST.json SOURCE_LOCK.json
```

Exact runtime source credit requires the composed gate from the checked-out repository:

```text
python validate_jspace_gwt_runtime_admission_v1.py RECEIPT.json BUNDLED_MANIFEST.json SOURCE_LOCK.json
```

A structural boot-validator PASS alone is therefore explicitly **SOURCE/STRUCTURE ONLY**. It must not be promoted to exact-source Ubuntu runtime evidence.

## Evidence boundary

This gate proves only that an otherwise valid boot receipt is bound to the clean Git commit/tree that actually contains the admission validator and its admitted repository-side manifest/source-lock inputs.

It does **not** prove:

- that Qwen3.5-0.8B executed;
- that checkpoint/tokenizer/runtime bytes have been admitted yet;
- J-Space causal usefulness;
- GWT/Thalamus/EPQ semantic quality;
- Zero identity persistence;
- Claude Code adapter runtime correctness;
- Whole-GWT, BASE, or whole Mini Entity PASS.

Those credits remain zero until the required exact intentional Ubuntu execution and later calibration/falsification gates actually run.
