#!/usr/bin/env python3
"""Fail-closed causal binding between a MiniUnifiedDB pipeline turn and UCF receipt.

This validator deliberately reuses the canonical UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1
validator. It adds only the missing cross-boundary law: the exact MiniUnifiedDB generation,
profile snapshot, canonical/packet hashes, boot binding, inference packet and candidate result
must be the same causal object that the UCF receipt describes and that the atomic pipeline
commit records.

A PASS is source/mechanism evidence only. It does not prove that the bundled ~0.8B model,
J-Space/GWT, Claude adapter, or Mini Entity runtime actually executed.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "MINI_ENTITY_PIPELINE_UCF_TURN_BINDING/v1"
PACKET_SCHEMA = "MINI_ENTITY_INFERENCE_PACKET/v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
GIT_OID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class TurnBindingError(ValueError):
    pass


def _load_ucf_module():
    here = Path(__file__).resolve()
    candidates = [here.with_name("validate_unified_cognitive_fabric_receipt_v1.py")]
    for parent in here.parents:
        candidates.append(parent / "tools" / "validate_unified_cognitive_fabric_receipt_v1.py")
    seen = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if path.is_file():
            spec = importlib.util.spec_from_file_location("canonical_ucf_receipt_v1", path)
            module = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(module)
            return module
    raise TurnBindingError("CANONICAL_UCF_VALIDATOR_NOT_FOUND")


UCF = _load_ucf_module()


def _obj(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if type(value) is not dict:
        raise TurnBindingError(f"{key}:OBJECT_REQUIRED")
    return value


def _text(parent: dict[str, Any], key: str, *, nullable: bool = False) -> str | None:
    value = parent.get(key)
    if value is None and nullable:
        return None
    if type(value) is not str or not value:
        raise TurnBindingError(f"{key}:TEXT_REQUIRED")
    return value


def _bool(parent: dict[str, Any], key: str) -> bool:
    value = parent.get(key)
    if type(value) is not bool:
        raise TurnBindingError(f"{key}:BOOL_REQUIRED")
    return value


def _count(parent: dict[str, Any], key: str, *, nullable: bool = False) -> int | None:
    value = parent.get(key)
    if value is None and nullable:
        return None
    if type(value) is not int or value < 0:
        raise TurnBindingError(f"{key}:NONNEGATIVE_INT_REQUIRED")
    return value


def _hex(parent: dict[str, Any], key: str, pattern: re.Pattern[str], *, nullable: bool = False) -> str | None:
    value = _text(parent, key, nullable=nullable)
    if value is None:
        return None
    if pattern.fullmatch(value) is None:
        raise TurnBindingError(f"{key}:DIGEST_FORMAT")
    if value in {"0" * len(value), "f" * len(value)}:
        raise TurnBindingError(f"{key}:IDENTITY_PLACEHOLDER")
    return value


def canonical_digest(value: dict[str, Any], *, omit_key: str | None = None) -> str:
    material = copy.deepcopy(value)
    if omit_key is not None:
        material.pop(omit_key, None)
    encoded = json.dumps(
        material,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate(binding: dict[str, Any]) -> dict[str, Any]:
    if type(binding) is not dict:
        raise TurnBindingError("ROOT_OBJECT_REQUIRED")
    if binding.get("schema") != SCHEMA:
        raise TurnBindingError("SCHEMA_MISMATCH")

    source = _obj(binding, "source")
    pipeline = _obj(binding, "pipeline")
    packet = _obj(binding, "inference_packet")
    ucf_receipt = _obj(binding, "ucf_receipt")
    gate = _obj(binding, "gate")
    commit = _obj(binding, "commit")

    source_commit = _hex(source, "commit", GIT_OID)
    if source.get("dirty") is not False:
        raise TurnBindingError("SOURCE_DIRTY_OR_UNKNOWN")

    if _text(pipeline, "state_authority") != "MiniUnifiedDB":
        raise TurnBindingError("STATE_AUTHORITY_MUST_BE_MINIUNIFIEDDB")
    generation_before = _count(pipeline, "generation_before")
    profile_snapshot_digest = _hex(pipeline, "profile_snapshot_digest", HEX64)
    canonical_state_hash = _hex(pipeline, "canonical_state_hash", HEX64)
    packet_hash = _hex(pipeline, "packet_hash", HEX64)

    if packet.get("schema") != PACKET_SCHEMA:
        raise TurnBindingError("INFERENCE_PACKET_SCHEMA_MISMATCH")
    if _count(packet, "generation") != generation_before:
        raise TurnBindingError("INFERENCE_PACKET_GENERATION_MISMATCH")
    if _hex(packet, "profile_snapshot_digest", HEX64) != profile_snapshot_digest:
        raise TurnBindingError("INFERENCE_PACKET_PROFILE_MISMATCH")
    if _hex(packet, "canonical_state_hash", HEX64) != canonical_state_hash:
        raise TurnBindingError("INFERENCE_PACKET_CANONICAL_HASH_MISMATCH")
    if _hex(packet, "packet_hash", HEX64) != packet_hash:
        raise TurnBindingError("INFERENCE_PACKET_EVENT_HASH_MISMATCH")
    boot_binding_digest = _hex(packet, "boot_binding_receipt_digest", HEX64)
    _hex(packet, "engine_selection_digest", HEX64)
    inference_packet_digest = canonical_digest(packet)

    try:
        ucf_checked = UCF.validate(ucf_receipt)
    except Exception as exc:  # preserve canonical validator as sole UCF semantic authority
        raise TurnBindingError(f"UCF_RECEIPT_REJECTED:{exc}") from exc

    if ucf_checked["source_commit"] != source_commit:
        raise TurnBindingError("UCF_SOURCE_COMMIT_MISMATCH")
    if ucf_checked["generation"] != generation_before:
        raise TurnBindingError("UCF_GENERATION_MISMATCH")
    if ucf_receipt["binding"]["boot_binding_receipt_digest"] != boot_binding_digest:
        raise TurnBindingError("UCF_BOOT_BINDING_MISMATCH")
    if ucf_receipt["inference"]["inference_packet_digest"] != inference_packet_digest:
        raise TurnBindingError("UCF_INFERENCE_PACKET_DIGEST_MISMATCH")

    candidate_result_digest = ucf_receipt["inference"]["candidate_result_digest"]
    gate_candidate_digest = _hex(gate, "candidate_result_digest", HEX64, nullable=True)
    if gate_candidate_digest != candidate_result_digest:
        raise TurnBindingError("GATE_CANDIDATE_DIGEST_MISMATCH")

    gate_decision = _text(gate, "decision")
    if gate_decision != ucf_receipt["authority"]["validation_decision"]:
        raise TurnBindingError("GATE_DECISION_MISMATCH")
    if gate_decision not in {"ACCEPT", "REJECT", "BLOCKED"}:
        raise TurnBindingError("GATE_DECISION_INVALID")
    if _hex(gate, "ucf_receipt_digest", HEX64) != ucf_checked["receipt_digest"]:
        raise TurnBindingError("GATE_UCF_RECEIPT_DIGEST_MISMATCH")

    committed = _bool(commit, "committed")
    generation_after = _count(commit, "generation_after", nullable=True)
    output_id = _text(commit, "output_id", nullable=True)

    if gate_decision == "ACCEPT":
        if not ucf_checked["canonical_write_committed"]:
            raise TurnBindingError("UCF_ACCEPT_WITHOUT_CANONICAL_WRITE")
        if not committed:
            raise TurnBindingError("ACCEPT_WITHOUT_PIPELINE_COMMIT")
        if generation_after != generation_before + 1:
            raise TurnBindingError("PIPELINE_GENERATION_NOT_EXACTLY_ONCE")
        if output_id is None:
            raise TurnBindingError("COMMIT_OUTPUT_ID_REQUIRED")
        if _hex(commit, "packet_hash", HEX64) != packet_hash:
            raise TurnBindingError("COMMIT_PACKET_HASH_MISMATCH")
        if _hex(commit, "canonical_state_hash", HEX64) != canonical_state_hash:
            raise TurnBindingError("COMMIT_CANONICAL_HASH_MISMATCH")
        if _hex(commit, "ucf_receipt_digest", HEX64) != ucf_checked["receipt_digest"]:
            raise TurnBindingError("COMMIT_UCF_RECEIPT_DIGEST_MISMATCH")
    else:
        if ucf_checked["canonical_write_committed"]:
            raise TurnBindingError("NONACCEPT_UCF_CANONICAL_WRITE_FORBIDDEN")
        if committed:
            raise TurnBindingError("NONACCEPT_PIPELINE_COMMIT_FORBIDDEN")
        if generation_after is not None or output_id is not None:
            raise TurnBindingError("NONACCEPT_COMMIT_FIELDS_MUST_BE_NULL")
        for key in ("packet_hash", "canonical_state_hash", "ucf_receipt_digest"):
            if commit.get(key) is not None:
                raise TurnBindingError("NONACCEPT_COMMIT_BINDINGS_MUST_BE_NULL")

    envelope = _hex(binding, "binding_envelope_digest", HEX64)
    expected = canonical_digest(binding, omit_key="binding_envelope_digest")
    if envelope != expected:
        raise TurnBindingError("BINDING_ENVELOPE_DIGEST_MISMATCH")

    return {
        "ok": True,
        "schema": SCHEMA,
        "source_commit": source_commit,
        "generation_before": generation_before,
        "generation_after": generation_after,
        "inference_packet_digest": inference_packet_digest,
        "ucf_receipt_digest": ucf_checked["receipt_digest"],
        "gate_decision": gate_decision,
        "committed": committed,
    }


def main() -> int:
    try:
        value = json.load(sys.stdin)
        result = validate(value)
    except (TurnBindingError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"ok": False, "schema": SCHEMA, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
