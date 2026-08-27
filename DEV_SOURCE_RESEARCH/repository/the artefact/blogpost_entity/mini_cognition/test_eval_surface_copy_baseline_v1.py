#!/usr/bin/env python3
"""Regression: literal canonical prompt-slot copying must not solve the surface-invariance OOD family."""
from __future__ import annotations

import json
import re
import subprocess
import sys
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

from eval_outputs_v1 import semantic_ok
from validate_sft_v1 import validate_code

CANONICAL = re.compile(
    r"^Keep (?P<chosen>\S+) and (?P<other>\S+) unresolved until receipt (?P<receipt>[^;]+); "
    r"receipt (?P=receipt) verifies (?P=chosen)\. Then encode runtime operation (?P<op>[^,]+), "
    r"schema (?P<schema>[^,]+), typed_args=(?P<args>\[.*\])\.$"
)


def q(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def literal_slot_copy(prompt):
    """Intentionally dumb baseline: parse only the old canonical surface, then copy slots."""
    m = CANONICAL.match(prompt)
    if not m:
        return None
    args = json.loads(m.group("args"))
    chosen, other, receipt = m.group("chosen"), m.group("other"), m.group("receipt")
    op, schema = m.group("op"), m.group("schema")
    lines = [
        "module clay.cog.turn",
        "fn think(i:Map)->Map {",
        "  let c = cog_new()",
        '  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))',
        '  role_bind(c,cfg("application.role"))',
        '  goal_bind(c,cfg("application.goal"))',
        '  personality_bind(c,cfg("application.personality"))',
        '  let hp = hyper_new(c,"copy_hp")',
        f'  hyper_alt(hp,{q(chosen)},"PLAUSIBLE")',
        f'  hyper_alt(hp,{q(other)},"PLAUSIBLE")',
        f'  grf_verify(c,"R6",{q(chosen)},{q(receipt)})',
        f'  collapse_exact(hp,{q(chosen)},{q(receipt)})',
        '  let w = omega_new(c,"w0")',
        f'  omega_bind(w,"operation",{q(op)})',
    ]
    for name, value, typ in args:
        lines.append(f'  omega_arg(w,{q(name)},{q(value)},{q(typ)})')
    lines.extend(
        [
            f'  omega_schema(w,{q(schema)})',
            '  omega_authority(w,cfg("architecture.effect_authority"))',
            '  omega_generation(w,cfg("state.generation"))',
            '  omega_validate(w,"grammar")',
            '  omega_validate(w,"types")',
            '  omega_validate(w,"schema")',
            '  omega_validate(w,"authority")',
            '  omega_validate(w,"generation")',
            '  omega_commit_candidate(c,w)',
            '  return c',
            '}',
        ]
    )
    return "\n".join(lines)


canonical = [row for row in specs if row["family"] == "compositional_hyper_to_omega"]
surface = [row for row in specs if row["family"] == "compositional_surface_invariance_omega"]
assert len(canonical) == 80 and len(surface) == 80

canonical_outputs = [literal_slot_copy(row["prompt"]) for row in canonical]
surface_outputs = [literal_slot_copy(row["prompt"]) for row in surface]
assert all(output is not None for output in canonical_outputs)
assert all(output is None for output in surface_outputs)

structural = sum(validate_code(output) == [] for output in canonical_outputs)
semantic = sum(
    validate_code(output) == [] and semantic_ok(output, row)
    for row, output in zip(canonical, canonical_outputs)
)
assert structural == 80
assert semantic == 80

print(
    json.dumps(
        {
            "baseline": "literal_old_surface_slot_copy_only",
            "canonical_cases": len(canonical),
            "canonical_parsed": 80,
            "canonical_structural_pass": structural,
            "canonical_semantic_pass": semantic,
            "surface_invariance_cases": len(surface),
            "surface_invariance_parsed": 0,
            "discriminator_preserved": True,
        },
        indent=2,
    )
)
