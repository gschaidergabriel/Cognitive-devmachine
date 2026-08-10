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
import claycode_wp04_explicit_contract_anchor_v1 as anchors

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"
CANDIDATE = ROOT / "research_entity/claycode/g9/CLAYCODE_FRANK_REWARD_CALLABLE_V1_CANDIDATE.clay"
TARGET = ("frank_reward.update", 1)


def lower_graph(ir: dict) -> dict:
    cycles = [x for x in ir["opaque_unlowered_semantics"] if x.get("kind") == "cycle_decl"]
    assert len(cycles) == 1, len(cycles)
    cycle = cycle_ir.lower_cycle_residual(cycles[0])
    return constraints.collect_calls(cycle, ir)


def obligations(graph: dict) -> dict[tuple[str, int], dict]:
    return {(x["identity"]["target"], x["identity"]["arity"]): x for x in graph["obligations"]}


def main() -> int:
    base_ir = typed_v2.compile_sources([G9, DIALECT], GRAMMAR)
    base_graph = lower_graph(base_ir)
    assert base_graph["summary"]["exact_declared_matches"] == 0
    assert base_graph["summary"]["unresolved_signatures"] == 26
    assert base_graph["summary"]["effect_boundary_missing_signatures"] == 1
    assert obligations(base_graph)[TARGET]["resolution_state"] == "UNRESOLVED_SIGNATURE"

    candidate_ir = typed_v2.compile_sources([G9, DIALECT, CANDIDATE], GRAMMAR)
    candidate_graph = lower_graph(candidate_ir)
    summary = candidate_graph["summary"]
    assert summary["call_site_occurrences"] == 27
    assert summary["unique_target_arities"] == 27
    assert summary["exact_declared_matches"] == 1, summary
    assert summary["unresolved_signatures"] == 25, summary
    assert summary["effect_boundary_missing_signatures"] == 1, summary
    assert summary["execution_admitted_calls"] == 0
    assert summary["effect_authority"] == summary["truth_authority"] == "NONE"
    assert obligations(candidate_graph)[TARGET]["resolution_state"] == "DECLARED_SIGNATURE_EXACT_NONEXECUTABLE_UNTIL_BINDING"
    assert obligations(candidate_graph)[("Needle.execute", 1)]["resolution_state"] == "EFFECT_BOUNDARY_SIGNATURE_MISSING"

    signatures = anchors.exact_signature_map(candidate_ir)
    assert TARGET in signatures
    sig = signatures[TARGET]
    assert sig["params"] == [{"name": "evidence", "type": "RewardOutcomeEvidence"}], sig
    assert sig["returns"] == "RewardPlasticityReceipt", sig

    metadata = anchors.explicit_call_metadata(CANDIDATE, GRAMMAR)
    assert metadata[TARGET] == {
        "effect_class": "DERIVED_STATE",
        "binding_authority": "NONE",
        "execution_admitted": "false",
        "truth_authority": "NONE",
    }, metadata[TARGET]

    source_ref = "research_entity/claycode/g9/CLAYCODE_FRANK_REWARD_CALLABLE_V1_CANDIDATE.clay"
    report = anchors.build_anchor_report(candidate_graph, candidate_ir, metadata, candidate_source_ref=source_ref)
    rsum = report["summary"]
    assert rsum["explicit_exact_contracts"] == 1, rsum
    assert rsum["concrete_anchor_nodes"] == 2, rsum
    assert 1 <= rsum["anchored_components"] <= 2, rsum
    assert rsum["conflicting_components"] == 0, rsum
    assert rsum["execution_admitted_calls"] == 0
    assert rsum["effect_authority"] == rsum["truth_authority"] == "NONE"
    contract = report["contracts"][0]
    assert contract["target"] == TARGET[0] and contract["arity"] == TARGET[1]
    assert contract["params"] == [{"name": "evidence", "type": "RewardOutcomeEvidence"}]
    assert contract["returns"] == "RewardPlasticityReceipt"
    assert contract["effect_class"] == "DERIVED_STATE"
    assert contract["binding_authority"] == "NONE"
    assert contract["execution_admitted"] is False

    # Deterministic replay under identical current bytes.
    candidate_ir_2 = typed_v2.compile_sources([G9, DIALECT, CANDIDATE], GRAMMAR)
    candidate_graph_2 = lower_graph(candidate_ir_2)
    metadata_2 = anchors.explicit_call_metadata(CANDIDATE, GRAMMAR)
    report_2 = anchors.build_anchor_report(candidate_graph_2, candidate_ir_2, metadata_2, candidate_source_ref=source_ref)
    assert candidate_ir_2["typed_ir_sha256"] == candidate_ir["typed_ir_sha256"]
    assert candidate_graph_2["constraint_graph_sha256"] == candidate_graph["constraint_graph_sha256"]
    assert report_2["anchor_report_sha256"] == report["anchor_report_sha256"]

    # Fail closed if a candidate tries to replace a concrete type with a dynamic escape.
    bad_ir = copy.deepcopy(candidate_ir)
    target_decl = next(x for x in bad_ir["declarations"] if x.get("kind") == "interface" and x.get("name") == "frank_reward")
    target_decl["methods"][0]["returns"] = "Any"
    try:
        anchors.build_anchor_report(candidate_graph, bad_ir, metadata, candidate_source_ref=source_ref)
    except anchors.ExplicitContractError:
        dynamic_escape = "REJECTED_FAIL_CLOSED"
    else:
        raise AssertionError("Any return escape was not rejected")

    # Fail closed if semantic metadata attempts to admit execution without a runtime binding.
    bad_meta = copy.deepcopy(metadata)
    bad_meta[TARGET]["execution_admitted"] = "true"
    try:
        anchors.build_anchor_report(candidate_graph, candidate_ir, bad_meta, candidate_source_ref=source_ref)
    except anchors.ExplicitContractError:
        execution_escape = "REJECTED_FAIL_CLOSED"
    else:
        raise AssertionError("execution admission without binding was not rejected")

    output = {
        "status": "PASS",
        "scope": "WP04_EXPLICIT_FRANK_REWARD_CALLABLE_ANCHOR_V1",
        "selected_grammar": "BASE_D_V18_REWARD_RELATIONS",
        "new_grammar_required": False,
        "target": "frank_reward.update/1",
        "baseline_exact_declared_matches": 0,
        "candidate_exact_declared_matches": summary["exact_declared_matches"],
        "candidate_unresolved_signatures": summary["unresolved_signatures"],
        "effect_boundary_missing_signatures": summary["effect_boundary_missing_signatures"],
        "contract_params": contract["params"],
        "contract_returns": contract["returns"],
        "contract_effect_class": contract["effect_class"],
        "contract_semantic_hash": contract["contract_semantic_hash"],
        "candidate_typed_ir_sha256": candidate_ir["typed_ir_sha256"],
        "candidate_constraint_graph_sha256": candidate_graph["constraint_graph_sha256"],
        "anchor_report_sha256": report["anchor_report_sha256"],
        "concrete_anchor_nodes": rsum["concrete_anchor_nodes"],
        "anchored_components": rsum["anchored_components"],
        "unanchored_components": rsum["unanchored_components"],
        "conflicting_components": 0,
        "determinism": "PASS",
        "dynamic_escape": dynamic_escape,
        "execution_without_binding": execution_escape,
        "execution_admitted_calls": 0,
        "effect_authority": "NONE",
        "truth_authority": "NONE",
        "promotion": "NONE",
        "wp03_status": "OPEN",
        "wp04_status": "OPEN",
        "next": "CURRENT_TARGET_VPS_REPLAY_THEN_RUNTIME_COMPONENT_BINDING_FOR_THIS_EXACT_CONTRACT_ONLY",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
