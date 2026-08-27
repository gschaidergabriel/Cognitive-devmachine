#!/usr/bin/env python3
"""Trigger-2 deterministic Qwen3.5 model-call receipt contract v1.

Source/evaluation contract only. This validator composes an already-observed
CLAY_TRIGGER2_CHECKPOINT_INPUT_IDENTITY_ABI/v1 receipt with a model-output
receipt that explicitly binds itself to the exact input-identity receipt.

It does not execute a model, select a checkpoint, admit training rows, or mint
J-Space/HCU/EntityOS/training credit.

The contract intentionally fails closed unless:
- checkpoint consumption identity was positively established by the upstream ABI;
- exact rendered UTF-8 + token tensor identities are present;
- tokenizer/template/runtime/checkpoint identities are present;
- the model-output receipt names the same candidate and exact input receipt digest;
- a cryptographic digest of the observed model output is present.

This closes transport/transplant ambiguity at the receipt layer. It does NOT by
itself prove that an upstream consumption probe is scientifically sufficient;
the upstream ABI still owns that claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

SCHEMA = "CLAY_TRIGGER2_QWEN35_MODEL_CALL_RECEIPT_CONTRACT/v1"
INPUT_SCHEMA = "CLAY_TRIGGER2_CHECKPOINT_INPUT_IDENTITY_ABI/v1"
OUTPUT_SCHEMA = "CLAY_TRIGGER2_QWEN35_MODEL_OUTPUT_RECEIPT/v1"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ContractError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require_sha(value: Any, code: str) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise ContractError(code)
    return value


def _require_tensor_identity(value: Any, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(code + "_OBJECT_REQUIRED")
    sha = _require_sha(value.get("sha256"), code + "_SHA256_INVALID")
    raw_sha = _require_sha(value.get("raw_bytes_sha256"), code + "_RAW_SHA256_INVALID")
    dtype = value.get("dtype")
    shape = value.get("shape")
    numel = value.get("numel")
    raw_nbytes = value.get("raw_nbytes")
    if not isinstance(dtype, str) or not dtype:
        raise ContractError(code + "_DTYPE_REQUIRED")
    if not isinstance(shape, list) or not shape or any(not isinstance(x, int) or x < 0 for x in shape):
        raise ContractError(code + "_SHAPE_INVALID")
    if not isinstance(numel, int) or numel < 0:
        raise ContractError(code + "_NUMEL_INVALID")
    if not isinstance(raw_nbytes, int) or raw_nbytes < 0:
        raise ContractError(code + "_NBYTES_INVALID")
    return {
        "sha256": sha,
        "raw_bytes_sha256": raw_sha,
        "dtype": dtype,
        "shape": shape,
        "numel": numel,
        "raw_nbytes": raw_nbytes,
    }


def normalize_input_identity(receipt: Any) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise ContractError("INPUT_RECEIPT_OBJECT_REQUIRED")
    if receipt.get("schema") != INPUT_SCHEMA:
        raise ContractError("INPUT_RECEIPT_SCHEMA_MISMATCH")
    if receipt.get("pass") is not True:
        raise ContractError("INPUT_RECEIPT_PASS_REQUIRED")
    if receipt.get("consumed_identity_match") is not True:
        raise ContractError("CONSUMED_IDENTITY_POSITIVE_REQUIRED")
    if receipt.get("prompt_input_identity_complete") is not True:
        raise ContractError("PROMPT_INPUT_IDENTITY_COMPLETE_REQUIRED")

    candidate_id = receipt.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise ContractError("CANDIDATE_ID_REQUIRED")

    checkpoint = receipt.get("checkpoint_bundle_identity")
    if not isinstance(checkpoint, dict):
        raise ContractError("CHECKPOINT_BUNDLE_IDENTITY_REQUIRED")
    revision = checkpoint.get("requested_revision")
    if not isinstance(revision, str) or not revision:
        raise ContractError("CHECKPOINT_REVISION_REQUIRED")
    for key in (
        "file_manifest_sha256",
        "config_json_sha256",
        "tokenizer_json_sha256",
    ):
        _require_sha(checkpoint.get(key), "CHECKPOINT_" + key.upper() + "_INVALID")
    chat_manifest_sha = checkpoint.get("chat_template_jinja_sha256")
    if chat_manifest_sha is not None:
        _require_sha(chat_manifest_sha, "CHECKPOINT_CHAT_TEMPLATE_SHA256_INVALID")

    consumed = receipt.get("consumed_identity")
    if not isinstance(consumed, dict) or consumed.get("pass") is not True:
        raise ContractError("CONSUMED_IDENTITY_RECEIPT_PASS_REQUIRED")
    if consumed.get("unknown_opened_local_files") not in ([], None):
        raise ContractError("CONSUMED_IDENTITY_UNKNOWN_OPENED_FILES")
    if consumed.get("digest_mismatches") not in ([], None):
        raise ContractError("CONSUMED_IDENTITY_DIGEST_MISMATCH")
    if consumed.get("missing_weight_shards") not in ([], None):
        raise ContractError("CONSUMED_IDENTITY_MISSING_WEIGHT_SHARDS")
    expected_shards = consumed.get("expected_weight_shards")
    opened_shards = consumed.get("opened_weight_shards")
    if not isinstance(expected_shards, list) or not expected_shards:
        raise ContractError("EXPECTED_WEIGHT_SHARDS_REQUIRED")
    if sorted(opened_shards or []) != sorted(expected_shards):
        raise ContractError("OPENED_WEIGHT_SHARDS_INCOMPLETE")

    child = receipt.get("child")
    if not isinstance(child, dict) or child.get("pass") is not True or child.get("forward_observed") is not True:
        raise ContractError("CHILD_FORWARD_OBSERVATION_REQUIRED")

    rendered_sha = _require_sha(child.get("rendered_utf8_sha256"), "RENDERED_UTF8_SHA256_INVALID")
    rendered_nbytes = child.get("rendered_utf8_nbytes")
    if not isinstance(rendered_nbytes, int) or rendered_nbytes < 0:
        raise ContractError("RENDERED_UTF8_NBYTES_INVALID")

    input_ids = _require_tensor_identity(child.get("input_ids"), "INPUT_IDS")
    attention_mask = child.get("attention_mask")
    norm_mask = None if attention_mask is None else _require_tensor_identity(attention_mask, "ATTENTION_MASK")

    messages_sha = _require_sha(child.get("canonical_messages_sha256"), "CANONICAL_MESSAGES_SHA256_INVALID")
    chat_template_text_sha = child.get("chat_template_text_sha256")
    if chat_template_text_sha is not None:
        _require_sha(chat_template_text_sha, "CHAT_TEMPLATE_TEXT_SHA256_INVALID")

    runtime = child.get("runtime")
    loader = child.get("loader")
    if not isinstance(runtime, dict) or not isinstance(loader, dict):
        raise ContractError("RUNTIME_AND_LOADER_IDENTITY_REQUIRED")

    normalized = {
        "candidate_id": candidate_id,
        "input_receipt_sha256": sha256_json(receipt),
        "checkpoint": {
            "repo": checkpoint.get("repo"),
            "requested_revision": revision,
            "file_manifest_sha256": checkpoint.get("file_manifest_sha256"),
            "config_json_sha256": checkpoint.get("config_json_sha256"),
            "tokenizer_json_sha256": checkpoint.get("tokenizer_json_sha256"),
            "tokenizer_config_json_sha256": checkpoint.get("tokenizer_config_json_sha256"),
            "chat_template_jinja_sha256": chat_manifest_sha,
        },
        "consumed_weight_paths": sorted(expected_shards),
        "model_visible_input": {
            "canonical_messages_sha256": messages_sha,
            "render_mode": receipt.get("render_mode"),
            "rendered_utf8_sha256": rendered_sha,
            "rendered_utf8_nbytes": rendered_nbytes,
            "input_ids": input_ids,
            "attention_mask": norm_mask,
            "resolved_chat_template": child.get("resolved_chat_template"),
            "chat_template_text_sha256": chat_template_text_sha,
            "apply_chat_template_parameters": child.get("apply_chat_template_parameters"),
        },
        "runtime": runtime,
        "loader": loader,
    }
    normalized["input_binding_sha256"] = sha256_json(normalized)
    return normalized


def normalize_model_output(output_receipt: Any, normalized_input: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(output_receipt, dict):
        raise ContractError("OUTPUT_RECEIPT_OBJECT_REQUIRED")
    if output_receipt.get("schema") != OUTPUT_SCHEMA:
        raise ContractError("OUTPUT_RECEIPT_SCHEMA_MISMATCH")
    if output_receipt.get("pass") is not True:
        raise ContractError("OUTPUT_RECEIPT_PASS_REQUIRED")
    if output_receipt.get("candidate_id") != normalized_input["candidate_id"]:
        raise ContractError("OUTPUT_CANDIDATE_TRANSPLANT")
    if output_receipt.get("input_receipt_sha256") != normalized_input["input_receipt_sha256"]:
        raise ContractError("OUTPUT_INPUT_RECEIPT_TRANSPLANT")
    if output_receipt.get("input_binding_sha256") != normalized_input["input_binding_sha256"]:
        raise ContractError("OUTPUT_INPUT_BINDING_TRANSPLANT")

    output_kind = output_receipt.get("output_kind")
    if output_kind not in ("GENERATED_TOKEN_IDS", "FORWARD_LOGITS", "CONSTRAINED_SYMBOL"):
        raise ContractError("OUTPUT_KIND_INVALID")
    output_sha = _require_sha(output_receipt.get("model_output_sha256"), "MODEL_OUTPUT_SHA256_INVALID")
    output_nbytes = output_receipt.get("model_output_nbytes")
    if not isinstance(output_nbytes, int) or output_nbytes < 0:
        raise ContractError("MODEL_OUTPUT_NBYTES_INVALID")

    runtime_call_id = output_receipt.get("runtime_call_id")
    if not isinstance(runtime_call_id, str) or not runtime_call_id:
        raise ContractError("RUNTIME_CALL_ID_REQUIRED")

    return {
        "schema": OUTPUT_SCHEMA,
        "candidate_id": normalized_input["candidate_id"],
        "runtime_call_id": runtime_call_id,
        "output_kind": output_kind,
        "model_output_sha256": output_sha,
        "model_output_nbytes": output_nbytes,
        "input_receipt_sha256": normalized_input["input_receipt_sha256"],
        "input_binding_sha256": normalized_input["input_binding_sha256"],
    }


def adjudicate(input_receipt: Any, output_receipt: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "pass": False,
        "credit_boundary": {
            "checkpoint_selection_credit": 0,
            "model_runtime_promotion_credit": 0,
            "jspace_model_credit": 0,
            "training_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
        },
    }
    try:
        normalized_input = normalize_input_identity(input_receipt)
        normalized_output = normalize_model_output(output_receipt, normalized_input)
        call_binding = {
            "candidate_id": normalized_input["candidate_id"],
            "input_binding_sha256": normalized_input["input_binding_sha256"],
            "output": normalized_output,
        }
        result.update(
            {
                "pass": True,
                "candidate_id": normalized_input["candidate_id"],
                "input_identity": normalized_input,
                "model_output": normalized_output,
                "model_call_digest": sha256_json(call_binding),
                "status": "PASS_RECEIPT_CONTRACT_ONLY",
                "promotion_boundary": (
                    "This validates exact receipt-layer binding only. It does not independently "
                    "upgrade the scientific sufficiency of the upstream consumption probe and "
                    "does not select a checkpoint or admit training/model/J-Space/HCU/EntityOS credit."
                ),
            }
        )
    except (ContractError, TypeError, ValueError) as exc:
        result["failure"] = str(exc)
        result["status"] = "FAIL_CLOSED_RECEIPT_CONTRACT"
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-identity-receipt", required=True)
    p.add_argument("--model-output-receipt", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args(argv)

    input_obj = json.loads(Path(args.input_identity_receipt).read_text(encoding="utf-8"))
    output_obj = json.loads(Path(args.model_output_receipt).read_text(encoding="utf-8"))
    result = adjudicate(input_obj, output_obj)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result.get("pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
