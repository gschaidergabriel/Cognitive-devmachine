#!/usr/bin/env python3
"""Fail-closed repository/source binding gate for Trigger-2 model-call ABI v2.

SOURCE-ONLY successor layer. It does not execute a model or provider and does not mint
checkpoint-selection, J-Space, training, HCU, or EntityOS credit.

The existing CHECKPOINT_MODEL_STATE_CONSUMPTION_ABI/v2 already binds consumed model
state, model-visible input, runtime identity and full last-token-logit identity. This
gate closes the remaining causal-lineage source gap by requiring an upstream-frozen
clean Git repository/source identity and then deriving one source-bound call identity.

Important: a caller-supplied source identity is not self-authenticating. The gate only
accepts it when its canonical digest exactly equals an expected digest frozen by an
independent repository-bound execution request/attestor before the model call.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping

SCHEMA = "CLAY_TRIGGER2_MODEL_CALL_REPOSITORY_BOUND_GATE/v1"
ABI_V2_SCHEMA = "CLAY_TRIGGER2_CHECKPOINT_MODEL_STATE_CONSUMPTION_ABI/v2"
CHILD_V2_SCHEMA = "CLAY_TRIGGER2_CHECKPOINT_MODEL_STATE_CONSUMPTION_CHILD/v2"
V2_BINDING_SCHEMA = "CLAY_TRIGGER2_MODEL_CALL_BINDING/v2"
SOURCE_IDENTITY_SCHEMA = "CLAY_REPOSITORY_SOURCE_IDENTITY/v1"
CANONICAL_REPOSITORY = "gschaidergabriel/clay-global-research-entity"
PROBE_SOURCE_PATH = "tools/trigger2_qwen35_checkpoint_model_state_consumption_probe_v2.py"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class GateError(RuntimeError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise GateError(code)


def _require_hex(value: Any, pattern: re.Pattern[str], code: str) -> str:
    _require(isinstance(value, str) and bool(pattern.fullmatch(value)), code)
    return value


def _mapping(value: Any, code: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), code)
    return value


def validate_source_identity(source: Mapping[str, Any], *, expected_sha256: str) -> dict[str, Any]:
    """Validate a precommitted clean Git/source identity.

    This proves only equality to the externally frozen identity commitment. Runtime
    attestation of these Git facts remains the responsibility of the admitted executor.
    """
    _require_hex(expected_sha256, HEX64, "EXPECTED_SOURCE_IDENTITY_SHA256_INVALID")
    _require(source.get("schema") == SOURCE_IDENTITY_SCHEMA, "SOURCE_IDENTITY_SCHEMA_MISMATCH")
    _require(source.get("repository_full_name") == CANONICAL_REPOSITORY, "SOURCE_REPOSITORY_MISMATCH")
    _require(source.get("source_path") == PROBE_SOURCE_PATH, "SOURCE_PATH_MISMATCH")
    _require(source.get("dirty") is False, "SOURCE_REPOSITORY_DIRTY_OR_UNKNOWN")
    _require_hex(source.get("head_sha"), HEX40, "SOURCE_HEAD_SHA_INVALID")
    _require_hex(source.get("tree_sha"), HEX40, "SOURCE_TREE_SHA_INVALID")
    _require_hex(source.get("source_blob_sha1"), HEX40, "SOURCE_BLOB_SHA1_INVALID")
    _require_hex(source.get("source_sha256"), HEX64, "SOURCE_SHA256_INVALID")
    observed = canonical_sha256(dict(source))
    _require(observed == expected_sha256, "SOURCE_IDENTITY_COMMITMENT_MISMATCH")
    return {
        "source_identity_sha256": observed,
        "head_sha": source["head_sha"],
        "tree_sha": source["tree_sha"],
        "source_sha256": source["source_sha256"],
        "source_blob_sha1": source["source_blob_sha1"],
        "dirty": False,
    }


def recompute_v2_call_binding(child: Mapping[str, Any]) -> str:
    """Recompute the ABI-v2 call binding from exact child receipt fields."""
    _require(child.get("schema") == CHILD_V2_SCHEMA, "CHILD_V2_SCHEMA_MISMATCH")
    _require(child.get("pass") is True, "CHILD_V2_NOT_PASS")
    reconciliation = _mapping(child.get("state_reconciliation"), "STATE_RECONCILIATION_REQUIRED")
    _require(reconciliation.get("pass") is True, "STATE_RECONCILIATION_NOT_PASS")
    _require(child.get("persistent_state_stable_across_forward") is True, "PERSISTENT_STATE_NOT_STABLE")
    _require(child.get("forward_observed") is True, "FORWARD_NOT_OBSERVED")

    candidate_id = child.get("candidate_id")
    checkpoint_manifest_sha256 = child.get("checkpoint_manifest_sha256")
    rendered_utf8_sha256 = child.get("rendered_utf8_sha256")
    _require(isinstance(candidate_id, str) and candidate_id, "CANDIDATE_ID_REQUIRED")
    _require_hex(checkpoint_manifest_sha256, HEX64, "CHECKPOINT_MANIFEST_SHA256_INVALID")
    _require_hex(rendered_utf8_sha256, HEX64, "RENDERED_UTF8_SHA256_INVALID")
    _require_hex(reconciliation.get("checkpoint_state_digest"), HEX64, "CHECKPOINT_STATE_DIGEST_INVALID")
    _require_hex(reconciliation.get("loaded_state_digest"), HEX64, "LOADED_STATE_DIGEST_INVALID")

    input_ids = _mapping(child.get("input_ids"), "INPUT_IDS_IDENTITY_REQUIRED")
    attention_mask = child.get("attention_mask")
    _require(attention_mask is None or isinstance(attention_mask, Mapping), "ATTENTION_MASK_IDENTITY_INVALID")
    runtime = _mapping(child.get("runtime"), "RUNTIME_IDENTITY_REQUIRED")
    forward_output = _mapping(child.get("forward_output"), "FORWARD_OUTPUT_IDENTITY_REQUIRED")
    last_logits = _mapping(forward_output.get("last_logits"), "LAST_LOGITS_IDENTITY_REQUIRED")
    _require_hex(last_logits.get("raw_bytes_sha256"), HEX64, "LAST_LOGITS_RAW_BYTES_SHA256_INVALID")
    _require(isinstance(forward_output.get("top1_token_id"), int), "TOP1_TOKEN_ID_REQUIRED")

    envelope = {
        "schema": V2_BINDING_SCHEMA,
        "candidate_id": candidate_id,
        "checkpoint_manifest_sha256": checkpoint_manifest_sha256,
        "checkpoint_state_digest": reconciliation["checkpoint_state_digest"],
        "loaded_state_digest": reconciliation["loaded_state_digest"],
        "rendered_utf8_sha256": rendered_utf8_sha256,
        "input_ids": dict(input_ids),
        "attention_mask": None if attention_mask is None else dict(attention_mask),
        "runtime": dict(runtime),
        "forward_output": dict(forward_output),
    }
    observed = canonical_sha256(envelope)
    claimed = child.get("model_call_binding_sha256")
    _require_hex(claimed, HEX64, "MODEL_CALL_BINDING_SHA256_INVALID")
    _require(observed == claimed, "MODEL_CALL_BINDING_RECOMPUTE_MISMATCH")
    return observed


def gate_receipt(abi_v2_receipt: Mapping[str, Any], source_identity: Mapping[str, Any], *, expected_source_identity_sha256: str) -> dict[str, Any]:
    """Bind exact ABI-v2 receipt + precommitted clean repository/source identity."""
    _require(abi_v2_receipt.get("schema") == ABI_V2_SCHEMA, "ABI_V2_SCHEMA_MISMATCH")
    _require(abi_v2_receipt.get("pass") is True, "ABI_V2_NOT_PASS")
    _require(abi_v2_receipt.get("status") == "PASS_COMPONENT_ONLY", "ABI_V2_STATUS_NOT_COMPONENT_PASS")
    _require(abi_v2_receipt.get("selection_grade_consumed_model_state_component_eligible") is True, "ABI_V2_CONSUMED_STATE_NOT_ELIGIBLE")
    _require(abi_v2_receipt.get("manifest_to_loaded_state_reconciled") is True, "ABI_V2_STATE_NOT_RECONCILED")
    _require(abi_v2_receipt.get("forward_bound_to_loaded_state_and_input") is True, "ABI_V2_FORWARD_NOT_BOUND")

    child = _mapping(abi_v2_receipt.get("child"), "ABI_V2_CHILD_REQUIRED")
    _require(child.get("candidate_id") == abi_v2_receipt.get("candidate_id"), "PARENT_CHILD_CANDIDATE_MISMATCH")
    v2_binding = recompute_v2_call_binding(child)
    source = validate_source_identity(source_identity, expected_sha256=expected_source_identity_sha256)

    receipt_sha256 = canonical_sha256(dict(abi_v2_receipt))
    output_identity_sha256 = canonical_sha256(dict(_mapping(child.get("forward_output"), "FORWARD_OUTPUT_IDENTITY_REQUIRED")))
    source_bound_envelope = {
        "schema": "CLAY_TRIGGER2_SOURCE_BOUND_MODEL_CALL_IDENTITY/v1",
        "abi_v2_receipt_sha256": receipt_sha256,
        "abi_v2_model_call_binding_sha256": v2_binding,
        "model_output_identity_sha256": output_identity_sha256,
        "source_identity_sha256": source["source_identity_sha256"],
        "candidate_id": child["candidate_id"],
        "checkpoint_manifest_sha256": child["checkpoint_manifest_sha256"],
        "rendered_utf8_sha256": child["rendered_utf8_sha256"],
    }
    return {
        "schema": SCHEMA,
        "pass": True,
        "status": "PASS_SOURCE_BOUND_CALL_IDENTITY_COMPONENT_ONLY",
        "source_bound_model_call_identity_sha256": canonical_sha256(source_bound_envelope),
        "abi_v2_receipt_sha256": receipt_sha256,
        "abi_v2_model_call_binding_sha256": v2_binding,
        "model_output_identity_sha256": output_identity_sha256,
        "source_identity": source,
        "source_bound_envelope": source_bound_envelope,
        "credit_boundary": {
            "checkpoint_selection_credit": 0,
            "jspace_model_credit": 0,
            "training_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
        },
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--abi-v2-receipt", type=Path, required=True)
    p.add_argument("--source-identity", type=Path, required=True)
    p.add_argument("--expected-source-identity-sha256", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)
    result: dict[str, Any]
    try:
        receipt = json.loads(args.abi_v2_receipt.read_text(encoding="utf-8"))
        source = json.loads(args.source_identity.read_text(encoding="utf-8"))
        result = gate_receipt(receipt, source, expected_source_identity_sha256=args.expected_source_identity_sha256)
    except Exception as exc:
        result = {
            "schema": SCHEMA,
            "pass": False,
            "status": "FAIL_CLOSED",
            "failure": f"{type(exc).__name__}:{exc}",
            "credit_boundary": {
                "checkpoint_selection_credit": 0,
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
