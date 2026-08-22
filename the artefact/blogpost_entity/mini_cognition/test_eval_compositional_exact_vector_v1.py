#!/usr/bin/env python3
"""Regression: compositional Hyperposition->R6->omega cases require exact typed vectors across prompt surfaces."""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
subprocess.run(
    [sys.executable, str(HERE / "generate_eval_compositional_ood_v1.py")],
    check=True,
    stdout=subprocess.DEVNULL,
)
specs = [
    json.loads(line)
    for line in (HERE / "eval_compositional_ood_v1.jsonl").read_text(encoding="utf-8").splitlines()
    if line.strip()
]

from eval_outputs_v1 import exact_omega_ok


def q(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def omega_output(expected, *, corrupt_first_arg=False):
    lines = [
        'module clay.cog.turn',
        'fn think(i:Map)->Map {',
        '  let c = cog_new()',
        '  let w = omega_new(c,"w0")',
        f'  omega_bind(w,"operation",{q(expected["operation"])})',
    ]
    for index, arg in enumerate(expected["args"]):
        value = arg["value"]
        if corrupt_first_arg and index == 0:
            value = "WRONG_VALUE"
        lines.append(f'  omega_arg(w,{q(arg["name"])},{q(value)},{q(arg["type"])})')
    lines.extend(
        [
            f'  omega_schema(w,{q(expected["schema"])})',
            f'  omega_authority(w,{expected["authority_expr"]})',
            f'  omega_generation(w,{expected["generation_expr"]})',
        ]
    )
    lines.extend(f'  omega_validate(w,{q(gate)})' for gate in expected["validators"])
    lines.extend(['  omega_commit_candidate(c,w)', '  return c', '}'])
    return "\n".join(lines) + "\n"


canonical = [row for row in specs if row["family"] == "compositional_hyper_to_omega"]
surface = [row for row in specs if row["family"] == "compositional_surface_invariance_omega"]
assert len(canonical) == 80
assert len(surface) == 80
assert all("expected_omega" in row for row in canonical + surface)
assert all(len(row["expected_omega"]["args"]) == 2 for row in canonical + surface)

sample = canonical[0]["expected_omega"]
assert exact_omega_ok(omega_output(sample), sample)
assert not exact_omega_ok(omega_output(sample, corrupt_first_arg=True), sample)

for row in canonical + surface:
    expected = row["expected_omega"]
    assert expected["validators"] == ["grammar", "types", "schema", "authority", "generation"]
    assert expected["authority_expr"] == 'cfg("architecture.effect_authority")'
    assert expected["generation_expr"] == 'cfg("state.generation")'
    assert expected["commit_count"] == 1

forms = Counter(row["surface_form"] for row in surface)
assert forms == {
    "evidence_first": 20,
    "contract_first": 20,
    "inputs_first": 20,
    "record_fields": 20,
}
assert all("typed_args=" not in row["prompt"] for row in surface)
assert Counter(row["expected_omega"]["operation"] for row in surface) == {
    "index.compact": 20,
    "blob.verify": 20,
    "route.reserve": 20,
    "ledger.annotate": 20,
}

print(
    json.dumps(
        {
            "canonical_exact_vector_cases": len(canonical),
            "surface_invariance_exact_vector_cases": len(surface),
            "surface_forms": dict(sorted(forms.items())),
            "exact_vector_bound": True,
            "wrong_typed_arg_rejected": True,
        },
        indent=2,
    )
)
