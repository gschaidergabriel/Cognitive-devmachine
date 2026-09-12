#!/usr/bin/env python3
"""Fail-closed successor promoter bound to the accepted quiesced matched-eye gate.

This wrapper deliberately preserves the already-reviewed atomic install/rollback
implementation in promote_semantic_shadow.py and changes only the evidence
contract.  Every textual anchor is cardinality-checked before execution, so a
future drift of the base promoter fails closed rather than silently changing
promotion semantics.

Required matched evidence:
  GO_AVATAR_EYE_MATCHED_QUIESCED_AB/v3
  exact canonical shadow/live/open-eye hashes (enforced by base promoter)
  all original visual checks true (enforced by base promoter)
  futureSchedulersBlocked == true
  at least one rAF and one timer cancellation attempt

Successful installation remains pending an independent post-live browser gate.
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "promote_semantic_shadow.py"
src = BASE.read_text(encoding="utf-8")

old_schema = "GO_AVATAR_EYE_MATCHED_FROZEN_AB/v1"
new_schema = "GO_AVATAR_EYE_MATCHED_QUIESCED_AB/v3"
# Exactly two references are expected in the base promoter: docstring + gate.
if src.count(old_schema) != 2:
    raise SystemExit(f"BASE_PROMOTER_SCHEMA_ANCHOR_DRIFT={src.count(old_schema)}")
src = src.replace(old_schema, new_schema)

anchor = '''    require_all_checks(matched, "GO_AVATAR_EYE_MATCHED_QUIESCED_AB/v3", "matched_ab")\n\n    before_sha = sha256_file(live)'''
if src.count(anchor) != 1:
    raise SystemExit(f"BASE_PROMOTER_MATCHED_GATE_ANCHOR_DRIFT={src.count(anchor)}")
replacement = '''    require_all_checks(matched, "GO_AVATAR_EYE_MATCHED_QUIESCED_AB/v3", "matched_ab")
    quiesce = matched.get("quiesce")
    if not isinstance(quiesce, dict):
        raise RuntimeError("matched_ab: missing quiesce evidence")
    if quiesce.get("futureSchedulersBlocked") is not True:
        raise RuntimeError("matched_ab: future scheduler block not proven")
    for key in ("rafCancelAttempts", "timerCancelAttempts"):
        value = quiesce.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise RuntimeError(f"matched_ab: invalid {key}={value!r}")

    before_sha = sha256_file(live)'''
src = src.replace(anchor, replacement)

# Make the durable promotion manifest self-describing.  Both creation and
# rollback validation are upgraded together by this exact cardinality check.
old_promotion_schema = "GO_AVATAR_EYE_LIVE_PROMOTION/v1"
if src.count(old_promotion_schema) != 2:
    raise SystemExit(f"BASE_PROMOTER_PROMOTION_SCHEMA_ANCHOR_DRIFT={src.count(old_promotion_schema)}")
src = src.replace(old_promotion_schema, "GO_AVATAR_EYE_LIVE_PROMOTION/v2")

old_copy = 'shutil.copy2(matched_report_path, evidence / "prelive.matched_ab.json")'
if src.count(old_copy) != 1:
    raise SystemExit(f"BASE_PROMOTER_COPY_ANCHOR_DRIFT={src.count(old_copy)}")
src = src.replace(
    old_copy,
    'shutil.copy2(matched_report_path, evidence / "prelive.matched_quiesced.json")',
)

ns = {"__name__": "__main__", "__file__": str(BASE), "__package__": None}
exec(compile(src, str(BASE) + "#quiesced-promoter-v2", "exec"), ns, ns)
