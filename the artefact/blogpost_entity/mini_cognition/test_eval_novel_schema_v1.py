#!/usr/bin/env python3
"""Ordinary regression: novel-schema specs compose with canonical #802 exact-omega scorer."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
subprocess.run([sys.executable, str(HERE / "generate_eval_novel_schema_v1.py")], check=True, stdout=subprocess.DEVNULL)
subprocess.run([sys.executable, str(HERE / "validate_eval_novel_schema_v1.py"), str(HERE / "eval_novel_schema_v1.jsonl")], check=True, stdout=subprocess.DEVNULL)

sys.path.insert(0, str(HERE))
from eval_outputs_v1 import exact_omega_ok  # noqa: E402


def q(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def exact_output(expected):
    out = 'module clay.cog.turn\nfn think(i:Map)->Map {\n  let c = cog_new()\n  let w = omega_new(c,"w0")\n'
    out += f'  omega_bind(w,"operation",{q(expected["operation"])})\n'
    for arg in expected["args"]:
        out += f'  omega_arg(w,{q(arg["name"])},{q(arg["value"])},{q(arg["type"])})\n'
    out += f'  omega_schema(w,{q(expected["schema"])})\n'
    out += f'  omega_authority(w,{expected["authority_expr"]})\n'
    out += f'  omega_generation(w,{expected["generation_expr"]})\n'
    for gate in expected["validators"]:
        out += f'  omega_validate(w,{q(gate)})\n'
    out += '  omega_commit_candidate(c,w)\n  return c\n}'
    return out


rows = [json.loads(line) for line in (HERE / "eval_novel_schema_v1.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
valid = [row for row in rows if row["family"] == "novel_schema_valid"]
assert len(valid) == 80

for row in valid:
    expected = row["expected_omega"]
    oracle = exact_output(expected)
    assert exact_omega_ok(oracle, expected), row["id"]

    # Ordinary regression of the already-established #802 bypass class: preserving
    # operation/gates while deleting a typed argument must never receive vector credit.
    first = expected["args"][0]
    arg_line = f'  omega_arg(w,{q(first["name"])},{q(first["value"])},{q(first["type"])})\n'
    missing_arg = oracle.replace(arg_line, "", 1)
    assert not exact_omega_ok(missing_arg, expected), row["id"]

print(json.dumps({
    "schema": "claycog-novel-schema-exact-omega-regression/v1",
    "novel_valid_cases": len(valid),
    "exact_oracles_pass": len(valid),
    "missing_arg_regressions_rejected": len(valid),
    "new_unusual_experiment": False,
}))
