#!/usr/bin/env python3
"""Deterministic ClayCode envelope adapter for COGNITIVE_PROCESS_ABI/v1.

This is an executable transport/validation bridge, not a claim that the full cognitive
payload is natively lowered into ClayCode TypedIR yet. The typed ABI payload remains a
canonical deterministic JSON value inside a ClayCode BASE-D V18 candidate envelope; the
actual checked-in ClayCode frontend parses/canonicalizes the envelope and binds its
source/grammar/semantic hashes.

Authority boundary: this adapter cannot grant canonical truth, capability, coordinator,
security, real-effect or Global J-Space causal authority. Model/Claude/provider execution
is outside this component.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from claycode_base_frontend import DEFAULT_GRAMMAR, compile_frontend

ABI_PATH = ROOT / "research_entity/global/COGNITIVE_PROCESS_ABI_v1.json"
PROTOCOL_PATH = ROOT / "research_entity/claycode/cognitive/COGNITIVE_PROCESS_PROTOCOL_v1.clay"
ENVELOPE_SCHEMA = "CLAYCODE_COGNITIVE_ENVELOPE/v1"
PAYLOAD_ENCODING = "DETERMINISTIC_JSON_V1"
SURFACE = "BASE_D_V18_REWARD_RELATIONS_CANDIDATE"

FORBIDDEN_AUTHORITY_KEYS = {
    "canonical_truth",
    "canonical_truth_authority",
    "truth_authority",
    "effect_authority",
    "direct_effect_execution",
    "real_effect_executed",
    "capability_grant",
    "capability_authority",
    "security_authority",
    "coordinator_authority",
    "direct_s0_write",
    "global_jspace_causal_credit",
    "activation_access_claimed",
}


class ClayCodeCognitiveProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class ClayCodeEnvelope:
    schema: str
    packet_kind: str
    packet_digest: str
    payload_encoding: str
    payload_json: str
    clay_source: str
    clay_source_sha256: str
    clay_semantic_hash: str
    clay_grammar_sha256: str


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ClayCodeCognitiveProtocolError(f"NONCANONICAL_PAYLOAD:{exc}") from exc


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ClayCodeCognitiveProtocolError(f"OBJECT_REQUIRED:{path}")
    return value


def _find_forbidden_authority(value: Any, path: str = "$") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in FORBIDDEN_AUTHORITY_KEYS:
                return f"{path}.{key}"
            nested = _find_forbidden_authority(child, f"{path}.{key}")
            if nested:
                return nested
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            nested = _find_forbidden_authority(child, f"{path}[{index}]")
            if nested:
                return nested
    return None


def load_abi() -> dict[str, Any]:
    abi = _load_json(ABI_PATH)
    if abi.get("schema") != "COGNITIVE_PROCESS_ABI/v1":
        raise ClayCodeCognitiveProtocolError("ABI_SCHEMA_DRIFT")
    return abi


def compile_protocol_contract() -> dict[str, Any]:
    source = PROTOCOL_PATH.read_text(encoding="utf-8")
    grammar = DEFAULT_GRAMMAR.read_text(encoding="utf-8")
    return compile_frontend(source, grammar, strict=False)


def validate_packet(packet_kind: str, packet: Mapping[str, Any], abi: dict[str, Any] | None = None) -> dict[str, Any]:
    if type(packet) is not dict:
        raise ClayCodeCognitiveProtocolError("PACKET_EXACT_DICT_REQUIRED")
    abi = abi or load_abi()
    packet_contracts = abi.get("packet_types")
    if type(packet_contracts) is not dict or packet_kind not in packet_contracts:
        raise ClayCodeCognitiveProtocolError(f"PACKET_KIND_UNSUPPORTED:{packet_kind}")
    if packet.get("schema") != packet_kind:
        raise ClayCodeCognitiveProtocolError("PACKET_SCHEMA_KIND_MISMATCH")
    contract = packet_contracts[packet_kind]
    required = contract.get("required")
    if not isinstance(required, list):
        raise ClayCodeCognitiveProtocolError("ABI_REQUIRED_FIELDS_MISSING")
    missing = [field for field in required if field not in packet]
    if missing:
        raise ClayCodeCognitiveProtocolError("PACKET_REQUIRED_FIELDS_MISSING:" + ",".join(missing))

    forbidden = _find_forbidden_authority(packet)
    if forbidden:
        raise ClayCodeCognitiveProtocolError(f"PACKET_AUTHORITY_SMUGGLING:{forbidden}")

    if packet_kind == "COGNITIVE_RESULT_PACKET/v1":
        allowed = set(contract.get("allowed_result_class", []))
        result_class = packet.get("result_class")
        if result_class not in allowed:
            raise ClayCodeCognitiveProtocolError(f"RESULT_CLASS_UNSUPPORTED:{result_class}")
        if result_class == "EFFECT_RECEIPT" and packet.get("process_id") != "ZECP17":
            raise ClayCodeCognitiveProtocolError("NON_ZECP17_EFFECT_RECEIPT_FORBIDDEN")

    if packet_kind == "WORKSPACE_REENTRY/v1":
        value = packet.get("observed_downstream_change")
        if value not in {"TRUE", "FALSE", "UNKNOWN"}:
            raise ClayCodeCognitiveProtocolError("REENTRY_DOWNSTREAM_CHANGE_TRI_STATE_REQUIRED")

    if packet_kind == "CLAUDE_CODE_BRIDGE_PACKET/v1":
        direction = packet.get("direction")
        if direction not in set(contract.get("allowed_direction", [])):
            raise ClayCodeCognitiveProtocolError("CLAUDE_BRIDGE_DIRECTION_UNSUPPORTED")
        interface_class = packet.get("interface_class")
        if interface_class not in set(contract.get("allowed_interface_class", [])):
            raise ClayCodeCognitiveProtocolError("CLAUDE_BRIDGE_INTERFACE_UNSUPPORTED")

    # Canonical JSON generation doubles as a closed scalar/NaN/unsupported-object fence.
    _canonical_json(packet)
    return dict(packet)


def _render_clay_source(packet_kind: str, packet_digest: str, payload_json: str) -> str:
    kind_literal = json.dumps(packet_kind, ensure_ascii=False)
    digest_literal = json.dumps(packet_digest, ensure_ascii=False)
    payload_literal = json.dumps(payload_json, ensure_ascii=False)
    return (
        "module entityos.hcu.cognitive_packet\n"
        "version \"1.0\"\n"
        "status CANDIDATE\n"
        f"metric packet_kind = {kind_literal}\n"
        f"metric packet_digest = {digest_literal}\n"
        f"metric packet_payload = {payload_literal}\n"
        "law packet_payload never_confers canonical_truth\n"
        "law packet_payload never_confers effect_authority\n"
        "law packet_payload never_confers capability_authority\n"
        "law packet_payload never_implies global_jspace_causal_truth\n"
    )


def encode_packet(packet_kind: str, packet: Mapping[str, Any], abi: dict[str, Any] | None = None) -> ClayCodeEnvelope:
    validated = validate_packet(packet_kind, packet, abi)
    payload_json = _canonical_json(validated)
    packet_digest = _sha256_text(payload_json)
    clay_source = _render_clay_source(packet_kind, packet_digest, payload_json)
    grammar = DEFAULT_GRAMMAR.read_text(encoding="utf-8")
    frontend = compile_frontend(clay_source, grammar, strict=False)
    if frontend.get("surface") != "BASE_D_V18_REWARD_RELATIONS":
        raise ClayCodeCognitiveProtocolError("CLAYCODE_FRONTEND_SURFACE_DRIFT")
    return ClayCodeEnvelope(
        schema=ENVELOPE_SCHEMA,
        packet_kind=packet_kind,
        packet_digest=packet_digest,
        payload_encoding=PAYLOAD_ENCODING,
        payload_json=payload_json,
        clay_source=clay_source,
        clay_source_sha256=frontend["source_sha256"],
        clay_semantic_hash=frontend["semantic_hash"],
        clay_grammar_sha256=frontend["grammar_sha256"],
    )


def decode_packet(envelope: ClayCodeEnvelope, abi: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(envelope, ClayCodeEnvelope):
        raise ClayCodeCognitiveProtocolError("ENVELOPE_TYPE_REQUIRED")
    if envelope.schema != ENVELOPE_SCHEMA or envelope.payload_encoding != PAYLOAD_ENCODING:
        raise ClayCodeCognitiveProtocolError("ENVELOPE_SCHEMA_OR_ENCODING_MISMATCH")
    if _sha256_text(envelope.payload_json) != envelope.packet_digest:
        raise ClayCodeCognitiveProtocolError("PAYLOAD_DIGEST_MISMATCH")
    expected_source = _render_clay_source(envelope.packet_kind, envelope.packet_digest, envelope.payload_json)
    if envelope.clay_source != expected_source:
        raise ClayCodeCognitiveProtocolError("CLAY_SOURCE_PAYLOAD_BINDING_MISMATCH")
    grammar = DEFAULT_GRAMMAR.read_text(encoding="utf-8")
    frontend = compile_frontend(envelope.clay_source, grammar, strict=False)
    if frontend["source_sha256"] != envelope.clay_source_sha256:
        raise ClayCodeCognitiveProtocolError("CLAY_SOURCE_IDENTITY_MISMATCH")
    if frontend["semantic_hash"] != envelope.clay_semantic_hash:
        raise ClayCodeCognitiveProtocolError("CLAY_SEMANTIC_IDENTITY_MISMATCH")
    if frontend["grammar_sha256"] != envelope.clay_grammar_sha256:
        raise ClayCodeCognitiveProtocolError("CLAY_GRAMMAR_IDENTITY_MISMATCH")
    try:
        packet = json.loads(envelope.payload_json)
    except json.JSONDecodeError as exc:
        raise ClayCodeCognitiveProtocolError("PAYLOAD_JSON_INVALID") from exc
    return validate_packet(envelope.packet_kind, packet, abi)


def roundtrip(packet_kind: str, packet: Mapping[str, Any], abi: dict[str, Any] | None = None) -> tuple[ClayCodeEnvelope, dict[str, Any]]:
    envelope = encode_packet(packet_kind, packet, abi)
    decoded = decode_packet(envelope, abi)
    if _canonical_json(decoded) != _canonical_json(packet):
        raise ClayCodeCognitiveProtocolError("ROUNDTRIP_SEMANTIC_MISMATCH")
    return envelope, decoded


if __name__ == "__main__":
    result = compile_protocol_contract()
    print(
        json.dumps(
            {
                "schema": "CLAYCODE_COGNITIVE_PROTOCOL_ADAPTER_SELF_CHECK/v1",
                "status": "PASS_SOURCE_CONTRACT_ONLY",
                "protocol_source": str(PROTOCOL_PATH.relative_to(ROOT)),
                "frontend_surface": result["surface"],
                "grammar_sha256": result["grammar_sha256"],
                "semantic_hash": result["semantic_hash"],
                "credit": {
                    "claycode_protocol_source_contract": 1,
                    "native_typed_ir_payload_lowering": 0,
                    "model_runtime": 0,
                    "claude_code_runtime": 0,
                    "global_jspace_causal_runtime": 0,
                    "training": 0,
                },
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
