#!/usr/bin/env python3
"""Source-only Trigger-2 gate binding NODE_RESULT authority to one existing model-call identity.

This successor does NOT create a second model-call identifier. It consumes the exact
``source_bound_model_call_identity_sha256`` already produced by
``trigger2_model_call_repository_bound_gate_v1.py`` and binds it, together with the exact
model-output identity, into a deterministic controller-owned lineage envelope around an
immutable proof-carrying NODE_RESULT packet.

The gate is intentionally fail-closed and source-only. It executes no model/provider and
mints zero checkpoint-selection, physical GRID10, J-Space, training, HCU, EntityOS,
canonical-truth or effect-authority credit.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

SCHEMA = "CLAY_TRIGGER2_NODE_RESULT_MODEL_CALL_LINEAGE_GATE/v1"
NODE_RESULT_SCHEMA = "NODE_RESULT/v1"
NODE_AUTHORITY_ENVELOPE_SCHEMA = "PROOF_CARRYING_NODE_RESULT/v1"
MODEL_CALL_GATE_SCHEMA = "CLAY_TRIGGER2_MODEL_CALL_REPOSITORY_BOUND_GATE/v1"
SOURCE_BOUND_CALL_SCHEMA = "CLAY_TRIGGER2_SOURCE_BOUND_MODEL_CALL_IDENTITY/v1"
CONTROLLER_LINEAGE_SCHEMA = "CLAY_TRIGGER2_CONTROLLER_LINEAGE_BINDING/v1"
LINEAGE_ENVELOPE_SCHEMA = "CLAY_TRIGGER2_NODE_RESULT_MODEL_CALL_LINEAGE/v1"
COHORT_SCHEMA = "CLAY_TRIGGER2_LINEAGE_BOUND_COHORT/v1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")

# These fields belong to deterministic controller/runtime authority, never the learned or
# process-produced NODE_RESULT cognitive body. Rejecting them prevents a model/process from
# self-minting authority that happens to hash consistently.
RESERVED_RAW_NODE_RESULT_AUTHORITY_FIELDS = frozenset(
    {
        "causal_event_id",
        "admission_id",
        "route_decision_identity_sha256",
        "resolved_engine_identity_sha256",
        "grid_plan_identity_sha256",
        "grid_cell_id",
        "source_bound_model_call_identity_sha256",
        "model_output_identity_sha256",
        "source_identity_sha256",
        "source_head_sha",
        "source_tree_sha",
        "controller_lineage_sha256",
        "lineage_authority_envelope_digest",
    }
)


class GateError(RuntimeError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise GateError(code)


def _mapping(value: Any, code: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), code)
    return value


def _nonempty(value: Any, code: str) -> str:
    _require(isinstance(value, str) and bool(value), code)
    return value


def _hex(value: Any, pattern: re.Pattern[str], code: str) -> str:
    _require(isinstance(value, str) and bool(pattern.fullmatch(value)), code)
    return value


def validate_model_call_receipt(
    receipt: Mapping[str, Any], *, expected_model_call_identity_sha256: str
) -> dict[str, Any]:
    """Validate integrity of the existing repository-bound call receipt without minting a new call ID."""
    _hex(expected_model_call_identity_sha256, HEX64, "EXPECTED_MODEL_CALL_IDENTITY_INVALID")
    _require(receipt.get("schema") == MODEL_CALL_GATE_SCHEMA, "MODEL_CALL_GATE_SCHEMA_MISMATCH")
    _require(receipt.get("pass") is True, "MODEL_CALL_GATE_NOT_PASS")
    _require(
        receipt.get("status") == "PASS_SOURCE_BOUND_CALL_IDENTITY_COMPONENT_ONLY",
        "MODEL_CALL_GATE_STATUS_INVALID",
    )

    call_identity = _hex(
        receipt.get("source_bound_model_call_identity_sha256"),
        HEX64,
        "MODEL_CALL_IDENTITY_INVALID",
    )
    _require(call_identity == expected_model_call_identity_sha256, "MODEL_CALL_REFERENCE_MISMATCH")

    source_bound = _mapping(receipt.get("source_bound_envelope"), "SOURCE_BOUND_ENVELOPE_REQUIRED")
    _require(source_bound.get("schema") == SOURCE_BOUND_CALL_SCHEMA, "SOURCE_BOUND_ENVELOPE_SCHEMA_MISMATCH")
    _require(canonical_sha256(dict(source_bound)) == call_identity, "MODEL_CALL_IDENTITY_RECOMPUTE_MISMATCH")

    output_identity = _hex(
        receipt.get("model_output_identity_sha256"), HEX64, "MODEL_OUTPUT_IDENTITY_INVALID"
    )
    _require(
        source_bound.get("model_output_identity_sha256") == output_identity,
        "MODEL_OUTPUT_IDENTITY_CALL_MISMATCH",
    )
    _require(
        source_bound.get("abi_v2_model_call_binding_sha256")
        == receipt.get("abi_v2_model_call_binding_sha256"),
        "ABI_V2_CALL_BINDING_REFERENCE_MISMATCH",
    )

    source = _mapping(receipt.get("source_identity"), "SOURCE_IDENTITY_REQUIRED")
    source_identity_sha256 = _hex(
        source.get("source_identity_sha256"), HEX64, "SOURCE_IDENTITY_SHA256_INVALID"
    )
    _require(
        source_bound.get("source_identity_sha256") == source_identity_sha256,
        "SOURCE_IDENTITY_CALL_MISMATCH",
    )
    head_sha = _hex(source.get("head_sha"), HEX40, "SOURCE_HEAD_SHA_INVALID")
    tree_sha = _hex(source.get("tree_sha"), HEX40, "SOURCE_TREE_SHA_INVALID")
    _require(source.get("dirty") is False, "SOURCE_REPOSITORY_DIRTY_OR_UNKNOWN")

    return {
        "source_bound_model_call_identity_sha256": call_identity,
        "model_output_identity_sha256": output_identity,
        "source_identity_sha256": source_identity_sha256,
        "source_head_sha": head_sha,
        "source_tree_sha": tree_sha,
        "candidate_id": _nonempty(source_bound.get("candidate_id"), "CANDIDATE_ID_REQUIRED"),
        "checkpoint_manifest_sha256": _hex(
            source_bound.get("checkpoint_manifest_sha256"),
            HEX64,
            "CHECKPOINT_MANIFEST_SHA256_INVALID",
        ),
        "rendered_utf8_sha256": _hex(
            source_bound.get("rendered_utf8_sha256"), HEX64, "RENDERED_UTF8_SHA256_INVALID"
        ),
    }


def validate_node_authority_envelope(envelope: Mapping[str, Any]) -> dict[str, Any]:
    """Validate immutable NODE_RESULT + existing proof-carrying membership/process envelope."""
    _require(
        envelope.get("schema") == NODE_AUTHORITY_ENVELOPE_SCHEMA,
        "NODE_AUTHORITY_ENVELOPE_SCHEMA_MISMATCH",
    )
    packet = _mapping(envelope.get("node_result"), "NODE_RESULT_REQUIRED")
    _require(packet.get("schema") == NODE_RESULT_SCHEMA, "NODE_RESULT_SCHEMA_MISMATCH")
    leaked = RESERVED_RAW_NODE_RESULT_AUTHORITY_FIELDS.intersection(packet.keys())
    _require(not leaked, "MODEL_OR_PROCESS_MINTED_AUTHORITY_FIELD_REJECTED:" + ",".join(sorted(leaked)))

    packet_digest = _hex(packet.get("packet_digest"), HEX64, "NODE_RESULT_PACKET_DIGEST_INVALID")
    _require(envelope.get("node_result_digest") == packet_digest, "NODE_RESULT_ENVELOPE_DIGEST_REFERENCE_MISMATCH")

    # Mirror the existing fused GRID10 packet rule: packet_digest commits the cognitive core;
    # s1_write_intent is a non-authoritative execution-intent bit and is not part of that digest.
    packet_core = {
        key: packet[key]
        for key in packet
        if key not in ("packet_digest", "s1_write_intent")
    }
    _require(canonical_sha256(packet_core) == packet_digest, "NODE_RESULT_PACKET_DIGEST_RECOMPUTE_MISMATCH")
    _require(packet.get("s1_write_intent") is False, "NODE_RESULT_SELF_WRITE_INTENT_REJECTED")

    envelope_digest = _hex(envelope.get("envelope_digest"), HEX64, "NODE_AUTHORITY_ENVELOPE_DIGEST_INVALID")
    envelope_core = {key: envelope[key] for key in envelope if key != "envelope_digest"}
    _require(
        canonical_sha256(envelope_core) == envelope_digest,
        "NODE_AUTHORITY_ENVELOPE_DIGEST_RECOMPUTE_MISMATCH",
    )

    node_id = _nonempty(packet.get("source_node_id"), "SOURCE_NODE_ID_REQUIRED")
    producer_pid = packet.get("producer_pid")
    _require(isinstance(producer_pid, int) and producer_pid > 0, "PRODUCER_PID_INVALID")
    payload = _mapping(packet.get("payload"), "NODE_RESULT_PAYLOAD_REQUIRED")
    _require(payload.get("process_pid") == producer_pid, "PRODUCER_PID_PAYLOAD_MISMATCH")

    membership_id = _nonempty(envelope.get("source_membership_id"), "SOURCE_MEMBERSHIP_ID_REQUIRED")
    membership = _mapping(envelope.get("membership_receipt"), "MEMBERSHIP_RECEIPT_REQUIRED")
    _require(membership.get("membership_id") == membership_id, "MEMBERSHIP_RECEIPT_ID_MISMATCH")
    _require(membership.get("node_id") == node_id, "MEMBERSHIP_RECEIPT_NODE_MISMATCH")
    _require(envelope.get("producer_pid") == producer_pid, "NODE_AUTHORITY_PRODUCER_PID_MISMATCH")

    generation = packet.get("generation")
    _require(isinstance(generation, int) and generation >= 0, "NODE_RESULT_GENERATION_INVALID")
    return {
        "node_result_packet_digest": packet_digest,
        "node_authority_envelope_digest": envelope_digest,
        "source_node_id": node_id,
        "source_membership_id": membership_id,
        "producer_pid": producer_pid,
        "runtime_generation": generation,
    }


def validate_controller_lineage(
    lineage: Mapping[str, Any],
    *,
    expected_controller_lineage_sha256: str,
    node: Mapping[str, Any],
    call: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate a precommitted controller-owned event->route->engine->cell->call binding."""
    _hex(expected_controller_lineage_sha256, HEX64, "EXPECTED_CONTROLLER_LINEAGE_SHA256_INVALID")
    _require(lineage.get("schema") == CONTROLLER_LINEAGE_SCHEMA, "CONTROLLER_LINEAGE_SCHEMA_MISMATCH")
    observed = canonical_sha256(dict(lineage))
    _require(observed == expected_controller_lineage_sha256, "CONTROLLER_LINEAGE_COMMITMENT_MISMATCH")

    for key in ("causal_event_id", "admission_id", "grid_cell_id"):
        _nonempty(lineage.get(key), f"{key.upper()}_REQUIRED")
    for key in (
        "route_decision_identity_sha256",
        "resolved_engine_identity_sha256",
        "grid_plan_identity_sha256",
        "raw_node_result_packet_digest",
        "node_authority_envelope_digest",
        "source_bound_model_call_identity_sha256",
        "model_output_identity_sha256",
        "source_identity_sha256",
    ):
        _hex(lineage.get(key), HEX64, f"{key.upper()}_INVALID")
    _hex(lineage.get("source_head_sha"), HEX40, "SOURCE_HEAD_SHA_INVALID")
    _hex(lineage.get("source_tree_sha"), HEX40, "SOURCE_TREE_SHA_INVALID")

    _require(lineage.get("controller_observed_node_id") == node["source_node_id"], "CALL_NODE_BINDING_MISMATCH")
    _require(lineage.get("source_membership_id") == node["source_membership_id"], "CALL_MEMBERSHIP_BINDING_MISMATCH")
    _require(lineage.get("producer_pid") == node["producer_pid"], "CALL_PROCESS_BINDING_MISMATCH")
    _require(lineage.get("runtime_generation") == node["runtime_generation"], "CALL_GENERATION_BINDING_MISMATCH")
    _require(
        lineage.get("raw_node_result_packet_digest") == node["node_result_packet_digest"],
        "CALL_PACKET_BINDING_MISMATCH",
    )
    _require(
        lineage.get("node_authority_envelope_digest") == node["node_authority_envelope_digest"],
        "CALL_NODE_AUTHORITY_ENVELOPE_BINDING_MISMATCH",
    )
    _require(
        lineage.get("source_bound_model_call_identity_sha256")
        == call["source_bound_model_call_identity_sha256"],
        "MODEL_CALL_REFERENCE_TRANSPLANT_REJECTED",
    )
    _require(
        lineage.get("model_output_identity_sha256") == call["model_output_identity_sha256"],
        "MODEL_OUTPUT_IDENTITY_MISMATCH_WITH_REFERENCED_CALL",
    )
    _require(lineage.get("source_identity_sha256") == call["source_identity_sha256"], "SOURCE_IDENTITY_TRANSPLANT_REJECTED")
    _require(lineage.get("source_head_sha") == call["source_head_sha"], "SOURCE_HEAD_TRANSPLANT_REJECTED")
    _require(lineage.get("source_tree_sha") == call["source_tree_sha"], "SOURCE_TREE_TRANSPLANT_REJECTED")

    return {
        **dict(lineage),
        "controller_lineage_sha256": observed,
    }


def gate_lineage(
    node_authority_envelope: Mapping[str, Any],
    model_call_receipt: Mapping[str, Any],
    controller_lineage: Mapping[str, Any],
    *,
    expected_model_call_identity_sha256: str,
    expected_controller_lineage_sha256: str,
) -> dict[str, Any]:
    """Bind one immutable NODE_RESULT authority envelope to one pre-existing exact call identity."""
    node = validate_node_authority_envelope(node_authority_envelope)
    call = validate_model_call_receipt(
        model_call_receipt,
        expected_model_call_identity_sha256=expected_model_call_identity_sha256,
    )
    lineage = validate_controller_lineage(
        controller_lineage,
        expected_controller_lineage_sha256=expected_controller_lineage_sha256,
        node=node,
        call=call,
    )

    authority = {
        "schema": LINEAGE_ENVELOPE_SCHEMA,
        "causal_event_id": lineage["causal_event_id"],
        "admission_id": lineage["admission_id"],
        "route_decision_identity_sha256": lineage["route_decision_identity_sha256"],
        "resolved_engine_identity_sha256": lineage["resolved_engine_identity_sha256"],
        "grid_plan_identity_sha256": lineage["grid_plan_identity_sha256"],
        "grid_cell_id": lineage["grid_cell_id"],
        "controller_observed_node_id": node["source_node_id"],
        "source_membership_id": node["source_membership_id"],
        "producer_pid": node["producer_pid"],
        "runtime_generation": node["runtime_generation"],
        "raw_node_result_packet_digest": node["node_result_packet_digest"],
        "node_authority_envelope_digest": node["node_authority_envelope_digest"],
        "source_bound_model_call_identity_sha256": call["source_bound_model_call_identity_sha256"],
        "model_output_identity_sha256": call["model_output_identity_sha256"],
        "source_identity_sha256": call["source_identity_sha256"],
        "source_head_sha": call["source_head_sha"],
        "source_tree_sha": call["source_tree_sha"],
        "controller_lineage_sha256": lineage["controller_lineage_sha256"],
        "model_generated": False,
        "s0_truth": False,
        "effect_authority": False,
    }
    return {
        "schema": SCHEMA,
        "pass": True,
        "status": "PASS_SOURCE_ONLY_LINEAGE_COMPONENT",
        "source_bound_model_call_identity_sha256": call["source_bound_model_call_identity_sha256"],
        "model_output_identity_sha256": call["model_output_identity_sha256"],
        "node_result_packet_digest": node["node_result_packet_digest"],
        "node_authority_envelope_digest": node["node_authority_envelope_digest"],
        "controller_lineage_sha256": lineage["controller_lineage_sha256"],
        "grid_plan_identity_sha256": lineage["grid_plan_identity_sha256"],
        "grid_cell_id": lineage["grid_cell_id"],
        "controller_observed_node_id": node["source_node_id"],
        "lineage_authority_envelope": authority,
        "lineage_authority_envelope_digest": canonical_sha256(authority),
        "credit_boundary": {
            "checkpoint_selection_credit": 0,
            "physical_grid10_runtime_credit": 0,
            "jspace_model_credit": 0,
            "training_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
        },
    }


def validate_lineage_bound_cohort(results: Sequence[Mapping[str, Any]], *, expected_member_count: int) -> dict[str, Any]:
    """Deterministically fail the whole cohort if any member lacks a valid lineage-gate result."""
    _require(expected_member_count > 0, "EXPECTED_MEMBER_COUNT_INVALID")
    _require(len(results) == expected_member_count, "LINEAGE_COHORT_MEMBER_COUNT_INVALID")
    for result in results:
        _require(result.get("schema") == SCHEMA, "LINEAGE_COHORT_MEMBER_SCHEMA_INVALID")
        _require(result.get("pass") is True, "LINEAGE_COHORT_MEMBER_NOT_PASS")
        authority = _mapping(result.get("lineage_authority_envelope"), "LINEAGE_COHORT_AUTHORITY_ENVELOPE_REQUIRED")
        digest = _hex(
            result.get("lineage_authority_envelope_digest"),
            HEX64,
            "LINEAGE_COHORT_AUTHORITY_ENVELOPE_DIGEST_INVALID",
        )
        _require(canonical_sha256(dict(authority)) == digest, "LINEAGE_COHORT_AUTHORITY_ENVELOPE_DIGEST_MISMATCH")

    plan_ids = {result.get("grid_plan_identity_sha256") for result in results}
    _require(len(plan_ids) == 1, "LINEAGE_COHORT_GRID_PLAN_MISMATCH")
    for field, code in (
        ("grid_cell_id", "LINEAGE_COHORT_DUPLICATE_GRID_CELL"),
        ("controller_observed_node_id", "LINEAGE_COHORT_DUPLICATE_NODE"),
        ("node_result_packet_digest", "LINEAGE_COHORT_DUPLICATE_PACKET"),
        ("lineage_authority_envelope_digest", "LINEAGE_COHORT_DUPLICATE_AUTHORITY_ENVELOPE"),
    ):
        _require(len({result.get(field) for result in results}) == expected_member_count, code)

    ordered = sorted(
        (
            {
                "grid_cell_id": result["grid_cell_id"],
                "controller_observed_node_id": result["controller_observed_node_id"],
                "node_result_packet_digest": result["node_result_packet_digest"],
                "source_bound_model_call_identity_sha256": result["source_bound_model_call_identity_sha256"],
                "lineage_authority_envelope_digest": result["lineage_authority_envelope_digest"],
            }
            for result in results
        ),
        key=lambda x: (x["grid_cell_id"], x["controller_observed_node_id"], x["node_result_packet_digest"]),
    )
    envelope = {
        "schema": COHORT_SCHEMA,
        "grid_plan_identity_sha256": next(iter(plan_ids)),
        "member_count": expected_member_count,
        "members": ordered,
    }
    return {
        "schema": COHORT_SCHEMA,
        "pass": True,
        "cohort_lineage_digest": canonical_sha256(envelope),
        "envelope": envelope,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--node-authority-envelope", type=Path, required=True)
    p.add_argument("--model-call-receipt", type=Path, required=True)
    p.add_argument("--controller-lineage", type=Path, required=True)
    p.add_argument("--expected-model-call-identity-sha256", required=True)
    p.add_argument("--expected-controller-lineage-sha256", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)

    try:
        result = gate_lineage(
            json.loads(args.node_authority_envelope.read_text(encoding="utf-8")),
            json.loads(args.model_call_receipt.read_text(encoding="utf-8")),
            json.loads(args.controller_lineage.read_text(encoding="utf-8")),
            expected_model_call_identity_sha256=args.expected_model_call_identity_sha256,
            expected_controller_lineage_sha256=args.expected_controller_lineage_sha256,
        )
    except Exception as exc:
        result = {
            "schema": SCHEMA,
            "pass": False,
            "status": "FAIL_CLOSED",
            "failure": f"{type(exc).__name__}:{exc}",
            "credit_boundary": {
                "checkpoint_selection_credit": 0,
                "physical_grid10_runtime_credit": 0,
                "jspace_model_credit": 0,
                "training_credit": 0,
                "whole_hcu_runtime_credit": 0,
                "whole_entityos_runtime_credit": 0,
            },
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result.get("pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
