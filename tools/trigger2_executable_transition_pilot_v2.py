#!/usr/bin/env python3
"""Trigger-2 executable cognitive-transition pilot v2.

Successor to ``trigger2_executable_transition_pilot_v1.py`` for issue #2022.

V1 correctly moved supervision from meta-rule narration to instantiated cognitive
transitions, but its supervised ``target`` also carried deterministic envelope fields
(admission/generation/lease/runtime identity).  Those fields are necessary to bind a
NODE_RESULT at runtime, but they are not model authority and must not be learned as if
an ordinary Xeno could mint them.

V2 therefore separates:

    evaluator/oracle authority envelope
      + model-predicted candidate cognition
      -> deterministic evaluator composition
      -> full COGNITIVE_RESULT_PACKET/v1

The model target contains only candidate cognition/proposals.  Deterministic IDs,
leases, epochs/runtime receipts and full packet identity remain evaluator-only.  The
full packet is reconstructed deterministically for scoring, preserving the runtime ABI
without creating a second semantic or authority path.

SOURCE/CANDIDATE EVAL ONLY.  No row is training-admitted and no runtime, J-Space,
HCU, EntityOS, accepted-token or training credit is minted.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
DONOR_PATH = ROOT / "tools/trigger2_executable_transition_pilot_v1.py"
ABI_PATH = ROOT / "research_entity/global/COGNITIVE_PROCESS_ABI_v1.json"
CENSUS_PATH = ROOT / "research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json"
COURSE_PATH = ROOT / "research_entity/global/TRIGGERWORT_2_CURRENT_TRAINING_COURSE_XENO_HARNESS_2026-08-26.md"

ROW_SCHEMA = "TRIGGER2_EXECUTABLE_COGNITIVE_TRANSITION_CANDIDATE/v2"
MODEL_TARGET_SCHEMA = "XENO_CANDIDATE_COGNITIVE_OUTPUT/v1"
ORACLE_SCHEMA = "XENO_RESULT_PACKET_ORACLE_ENVELOPE/v1"
AUDIT_SCHEMA = "TRIGGER2_EXECUTABLE_COGNITIVE_TRANSITION_AUDIT/v2"
FULL_PACKET_SCHEMA = "COGNITIVE_RESULT_PACKET/v1"

# Keys that represent deterministic runtime/evidence authority.  They may occur in
# evaluator-only oracle context, never in model supervision.  Candidate proposal
# fields such as ``executed=False`` and ``commit=False`` remain allowed because they
# encode the required negative authority semantics rather than minting authority.
FORBIDDEN_MODEL_KEYS = frozenset({
    "causal_event_id",
    "admission_id",
    "generation",
    "work_id",
    "process_id",
    "executor_binding",
    "grid_instance_id",
    "requested_N",
    "available_N",
    "executor_id",
    "lease_id",
    "runtime_identity",
    "started_at",
    "ended_at",
    "result_id",
    "runtime_receipt",
    "source_result_id",
    "source_process_id",
    "from_workspace_epoch",
    "to_workspace_epoch",
    "reentry_digest",
})


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


donor = _load_module(DONOR_PATH, "trigger2_executable_transition_pilot_v1_for_v2")


def cj(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def dg(value: Any) -> str:
    return hashlib.sha256(cj(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_bindings() -> dict[str, Any]:
    paths = {
        "donor": DONOR_PATH,
        "abi": ABI_PATH,
        "census": CENSUS_PATH,
        "course": COURSE_PATH,
    }
    return {
        "schema": "TRIGGER2_EXECUTABLE_TRANSITION_SOURCE_BINDING/v1",
        "files": {
            name: {
                "repo_path": str(path.relative_to(ROOT)),
                "sha256": file_sha256(path),
            }
            for name, path in paths.items()
        },
        "issue": 2022,
    }


def _forbidden_path(value: Any, path: str = "$") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            skey = str(key)
            if skey in FORBIDDEN_MODEL_KEYS:
                return f"{path}.{skey}"
            got = _forbidden_path(child, f"{path}.{skey}")
            if got:
                return got
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            got = _forbidden_path(child, f"{path}[{idx}]")
            if got:
                return got
    return None


def _oracle_from_v1_target(target: Mapping[str, Any]) -> dict[str, Any]:
    reentry = target.get("workspace_reentry")
    if not isinstance(reentry, Mapping):
        raise ValueError("V1_WORKSPACE_REENTRY_REQUIRED")
    return {
        "schema": ORACLE_SCHEMA,
        "packet_schema": target.get("schema"),
        "causal_event_id": target.get("causal_event_id"),
        "admission_id": target.get("admission_id"),
        "generation": target.get("generation"),
        "work_id": target.get("work_id"),
        "process_id": target.get("process_id"),
        "executor_binding": copy.deepcopy(target.get("executor_binding")),
        "result_id": target.get("result_id"),
        "result_class": target.get("result_class"),
        "runtime_receipt": copy.deepcopy(target.get("runtime_receipt")),
        "workspace_reentry_binding": {
            "source_result_id": reentry.get("source_result_id"),
            "source_process_id": reentry.get("source_process_id"),
            "causal_event_id": reentry.get("causal_event_id"),
            "from_workspace_epoch": reentry.get("from_workspace_epoch"),
            "to_workspace_epoch": reentry.get("to_workspace_epoch"),
            "reentry_payload_ref": reentry.get("reentry_payload_ref"),
        },
    }


def _model_target_from_v1(target: Mapping[str, Any]) -> dict[str, Any]:
    payload_ref = target.get("result_payload_ref")
    if not isinstance(payload_ref, Mapping):
        raise ValueError("V1_RESULT_PAYLOAD_REF_REQUIRED")
    reentry = target.get("workspace_reentry")
    if not isinstance(reentry, Mapping):
        raise ValueError("V1_WORKSPACE_REENTRY_REQUIRED")
    out = {
        "schema": MODEL_TARGET_SCHEMA,
        "result_payload": copy.deepcopy(payload_ref.get("payload")),
        "evidence_refs": copy.deepcopy(target.get("evidence_refs", [])),
        "unknowns": copy.deepcopy(target.get("unknowns", [])),
        "db_write_proposals": copy.deepcopy(target.get("db_write_proposals", [])),
        "effect_request_candidates": copy.deepcopy(target.get("effect_request_candidates", [])),
        "workspace_reentry_intent": {
            "observed_downstream_change": reentry.get("observed_downstream_change"),
            "acceptance": reentry.get("acceptance"),
        },
    }
    forbidden = _forbidden_path(out)
    if forbidden:
        raise ValueError("MODEL_TARGET_AUTHORITY_FIELD:" + forbidden)
    return out


def compose_full_packet(row: Mapping[str, Any], model_target: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Deterministically compose a full runtime-shaped packet for evaluator scoring.

    This function is an evaluator/oracle operation.  It does not grant the model the
    ability to choose envelope identity, lease, generation or runtime facts.
    """
    oracle = row.get("oracle_context_evaluator_only")
    if not isinstance(oracle, Mapping) or oracle.get("schema") != ORACLE_SCHEMA:
        raise ValueError("ORACLE_CONTEXT_REQUIRED")
    model_target = model_target or row.get("expected_model_target")
    if not isinstance(model_target, Mapping) or model_target.get("schema") != MODEL_TARGET_SCHEMA:
        raise ValueError("MODEL_TARGET_SCHEMA_REQUIRED")
    forbidden = _forbidden_path(model_target)
    if forbidden:
        raise ValueError("MODEL_TARGET_AUTHORITY_FIELD:" + forbidden)

    payload = copy.deepcopy(model_target.get("result_payload"))
    result_digest = dg(payload)
    wr_binding = oracle.get("workspace_reentry_binding")
    if not isinstance(wr_binding, Mapping):
        raise ValueError("WORKSPACE_REENTRY_ORACLE_REQUIRED")
    intent = model_target.get("workspace_reentry_intent")
    if not isinstance(intent, Mapping):
        raise ValueError("WORKSPACE_REENTRY_INTENT_REQUIRED")
    workspace_reentry = {
        **copy.deepcopy(dict(wr_binding)),
        "observed_downstream_change": intent.get("observed_downstream_change"),
        "acceptance": intent.get("acceptance"),
    }
    workspace_reentry["reentry_digest"] = dg(workspace_reentry)

    return {
        "schema": oracle.get("packet_schema"),
        "causal_event_id": oracle.get("causal_event_id"),
        "admission_id": oracle.get("admission_id"),
        "generation": oracle.get("generation"),
        "work_id": oracle.get("work_id"),
        "process_id": oracle.get("process_id"),
        "executor_binding": copy.deepcopy(oracle.get("executor_binding")),
        "result_id": oracle.get("result_id"),
        "result_class": oracle.get("result_class"),
        "result_payload_ref": {"encoding": "DETERMINISTIC_JSON_V1", "payload": payload},
        "result_digest": result_digest,
        "evidence_refs": copy.deepcopy(model_target.get("evidence_refs", [])),
        "unknowns": copy.deepcopy(model_target.get("unknowns", [])),
        "db_write_proposals": copy.deepcopy(model_target.get("db_write_proposals", [])),
        "effect_request_candidates": copy.deepcopy(model_target.get("effect_request_candidates", [])),
        "workspace_reentry": workspace_reentry,
        "runtime_receipt": copy.deepcopy(oracle.get("runtime_receipt")),
    }


def _convert(v1row: Mapping[str, Any], index: int, bindings: Mapping[str, Any]) -> dict[str, Any]:
    target = v1row.get("target")
    if not isinstance(target, Mapping):
        raise ValueError("V1_TARGET_REQUIRED")
    oracle = _oracle_from_v1_target(target)
    model_target = _model_target_from_v1(target)
    process_id = v1row.get("process_id_evaluator_only")
    case_id = str(v1row.get("case_id"))

    row = {
        "schema": ROW_SCHEMA,
        "case_id": case_id,
        "status": "CANDIDATE_EVAL_ONLY_NOT_TRAINING_ELIGIBLE",
        "predecessor_schema": v1row.get("schema"),
        "predecessor_case_digest_evaluator_only": dg(v1row),
        "family_id_evaluator_only": f"T2ECTV2:{process_id}",
        "provenance_ancestry_id_evaluator_only": f"T2ECTV2:donor:{case_id}",
        "split_evaluator_only": "CANDIDATE_UNSPLIT",
        "process_id_evaluator_only": process_id,
        "implementation_class_evaluator_only": v1row.get("implementation_class_evaluator_only"),
        "oracle_context_evaluator_only": oracle,
        "source_bindings_evaluator_only": copy.deepcopy(bindings),
        "state_before": copy.deepcopy(v1row.get("state_before")),
        "state_before_digest_evaluator_only": v1row.get("state_before_digest"),
        "decisive_semantic_delta": copy.deepcopy(v1row.get("decisive_semantic_delta")),
        "expected_model_target": model_target,
        "expected_model_target_digest_evaluator_only": dg(model_target),
        "expected_state_after_evaluator_only": copy.deepcopy(v1row.get("expected_state_after")),
        "expected_state_after_digest_evaluator_only": v1row.get("expected_state_after_digest"),
        "required_unknowns_evaluator_only": copy.deepcopy(v1row.get("required_unknowns_preserved", [])),
        "model_input_fields": ["state_before", "decisive_semantic_delta"],
        "model_supervision_fields": ["expected_model_target"],
        "evaluator_only_fields_are_loss_masked": True,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
    }
    packet = compose_full_packet(row, model_target)
    row["expected_full_packet_digest_evaluator_only"] = dg(packet)
    row["transition_semantic_digest_evaluator_only"] = dg({
        "source_binding_digest": dg(bindings),
        "process_id": process_id,
        "state_before_digest": row["state_before_digest_evaluator_only"],
        "decisive_semantic_delta": row["decisive_semantic_delta"],
        "model_target_digest": row["expected_model_target_digest_evaluator_only"],
        "state_after_digest": row["expected_state_after_digest_evaluator_only"],
    })
    return row


def rows() -> list[dict[str, Any]]:
    bindings = source_bindings()
    return [_convert(row, idx, bindings) for idx, row in enumerate(donor.rows())]


def _source_bindings_match(binding: Mapping[str, Any]) -> bool:
    expected = source_bindings()
    return dict(binding) == expected


def audit(generated: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    process_ids: set[str] = set()
    for row in generated:
        cid = str(row.get("case_id", "UNKNOWN"))
        if row.get("schema") != ROW_SCHEMA:
            failures.append("ROW_SCHEMA_DRIFT:" + cid)
        if row.get("training_eligible") is not False or row.get("accepted_dataset_tokens_minted") != 0 or row.get("training_credit_minted") != 0:
            failures.append("TRAINING_CREDIT_LEAK:" + cid)
        if row.get("canonical_truth_allowed") is not False or row.get("direct_effect_authority") is not False:
            failures.append("ROW_AUTHORITY_LEAK:" + cid)
        if row.get("split_evaluator_only") != "CANDIDATE_UNSPLIT":
            failures.append("PREMATURE_SPLIT_CLAIM:" + cid)
        if row.get("evaluator_only_fields_are_loss_masked") is not True:
            failures.append("EVALUATOR_ONLY_NOT_LOSS_MASKED:" + cid)
        if row.get("model_supervision_fields") != ["expected_model_target"]:
            failures.append("MODEL_SUPERVISION_SCOPE_DRIFT:" + cid)

        bindings = row.get("source_bindings_evaluator_only")
        if not isinstance(bindings, Mapping) or not _source_bindings_match(bindings):
            failures.append("SOURCE_BINDING_MISMATCH:" + cid)

        process_id = row.get("process_id_evaluator_only")
        if isinstance(process_id, str):
            process_ids.add(process_id)
        oracle = row.get("oracle_context_evaluator_only")
        if not isinstance(oracle, Mapping) or oracle.get("schema") != ORACLE_SCHEMA:
            failures.append("ORACLE_CONTEXT_INVALID:" + cid)
            continue
        if oracle.get("packet_schema") != FULL_PACKET_SCHEMA:
            failures.append("ORACLE_PACKET_SCHEMA_DRIFT:" + cid)
        if oracle.get("process_id") != process_id:
            failures.append("ORACLE_PROCESS_MISMATCH:" + cid)

        mt = row.get("expected_model_target")
        if not isinstance(mt, Mapping) or mt.get("schema") != MODEL_TARGET_SCHEMA:
            failures.append("MODEL_TARGET_INVALID:" + cid)
            continue
        forbidden = _forbidden_path(mt)
        if forbidden:
            failures.append("MODEL_TARGET_AUTHORITY_FIELD:" + cid + ":" + forbidden)
        if dg(mt) != row.get("expected_model_target_digest_evaluator_only"):
            failures.append("MODEL_TARGET_DIGEST_MISMATCH:" + cid)

        required_unknowns = set(row.get("required_unknowns_evaluator_only") or [])
        actual_unknowns = set(mt.get("unknowns") or [])
        if not required_unknowns.issubset(actual_unknowns):
            failures.append("UNKNOWN_COLLAPSE:" + cid)

        for proposal in mt.get("db_write_proposals") or []:
            if not isinstance(proposal, Mapping) or proposal.get("status") != "CANDIDATE_ONLY" or proposal.get("commit") is not False:
                failures.append("DB_AUTHORITY_SELF_MINT:" + cid)
        for proposal in mt.get("effect_request_candidates") or []:
            if not isinstance(proposal, Mapping) or proposal.get("status") != "CANDIDATE_ONLY" or proposal.get("executed") is not False:
                failures.append("EFFECT_AUTHORITY_SELF_MINT:" + cid)

        try:
            packet = compose_full_packet(row, mt)
        except Exception as exc:
            failures.append("FULL_PACKET_COMPOSE_FAIL:" + cid + ":" + type(exc).__name__)
        else:
            if dg(packet) != row.get("expected_full_packet_digest_evaluator_only"):
                failures.append("FULL_PACKET_DIGEST_MISMATCH:" + cid)
            runtime = packet.get("runtime_receipt")
            if not isinstance(runtime, Mapping) or runtime.get("model_runtime_observed") is not False or runtime.get("canonical_truth_minted") is not False or runtime.get("effect_executed") is not False:
                failures.append("ORACLE_RUNTIME_SCOPE_FAIL:" + cid)

        if dg(row.get("state_before")) != row.get("state_before_digest_evaluator_only"):
            failures.append("STATE_BEFORE_DIGEST_MISMATCH:" + cid)
        if dg(row.get("expected_state_after_evaluator_only")) != row.get("expected_state_after_digest_evaluator_only"):
            failures.append("STATE_AFTER_DIGEST_MISMATCH:" + cid)

        expected_transition = dg({
            "source_binding_digest": dg(bindings),
            "process_id": process_id,
            "state_before_digest": row.get("state_before_digest_evaluator_only"),
            "decisive_semantic_delta": row.get("decisive_semantic_delta"),
            "model_target_digest": row.get("expected_model_target_digest_evaluator_only"),
            "state_after_digest": row.get("expected_state_after_digest_evaluator_only"),
        })
        if expected_transition != row.get("transition_semantic_digest_evaluator_only"):
            failures.append("TRANSITION_DIGEST_MISMATCH:" + cid)

    failures = sorted(set(failures))
    return {
        "schema": AUDIT_SCHEMA,
        "pass": not failures,
        "rows": len(generated),
        "process_ids": sorted(process_ids),
        "failures": failures,
        "authority_masking": "PASS" if not [f for f in failures if "AUTHORITY" in f or "ORACLE" in f] else "FAIL",
        "full_packet_scoring_preserved": not [f for f in failures if "FULL_PACKET" in f],
        "source_identity_bound": not [f for f in failures if "SOURCE_BINDING" in f],
        "split_status": "CANDIDATE_UNSPLIT_NOT_ADMITTED",
        "claycode_roundtrip_gate": "PENDING_SEPARATE_EXACT_V18_GATE",
        "nuisance_family_split_gate": "PENDING_SEPARATE_RENDERED_BYTES_GATE",
        "canonical_dataset_write_performed": False,
        "positive_rows_admitted": 0,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "model_runtime_credit_minted": 0,
        "jspace_credit_minted": 0,
        "hcu_credit_minted": 0,
        "entityos_credit_minted": 0,
    }


def main() -> None:
    generated = rows()
    report = audit(generated)
    print(json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
