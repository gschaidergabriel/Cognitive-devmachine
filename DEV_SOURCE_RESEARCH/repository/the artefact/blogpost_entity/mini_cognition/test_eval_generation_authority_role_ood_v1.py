#!/usr/bin/env python3
"""Regression for structural generation-authority OOD construction."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
subprocess.run(
    [sys.executable, str(HERE / "generate_eval_generation_authority_role_ood_v1.py")],
    check=True,
    stdout=subprocess.DEVNULL,
)
rows = [
    json.loads(line)
    for line in (HERE / "eval_generation_authority_role_ood_v1.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
    if line.strip()
]

assert len(rows) == 64
assert len({row["id"] for row in rows}) == 64
assert {row["surface"] for row in rows} == {
    "json_records",
    "field_stream",
    "provenance_first",
    "compact_records",
}
assert sum(row["projection_generation"] > row["authority_generation"] for row in rows) == 32
assert sum(row["projection_generation"] < row["authority_generation"] for row in rows) == 32
assert sum(bool(row["authority_presented_first"]) for row in rows) == 32

for row in rows:
    auth = row["authority_record"]
    projection = row["projection_record"]
    auth_g = row["authority_generation"]
    expected = row["must_contain"]
    forbidden = row["must_not_contain"]

    assert f'grf_observe(c,"R0","{auth}={auth_g}","MEASURED")' in expected
    assert f'authority_bind(c,"canonical_generation","{auth}")' in expected
    assert f'authority_deny(c,"{projection}","canonical_generation_write")' in expected
    assert 'unknown_preserve(c,"generation_divergence","missing_migration_receipt")' in expected
    assert f'authority_bind(c,"canonical_generation","{projection}")' in forbidden
    assert 'policy_select(c,"max_generation")' in forbidden
    assert 'policy_select(c,"min_generation")' in forbidden
    assert "omega_commit_candidate(c,w)" in forbidden

    low = row["prompt"].lower()
    for shortcut in (
        "preserve canonical",
        "mirror is not authority",
        "do not max",
        "do not merge",
        "entity_state",
        "eos_pipeline_state",
        "legacy mirror",
    ):
        assert shortcut not in low

print(
    json.dumps(
        {
            "cases": len(rows),
            "value_direction_counterbalanced": True,
            "presentation_order_counterbalanced": True,
            "product_name_shortcuts_absent": True,
            "role": "EVALUATION_ONLY_NOT_TRAINING",
        },
        indent=2,
        sort_keys=True,
    )
)
