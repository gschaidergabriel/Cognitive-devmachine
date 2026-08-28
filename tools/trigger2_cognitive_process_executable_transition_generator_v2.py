#!/usr/bin/env python3
"""Executable-transition successor for Trigger-2 cognitive-process supervision.

This is a SOURCE/EVAL donor only. It does not admit positive training rows.

V1 described desired rules and emitted output field names. V2 instead constructs concrete
COGNITIVE_WORK_PACKET/v1 inputs and concrete COGNITIVE_RESULT_PACKET/v1 candidate outputs,
plus an evaluator-only expected state-after projection. Every result packet is passed through
the current deterministic ClayCode cognitive adapter roundtrip.

Authority boundary:
- only model/cognitive process classes are supervised here;
- deterministic DB admission, capability, lease, canonical commit and EffectGate outcomes are
  provided as inputs/oracles, never minted by the model target;
- model results remain CANDIDATE/PROJECTION/MEASUREMENT;
- UNKNOWN stays explicit;
- no runtime/J-Space/training/accepted-token credit is created by generation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from claycode_cognitive_protocol_adapter_v1 import roundtrip

GENERATOR_SCHEMA = "CLAY_TRIGGER2_COGNITIVE_PROCESS_EXECUTABLE_TRANSITION_GENERATOR/v2"
ROW_SCHEMA = "ENTITYOS_HCU_EXECUTABLE_TRANSITION_CANDIDATE/v2"
TARGET_SCHEMA = "ENTITYOS_HCU_EXECUTABLE_TRANSITION_TARGET/v2"
SOURCE_CENSUS = ROOT / "research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json"
SOURCE_ABI = ROOT / "research_entity/global/COGNITIVE_PROCESS_ABI_v1.json"
SOURCE_CLAYCODE_PROTOCOL = ROOT / "research_entity/global/CLAYCODE_COGNITIVE_PROTOCOL_v1.json"
SOURCE_CLAYCODE_ADAPTER = ROOT / "tools/claycode_cognitive_protocol_adapter_v1.py"
TRAINABLE_CLASSES = {"SIMULATE_ON_GRID", "EXTERNAL_STRONG_MODEL_BRIDGE", "OPTIONAL_CAUSAL_RESEARCH"}


def cj(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def dg(value: Any) -> str:
    return hashlib.sha256(cj(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"OBJECT_REQUIRED:{path}")
    return value


def process_index() -> dict[str, dict[str, Any]]:
    census = load_json(SOURCE_CENSUS)
    if census.get("schema") != "ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS/v1":
        raise ValueError("CENSUS_SCHEMA_DRIFT")
    processes = census.get("processes")
    if not isinstance(processes, list):
        raise ValueError("CENSUS_PROCESSES_REQUIRED")
    result = {p["id"]: p for p in processes if isinstance(p, dict) and isinstance(p.get("id"), str)}
    return result


def source_bindings() -> dict[str, Any]:
    return {
        "census": {"path": str(SOURCE_CENSUS.relative_to(ROOT)), "sha256": file_sha256(SOURCE_CENSUS)},
        "abi": {"path": str(SOURCE_ABI.relative_to(ROOT)), "sha256": file_sha256(SOURCE_ABI)},
        "claycode_protocol": {
            "path": str(SOURCE_CLAYCODE_PROTOCOL.relative_to(ROOT)),
            "sha256": file_sha256(SOURCE_CLAYCODE_PROTOCOL),
        },
        "claycode_adapter": {
            "path": str(SOURCE_CLAYCODE_ADAPTER.relative_to(ROOT)),
            "sha256": file_sha256(SOURCE_CLAYCODE_ADAPTER),
        },
    }


def base_work_packet(process_id: str, variant: dict[str, Any], case_id: str) -> dict[str, Any]:
    n = int(variant["n"])
    executor = str(variant["executor"])
    return {
        "schema": "COGNITIVE_WORK_PACKET/v1",
        "causal_event_id": f"ce-{case_id.lower()}",
        "admission_id": f"adm-{case_id.lower()}",
        "generation": 7,
        "work_id": f"work-{case_id.lower()}",
        "process_id": process_id,
        "parent_work_ids": [],
        "workspace_epoch": 41,
        "state_snapshot_ref": {
            "ref_id": "s0-snapshot-0041",
            "store": "UnifiedDB",
            "snapshot_or_epoch": 41,
            "object_key": "task/current",
            "digest": "a" * 64,
            "provenance": "DETERMINISTIC_S0_FIXTURE",
            "mutability": "IMMUTABLE_SNAPSHOT",
        },
        "input_refs": [],
        "epistemic_inputs": [],
        "capability_scope_ref": "capability://fixture/read-and-propose",
        "resource_budget": {"max_input_tokens": 1024, "max_output_tokens": 384, "deadline_ms": 2500},
        "grid_runtime": {
            "grid_instance_id": "grid-fixture-a",
            "requested_N": n,
            "observed_available_N": n,
            "executor_id": executor,
        },
        "route_policy_ref": "route://deterministic-fixture-v1",
        "completion_contract": {
            "must_emit_concrete_result": True,
            "must_preserve_unknown": True,
            "must_remain_candidate_only": True,
            "must_not_mint_db_or_effect_authority": True,
        },
    }


def result_packet(
    work: dict[str, Any],
    payload: dict[str, Any],
    *,
    result_class: str = "CANDIDATE",
    unknowns: list[dict[str, Any]] | None = None,
    db_write_proposals: list[dict[str, Any]] | None = None,
    effect_request_candidates: list[dict[str, Any]] | None = None,
    workspace_reentry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload_digest = dg(payload)
    executor = work["grid_runtime"]["executor_id"]
    packet = {
        "schema": "COGNITIVE_RESULT_PACKET/v1",
        "causal_event_id": work["causal_event_id"],
        "admission_id": work["admission_id"],
        "generation": work["generation"],
        "work_id": work["work_id"],
        "process_id": work["process_id"],
        "executor_binding": {
            "grid_instance_id": work["grid_runtime"]["grid_instance_id"],
            "requested_N": work["grid_runtime"]["requested_N"],
            "available_N": work["grid_runtime"]["observed_available_N"],
            "executor_id": executor,
            "lease_id": f"lease-{work['work_id']}-{executor}",
            "process_id": work["process_id"],
            "runtime_identity": "MODEL_RUNTIME_IDENTITY_UNKNOWN_IN_SOURCE_DONOR",
            "started_at": "UNKNOWN",
            "ended_at": "UNKNOWN",
        },
        "result_id": f"result-{payload_digest[:20]}",
        "result_class": result_class,
        "result_payload_ref": f"inline-sha256:{payload_digest}",
        "result_digest": payload_digest,
        "evidence_refs": [work["state_snapshot_ref"]["ref_id"]],
        "unknowns": unknowns or [],
        "db_write_proposals": db_write_proposals or [],
        "effect_request_candidates": effect_request_candidates or [],
        "workspace_reentry": workspace_reentry
        or {
            "status": "NO_REENTRY_REQUESTED",
            "source_work_id": work["work_id"],
            "target_workspace_epoch": work["workspace_epoch"],
        },
        "runtime_receipt": {
            "status": "UNKNOWN_PRE_EXECUTION",
            "runtime_identity": "UNKNOWN",
            "self_attested": False,
        },
        "result_payload_inline": payload,
    }
    return packet


def case_hyperposition(work: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state = {
        "claim": "which-plan",
        "alternatives": [
            {"id": "h1", "support": ["ev-a"], "status": "UNRESOLVED"},
            {"id": "h2", "support": ["ev-b"], "status": "UNRESOLVED"},
        ],
        "votes": {"h1": 8, "h2": 2},
        "causal_discriminator_observed": False,
    }
    payload = {
        "alternative_set": ["h1", "h2"],
        "resolution": "UNRESOLVED",
        "uncertainty_readout": "DISCRIMINATOR_REQUIRED",
        "discriminator_candidates": ["obtain-fresh-causal-test"],
        "majority_is_truth": False,
    }
    packet = result_packet(work, payload)
    after = {"live_alternatives": ["h1", "h2"], "resolution": "UNRESOLVED", "next_gate": "obtain-fresh-causal-test"}
    return state, packet, after


def case_stale_contradiction(work: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state = {
        "candidate_claim": "task-is-open",
        "candidate_state_ref": {"epoch": 39, "digest": "b" * 64},
        "current_state_ref": {"epoch": 41, "digest": "a" * 64},
        "fresh_read_available": False,
    }
    payload = {
        "quality_readout": "STALE_EVIDENCE",
        "contradiction_flags": ["OBSERVATION_IDENTITY_STALE"],
        "revision_request": {"action": "REREAD_OR_EXPLICIT_REVALIDATION", "relabel_old_observation": False},
    }
    packet = result_packet(
        work,
        payload,
        unknowns=[{"field": "task_current_status", "status": "UNKNOWN", "reason": "stale observation"}],
    )
    after = {"task_current_status": "UNKNOWN", "old_observation_preserved": True, "revalidation_required": True}
    return state, packet, after


def case_claude_return(work: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state = {
        "bridge_request_id": "bridge-req-17",
        "claude_text": "The repository is healthy and deployment succeeded.",
        "tool_results": [{"ref": "tool://git/status/17", "observed": "clean tree"}],
        "deployment_receipt": None,
    }
    payload = {
        "bridge_return_packet": {"request_id": "bridge-req-17", "status": "RETURNED"},
        "evidence_candidates": [{"ref": "tool://git/status/17", "class": "TOOL_OBSERVATION"}],
        "model_assertions": [{"claim": "deployment succeeded", "status": "UNVERIFIED"}],
        "workspace_reentry_candidate": "bridge-return-17",
    }
    packet = result_packet(
        work,
        payload,
        unknowns=[{"field": "deployment_succeeded", "status": "UNKNOWN", "reason": "no deployment receipt"}],
        workspace_reentry={
            "status": "CANDIDATE_REENTRY",
            "source_result": "bridge-return-17",
            "target_workspace_epoch": 42,
            "causal_credit": "UNPROVEN",
        },
    )
    after = {"git_tree_clean": True, "deployment_succeeded": "UNKNOWN", "bridge_return_admitted_as_candidate": True}
    return state, packet, after


def case_memory_proposal(work: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state = {
        "verified_outcome_ref": "effect://receipt/ok-19",
        "current_memory_ref": "db://memory/project/7",
        "proposed_fact": "fixture preference alpha",
        "deterministic_admission_result": "NOT_RUN",
    }
    proposal = {
        "proposal_id": "mem-prop-19",
        "target_ref": "db://memory/project/7",
        "value": "fixture preference alpha",
        "evidence_refs": ["effect://receipt/ok-19"],
        "status": "PROPOSED_ONLY",
    }
    payload = {"memory_update_proposal": proposal, "commit_status": "NOT_COMMITTED"}
    packet = result_packet(work, payload, db_write_proposals=[proposal])
    after = {"canonical_memory_unchanged": True, "pending_proposal_id": "mem-prop-19"}
    return state, packet, after


def case_effect_proposal(work: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state = {
        "selected_intent": "write candidate report",
        "capability_view_ref": "capability://fixture/write-report",
        "effectgate_result": "NOT_RUN",
    }
    proposal = {
        "request_id": "effect-candidate-23",
        "effect_type": "WRITE_REPORT",
        "target": "fixture://report/current",
        "capability_scope_ref": "capability://fixture/write-report",
        "precondition_refs": ["s0-snapshot-0041"],
        "status": "CANDIDATE_ONLY",
    }
    payload = {"effect_request_candidate": proposal, "executed": False, "effect_receipt": "NONE"}
    packet = result_packet(work, payload, effect_request_candidates=[proposal])
    after = {"real_effect_executed": False, "pending_effect_request": "effect-candidate-23", "next_authority": "EffectGate"}
    return state, packet, after


def case_unknown_outcome(work: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state = {
        "submitted_effect_ref": "effect://submission/31",
        "transport_result": "TIMEOUT_AFTER_SUBMISSION",
        "provider_outcome_verified": False,
        "blind_replay_requested": True,
    }
    payload = {
        "reconciled_state_candidate": {"effect_outcome": "UNKNOWN"},
        "next_work_units": ["verify-provider-outcome-before-any-replay"],
        "rejoin_plan": "PRESERVE_EFFECT_IDENTITY_AND_WAIT_FOR_VERIFICATION",
        "blind_replay_allowed": False,
    }
    packet = result_packet(
        work,
        payload,
        unknowns=[{"field": "effect_outcome", "status": "UNKNOWN", "reason": "transport timeout after possible acceptance"}],
    )
    after = {"effect_outcome": "UNKNOWN", "blind_replay_allowed": False, "verification_required": True}
    return state, packet, after


def case_jspace_measurement(work: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state = {
        "exact_model_runtime_identity": "model://fixture/qwen35-08b/rev-x",
        "observable_bridge_state": "decoded-output-only",
        "hidden_activation_interface_exposed": False,
        "intervention_receipt": None,
    }
    payload = {
        "jspace_measurement": {"observable": "decoded-output-only", "value": "MEASURED_INTERFACE_STATE"},
        "causal_probe_receipt": "NONE",
        "credit_scope": "MEASUREMENT_ONLY_NO_CAUSAL_PROMOTION",
        "hidden_activation_access": "UNKNOWN_NOT_EXPOSED",
    }
    packet = result_packet(
        work,
        payload,
        result_class="MEASUREMENT",
        unknowns=[{"field": "hidden_activation_causality", "status": "UNKNOWN", "reason": "no exposed hook/intervention receipt"}],
    )
    after = {"measurement_preserved": True, "causal_promotion": False, "hidden_activation_causality": "UNKNOWN"}
    return state, packet, after


CASES = {
    "HP_UNRESOLVED_MAJORITY": ("ZECP07", case_hyperposition),
    "STALE_OBSERVATION_CRITIQUE": ("ZECP09", case_stale_contradiction),
    "CLAUDE_RETURN_EVIDENCE_SPLIT": ("ZECP14", case_claude_return),
    "MEMORY_PROPOSAL_NO_COMMIT": ("ZECP15", case_memory_proposal),
    "EFFECT_PROPOSAL_NO_EXECUTION": ("ZECP16", case_effect_proposal),
    "UNKNOWN_EFFECT_OUTCOME_NO_REPLAY": ("ZECP18", case_unknown_outcome),
    "JSPACE_MEASUREMENT_NO_CAUSAL_UPGRADE": ("ZECP20", case_jspace_measurement),
}

VARIANTS = (
    {"variant_id": "N10_A", "n": 10, "executor": "node-alpha"},
    {"variant_id": "N20_B", "n": 20, "executor": "node-beta"},
)


def make_row(case_id: str, process_id: str, builder: Any, variant: dict[str, Any], index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    process = index.get(process_id)
    if not process:
        raise ValueError(f"PROCESS_NOT_IN_CENSUS:{process_id}")
    implementation_class = process.get("implementation_class")
    if implementation_class not in TRAINABLE_CLASSES:
        raise ValueError(f"DETERMINISTIC_OR_STORE_PROCESS_CANNOT_BE_MODEL_TARGET:{process_id}:{implementation_class}")

    work = base_work_packet(process_id, variant, case_id)
    state_before, packet, state_after = builder(work)
    envelope, decoded = roundtrip("COGNITIVE_RESULT_PACKET/v1", packet)
    if cj(decoded) != cj(packet):
        raise AssertionError("CLAYCODE_ROUNDTRIP_SEMANTIC_DRIFT")
    if packet["result_digest"] != dg(packet["result_payload_inline"]):
        raise AssertionError("RESULT_PAYLOAD_DIGEST_DRIFT")

    prompt_obj = {
        "schema": "ENTITYOS_HCU_EXECUTABLE_TRANSITION_INPUT/v2",
        "work_packet": work,
        "state_before": state_before,
        "instruction": "Execute the process-specific cognitive transition. Return the concrete candidate result packet and state-after candidate; do not narrate a rule and do not mint deterministic authority.",
    }
    target_obj = {
        "schema": TARGET_SCHEMA,
        "result_packet": packet,
        "state_after_candidate": state_after,
    }
    semantic_core = {
        "case_id": case_id,
        "process_id": process_id,
        "state_before": state_before,
        "result_payload": packet["result_payload_inline"],
        "unknowns": packet["unknowns"],
        "db_write_proposals": packet["db_write_proposals"],
        "effect_request_candidates": packet["effect_request_candidates"],
        "state_after_candidate": state_after,
    }
    return {
        "schema": ROW_SCHEMA,
        "row_id": f"TR2-EXTRANS-V2-{case_id}-{variant['variant_id']}",
        "case_id": case_id,
        "process_id_evaluator_only": process_id,
        "implementation_class_evaluator_only": implementation_class,
        "variant_evaluator_only": variant,
        "semantic_core_digest_evaluator_only": dg(semantic_core),
        "split_unit": "CASE_AND_PROVENANCE_ANCESTRY",
        "evidence_class": "SYNTHETIC_EXECUTABLE_TRANSITION_METHOD_DONOR",
        "reality_level": "R2_GENERATED",
        "training_eligible": False,
        "positive_training_admission": "CLOSED",
        "accepted_dataset_tokens": 0,
        "target_visible_only_during_supervision": True,
        "model_visible_fields": ["prompt"],
        "prompt": cj(prompt_obj),
        "target": cj(target_obj),
        "claycode_roundtrip_evaluator_only": {
            "packet_digest": envelope.packet_digest,
            "clay_source_sha256": envelope.clay_source_sha256,
            "clay_semantic_hash": envelope.clay_semantic_hash,
            "clay_grammar_sha256": envelope.clay_grammar_sha256,
            "status": "PASS_SOURCE_COMPONENT",
        },
        "oracle_evaluator_only": {
            "canonical_state_commit": "NOT_PERFORMED_BY_MODEL",
            "capability_grant": "NOT_PERFORMED_BY_MODEL",
            "coordinator_or_executor_lease_grant": "NOT_PERFORMED_BY_MODEL",
            "effect_execution": "NOT_PERFORMED_BY_MODEL",
            "result_payload_digest_recomputed": dg(packet["result_payload_inline"]),
            "expected_state_after_candidate": state_after,
        },
    }


def rows() -> list[dict[str, Any]]:
    index = process_index()
    out: list[dict[str, Any]] = []
    for case_id, (process_id, builder) in CASES.items():
        for variant in VARIANTS:
            out.append(make_row(case_id, process_id, builder, variant, index))
    return out


def report(generated: list[dict[str, Any]]) -> dict[str, Any]:
    by_case: dict[str, list[dict[str, Any]]] = {}
    for row in generated:
        by_case.setdefault(row["case_id"], []).append(row)
    nuisance_invariance = {}
    for case_id, family in sorted(by_case.items()):
        # Prompt/executor envelope may vary with runtime N, but the process semantic core must not.
        nuisance_invariance[case_id] = {
            "variants": len(family),
            "semantic_core_identical": len({r["semantic_core_digest_evaluator_only"] for r in family}) == 1,
        }
    return {
        "schema": GENERATOR_SCHEMA,
        "status": "SOURCE_EVAL_DONOR_ONLY_NOT_TRAINING_ADMISSION",
        "row_count": len(generated),
        "case_count": len(CASES),
        "variants_per_case": len(VARIANTS),
        "process_ids": sorted({r["process_id_evaluator_only"] for r in generated}),
        "implementation_classes": sorted({r["implementation_class_evaluator_only"] for r in generated}),
        "all_targets_concrete_json": all(json.loads(r["target"])["schema"] == TARGET_SCHEMA for r in generated),
        "all_claycode_roundtrips_passed": all(r["claycode_roundtrip_evaluator_only"]["status"] == "PASS_SOURCE_COMPONENT" for r in generated),
        "contains_meta_rule_targets": any("\"rule\"" in r["target"] or "\"emit\"" in r["target"] for r in generated),
        "nuisance_invariance": nuisance_invariance,
        "source_bindings": source_bindings(),
        "credit": {
            "source_eval_donor": 1,
            "positive_training_rows_admitted": 0,
            "accepted_dataset_tokens": 0,
            "model_runtime": 0,
            "jspace_causal": 0,
            "whole_hcu": 0,
            "whole_entityos": 0,
            "training": 0,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    generated = rows()
    rep = report(generated)
    if not all(v["semantic_core_identical"] for v in rep["nuisance_invariance"].values()):
        raise SystemExit("RUNTIME_N_OR_EXECUTOR_CHANGED_PROCESS_SEMANTIC_CORE")
    if rep["contains_meta_rule_targets"]:
        raise SystemExit("META_RULE_TARGET_REINTRODUCED")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text("".join(cj(row) + "\n" for row in generated), encoding="utf-8")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(rep, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(rep, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
