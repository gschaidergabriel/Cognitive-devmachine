#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import claycode_wp04_call_constraint_inference_v1 as constraints


def tok(value: str, token: str = "NAME") -> dict:
    return {"token": token, "value": value}


def qid(name: str) -> dict:
    parts = name.split(".")
    children: list[dict] = []
    for i, part in enumerate(parts):
        if i:
            children.append(tok(".", "DOT"))
        children.append(tok(part))
    return {"kind": "qid", "children": children}


def call(name: str) -> dict:
    return {"kind": "call", "children": [qid(name)]}


def assign(op_id: str, target: str, call_name: str) -> dict:
    return {
        "kind": "ASSIGN",
        "op_semantic_id": op_id,
        "target": target,
        "rhs_ast": call(call_name),
    }


def expr(op_id: str, call_name: str) -> dict:
    return {
        "kind": "EXPR",
        "op_semantic_id": op_id,
        "expr_ast": call(call_name),
    }


def main() -> int:
    cycle = {
        "cycle_semantic_id": "synthetic:nested-path-v2",
        "region": {
            "ops": [
                assign("top:0", "a", "top_zero"),
                {
                    "kind": "IF",
                    "op_semantic_id": "top:1-if",
                    "condition_ast": call("condition_call"),
                    "then_region": {
                        "ops": [
                            assign("nested:0", "b", "nested_zero"),
                            {
                                "kind": "IF",
                                "op_semantic_id": "nested:1-if",
                                "condition_ast": qid("flag"),
                                "then_region": {
                                    "ops": [expr("deep:0", "deep_zero")]
                                },
                            },
                        ]
                    },
                },
                expr("top:2", "top_two"),
            ]
        },
    }
    typed_ir = {"typed_ir_sha256": "synthetic", "declarations": [], "types": []}
    graph = constraints.collect_calls(cycle, typed_ir)
    paths = {row["target"]: row["path"] for row in graph["occurrences"]}

    expected = {
        "top_zero": [0],
        "condition_call": [1, constraints.CONDITION_PATH_SENTINEL],
        "nested_zero": [1, constraints.THEN_REGION_PATH_SENTINEL, 0],
        "deep_zero": [1, constraints.THEN_REGION_PATH_SENTINEL, 1, constraints.THEN_REGION_PATH_SENTINEL, 0],
        "top_two": [2],
    }
    assert paths == expected, (paths, expected)
    assert len({tuple(path) for path in paths.values()}) == len(paths)
    assert graph["summary"]["call_site_occurrences"] == 5
    assert graph["summary"]["execution_admitted_calls"] == 0
    assert graph["summary"]["effect_authority"] == "NONE"
    assert graph["invariants"]["nested_region_path_collision"] == "FORBIDDEN"

    # Fail-closed structural control: malformed IF cannot silently discard ancestry.
    malformed = {
        "cycle_semantic_id": "synthetic:missing-then",
        "region": {"ops": [{"kind": "IF", "op_semantic_id": "bad", "condition_ast": qid("flag")}]},
    }
    try:
        constraints.collect_calls(malformed, typed_ir)
    except constraints.CallConstraintError as exc:
        assert "then_region" in str(exc)
    else:
        raise AssertionError("missing then_region must fail closed")

    print(json.dumps({
        "status": "PASS",
        "scope": "WP04_NESTED_CALL_STRUCTURAL_PATH_V2",
        "paths": paths,
        "unique_structural_paths": len(paths),
        "malformed_if": "REJECTED_FAIL_CLOSED",
        "execution_admitted_calls": 0,
        "effect_authority": "NONE",
        "promotion": "NONE",
        "wp03_status": "OPEN",
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
