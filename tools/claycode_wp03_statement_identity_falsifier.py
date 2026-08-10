#!/usr/bin/env python3
"""Adversarial CC-WP-03 falsifier for semantic-statement identity preservation.

The V18 frontend distinguishes semantic rule/reward mutations. TypedIR must not collapse
those different frontend programs to one semantic identity merely because they contain no
typed declarations. This test is deliberately diagnostic: reproducing a collision is a
negative result and blocks WP03 promotion, but does not itself prescribe the repair.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import claycode_base_frontend as front
import claycode_base_typed_ir as typed

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = front.DEFAULT_GRAMMAR

CASES = {
    "greater_vs_less": ("rule x>0\n", "rule x<0\n"),
    "preserves_vs_required_before": ("rule a preserves b\n", "rule a required_before b\n"),
    "preserves_vs_plain_relation": ("rule a preserves b\n", "rule a requires b\n"),
    "postfix_reward_vs_plain": (
        "rule brake cannot_be_silently_averaged_away\n",
        "rule brake\n",
    ),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(source: str, label: str) -> tuple[dict, dict]:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    artifact = front.compile_frontend(source, grammar, strict=True)
    ir = typed.build_typed_ir([typed.SourceUnit(Path(f"{label}.clay"), artifact)])
    return artifact, ir


def main() -> int:
    rows = []
    for name, (left, right) in CASES.items():
        la, li = build(left, name + "-left")
        ra, ri = build(right, name + "-right")
        frontend_distinct = la["semantic_hash"] != ra["semantic_hash"]
        typed_distinct = li["typed_ir_sha256"] != ri["typed_ir_sha256"]
        rows.append({
            "case": name,
            "left_source_sha256": la["source_sha256"],
            "right_source_sha256": ra["source_sha256"],
            "left_frontend_semantic_hash": la["semantic_hash"],
            "right_frontend_semantic_hash": ra["semantic_hash"],
            "frontend_distinct": frontend_distinct,
            "left_typed_ir_sha256": li["typed_ir_sha256"],
            "right_typed_ir_sha256": ri["typed_ir_sha256"],
            "typed_ir_distinct": typed_distinct,
            "identity_preserved": frontend_distinct and typed_distinct,
            "collision_reproduced": frontend_distinct and not typed_distinct,
        })

    collisions = [r["case"] for r in rows if r["collision_reproduced"]]
    unexpected_frontend = [r["case"] for r in rows if not r["frontend_distinct"]]
    out = {
        "schema_version": "1.0",
        "experiment": "CC-WP03 semantic statement identity preservation falsifier",
        "grammar_path": str(GRAMMAR.relative_to(ROOT)),
        "grammar_blob_sha256": sha256(GRAMMAR.read_bytes()),
        "typed_ir_source_blob_sha256": sha256((ROOT / "tools/claycode_base_typed_ir.py").read_bytes()),
        "case_count": len(rows),
        "rows": rows,
        "collision_count": len(collisions),
        "collisions": collisions,
        "frontend_failures": unexpected_frontend,
        "wp03_identity_gate_pass": not collisions and not unexpected_frontend,
        "classification": (
            "TYPED_IR_SEMANTIC_IDENTITY_COLLISION_REPRODUCED"
            if collisions and not unexpected_frontend
            else "NO_COLLISION_ON_SELECTED_FIXTURES"
            if not collisions and not unexpected_frontend
            else "FRONTEND_FIXTURE_INVALID"
        ),
        "promotion": "NONE",
        "authority": "NONE",
        "scope_guard": "Negative collision evidence blocks WP03 identity promotion for the tested TypedIR bytes. It does not by itself define the repair, change Frank Harness authority, or authorize training/effects.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    # Diagnostic succeeds as an executable falsifier when the frontend fixtures are valid;
    # collision/non-collision is carried in the receipt rather than hidden as CI plumbing.
    return 2 if unexpected_frontend else 0


if __name__ == "__main__":
    raise SystemExit(main())
