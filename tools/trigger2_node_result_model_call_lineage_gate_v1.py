#!/usr/bin/env python3
"""Trigger-2 SOURCE-ONLY NODE_RESULT -> model-call lineage binding gate.

This successor does not execute a model/provider and does not mint runtime, J-Space,
training, HCU, or EntityOS credit. It reuses the already-existing source-bound model
call identity from CLAY_TRIGGER2_MODEL_CALL_REPOSITORY_BOUND_GATE/v1 and binds that
identity plus model-output identity into a NODE_RESULT/v1 packet. Route/engine/cell
identity is accepted only through an independently precommitted chain digest.

No second model-call ID authority is introduced: this module never derives a new call ID.
It only references the upstream source_bound_model_call_identity_sha256 verbatim.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Mapping

SCHEMA = "CLAY_TRIGGER2_NODE_RESULT_MODEL_CALL_LINEAGE_GATE/v1"
LINEAGE_SCHEMA = "CLAY_TRIGGER2_NODE_RESULT_MODEL_CALL_LINEAGE/v1"
CHAIN_SCHEMA = "CLAY_TRIGGER2_ROUTE_ENGINE_CELL_CHAIN/v1"
NODE_RESULT_SCHEMA = "NODE_RESULT/v1"
CALL_GATE_SCHEMA = "CLAY_TRIGGER2_MODEL_CALL_REPOSITORY_BOUND_GATE/v1"
CALL_GATE_STATUS = "PASS_SOURCE_BOUND_CALL_IDENTITY_COMPONENT_ONLY"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class LineageError(RuntimeError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise LineageError(code)


def _mapping(value: Any, code: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), code)
    return value


def _hex64(value: Any, code: str) -> str:
    _require(isinstance(value, str) and bool(HEX64.fullmatch(value)), code)
    return value


def _packet_core(packet: Mapping[str, Any]) -> dict[str, Any]:
    return {k: packet[k] for k in packet if k not in ("packet_digest", "s1_write_intent")}


def _validate_node_result(packet: Mapping[str, Any], *, allow_lineage: bool) -> None:
    _require(packet.get("schema") == NODE_RESULT_SCHEMA, "NODE_RESULT_SCHEMA_MISMATCH")
    _require(packet.get("source_kind") == "ORDINARY_NODE", "NODE_RESULT_SOURCE_KIND_MISMATCH")
    _require(packet.get("s1_write_intent") is False, "NODE_RESULT_S1_WRITE_INTENT_INVALID")
    _require(isinstance(packet.get("source_node_id"), str) and packet.get("source_node_id"), "NODE_RESULT_SOURCE_NODE_ID_REQUIRED")
    _require(isinstance(packet.get("scope"), str) and packet.get("scope"), "NODE_RESULT_SCOPE_REQUIRED")
    _require(isinstance(packet.get("generation"), int), "NODE_RESULT_GENERATION_REQUIRED")
    _require(isinstance(packet.get("state_epoch"), int), "NODE_RESULT_STATE_EPOCH_REQUIRED")
    _hex64(packet.get("state_digest"), "NODE_RESULT_STATE_DIGEST_INVALID")
    payload = _mapping(packet.get("payload"), "NODE_RESULT_PAYLOAD_REQUIRED")
    _require(isinstance(payload.get("task_id"), str) and payload.get("task_id"), "NODE_RESULT_TASK_ID_REQUIRED")
    if not allow_lineage:
        _require("model_call_lineage" not in payload, "NODE_RESULT_LINEAGE_ALREADY_PRESENT")
    _hex64(packet.get("packet_digest"), "NODE_RESULT_PACKET_DIGEST_INVALID")
    _require(packet.get("packet_digest") == canonical_sha256(_packet_core(packet)), "NODE_RESULT_PACKET_DIGEST_MISMATCH")


def _validate_call_gate(receipt: Mapping[str, Any], *, expected_sha256: str) -> dict[str, str]:
    _hex64(expected_sha256, "EXPECTED_CALL_GATE_RECEIPT_SHA256_INVALID")
    _require(receipt.get("schema") == CALL_GATE_SCHEMA, "CALL_GATE_SCHEMA_MISMATCH")
    _require(receipt.get("pass") is True, "CALL_GATE_NOT_PASS")
    _require(receipt.get("status") == CALL_GATE_STATUS, "CALL_GATE_STATUS_MISMATCH")
    observed = canonical_sha256(dict(receipt))
    _require(observed == expected_sha256, "CALL_GATE_RECEIPT_COMMITMENT_MISMATCH")
    call_id = _hex64(receipt.get("source_bound_model_call_identity_sha256"), "MODEL_CALL_IDENTITY_INVALID")
    output_id = _hex64(receipt.get("model_output_identity_sha256"), "MODEL_OUTPUT_IDENTITY_INVALID")
    source = _mapping(receipt.get("source_identity"), "CALL_GATE_SOURCE_IDENTITY_REQUIRED")
    source_id = _hex64(source.get("source_identity_sha256"), "SOURCE_IDENTITY_SHA256_INVALID")
    return {
        "call_gate_receipt_sha256": observed,
        "model_call_identity_sha256": call_id,
        "model_output_identity_sha256": output_id,
        "source_identity_sha256": source_id,
    }


def _validate_chain(chain: Mapping[str, Any], *, expected_sha256: str) -> dict[str, str]:
    _hex64(expected_sha256, "EXPECTED_ROUTE_ENGINE_CELL_CHAIN_SHA256_INVALID")
    _require(chain.get("schema") == CHAIN_SCHEMA, "ROUTE_ENGINE_CELL_CHAIN_SCHEMA_MISMATCH")
    _require(chain.get("authority_semantics") == "REFERENCE_ONLY_NO_EFFECT_OR_TRUTH_AUTHORITY", "ROUTE_ENGINE_CELL_CHAIN_AUTHORITY_SEMANTICS_INVALID")
    route_id = _hex64(chain.get("route_identity_sha256"), "ROUTE_IDENTITY_SHA256_INVALID")
    engine_id = _hex64(chain.get("engine_identity_sha256"), "ENGINE_IDENTITY_SHA256_INVALID")
    cell_id = _hex64(chain.get("cell_identity_sha256"), "CELL_IDENTITY_SHA256_INVALID")
    observed = canonical_sha256(dict(chain))
    _require(observed == expected_sha256, "ROUTE_ENGINE_CELL_CHAIN_COMMITMENT_MISMATCH")
    return {
        "route_engine_cell_chain_sha256": observed,
        "route_identity_sha256": route_id,
        "engine_identity_sha256": engine_id,
        "cell_identity_sha256": cell_id,
    }


def _expected_lineage(
    base_packet: Mapping[str, Any],
    call_info: Mapping[str, str],
    chain_info: Mapping[str, str],
) -> dict[str, Any]:
    payload = _mapping(base_packet.get("payload"), "NODE_RESULT_PAYLOAD_REQUIRED")
    return {
        "schema": LINEAGE_SCHEMA,
        "base_node_result_packet_digest": base_packet["packet_digest"],
        "source_node_id": base_packet["source_node_id"],
        "scope": base_packet["scope"],
        "generation": base_packet["generation"],
        "state_epoch": base_packet["state_epoch"],
        "state_digest": base_packet["state_digest"],
        "task_id": payload["task_id"],
        "call_gate_receipt_sha256": call_info["call_gate_receipt_sha256"],
        "source_identity_sha256": call_info["source_identity_sha256"],
        "model_call_identity_sha256": call_info["model_call_identity_sha256"],
        "model_output_identity_sha256": call_info["model_output_identity_sha256"],
        "route_engine_cell_chain_sha256": chain_info["route_engine_cell_chain_sha256"],
        "route_identity_sha256": chain_info["route_identity_sha256"],
        "engine_identity_sha256": chain_info["engine_identity_sha256"],
        "cell_identity_sha256": chain_info["cell_identity_sha256"],
        "identity_semantics": "REFERENCE_EXISTING_CALL_ID_NO_SECOND_CALL_AUTHORITY",
    }


def bind_node_result(
    packet: Mapping[str, Any],
    call_gate_receipt: Mapping[str, Any],
    route_engine_cell_chain: Mapping[str, Any],
    *,
    expected_call_gate_receipt_sha256: str,
    expected_route_engine_cell_chain_sha256: str,
) -> dict[str, Any]:
    """Return a new NODE_RESULT/v1 carrying exact precommitted model-call lineage."""
    _validate_node_result(packet, allow_lineage=False)
    call_info = _validate_call_gate(call_gate_receipt, expected_sha256=expected_call_gate_receipt_sha256)
    chain_info = _validate_chain(route_engine_cell_chain, expected_sha256=expected_route_engine_cell_chain_sha256)

    base = dict(packet)
    lineage = _expected_lineage(base, call_info, chain_info)
    lineage["lineage_identity_sha256"] = canonical_sha256(lineage)

    payload = dict(_mapping(base["payload"], "NODE_RESULT_PAYLOAD_REQUIRED"))
    payload["model_call_lineage"] = lineage
    bound = {k: base[k] for k in base if k not in ("packet_digest", "payload")}
    bound["payload"] = payload
    core = _packet_core(bound)
    bound["packet_digest"] = canonical_sha256(core)
    bound["s1_write_intent"] = False
    return bound


def validate_bound_node_result(
    packet: Mapping[str, Any],
    call_gate_receipt: Mapping[str, Any],
    route_engine_cell_chain: Mapping[str, Any],
    *,
    expected_call_gate_receipt_sha256: str,
    expected_route_engine_cell_chain_sha256: str,
) -> dict[str, Any]:
    """Fail closed on call/output/source/route/engine/cell or base-packet transplants."""
    _validate_node_result(packet, allow_lineage=True)
    call_info = _validate_call_gate(call_gate_receipt, expected_sha256=expected_call_gate_receipt_sha256)
    chain_info = _validate_chain(route_engine_cell_chain, expected_sha256=expected_route_engine_cell_chain_sha256)

    payload = dict(_mapping(packet["payload"], "NODE_RESULT_PAYLOAD_REQUIRED"))
    lineage = dict(_mapping(payload.get("model_call_lineage"), "MODEL_CALL_LINEAGE_REQUIRED"))
    claimed_lineage_identity = _hex64(lineage.get("lineage_identity_sha256"), "LINEAGE_IDENTITY_SHA256_INVALID")

    payload.pop("model_call_lineage", None)
    base = {k: packet[k] for k in packet if k not in ("packet_digest", "payload")}
    base["payload"] = payload
    base_core = _packet_core(base)
    base["packet_digest"] = canonical_sha256(base_core)
    base["s1_write_intent"] = False
    _validate_node_result(base, allow_lineage=False)

    expected = _expected_lineage(base, call_info, chain_info)
    expected_identity = canonical_sha256(expected)
    _require(claimed_lineage_identity == expected_identity, "MODEL_CALL_LINEAGE_IDENTITY_MISMATCH")
    _require(lineage == {**expected, "lineage_identity_sha256": expected_identity}, "MODEL_CALL_LINEAGE_TRANSPLANT_OR_MUTATION")

    return {
        "schema": SCHEMA,
        "pass": True,
        "status": "PASS_SOURCE_ONLY_NODE_RESULT_CALL_LINEAGE",
        "bound_node_result_packet_digest": packet["packet_digest"],
        "base_node_result_packet_digest": base["packet_digest"],
        "lineage_identity_sha256": expected_identity,
        "model_call_identity_sha256": call_info["model_call_identity_sha256"],
        "model_output_identity_sha256": call_info["model_output_identity_sha256"],
        "route_engine_cell_chain_sha256": chain_info["route_engine_cell_chain_sha256"],
        "credit_boundary": {
            "checkpoint_selection_credit": 0,
            "jspace_model_credit": 0,
            "training_credit": 0,
            "physical_grid10_runtime_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
        },
    }
