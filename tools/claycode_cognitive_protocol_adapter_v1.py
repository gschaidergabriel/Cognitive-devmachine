#!/usr/bin/env python3
"""Model-free ClayCode cognitive protocol adapter for the variable EntityOS/HCU grid.

This is a deterministic component adapter, not a model runtime and not a new authority.
It preserves the canonical COGNITIVE_PROCESS_ABI/v1 identity/state/effect boundaries
while giving variable-grid work a compact replayable ClayCode wire projection.

Wire identity is deliberately distinct from semantic identity:
  CLAYCODE-CP/1\n<sorted compact JSON>\n
No provider, Claude Code, network, model, real-effect or canonical DB write is performed
by this adapter. The existing deterministic DB authority and EffectGate/EffectJournal
remain authoritative.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

PROTOCOL_SCHEMA = "CLAYCODE_COGNITIVE_PROTOCOL/v1"
WIRE_PREFIX = b"CLAYCODE-CP/1\n"
WORK_SCHEMA = "CLAYCODE_COGNITIVE_WORK/v1"
RESULT_SCHEMA = "CLAYCODE_COGNITIVE_RESULT/v1"
PLACEMENT_SCHEMA = "STATE_PLACEMENT_DECISION/v1"
CLAUDE_REQUEST_SCHEMA = "CLAUDE_CODE_BRIDGE_PACKET/v1"
CLAUDE_RESULT_SCHEMA = "CLAUDE_CODE_BRIDGE_PACKET/v1"
REENTRY_SCHEMA = "WORKSPACE_REENTRY/v1"

WORK_FIELDS = {
    "schema", "protocol", "causal_event_id", "admission_id", "entry_event_sha256",
    "entry_admission_sha256", "generation", "workspace_epoch", "process_id",
    "state_snapshot_ref", "payload", "capability_scope_ref", "resource_budget",
    "epistemic_inputs", "op_id", "op_semantics_hash",
}
ALLOWED_EPISTEMIC = {"OBSERVED", "INFERRED", "HYPOTHESIS", "UNKNOWN"}
ALLOWED_CLAUDE_INTERFACE = {"TEXT", "STRUCTURED_TEXT", "TOOL_PROTOCOL", "SESSION_STATE_EXPOSED", "OTHER_EXPLICITLY_OBSERVED"}


class ClayCodeProtocolError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_text(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value.lower() != value:
        raise ClayCodeProtocolError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if any(ch not in "0123456789abcdef" for ch in value):
        raise ClayCodeProtocolError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ClayCodeProtocolError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ClayCodeProtocolError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def trusted_op_semantics_hash() -> str:
    """Hash trusted adapter semantics, never a model-declared effect footprint."""
    return sha256_text({
        "op_id": "entityos.cognition.execute",
        "version": 1,
        "authority": "READ_OR_PROPOSE_ONLY",
        "canonical_db_write": False,
        "real_effect_execution": False,
        "process_identity_independent_of_grid_n": True,
        "typed_entry_digest_binding_required": True,
    })


def make_work_packet(
    *,
    causal_event_id: str,
    admission_id: str,
    entry_event_sha256: str,
    entry_admission_sha256: str,
    generation: int,
    workspace_epoch: int,
    process_id: str,
    state_snapshot_ref: str,
    payload: Any,
    capability_scope_ref: str,
    resource_budget: Mapping[str, int],
    epistemic_inputs: list[dict[str, Any]],
) -> dict[str, Any]:
    _nonempty(causal_event_id, "causal_event_id")
    _nonempty(admission_id, "admission_id")
    _sha256(entry_event_sha256, "entry_event_sha256")
    _sha256(entry_admission_sha256, "entry_admission_sha256")
    _nonnegative_int(generation, "generation")
    _nonnegative_int(workspace_epoch, "workspace_epoch")
    process_id = _nonempty(process_id, "process_id")
    if not process_id.startswith("ZECP") or len(process_id) != 6 or not process_id[4:].isdigit():
        raise ClayCodeProtocolError("process_id:ZECP_ID_REQUIRED")
    _nonempty(state_snapshot_ref, "state_snapshot_ref")
    _nonempty(capability_scope_ref, "capability_scope_ref")
    if not isinstance(resource_budget, Mapping) or any(
        isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in resource_budget.values()
    ):
        raise ClayCodeProtocolError("resource_budget:NONNEGATIVE_INTEGER_MAP_REQUIRED")
    if not isinstance(epistemic_inputs, list):
        raise ClayCodeProtocolError("epistemic_inputs:LIST_REQUIRED")
    for item in epistemic_inputs:
        if not isinstance(item, dict) or item.get("status") not in ALLOWED_EPISTEMIC:
            raise ClayCodeProtocolError("epistemic_inputs:STATUS_REQUIRED")

    packet = {
        "schema": WORK_SCHEMA,
        "protocol": PROTOCOL_SCHEMA,
        "causal_event_id": causal_event_id,
        "admission_id": admission_id,
        "entry_event_sha256": entry_event_sha256,
        "entry_admission_sha256": entry_admission_sha256,
        "generation": generation,
        "workspace_epoch": workspace_epoch,
        "process_id": process_id,
        "state_snapshot_ref": state_snapshot_ref,
        "payload": payload,
        "capability_scope_ref": capability_scope_ref,
        "resource_budget": dict(resource_budget),
        "epistemic_inputs": epistemic_inputs,
        "op_id": "entityos.cognition.execute",
        "op_semantics_hash": trusted_op_semantics_hash(),
    }
    # Deliberately excludes grid N, executor/lease identity and wire bytes.
    packet["semantic_hash"] = semantic_hash(packet)
    return packet


def semantic_hash(packet: Mapping[str, Any]) -> str:
    basis = {k: packet[k] for k in sorted(WORK_FIELDS) if k in packet}
    if set(basis) != WORK_FIELDS:
        missing = sorted(WORK_FIELDS - set(basis))
        raise ClayCodeProtocolError(f"WORK_FIELDS_MISSING:{','.join(missing)}")
    return sha256_text(basis)


def serialize_work(packet: Mapping[str, Any]) -> bytes:
    parsed = validate_work_packet(dict(packet))
    wire_value = dict(parsed)
    wire_value["wire_profile"] = "SORTED_COMPACT_JSON/v1"
    wire_value["wire_sha256"] = "0" * 64
    provisional = WIRE_PREFIX + canonical_json(wire_value).encode("utf-8") + b"\n"
    wire_value["wire_sha256"] = hashlib.sha256(provisional).hexdigest()
    return WIRE_PREFIX + canonical_json(wire_value).encode("utf-8") + b"\n"


def parse_work(wire: bytes) -> dict[str, Any]:
    if not isinstance(wire, (bytes, bytearray)) or not bytes(wire).startswith(WIRE_PREFIX):
        raise ClayCodeProtocolError("WIRE_PREFIX_INVALID")
    body = bytes(wire)[len(WIRE_PREFIX):]
    if not body.endswith(b"\n"):
        raise ClayCodeProtocolError("WIRE_NEWLINE_REQUIRED")
    try:
        value = json.loads(body[:-1].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClayCodeProtocolError("WIRE_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise ClayCodeProtocolError("WIRE_OBJECT_REQUIRED")
    if value.pop("wire_profile", None) != "SORTED_COMPACT_JSON/v1":
        raise ClayCodeProtocolError("WIRE_PROFILE_INVALID")
    wire_sha = value.pop("wire_sha256", None)
    _sha256(wire_sha, "wire_sha256")
    provisional_value = dict(value)
    provisional_value["wire_profile"] = "SORTED_COMPACT_JSON/v1"
    provisional_value["wire_sha256"] = "0" * 64
    expected_wire_sha = hashlib.sha256(
        WIRE_PREFIX + canonical_json(provisional_value).encode("utf-8") + b"\n"
    ).hexdigest()
    if wire_sha != expected_wire_sha:
        raise ClayCodeProtocolError("WIRE_SHA256_MISMATCH")
    return validate_work_packet(value)


def validate_work_packet(packet: dict[str, Any]) -> dict[str, Any]:
    expected = WORK_FIELDS | {"semantic_hash"}
    if set(packet) != expected:
        raise ClayCodeProtocolError("WORK_PACKET_FIELDS_INVALID")
    if packet.get("schema") != WORK_SCHEMA or packet.get("protocol") != PROTOCOL_SCHEMA:
        raise ClayCodeProtocolError("WORK_PACKET_SCHEMA_INVALID")
    _sha256(packet.get("entry_event_sha256"), "entry_event_sha256")
    _sha256(packet.get("entry_admission_sha256"), "entry_admission_sha256")
    _nonnegative_int(packet.get("generation"), "generation")
    _nonnegative_int(packet.get("workspace_epoch"), "workspace_epoch")
    if packet.get("op_id") != "entityos.cognition.execute":
        raise ClayCodeProtocolError("OP_ID_INVALID")
    if packet.get("op_semantics_hash") != trusted_op_semantics_hash():
        raise ClayCodeProtocolError("OP_SEMANTICS_HASH_MISMATCH")
    expected_semantic = semantic_hash(packet)
    if packet.get("semantic_hash") != expected_semantic:
        raise ClayCodeProtocolError("SEMANTIC_HASH_MISMATCH")
    return dict(packet)


def execute_on_grid(runtime: Any, packet: Mapping[str, Any], *, current_generation: int) -> dict[str, Any]:
    work = validate_work_packet(dict(packet))
    if work["generation"] != current_generation:
        raise ClayCodeProtocolError("STALE_GENERATION")
    # Exact identity/state references are part of the cognitive payload that the existing
    # variable-grid runtime hashes; N remains outside this semantic basis.
    runtime_payload = {
        "clay_semantic_hash": work["semantic_hash"],
        "entry_event_sha256": work["entry_event_sha256"],
        "entry_admission_sha256": work["entry_admission_sha256"],
        "state_snapshot_ref": work["state_snapshot_ref"],
        "workspace_epoch": work["workspace_epoch"],
        "payload": work["payload"],
    }
    queued = runtime.enqueue(work["process_id"], runtime_payload)
    raw_result = runtime.execute(queued)
    return {
        "schema": RESULT_SCHEMA,
        "protocol": PROTOCOL_SCHEMA,
        "causal_event_id": work["causal_event_id"],
        "admission_id": work["admission_id"],
        "entry_event_sha256": work["entry_event_sha256"],
        "entry_admission_sha256": work["entry_admission_sha256"],
        "generation": work["generation"],
        "workspace_epoch": work["workspace_epoch"],
        "process_id": work["process_id"],
        "state_snapshot_ref": work["state_snapshot_ref"],
        "clay_semantic_hash": work["semantic_hash"],
        "runtime_result": raw_result,
        "result_class": "CANDIDATE",
        "canonical_truth": False,
        "canonical_db_write": False,
        "real_effect_authority": False,
    }


def classify_state(
    *, entry_event_sha256: str, generation: int, datum_ref: str,
    durable: bool, exact: bool, queryable: bool, restart_surviving: bool,
    epistemic_status: str, shared_workspace: bool = True,
) -> dict[str, Any]:
    _sha256(entry_event_sha256, "entry_event_sha256")
    _nonnegative_int(generation, "generation")
    if epistemic_status not in ALLOWED_EPISTEMIC:
        raise ClayCodeProtocolError("epistemic_status:INVALID")
    selected = "DATABASE_S0" if (durable or restart_surviving or (exact and queryable)) else (
        "WORKSPACE_S1" if shared_workspace else "LOCAL_EPHEMERAL_S2"
    )
    decision_basis = {
        "entry_event_sha256": entry_event_sha256,
        "generation": generation,
        "datum_ref": datum_ref,
        "durable": durable,
        "exact": exact,
        "queryable": queryable,
        "restart_surviving": restart_surviving,
        "epistemic_status": epistemic_status,
        "selected_plane": selected,
    }
    return {
        "schema": PLACEMENT_SCHEMA,
        "placement_id": "place-" + sha256_text(decision_basis)[:24],
        **decision_basis,
        "canonical_write": False,
        "canonical_fact": False,
        "requires_deterministic_admission": selected == "DATABASE_S0",
    }


def claude_bridge_request(work: Mapping[str, Any], *, interface_class: str, payload: Any) -> dict[str, Any]:
    work = validate_work_packet(dict(work))
    if interface_class not in ALLOWED_CLAUDE_INTERFACE:
        raise ClayCodeProtocolError("CLAUDE_INTERFACE_CLASS_INVALID")
    request = {
        "schema": CLAUDE_REQUEST_SCHEMA,
        "direction": "GRID_TO_CLAUDE",
        "entry_event_sha256": work["entry_event_sha256"],
        "entry_admission_sha256": work["entry_admission_sha256"],
        "generation": work["generation"],
        "work_id": work["semantic_hash"],
        "workspace_epoch": work["workspace_epoch"],
        "interface_class": interface_class,
        "interface_evidence_ref": "EXPOSED_TEXT_TOOL_SESSION_ONLY",
        "payload": payload,
        "activation_access_claimed": False,
        "claude_execution_observed": False,
        "tool_scope_ref": work["capability_scope_ref"],
        "authority": "REQUEST_ONLY",
    }
    request["bridge_id"] = "bridge-" + sha256_text(request)[:24]
    return request


def claude_bridge_stub_result(request: Mapping[str, Any], *, payload: Any) -> dict[str, Any]:
    if request.get("schema") != CLAUDE_REQUEST_SCHEMA or request.get("direction") != "GRID_TO_CLAUDE":
        raise ClayCodeProtocolError("CLAUDE_REQUEST_INVALID")
    return {
        "schema": CLAUDE_RESULT_SCHEMA,
        "direction": "CLAUDE_TO_GRID",
        "bridge_id": request["bridge_id"],
        "entry_event_sha256": request["entry_event_sha256"],
        "entry_admission_sha256": request["entry_admission_sha256"],
        "generation": request["generation"],
        "workspace_epoch": request["workspace_epoch"],
        "interface_class": request["interface_class"],
        "interface_evidence_ref": request["interface_evidence_ref"],
        "payload": payload,
        "activation_access_claimed": False,
        "claude_execution_observed": False,
        "global_jspace_causal_credit": False,
        "authority": "CANDIDATE_ONLY",
    }


def workspace_reentry(result: Mapping[str, Any], bridge_result: Mapping[str, Any]) -> dict[str, Any]:
    for field in ("entry_event_sha256", "entry_admission_sha256", "generation", "workspace_epoch"):
        if result.get(field) != bridge_result.get(field):
            raise ClayCodeProtocolError(f"REENTRY_BINDING_MISMATCH:{field}")
    payload_digest = sha256_text(bridge_result.get("payload"))
    return {
        "schema": REENTRY_SCHEMA,
        "source_result_id": result["runtime_result"]["result_id"],
        "source_process_id": "ZECP14",
        "entry_event_sha256": result["entry_event_sha256"],
        "entry_admission_sha256": result["entry_admission_sha256"],
        "generation": result["generation"],
        "from_workspace_epoch": result["workspace_epoch"],
        "to_workspace_epoch": result["workspace_epoch"] + 1,
        "reentry_payload_ref": "sha256:" + payload_digest,
        "reentry_digest": payload_digest,
        "observed_downstream_change": "UNKNOWN",
        "global_jspace_causal_credit": False,
        "canonical_truth": False,
    }
