#!/usr/bin/env python3
"""Regression for temporal R_next=F omega admission semantics."""
from __future__ import annotations

from eval_outputs_v1 import exact_omega_ok
from validate_sft_v1 import validate_code

EXPECTED = {
    "operation": "route.reserve",
    "args": [
        {"name": "route", "value": "west", "type": "Identifier"},
        {"name": "ttl_sec", "value": 120, "type": "Int"},
    ],
    "schema": "tool.route.reserve/v6",
    "authority_expr": 'cfg("architecture.effect_authority")',
    "generation_expr": 'cfg("state.generation")',
    "validators": ["grammar", "types", "schema", "authority", "generation"],
    "commit_count": 1,
}

HEAD = '''module clay.cog.turn
fn think(i:Map)->Map {
  let c = cog_new()
  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))
  role_bind(c,cfg("application.role"))
  goal_bind(c,cfg("application.goal"))
  personality_bind(c,cfg("application.personality"))
  let w = omega_new(c,"w0")
  omega_bind(w,"operation","route.reserve")
  omega_arg(w,"route","west","Identifier")
  omega_arg(w,"ttl_sec",120,"Int")
  omega_schema(w,"tool.route.reserve/v6")
  omega_authority(w,cfg("architecture.effect_authority"))
  omega_generation(w,cfg("state.generation"))
'''
TAIL = '''  return c
}'''

GOOD = HEAD + '''  omega_validate(w,"grammar")
  omega_validate(w,"types")
  omega_validate(w,"schema")
  omega_validate(w,"authority")
  omega_validate(w,"generation")
  omega_commit_candidate(c,w)
''' + TAIL

COMMIT_BEFORE_GENERATION = HEAD + '''  omega_validate(w,"grammar")
  omega_validate(w,"types")
  omega_validate(w,"schema")
  omega_validate(w,"authority")
  omega_commit_candidate(c,w)
  omega_validate(w,"generation")
''' + TAIL

SWAPPED_GATES = HEAD + '''  omega_validate(w,"types")
  omega_validate(w,"grammar")
  omega_validate(w,"schema")
  omega_validate(w,"authority")
  omega_validate(w,"generation")
  omega_commit_candidate(c,w)
''' + TAIL


def test_canonical_order_is_admitted_by_training_and_eval() -> None:
    assert validate_code(GOOD) == []
    assert exact_omega_ok(GOOD, EXPECTED)


def test_commit_before_last_gate_is_rejected_by_training_and_eval() -> None:
    assert "omega_validation_before_commit" in validate_code(COMMIT_BEFORE_GENERATION)
    assert not exact_omega_ok(COMMIT_BEFORE_GENERATION, EXPECTED)


def test_gate_permutation_before_commit_remains_admitted() -> None:
    assert validate_code(SWAPPED_GATES) == []
    assert exact_omega_ok(SWAPPED_GATES, EXPECTED)
