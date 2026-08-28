#!/usr/bin/env python3
"""Exact successor adapter for replay-stable backfill line identity after provenance fusion.

The original GO878 line-checkpoint patcher deliberately admits one exact predecessor
blob. Subsequent canonical work hardened historical batch identity and replay-provenance
source-count semantics without repairing the still-present incremental `local_line`
reset. This adapter rebinds the unchanged cumulative-line transformation to that exact
post-provenance source only.

Fail-closed law:
- the delegated base patcher must still name the currently audited post-provenance source
  and exact test blob;
- the current backfill source must hash to POST_PROVENANCE_FUSION_SOURCE_BLOB when the
  delegated patcher executes;
- any further source movement requires another explicit audit/successor, never widening
  admission implicitly.

Source/tool presence is not runtime evidence and grants no EntityOS/HCU/J-Space/training
credit. The resulting source plus regressions still require authorized exact-source
execution and a bounded receipt before promotion.
"""
from __future__ import annotations

import apply_go878_backfill_line_checkpoint as base

EXPECTED_BASE_PATCHER_SOURCE = "5cb0045f5c355170372efd4f08c033b33c91fbed"
EXPECTED_TEST_BLOB = "702c2e42fe6e4881ef7a08b67f6b8b0b567ac8b4"
POST_PROVENANCE_FUSION_SOURCE_BLOB = "5cb0045f5c355170372efd4f08c033b33c91fbed"


def main() -> int:
    if base.EXPECTED_SOURCE_BLOB != EXPECTED_BASE_PATCHER_SOURCE:
        raise SystemExit(
            "LINE_CHECKPOINT_BASE_PATCHER_MOVED_FAIL_CLOSED:"
            f"expected={EXPECTED_BASE_PATCHER_SOURCE}:observed={base.EXPECTED_SOURCE_BLOB}"
        )
    if base.EXPECTED_TEST_BLOB != EXPECTED_TEST_BLOB:
        raise SystemExit(
            "LINE_CHECKPOINT_TEST_IDENTITY_MOVED_FAIL_CLOSED:"
            f"expected={EXPECTED_TEST_BLOB}:observed={base.EXPECTED_TEST_BLOB}"
        )

    base.EXPECTED_SOURCE_BLOB = POST_PROVENANCE_FUSION_SOURCE_BLOB
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
