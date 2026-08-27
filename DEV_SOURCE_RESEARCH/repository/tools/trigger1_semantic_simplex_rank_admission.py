#!/usr/bin/env python3
"""Fail-closed provenance admission for the canonical Trigger-1 simplex rank analyzer.

This layer intentionally does not define a second rank statistic. It validates that an
activation packet is calibration-only, holdout-closed, model-facing-label-free,
lexically disjoint, output-code-independent, and bound to exact model/tokenizer/runtime
identity. Only then is a stripped numeric packet delegated to
trigger1_semantic_simplex_rank_analyze.

The wrapper itself never runs a model, never applies cvec, and never grants runtime,
J-Space, HCU, training, or canonical-semantics credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from tools import trigger1_semantic_simplex_rank_analyze as rank

INPUT_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_SIMPLEX_CALIBRATION_ADMISSION/v1"
OUTPUT_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_SIMPLEX_RANK_ADMISSION_RESULT/v1"
CLASSES = rank.CLASSES
HEX64_KEYS = (
    "model_checkpoint_sha256",
    "tokenizer_sha256",
    "runtime_build_sha256",
)
TRUE_ATTESTATIONS = (
    "calibration_only",
    "label_free_model_facing_prompts",
    "lexically_disjoint_families",
    "output_code_independent",
)


class AdmissionError(ValueError):
    pass


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _require_hex64(value: Any, name: str) -> str:
    text = str(value or "").lower()
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise AdmissionError(f"{name}:LOWERCASE_SHA256_REQUIRED")
    return text


def _validate_source_identity(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AdmissionError("source_identity:OBJECT_REQUIRED")
    out = {key: _require_hex64(value.get(key), f"source_identity.{key}") for key in HEX64_KEYS}
    activation_site = value.get("activation_site")
    token_scope = value.get("token_scope")
    layer = value.get("layer")
    if not isinstance(activation_site, str) or not activation_site.strip():
        raise AdmissionError("source_identity.activation_site:NONEMPTY_STRING_REQUIRED")
    if not isinstance(token_scope, str) or not token_scope.strip():
        raise AdmissionError("source_identity.token_scope:NONEMPTY_STRING_REQUIRED")
    if not isinstance(layer, int) or isinstance(layer, bool) or layer < 0:
        raise AdmissionError("source_identity.layer:NONNEGATIVE_INTEGER_REQUIRED")
    out.update(
        {
            "activation_site": activation_site.strip(),
            "token_scope": token_scope.strip(),
            "layer": layer,
        }
    )
    return out


def _validate_attestation(value: Any) -> dict[str, bool]:
    if not isinstance(value, dict):
        raise AdmissionError("design_attestation:OBJECT_REQUIRED")
    for key in TRUE_ATTESTATIONS:
        if value.get(key) is not True:
            raise AdmissionError(f"design_attestation.{key}:TRUE_REQUIRED")
    if value.get("fresh_holdout_opened") is not False:
        raise AdmissionError("design_attestation.fresh_holdout_opened:FALSE_REQUIRED")
    return {
        **{key: True for key in TRUE_ATTESTATIONS},
        "fresh_holdout_opened": False,
    }


def _validate_rows(value: Any) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    if not isinstance(value, list) or not value:
        raise AdmissionError("rows:NONEMPTY_LIST_REQUIRED")
    prompt_hashes: set[str] = set()
    row_ids: set[str] = set()
    numeric_rows: list[dict[str, Any]] = []
    provenance_rows: list[dict[str, str]] = []
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise AdmissionError(f"row[{index}]:OBJECT_REQUIRED")
        row_id = str(row.get("row_id") or "").strip()
        family = str(row.get("family_group_id") or "").strip()
        semantic = str(row.get("semantic_class") or "").strip().upper()
        if not row_id:
            raise AdmissionError(f"row[{index}].row_id:REQUIRED")
        if row_id in row_ids:
            raise AdmissionError(f"row[{index}].row_id:DUPLICATE:{row_id}")
        row_ids.add(row_id)
        if not family:
            raise AdmissionError(f"row[{index}].family_group_id:REQUIRED")
        if semantic not in CLASSES:
            raise AdmissionError(f"row[{index}].semantic_class:INVALID:{semantic}")
        if row.get("label_free") is not True:
            raise AdmissionError(f"row[{index}].label_free:TRUE_REQUIRED")
        if row.get("output_code_free") is not True:
            raise AdmissionError(f"row[{index}].output_code_free:TRUE_REQUIRED")
        prompt_sha = _require_hex64(row.get("prompt_sha256"), f"row[{index}].prompt_sha256")
        if prompt_sha in prompt_hashes:
            raise AdmissionError(f"row[{index}].prompt_sha256:REUSED:{prompt_sha}")
        prompt_hashes.add(prompt_sha)
        activation = row.get("activation")
        if not isinstance(activation, list) or not activation:
            raise AdmissionError(f"row[{index}].activation:NONEMPTY_LIST_REQUIRED")
        numeric_rows.append(
            {
                "row_id": row_id,
                "family_group_id": family,
                "semantic_class": semantic,
                "activation": activation,
            }
        )
        provenance_rows.append(
            {
                "row_id": row_id,
                "family_group_id": family,
                "semantic_class": semantic,
                "prompt_sha256": prompt_sha,
            }
        )
    return numeric_rows, provenance_rows


def admit_and_analyze(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") != INPUT_SCHEMA:
        raise AdmissionError("INPUT_SCHEMA_INVALID")
    source_identity = _validate_source_identity(payload.get("source_identity"))
    design_attestation = _validate_attestation(payload.get("design_attestation"))
    numeric_rows, provenance_rows = _validate_rows(payload.get("rows"))

    dimension = payload.get("dimension")
    if not isinstance(dimension, int) or isinstance(dimension, bool) or dimension <= 0:
        raise AdmissionError("dimension:POSITIVE_INTEGER_REQUIRED")
    decision_config = payload.get("decision_config")
    if not isinstance(decision_config, dict):
        raise AdmissionError("decision_config:OBJECT_REQUIRED")

    numeric_packet = {
        "schema": rank.INPUT_SCHEMA,
        "dimension": dimension,
        "decision_config": decision_config,
        "rows": numeric_rows,
    }
    numeric_result = rank.analyze(numeric_packet)
    provenance_core = {
        "source_identity": source_identity,
        "design_attestation": design_attestation,
        "row_provenance": provenance_rows,
    }
    result_core = {
        "schema": OUTPUT_SCHEMA,
        "input_schema": INPUT_SCHEMA,
        "input_sha256": canonical_sha(payload),
        "numeric_analyzer_schema": rank.OUTPUT_SCHEMA,
        "numeric_input_sha256": canonical_sha(numeric_packet),
        "numeric_analysis_receipt_sha256": numeric_result["analysis_receipt_sha256"],
        "provenance_receipt_sha256": canonical_sha(provenance_core),
        "source_identity": source_identity,
        "design_attestation": design_attestation,
        "row_provenance": provenance_rows,
        "numeric_result": numeric_result,
        "admission": "PASS",
        "evidence_scope": "CALIBRATION_ONLY_PROVENANCE_BOUND_NUMERIC_ANALYSIS",
        "epistemic_boundary": (
            "label-free/lexical-disjoint/output-code-independent status is an upstream "
            "attested input property; this wrapper verifies required declarations and hashes "
            "but does not semantically re-audit prompt text that is intentionally absent"
        ),
        "promotion_boundary": {
            "fresh_holdout_opened": False,
            "model_executed": False,
            "native_cvec_intervention_executed": False,
            "new_runtime_credit": 0,
            "jspace_model_runtime_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
            "training_credit": 0,
            "canonical_semantics_promotion": False,
        },
    }
    return {**result_core, "admission_receipt_sha256": canonical_sha(result_core)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        result = admit_and_analyze(payload)
    except (OSError, json.JSONDecodeError, ValueError, AdmissionError) as exc:
        failure = {
            "schema": OUTPUT_SCHEMA,
            "admission": "FAIL_CLOSED",
            "error": str(exc),
            "promotion_boundary": {
                "new_runtime_credit": 0,
                "canonical_semantics_promotion": False,
            },
        }
        Path(args.output).write_text(
            json.dumps(failure, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return 2
    Path(args.output).write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
