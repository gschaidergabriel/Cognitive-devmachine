#!/usr/bin/env python3
"""Exact successor adapter for the GO878 line-checkpoint repair after batch-identity fusion.

The original line-checkpoint patcher deliberately fail-closes on source movement. Commit
329350ac fused the orthogonal historical batch causal-identity guard first, changing only
the exact backfill source identity relevant to the guard. This adapter preserves that
fail-closed law: it admits exactly the post-batch-guard source blob and delegates the
unchanged line-checkpoint transformation/regressions to the original patcher.

Source/tool presence is not runtime evidence and grants no EntityOS/HCU/J-Space/training
credit. A tested source merge still requires the focused regression gate on the exact
post-batch-guard source.
"""
from __future__ import annotations

import apply_go878_backfill_line_checkpoint as base

EXPECTED_BASE_PATCHER_SOURCE = "6c441c92024df8b0ff14c4246478523ae3d54266"
POST_BATCH_GUARD_SOURCE_BLOB = "f095ec12ab28aa5df87b1762b2cc19afca592365"
POST_BATCH_GUARD_TEST_BLOB = "702c2e42fe6e4881ef7a08b67f6b8b0b567ac8b4"


def main() -> int:
    # Fail closed if the delegated patcher's declared predecessor changed. A future
    # successor must re-audit the transformation instead of silently widening admission.
    if base.EXPECTED_SOURCE_BLOB != EXPECTED_BASE_PATCHER_SOURCE:
        raise SystemExit(
            "LINE_CHECKPOINT_BASE_PATCHER_MOVED_FAIL_CLOSED:"
            f"expected={EXPECTED_BASE_PATCHER_SOURCE}:observed={base.EXPECTED_SOURCE_BLOB}"
        )
    if base.EXPECTED_TEST_BLOB != POST_BATCH_GUARD_TEST_BLOB:
        raise SystemExit(
            "LINE_CHECKPOINT_TEST_IDENTITY_MOVED_FAIL_CLOSED:"
            f"expected={POST_BATCH_GUARD_TEST_BLOB}:observed={base.EXPECTED_TEST_BLOB}"
        )

    base.EXPECTED_SOURCE_BLOB = POST_BATCH_GUARD_SOURCE_BLOB
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
