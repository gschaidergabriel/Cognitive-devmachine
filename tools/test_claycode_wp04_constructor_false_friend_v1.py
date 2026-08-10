#!/usr/bin/env python3
"""Adversarial WP04 probe: record-name resemblance must not invent call contracts.

The real G9 V18 cycle contains EffectIntent/1 and Delta/1 calls. Both names also name
records, but their record field arities are 5 and 6 respectively. This probe demonstrates
that those observed calls cannot be promoted as ordinary positional record constructors
from type-name resemblance. It does not define constructor semantics and it never admits
execution; it preserves both obligations fail-closed until an independent exact contract
exists.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import claycode_wp03_cycle_ir_v1 as cycle_ir
import claycode_wp03_typed_ir_v2_state_identity as typed_v2
import claycode_wp04_call_constraint_inference_v1 as constraints

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"


def build() -> tuple[dict, dict]:
    ir = typed_v2.compile_sources([G9, DIALECT], GRAMMAR)
    cycle_row = next(x for x in ir["opaque_unlowered_semantics"] if x.get("kind") == "cycle_decl")
    cycle = cycle_ir.lower_cycle_residual(cycle_row)
    return ir, constraints.collect_calls(cycle, ir)


def obligations(graph: dict) -> dict[tuple[str, int], dict]:
    return {(row["identity"]["target"], row["identity"]["arity"]): row for row in graph["obligations"]}


def declarations(ir: dict, kind: str, name: str) -> list[dict]:
    return [row for row in ir["declarations"] if row.get("kind") == kind and row.get("name") == name]


def main() -> int:
    ir, graph = build()
    by_call = obligations(graph)

    cases = {
        "EffectIntent": {"call_arity": 1, "record_field_count": 5},
        "Delta": {"call_arity": 1, "record_field_count": 6},
    }
    result_rows = []

    for name, expected in cases.items():
        call_key = (name, expected["call_arity"])
        assert call_key in by_call, call_key
        obligation = by_call[call_key]
        records = declarations(ir, "record", name)
        functions = declarations(ir, "function", name)

        assert len(records) == 1, (name, records)
        assert len(functions) == 0, (name, functions)
        field_count = len(records[0].get("fields", []))
        assert field_count == expected["record_field_count"], (name, field_count)
        assert field_count != expected["call_arity"]
        assert obligation["type_name_resemblance"] == name
        assert obligation["resolution_state"] == "UNRESOLVED_SIGNATURE"
        assert obligation["execution_admitted"] is False

        # Exact-function positive control: only an explicit target+arity declaration moves the
        # resolver, and even then execution remains blocked pending current runtime binding.
        exact_ir = copy.deepcopy(ir)
        exact_ir["declarations"].append({
            "kind": "function",
            "name": name,
            "params": [{"name": "arg0", "type": "ExternalNominal"}],
            "returns": "ExternalNominal",
            "effects": [],
            "authority": "NONE",
        })
        cycle_row = next(x for x in ir["opaque_unlowered_semantics"] if x.get("kind") == "cycle_decl")
        cycle = cycle_ir.lower_cycle_residual(cycle_row)
        exact_graph = constraints.collect_calls(cycle, exact_ir)
        exact_obligation = obligations(exact_graph)[call_key]
        assert exact_obligation["resolution_state"] == "DECLARED_SIGNATURE_EXACT_NONEXECUTABLE_UNTIL_BINDING"
        assert exact_obligation["execution_admitted"] is False

        result_rows.append({
            "target_arity": f"{name}/{expected['call_arity']}",
            "record_field_count": field_count,
            "record_positional_arity_matches": False,
            "exact_function_declarations": 0,
            "type_name_resemblance_only": True,
            "resolution_state": obligation["resolution_state"],
            "execution_admitted": False,
            "positive_control_exact_fn": "RESOLVES_NONEXECUTABLE_UNTIL_BINDING",
        })

    # Global authority guard remains unchanged by this diagnostic.
    assert graph["summary"]["execution_admitted_calls"] == 0
    assert graph["summary"]["effect_authority"] == "NONE"
    assert graph["summary"]["truth_authority"] == "NONE"

    report = {
        "status": "PASS",
        "scope": "WP04_CONSTRUCTOR_FALSE_FRIEND_V1",
        "source_constraint_graph_sha256": graph["constraint_graph_sha256"],
        "cases": result_rows,
        "finding": "RECORD_NAME_RESEMBLANCE_PLUS_POSITIONAL_ARITY_MISMATCH_CANNOT_JUSTIFY_CALL_CONTRACT",
        "signature_invention": "FORBIDDEN",
        "execution_promotion": "NONE",
        "effect_authority": "NONE",
        "truth_authority": "NONE",
        "wp03_status": "OPEN",
        "wp04_status": "OPEN",
        "next": "SEARCH_INDEPENDENT_EXACT_SIGNATURE_AND_CURRENT_RUNTIME_BINDING; DO_NOT PROMOTE RECORD RESEMBLANCE",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
