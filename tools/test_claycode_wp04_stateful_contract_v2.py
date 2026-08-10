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
import claycode_wp04_explicit_contract_anchor_v1 as anchor_v1
import claycode_wp04_stateful_contract_v2 as stateful_v2

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"
V1 = ROOT / "research_entity/claycode/g9/CLAYCODE_FRANK_REWARD_CALLABLE_V1_CANDIDATE.clay"
V2 = ROOT / "research_entity/claycode/g9/CLAYCODE_FRANK_REWARD_CALLABLE_V2_STATEFUL_CANDIDATE.clay"
TARGET = ("frank_reward.update", 1)


def lower_graph(ir: dict) -> dict:
    cycles = [x for x in ir["opaque_unlowered_semantics"] if x.get("kind") == "cycle_decl"]
    assert len(cycles) == 1, len(cycles)
    return constraints.collect_calls(cycle_ir.lower_cycle_residual(cycles[0]), ir)


def main() -> int:
    # V1 is an exact signature, but the reward-successor semantics prove the call is state-dependent.
    # It must therefore fail the V2 execution-readiness contract until receiver state is explicit.
    v1_ir = typed_v2.compile_sources([G9, DIALECT, V1], GRAMMAR)
    v1_graph = lower_graph(v1_ir)
    v1_call_meta = anchor_v1.explicit_call_metadata(V1, GRAMMAR)
    v1_state_meta = stateful_v2.state_metadata(V1, GRAMMAR)
    try:
        stateful_v2.build_stateful_report(
            v1_graph,
            v1_ir,
            v1_call_meta,
            v1_state_meta,
            candidate_source_ref=str(V1.relative_to(ROOT)),
            required_stateful_targets={TARGET},
        )
    except stateful_v2.StatefulContractError:
        v1_hidden_state = "REJECTED_FAIL_CLOSED"
    else:
        raise AssertionError("V1 param/return-only contract incorrectly passed stateful readiness")

    v2_ir = typed_v2.compile_sources([G9, DIALECT, V2], GRAMMAR)
    v2_graph = lower_graph(v2_ir)
    summary = v2_graph["summary"]
    assert summary["call_site_occurrences"] == 27, summary
    assert summary["unique_target_arities"] == 27, summary
    assert summary["exact_declared_matches"] == 1, summary
    assert summary["unresolved_signatures"] == 25, summary
    assert summary["effect_boundary_missing_signatures"] == 1, summary
    assert summary["execution_admitted_calls"] == 0, summary

    call_meta = anchor_v1.explicit_call_metadata(V2, GRAMMAR)
    state_meta = stateful_v2.state_metadata(V2, GRAMMAR)
    assert state_meta[TARGET] == {
        "receiver_state_type": "FrankRewardReceiverState",
        "state_access": "MUTATE_RECEIVER_STATE",
        "state_epoch_field": "state_epoch",
    }, state_meta[TARGET]

    report = stateful_v2.build_stateful_report(
        v2_graph,
        v2_ir,
        call_meta,
        state_meta,
        candidate_source_ref=str(V2.relative_to(ROOT)),
        required_stateful_targets={TARGET},
    )
    rsum = report["summary"]
    assert rsum["explicit_exact_contracts"] == 1, rsum
    assert rsum["stateful_contracts"] == 1, rsum
    assert rsum["receiver_state_records_verified"] == 1, rsum
    assert rsum["epoch_fields_verified"] == 1, rsum
    assert rsum["execution_admitted_calls"] == 0, rsum
    assert rsum["effect_authority"] == rsum["truth_authority"] == "NONE", rsum
    contract = report["stateful_contracts"][0]
    assert contract["receiver_state_type"] == "FrankRewardReceiverState", contract
    assert contract["state_access"] == "MUTATE_RECEIVER_STATE", contract
    assert contract["state_epoch_field"] == "state_epoch", contract
    assert contract["runtime_binding"] == "NONE", contract
    assert contract["execution_admitted"] is False, contract

    # Concrete structural state must preserve both typed per-dimension state and an explicit epoch.
    state_record = next(x for x in v2_ir["structural_records"] if x["name"] == "FrankRewardReceiverState")
    fields = {x["name"]: x["type_expr"] for x in state_record["fields"]}
    assert fields["by_dimension"]["name"] == "Map", fields
    assert [x["name"] for x in fields["by_dimension"]["args"]] == ["RewardDimension", "TypedValueState"], fields
    assert fields["state_epoch"]["name"] == "Epoch" and not fields["state_epoch"].get("optional"), fields

    # Reject an epoch-type downgrade.
    bad_ir = copy.deepcopy(v2_ir)
    bad_state = next(x for x in bad_ir["structural_records"] if x["name"] == "FrankRewardReceiverState")
    next(x for x in bad_state["fields"] if x["name"] == "state_epoch")["type_expr"]["name"] = "Int"
    try:
        stateful_v2.build_stateful_report(
            v2_graph,
            bad_ir,
            call_meta,
            state_meta,
            candidate_source_ref=str(V2.relative_to(ROOT)),
            required_stateful_targets={TARGET},
        )
    except stateful_v2.StatefulContractError:
        epoch_downgrade = "REJECTED_FAIL_CLOSED"
    else:
        raise AssertionError("receiver state epoch downgrade was not rejected")

    # Reject a false stateless claim.
    bad_meta = copy.deepcopy(state_meta)
    bad_meta[TARGET]["state_access"] = "STATELESS"
    try:
        stateful_v2.build_stateful_report(
            v2_graph,
            v2_ir,
            call_meta,
            bad_meta,
            candidate_source_ref=str(V2.relative_to(ROOT)),
            required_stateful_targets={TARGET},
        )
    except stateful_v2.StatefulContractError:
        stateless_escape = "REJECTED_FAIL_CLOSED"
    else:
        raise AssertionError("state-dependent call accepted STATELESS escape")

    # Deterministic replay.
    v2_ir_b = typed_v2.compile_sources([G9, DIALECT, V2], GRAMMAR)
    v2_graph_b = lower_graph(v2_ir_b)
    report_b = stateful_v2.build_stateful_report(
        v2_graph_b,
        v2_ir_b,
        anchor_v1.explicit_call_metadata(V2, GRAMMAR),
        stateful_v2.state_metadata(V2, GRAMMAR),
        candidate_source_ref=str(V2.relative_to(ROOT)),
        required_stateful_targets={TARGET},
    )
    assert v2_ir_b["typed_ir_sha256"] == v2_ir["typed_ir_sha256"]
    assert v2_graph_b["constraint_graph_sha256"] == v2_graph["constraint_graph_sha256"]
    assert report_b["stateful_report_sha256"] == report["stateful_report_sha256"]

    out = {
        "status": "PASS",
        "scope": "WP04_STATEFUL_FRANK_REWARD_CALL_CONTRACT_V2",
        "target": "frank_reward.update/1",
        "v1_hidden_receiver_state": v1_hidden_state,
        "v2_exact_declared_matches": summary["exact_declared_matches"],
        "v2_unresolved_signatures": summary["unresolved_signatures"],
        "effect_boundary_missing_signatures": summary["effect_boundary_missing_signatures"],
        "receiver_state_type": contract["receiver_state_type"],
        "state_access": contract["state_access"],
        "state_epoch_field": contract["state_epoch_field"],
        "state_contract_semantic_hash": contract["state_contract_semantic_hash"],
        "stateful_report_sha256": report["stateful_report_sha256"],
        "typed_ir_sha256": v2_ir["typed_ir_sha256"],
        "constraint_graph_sha256": v2_graph["constraint_graph_sha256"],
        "epoch_downgrade": epoch_downgrade,
        "stateless_escape": stateless_escape,
        "determinism": "PASS",
        "runtime_binding": "NONE",
        "execution_admitted_calls": 0,
        "effect_authority": "NONE",
        "truth_authority": "NONE",
        "promotion": "NONE",
        "wp03_status": "OPEN",
        "wp04_status": "OPEN",
        "next": "IMPLEMENT_STATEFUL_NONAUTHORITATIVE_EVALUATOR_AGAINST_EXPLICIT_RECEIVER_STATE_THEN_TARGET_VPS_DIFFERENTIAL",
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
