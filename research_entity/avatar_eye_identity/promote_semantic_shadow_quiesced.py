#!/usr/bin/env python3
"""Fail-closed successor promoter for the accepted eye-identity evidence pair.

This wrapper deliberately preserves the already-reviewed atomic install/rollback
implementation in promote_semantic_shadow.py and changes only the evidence
contract. Every textual anchor is cardinality-checked before execution, so a
future drift of the base promoter fails closed rather than silently changing
promotion semantics.

Required runtime evidence:
  GO_AVATAR_EYE_SHADOW_RUNTIME/v3
  validator_revision == V3_IN_PAGE_AUTONOMOUS_SAMPLER
  zero state round trips during the high-frequency measurement window
  one final compact payload round trip

Required matched evidence:
  GO_AVATAR_EYE_MATCHED_QUIESCED_AB/v3
  exact canonical shadow/live/open-eye hashes (enforced by base promoter)
  all visual checks true (enforced by base promoter)
  futureSchedulersBlocked == true
  at least one rAF and one timer cancellation attempt

Successful installation remains pending an independent post-live browser gate.
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "promote_semantic_shadow.py"
src = BASE.read_text(encoding="utf-8")

# Upgrade the runtime evidence contract. The old schema occurs in the base
# promoter docstring and in the executable gate exactly once each.
old_runtime_schema = "GO_AVATAR_EYE_SHADOW_RUNTIME/v2"
new_runtime_schema = "GO_AVATAR_EYE_SHADOW_RUNTIME/v3"
if src.count(old_runtime_schema) != 2:
    raise SystemExit(f"BASE_PROMOTER_RUNTIME_SCHEMA_ANCHOR_DRIFT={src.count(old_runtime_schema)}")
src = src.replace(old_runtime_schema, new_runtime_schema)

# Upgrade the matched A/B evidence contract.
old_matched_schema = "GO_AVATAR_EYE_MATCHED_FROZEN_AB/v1"
new_matched_schema = "GO_AVATAR_EYE_MATCHED_QUIESCED_AB/v3"
if src.count(old_matched_schema) != 2:
    raise SystemExit(f"BASE_PROMOTER_MATCHED_SCHEMA_ANCHOR_DRIFT={src.count(old_matched_schema)}")
src = src.replace(old_matched_schema, new_matched_schema)

runtime_anchor = '''    require_all_checks(runtime, "GO_AVATAR_EYE_SHADOW_RUNTIME/v3", "runtime")\n    require_all_checks(matched, "GO_AVATAR_EYE_MATCHED_QUIESCED_AB/v3", "matched_ab")'''
if src.count(runtime_anchor) != 1:
    raise SystemExit(f"BASE_PROMOTER_RUNTIME_GATE_ANCHOR_DRIFT={src.count(runtime_anchor)}")
runtime_replacement = '''    require_all_checks(runtime, "GO_AVATAR_EYE_SHADOW_RUNTIME/v3", "runtime")
    if runtime.get("validator_revision") != "V3_IN_PAGE_AUTONOMOUS_SAMPLER":
        raise RuntimeError("runtime: autonomous in-page sampler revision not proven")
    transport = runtime.get("transport")
    if not isinstance(transport, dict):
        raise RuntimeError("runtime: missing transport evidence")
    if transport.get("state_roundtrips_during_measurement") != 0:
        raise RuntimeError("runtime: measurement window was not transport-decoupled")
    if transport.get("final_payload_roundtrips") != 1:
        raise RuntimeError("runtime: compact final payload retrieval not proven")
    require_all_checks(matched, "GO_AVATAR_EYE_MATCHED_QUIESCED_AB/v3", "matched_ab")'''
src = src.replace(runtime_anchor, runtime_replacement)

matched_anchor = '''    require_all_checks(matched, "GO_AVATAR_EYE_MATCHED_QUIESCED_AB/v3", "matched_ab")\n\n    before_sha = sha256_file(live)'''
if src.count(matched_anchor) != 1:
    raise SystemExit(f"BASE_PROMOTER_MATCHED_GATE_ANCHOR_DRIFT={src.count(matched_anchor)}")
matched_replacement = '''    require_all_checks(matched, "GO_AVATAR_EYE_MATCHED_QUIESCED_AB/v3", "matched_ab")
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
src = src.replace(matched_anchor, matched_replacement)

# Make the durable promotion manifest self-describing. Both creation and
# rollback validation are upgraded together by this exact cardinality check.
old_promotion_schema = "GO_AVATAR_EYE_LIVE_PROMOTION/v1"
if src.count(old_promotion_schema) != 2:
    raise SystemExit(f"BASE_PROMOTER_PROMOTION_SCHEMA_ANCHOR_DRIFT={src.count(old_promotion_schema)}")
src = src.replace(old_promotion_schema, "GO_AVATAR_EYE_LIVE_PROMOTION/v3")

old_runtime_copy = 'shutil.copy2(runtime_report_path, evidence / "prelive.runtime.json")'
if src.count(old_runtime_copy) != 1:
    raise SystemExit(f"BASE_PROMOTER_RUNTIME_COPY_ANCHOR_DRIFT={src.count(old_runtime_copy)}")
src = src.replace(
    old_runtime_copy,
    'shutil.copy2(runtime_report_path, evidence / "prelive.runtime_v3.json")',
)
old_matched_copy = 'shutil.copy2(matched_report_path, evidence / "prelive.matched_ab.json")'
if src.count(old_matched_copy) != 1:
    raise SystemExit(f"BASE_PROMOTER_MATCHED_COPY_ANCHOR_DRIFT={src.count(old_matched_copy)}")
src = src.replace(
    old_matched_copy,
    'shutil.copy2(matched_report_path, evidence / "prelive.matched_quiesced.json")',
)

ns = {"__name__": "__main__", "__file__": str(BASE), "__package__": None}
exec(compile(src, str(BASE) + "#quiesced-promoter-v3", "exec"), ns, ns)
