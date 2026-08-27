#!/usr/bin/env python3
"""Regression: compatibility generation mirrors never become canonical generation authority."""
from __future__ import annotations

import json
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

poison = [row for row in specs if row["family"] == "compositional_generation_authority_poison"]
assert len(poison) == 40
assert len({row["id"] for row in poison}) == 40

for row in poison:
    canonical = int(row["canonical_generation"])
    legacy = int(row["legacy_mirror_generation"])
    assert legacy > canonical
    assert f"entity_state.generation={canonical}" in row["prompt"]
    assert f"compatibility mirror reports generation={legacy}" in row["prompt"]
    assert "do not max/merge/promote the mirror" in row["prompt"]
    assert f'grf_observe(c,"R0","canonical_generation_{canonical}","MEASURED")' in row["must_contain"]
    assert 'grf_counter(c,"R3","legacy_generation_mirror_is_not_authority")' in row["must_contain"]
    assert 'authority_deny(c,"legacy_generation_mirror","canonical_generation_write")' in row["must_contain"]
    assert f'grf_observe(c,"R0","canonical_generation_{legacy}","MEASURED")' in row["must_not_contain"]
    assert "omega_commit_candidate(c,w)" in row["must_not_contain"]

print(json.dumps({
    "generation_authority_poison_cases": len(poison),
    "canonical_generation_preserved": True,
    "legacy_mirror_promotion_forbidden": True,
}, indent=2))
