#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import claycode_wp03_cycle_ir_v1 as cycle_ir
import claycode_wp03_typed_ir_v2_state_identity as typed_v2
import claycode_wp04_call_anchor_planner_v1 as planner
import claycode_wp04_call_constraint_inference_v1 as constraints

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"


def build_graph() -> dict:
    ir = typed_v2.compile_sources([G9, DIALECT], GRAMMAR)
    cycle_row = next(x for x in ir["opaque_unlowered_semantics"] if x.get("kind") == "cycle_decl")
    cycle = cycle_ir.lower_cycle_residual(cycle_row)
    return constraints.collect_calls(cycle, ir)


def main() -> int:
    graph = build_graph()
    plan = planner.build_anchor_plan(graph)
    s = plan["summary"]
    assert graph["summary"]["type_equality_components"] == 37
    assert s["type_equality_components"] == 37
    assert 0 < s["call_associated_components"] <= 37
    assert 0 < s["greedy_signature_contracts_for_call_component_cover"] <= 27
    assert s["max_components_covered_by_one_signature"] >= 1
    assert s["max_symbolic_nodes_covered_by_one_signature"] >= 2
    assert s["execution_admitted_calls"] == 0
    assert s["effect_authority"] == s["truth_authority"] == "NONE"

    ranked = plan["ranked_signature_anchor_leverage"]
    assert len(ranked) == 27
    assert len({x["target_arity_key"] for x in ranked}) == 27
    assert all(x["execution_admitted"] is False for x in ranked)
    assert all(x["effect_authority"] == x["truth_authority"] == "NONE" for x in ranked)
    assert all("concrete_type" not in json.dumps(x, sort_keys=True) for x in ranked)

    needle = next(x for x in ranked if x["target_arity_key"] == "Needle.execute/1")
    assert needle["effect_boundary"] is True
    assert needle["resolution_state"] == "EFFECT_BOUNDARY_SIGNATURE_MISSING"

    selected = plan["greedy_signature_set_cover"]
    covered = set()
    for row in selected:
        gain = set(row["newly_covered_component_ids"])
        assert gain and not gain <= covered
        covered |= gain
    assert covered == set(plan["call_associated_component_ids"])

    # Determinism.
    plan2 = planner.build_anchor_plan(build_graph())
    assert plan2["anchor_plan_sha256"] == plan["anchor_plan_sha256"]
    assert planner.stable_json(plan2) == planner.stable_json(plan)

    top = [
        {
            "target_arity_key": row["target_arity_key"],
            "covered_component_count": row["covered_component_count"],
            "covered_symbolic_node_count": row["covered_symbolic_node_count"],
            "effect_boundary": row["effect_boundary"],
        }
        for row in ranked[:10]
    ]
    report = {
        "status": "PASS",
        "scope": "WP04_G9_CALL_ANCHOR_LEVERAGE_V1",
        "source_constraint_graph_sha256": plan["source_constraint_graph_sha256"],
        "anchor_plan_sha256": plan["anchor_plan_sha256"],
        **s,
        "top_anchor_leverage": top,
        "greedy_signature_set_cover": selected,
        "concrete_type_invention": "FORBIDDEN",
        "signature_promotion": "NONE",
        "execution_promotion": "NONE",
        "next": "DECLARE_ONLY_INDEPENDENTLY_JUSTIFIED_HIGH_LEVERAGE_SIGNATURES_THEN_REMEASURE",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
