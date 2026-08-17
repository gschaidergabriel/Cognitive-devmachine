#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import claycode_wp03_typed_ir_v2_state_identity as typed_v2
import claycode_wp03_cycle_ir_v1 as cycle_ir
import claycode_wp04_call_constraint_inference_v1 as constraints

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"


def build() -> tuple[dict, dict]:
    ir = typed_v2.compile_sources([G9, DIALECT], GRAMMAR)
    cycles = [x for x in ir["opaque_unlowered_semantics"] if x.get("kind") == "cycle_decl"]
    assert len(cycles) == 1
    cycle = cycle_ir.lower_cycle_residual(cycles[0])
    return ir, constraints.collect_calls(cycle, ir)


def obligation_map(graph: dict) -> dict[tuple[str, int], dict]:
    return {(x["identity"]["target"], x["identity"]["arity"]): x for x in graph["obligations"]}


def first_call(node: object) -> dict:
    if isinstance(node, dict):
        if node.get("kind") == "call":
            return node
        for child in node.get("children", []):
            try:
                return first_call(child)
            except LookupError:
                pass
    elif isinstance(node, list):
        for child in node:
            try:
                return first_call(child)
            except LookupError:
                pass
    raise LookupError("no call node")


def main() -> int:
    ir, graph = build()
    s = graph["summary"]
    assert s["call_site_occurrences"] == 27, s
    assert s["unique_target_arities"] == 27, s
    assert s["exact_declared_matches"] == 0, s
    assert s["unresolved_signatures"] == 26, s
    assert s["effect_boundary_missing_signatures"] == 1, s
    assert s["type_name_resemblance_only"] == 2, s
    assert s["type_equality_constraints"] > 20, s
    assert s["type_equality_components"] > 0, s
    assert s["execution_admitted_calls"] == 0
    assert s["effect_authority"] == s["truth_authority"] == "NONE"

    obligations = obligation_map(graph)
    expected_keys = {
        ("resolve_latest", 3), ("load_dialects", 1), ("task", 1), ("verify", 5),
        ("normalize", 1), ("observe_changes", 2), ("apply_incremental", 1),
        ("state.query", 1), ("task_relevant", 1), ("graph.project", 1),
        ("preserve_conflict_unknown", 1), ("state.open_pressures", 1), ("emerge", 1),
        ("gwt.select", 1), ("state.answer_capsule", 1), ("cognitive_choice", 1),
        ("EffectIntent", 1), ("Needle.execute", 1), ("verify", 1), ("causal_credit", 2),
        ("frank_reward.derive_typed_reward_outcome_evidence", 3), ("frank_reward.update", 1),
        ("frank_reward.control", 2), ("admit_slow_plasticity", 3), ("reenter", 1),
        ("Delta", 1), ("meta.analyze_explicit_turn", 0),
    }
    assert set(obligations) == expected_keys, sorted(set(obligations) ^ expected_keys)

    needle = obligations[("Needle.execute", 1)]
    assert needle["resolution_state"] == "EFFECT_BOUNDARY_SIGNATURE_MISSING"
    assert needle["effect_boundary"] is True
    assert needle["execution_admitted"] is False

    assert obligations[("EffectIntent", 1)]["type_name_resemblance"] == "EffectIntent"
    assert obligations[("Delta", 1)]["type_name_resemblance"] == "Delta"
    assert obligations[("EffectIntent", 1)]["resolution_state"] == "UNRESOLVED_SIGNATURE"
    assert obligations[("Delta", 1)]["resolution_state"] == "UNRESOLVED_SIGNATURE"

    # `verify/1` must not inherit Verifiable.verify/1 by suffix/basename similarity.
    assert obligations[("verify", 1)]["resolution_state"] == "UNRESOLVED_SIGNATURE"
    assert ("Verifiable.verify", 1) in constraints.declared_function_keys(ir)

    # Positive exact-match control: only an injected exact target+arity declaration can resolve.
    exact_ir = copy.deepcopy(ir)
    exact_ir["declarations"].append({"kind": "function", "name": "normalize", "params": [{"name": "x"}]})
    cycle_row = next(x for x in ir["opaque_unlowered_semantics"] if x.get("kind") == "cycle_decl")
    cycle = cycle_ir.lower_cycle_residual(cycle_row)
    exact_graph = constraints.collect_calls(cycle, exact_ir)
    exact_obligations = obligation_map(exact_graph)
    assert exact_obligations[("normalize", 1)]["resolution_state"] == "DECLARED_SIGNATURE_EXACT_NONEXECUTABLE_UNTIL_BINDING"
    assert exact_obligations[("normalize", 1)]["execution_admitted"] is False
    assert exact_graph["summary"]["exact_declared_matches"] == 1

    # Counter-control: same basename under another qualified target must not resolve normalize/1.
    fuzzy_ir = copy.deepcopy(ir)
    fuzzy_ir["declarations"].append({"kind": "function", "name": "Other.normalize", "params": [{"name": "x"}]})
    fuzzy_graph = constraints.collect_calls(cycle, fuzzy_ir)
    assert obligation_map(fuzzy_graph)[("normalize", 1)]["resolution_state"] == "UNRESOLVED_SIGNATURE"
    assert fuzzy_graph["summary"]["exact_declared_matches"] == 0

    # Determinism and semantic mutation discrimination.
    _, graph2 = build()
    assert graph2["constraint_graph_sha256"] == graph["constraint_graph_sha256"]
    mutated_cycle = copy.deepcopy(cycle)
    first_op = mutated_cycle["region"]["ops"][0]
    call = first_call(first_op["rhs_ast"])
    target_qid = next(x for x in call["children"] if isinstance(x, dict) and x.get("kind") == "qid")
    target_qid["children"][0]["value"] = "resolve_latest_mutant"
    mutated = constraints.collect_calls(mutated_cycle, ir)
    assert mutated["constraint_graph_sha256"] != graph["constraint_graph_sha256"]
    assert mutated["summary"]["execution_admitted_calls"] == 0
    assert mutated["summary"]["effect_authority"] == "NONE"

    report = {
        "status": "PASS",
        "scope": "WP04_G9_CALL_CONSTRAINT_INFERENCE_V1",
        "constraint_graph_sha256": graph["constraint_graph_sha256"],
        **s,
        "exact_target_arity_keys": [f"{t}/{a}" for t, a in sorted(expected_keys)],
        "type_name_resemblance_targets": ["Delta/1", "EffectIntent/1"],
        "verify_suffix_fuzzy_resolution": "REJECTED",
        "exact_declared_positive_control": "PASS_NONEXECUTABLE",
        "same_basename_counter_control": "PASS_FAIL_CLOSED",
        "determinism": "PASS",
        "semantic_mutation_discrimination": "PASS",
        "signature_invention": "FORBIDDEN",
        "promotion": "NONE",
        "wp03_status": "OPEN",
        "next": "EVIDENCE_BACKED_TYPE_ANCHORS_AND_EXACT_RUNTIME_BINDINGS_ONLY",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
