#!/usr/bin/env python3
"""Build a scratch-only Avatar shadow with residual roll/eye translation.

The input source is never modified. The output path must be different from the input.
This is intentionally a candidate builder, not a production installer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "FRANK_AVATAR_ROLL_EYE_RESIDUAL_SHADOW/v1"
HELPER = r'''
// ⭐ CANDIDATE SHADOW ONLY — residual registration for measured roll-eye anchor.
// KOPF_ROLL_AUGEN_OFFSET is the final generator-measured displacement of the
// eye marker (610,207). rotate() about the neck anchor (768,600) already
// contributes a rigid displacement, so translate() must carry only the residual.
const KOPF_AUGEN_MARKER_X = 610, KOPF_AUGEN_MARKER_Y = 207;
const KOPF_NECK_ANCHOR_X = 768, KOPF_NECK_ANCHOR_Y = 600;
function kopfRollAugenResidual(rollDeg, gemessen){
  const a = rollDeg * Math.PI / 180;
  const vx = KOPF_AUGEN_MARKER_X - KOPF_NECK_ANCHOR_X;
  const vy = KOPF_AUGEN_MARKER_Y - KOPF_NECK_ANCHOR_Y;
  const rx = KOPF_NECK_ANCHOR_X + Math.cos(a)*vx - Math.sin(a)*vy - KOPF_AUGEN_MARKER_X;
  const ry = KOPF_NECK_ANCHOR_Y + Math.sin(a)*vx + Math.cos(a)*vy - KOPF_AUGEN_MARKER_Y;
  return {dx: gemessen.dx - rx, dy: gemessen.dy - ry};
}
'''.strip()

OLD_ASSIGN = '''  const zielOffset = KOPF_ROLL_AUGEN_OFFSET[String(kopfRollWert)] || {dx:0, dy:0};
  augenOffsetDx = zielOffset.dx;
  augenOffsetDy = zielOffset.dy;'''
NEW_ASSIGN = '''  const zielOffset = KOPF_ROLL_AUGEN_OFFSET[String(kopfRollWert)] || {dx:0, dy:0};
  const residualOffset = kopfRollAugenResidual(kopfRollWert, zielOffset);
  augenOffsetDx = residualOffset.dx;
  augenOffsetDy = residualOffset.dy;'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(reason: str, **extra) -> int:
    print(json.dumps({"schema": SCHEMA, "status": "EVIDENCE_INVALID", "reason": reason, **extra}, indent=2))
    return 3


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--expected-sha256", required=True)
    args = ap.parse_args()

    try:
        same = args.input.resolve() == args.output.resolve()
    except FileNotFoundError:
        same = args.input.absolute() == args.output.absolute()
    if same:
        return fail("output_must_not_equal_input")
    if not args.input.is_file():
        return fail("input_missing")

    before_sha = digest(args.input)
    if before_sha != args.expected_sha256:
        return fail("source_hash_mismatch", expected=args.expected_sha256, actual=before_sha)

    text = args.input.read_text(encoding="utf-8")
    if text.count(OLD_ASSIGN) != 1:
        return fail("assignment_subject_not_unique", count=text.count(OLD_ASSIGN))
    if "function kopfRollAugenResidual(" in text:
        return fail("source_already_contains_candidate_helper")

    table_start = text.find("const KOPF_ROLL_AUGEN_OFFSET")
    if table_start < 0:
        return fail("offset_table_missing")
    table_end = text.find("\n};", table_start)
    if table_end < 0:
        return fail("offset_table_end_missing")
    insert_at = table_end + len("\n};")

    candidate = text[:insert_at] + "\n" + HELPER + text[insert_at:]
    candidate = candidate.replace(OLD_ASSIGN, NEW_ASSIGN, 1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(candidate, encoding="utf-8")
    after_input_sha = digest(args.input)
    output_sha = digest(args.output)
    if after_input_sha != before_sha:
        return fail("input_mutated", before=before_sha, after=after_input_sha)

    report = {
        "schema": SCHEMA,
        "status": "PASS",
        "scope": "SCRATCH_SHADOW_ONLY_NO_PRODUCTION_CREDIT",
        "input": str(args.input),
        "input_sha256": before_sha,
        "output": str(args.output),
        "output_sha256": output_sha,
        "input_mutation": False,
        "rule": "translate = measured_generator_displacement - rigid_rotation_displacement",
        "production_credit": 0,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
