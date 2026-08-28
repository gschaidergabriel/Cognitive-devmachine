#!/usr/bin/env python3
"""Fail-closed source validator for CLAYCODE_COGNITIVE_PROTOCOL/v1.

Validates exact ClayCode bytes against the bound V18 frontend/grammar and checks
that ClayCode record field names cover the current COGNITIVE_PROCESS_ABI/v1
required fields. This grants source-contract evidence only. It does not execute a
small model, Claude Code, Global J-Space, a real effect, or the whole EntityOS/HCU.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from claycode_base_frontend import compile_frontend

EXPECTED_MANIFEST_SCHEMA = "CLAYCODE_COGNITIVE_PROTOCOL/v1"
EXPECTED_ABI_SCHEMA = "COGNITIVE_PROCESS_ABI/v1"
EXPECTED_FRONTEND_SCHEMA = "ClayCodeBaseFrontendAST/v1"
EXPECTED_FRONTEND_SURFACE = "BASE_D_V18_REWARD_RELATIONS"

ABI_RECORD_MAP = {
    "CognitiveWorkPacket": "COGNITIVE_WORK_PACKET/v1",
    "CognitiveResultPacket": "COGNITIVE_RESULT_PACKET/v1",
    "DBStateRef": "DB_STATE_REF/v1",
    "WorkspaceReentry": "WORKSPACE_REENTRY/v1",
    "ClaudeCodeBridgePacket": "CLAUDE_CODE_BRIDGE_PACKET/v1",
    "GridExecutorBinding": "GRID_EXECUTOR_BINDING/v1",
}

REQUIRED_AUXILIARY_FIELDS = {
    "GridRuntime": {"requested_N", "available_N"},
    "DBWriteProposal": {
        "proposal_id", "source_result_id", "generation", "state_snapshot_ref",
        "object_key", "value_ref", "value_digest", "canonical_commit",
    },
    "EffectProposal": {
        "proposal_id", "source_result_id", "generation", "capability_scope_ref",
        "request_ref", "request_digest", "executed",
    },
    "JSpaceMeasurement": {
        "measurement_id", "causal_event_id", "exact_model_runtime_identity",
        "exposed_interface_class", "observed", "intervened", "measurement_ref",
        "causal_credit",
    },
}


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    require(isinstance(value, dict), f"{path}: JSON object required")
    return value


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    prefix = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(prefix + data).hexdigest()


def parse_record_fields(source: str) -> dict[str, set[str]]:
    records: dict[str, set[str]] = {}
    for match in re.finditer(r"(?ms)^record\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{(.*?)^\}", source):
        name, body = match.group(1), match.group(2)
        fields: set[str] = set()
        for raw in body.splitlines():
            line = raw.strip()
            if not line or line.startswith("//"):
                continue
            field_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*.+$", line)
            require(field_match is not None, f"{name}: invalid record field line: {line!r}")
            fields.add(field_match.group(1))
        require(fields, f"{name}: empty record")
        require(name not in records, f"duplicate record {name}")
        records[name] = fields
    return records


def normalized_laws(source: str) -> set[str]:
    return {
        line.strip()[4:].strip()
        for line in source.splitlines()
        if line.strip().startswith("law ")
    }


def validate(
    manifest: dict[str, Any],
    abi: dict[str, Any],
    protocol_bytes: bytes,
    grammar_bytes: bytes,
) -> dict[str, Any]:
    require(manifest.get("schema") == EXPECTED_MANIFEST_SCHEMA, "manifest schema drift")
    require(abi.get("schema") == EXPECTED_ABI_SCHEMA, "ABI schema drift")

    source = protocol_bytes.decode("utf-8")
    grammar = grammar_bytes.decode("utf-8")
    protocol_binding = manifest.get("protocol_source", {})
    grammar_binding = manifest.get("grammar_dependency", {})
    frontend_binding = manifest.get("frontend_dependency", {})

    require(
        git_blob_sha1(protocol_bytes) == protocol_binding.get("git_blob_sha1"),
        "protocol git blob binding mismatch",
    )
    require(
        sha256_bytes(protocol_bytes) == protocol_binding.get("sha256"),
        "protocol SHA-256 binding mismatch",
    )
    require(
        git_blob_sha1(grammar_bytes) == grammar_binding.get("git_blob_sha1"),
        "grammar git blob binding mismatch",
    )
    require(
        sha256_bytes(grammar_bytes) == grammar_binding.get("sha256"),
        "grammar SHA-256 binding mismatch",
    )
    require(
        frontend_binding.get("frontend_schema") == EXPECTED_FRONTEND_SCHEMA,
        "frontend schema binding drift",
    )
    require(
        frontend_binding.get("surface") == EXPECTED_FRONTEND_SURFACE,
        "frontend surface binding drift",
    )

    compiled = compile_frontend(source, grammar, strict=False)
    require(compiled.get("frontend_schema") == EXPECTED_FRONTEND_SCHEMA, "frontend result schema drift")
    require(compiled.get("surface") == EXPECTED_FRONTEND_SURFACE, "frontend result surface drift")
    require(compiled.get("source_sha256") == protocol_binding.get("sha256"), "frontend source digest drift")
    require(compiled.get("grammar_sha256") == grammar_binding.get("sha256"), "frontend grammar digest drift")
    require(
        compiled.get("semantic_hash") == protocol_binding.get("frontend_semantic_sha256"),
        "frontend semantic hash mismatch",
    )
    require(
        compiled.get("contract_hash") == protocol_binding.get("frontend_contract_sha256"),
        "frontend contract hash mismatch",
    )

    records = parse_record_fields(source)
    declared_records = set(manifest.get("claycode_records", []))
    require(declared_records == set(records), "manifest/source ClayCode record set mismatch")

    packet_types = abi.get("packet_types")
    require(isinstance(packet_types, dict), "ABI packet_types missing")
    mapping = manifest.get("mapping_to_abi", {})
    for record_name, packet_schema in ABI_RECORD_MAP.items():
        require(mapping.get(record_name) == packet_schema, f"manifest ABI mapping drift for {record_name}")
        packet = packet_types.get(packet_schema)
        require(isinstance(packet, dict), f"ABI packet missing: {packet_schema}")
        required = packet.get("required")
        require(isinstance(required, list) and required, f"ABI required fields missing: {packet_schema}")
        missing = set(required) - records.get(record_name, set())
        require(not missing, f"{record_name}: missing ABI fields {sorted(missing)}")

    for record_name, required in REQUIRED_AUXILIARY_FIELDS.items():
        require(record_name in records, f"missing auxiliary record {record_name}")
        missing = required - records[record_name]
        require(not missing, f"{record_name}: missing protocol fields {sorted(missing)}")

    work_fields = records["CognitiveWorkPacket"]
    require("grid_runtime" in work_fields, "CognitiveWorkPacket must carry grid_runtime")
    require("resource_budget" in work_fields, "CognitiveWorkPacket must carry resource_budget")
    require("completion_contract" in work_fields, "CognitiveWorkPacket must carry completion_contract")
    require(
        "requested_N" not in work_fields and "available_N" not in work_fields,
        "CognitiveWorkPacket must not flatten runtime N outside ABI grid_runtime",
    )

    source_laws = normalized_laws(source)
    required_laws = set(manifest.get("required_laws", []))
    require(required_laws, "manifest required_laws missing")
    require(required_laws <= source_laws, f"missing required ClayCode laws: {sorted(required_laws - source_laws)}")

    require(
        "type CognitivePacket = CognitiveWorkPacket | CognitiveResultPacket | ClaudeCodeBridgePacket | WorkspaceReentry | JSpaceMeasurement"
        in source,
        "CognitivePacket union drift",
    )
    require(
        "execute(work:CognitiveWorkPacket) -> CognitiveResultPacket" in source,
        "CognitiveProcess interface drift",
    )

    credits = manifest.get("credit_boundary", {})
    require(credits.get("claycode_protocol_source_contract") == 1, "source-contract credit missing")
    for key, value in credits.items():
        if key != "claycode_protocol_source_contract" and key != "whole_product_pass":
            require(value == 0, f"runtime/model/training credit inflation: {key}={value!r}")
    require(credits.get("whole_product_pass") is False, "whole-product PASS inflation")

    return {
        "schema": "CLAYCODE_COGNITIVE_PROTOCOL_VALIDATION_RESULT/v1",
        "status": "PASS",
        "scope": "CLAYCODE_COGNITIVE_PROTOCOL_SOURCE_CONTRACT_ONLY",
        "protocol_git_blob_sha1": git_blob_sha1(protocol_bytes),
        "protocol_sha256": sha256_bytes(protocol_bytes),
        "grammar_git_blob_sha1": git_blob_sha1(grammar_bytes),
        "grammar_sha256": sha256_bytes(grammar_bytes),
        "frontend_semantic_sha256": compiled["semantic_hash"],
        "frontend_contract_sha256": compiled["contract_hash"],
        "records": sorted(records),
        "abi_record_mappings_checked": ABI_RECORD_MAP,
        "runtime_credit": 0,
        "model_runtime_credit": 0,
        "claude_code_runtime_credit": 0,
        "global_jspace_causal_runtime_credit": 0,
        "training_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "research_entity/global/CLAYCODE_COGNITIVE_PROTOCOL_v1.json",
    )
    parser.add_argument(
        "--abi",
        type=Path,
        default=ROOT / "research_entity/global/COGNITIVE_PROCESS_ABI_v1.json",
    )
    parser.add_argument(
        "--protocol",
        type=Path,
        default=ROOT / "research_entity/claycode/contracts/ZERO_ENTITYOS_COGNITIVE_PROTOCOL_V1.clay",
    )
    parser.add_argument(
        "--grammar",
        type=Path,
        default=ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark",
    )
    args = parser.parse_args()

    try:
        result = validate(
            load_json(args.manifest),
            load_json(args.abi),
            args.protocol.read_bytes(),
            args.grammar.read_bytes(),
        )
    except (ValidationError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1

    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
