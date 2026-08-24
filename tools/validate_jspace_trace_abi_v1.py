#!/usr/bin/env python3
"""Fail-closed standard-library validator for JSPACE_TRACE_ABI/v1.

This validates the machine-readable trace envelope defined by
HCU_JSPACE_OBSERVE_CONTROL_TRANSLATE_ARCHITECTURE_V1.md. It performs no model,
provider, network, canonical-state or real-effect operation and grants no runtime
or training credit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

SCHEMA = "JSPACE_TRACE_ABI/v1"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
OBSERVATION_CLASSES = {
    "RAW_ACTIVATION_MEASUREMENT",
    "PROJECTED_LATENT_MEASUREMENT",
    "JACOBIAN_OR_READOUT_MEASUREMENT",
    "PROBE_SCORE_MEASUREMENT",
    "WORKSPACE_CANDIDATE_MEASUREMENT",
}
SPLITS = {"CALIBRATION", "DEV", "CAUSAL_HOLDOUT", "OOD_HOLDOUT"}
REQUIRED = {
    "schema",
    "causal_event_id",
    "admission_id",
    "generation",
    "model_id",
    "model_revision",
    "checkpoint_sha256",
    "tokenizer_sha256",
    "runtime_build_sha256",
    "loader_consumption_identity",
    "inference_receipt_id",
    "jspace_adapter_id",
    "activation_site",
    "token_position_policy",
    "observation_class",
    "activation_or_projection_sha256",
    "semantic_family_id",
    "task_family_id",
    "context_polarity_id",
    "split_id",
    "intervention_id",
    "control_class",
    "target_metrics",
    "off_target_metrics",
    "result_classification",
    "credit_scope",
}


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_trace(obj: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(obj, dict):
        return ["TRACE_NOT_OBJECT"]

    missing = sorted(REQUIRED - obj.keys())
    errors.extend(f"MISSING:{name}" for name in missing)
    if missing:
        return errors

    if obj.get("schema") != SCHEMA:
        errors.append("WRONG_SCHEMA")

    for name in (
        "causal_event_id",
        "admission_id",
        "model_id",
        "model_revision",
        "inference_receipt_id",
        "jspace_adapter_id",
        "token_position_policy",
        "semantic_family_id",
        "task_family_id",
        "context_polarity_id",
        "intervention_id",
        "control_class",
        "result_classification",
        "credit_scope",
    ):
        if not _nonempty_string(obj.get(name)):
            errors.append(f"INVALID_STRING:{name}")

    generation = obj.get("generation")
    if isinstance(generation, bool) or not (
        (isinstance(generation, int) and generation >= 0) or _nonempty_string(generation)
    ):
        errors.append("INVALID_GENERATION")

    for name in (
        "checkpoint_sha256",
        "tokenizer_sha256",
        "runtime_build_sha256",
        "activation_or_projection_sha256",
    ):
        value = obj.get(name)
        if not isinstance(value, str) or SHA256.fullmatch(value) is None:
            errors.append(f"INVALID_SHA256:{name}")

    loader = obj.get("loader_consumption_identity")
    if not (
        loader == "UNKNOWN"
        or _nonempty_string(loader)
        or (isinstance(loader, dict) and bool(loader))
    ):
        errors.append("INVALID_LOADER_CONSUMPTION_IDENTITY")

    site = obj.get("activation_site")
    if not isinstance(site, dict) or not site:
        errors.append("INVALID_ACTIVATION_SITE")

    if obj.get("observation_class") not in OBSERVATION_CLASSES:
        errors.append("INVALID_OBSERVATION_CLASS")
    if obj.get("split_id") not in SPLITS:
        errors.append("INVALID_SPLIT_ID")

    for name in ("target_metrics", "off_target_metrics"):
        value = obj.get(name)
        if not isinstance(value, (list, dict)):
            errors.append(f"INVALID_METRICS:{name}")

    intervention = obj.get("intervention_id")
    control = obj.get("control_class")
    if intervention == "NONE" and control != "NONE":
        errors.append("CONTROL_WITHOUT_INTERVENTION")
    if intervention != "NONE" and control == "NONE":
        errors.append("INTERVENTION_WITHOUT_CONTROL_CLASS")

    if obj.get("canonical_truth") is True:
        errors.append("CANONICAL_TRUTH_PROMOTION_FORBIDDEN")
    truth_status = obj.get("truth_status")
    if truth_status is not None and truth_status != "CANDIDATE_MEASUREMENT_ONLY":
        errors.append("INVALID_TRUTH_STATUS")

    return errors


def validate_jsonl(path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": "JSPACE_TRACE_ABI_VALIDATION_RESULT/v1",
        "path": str(path),
        "seen": 0,
        "valid": 0,
        "invalid": 0,
        "errors": [],
        "credit_scope": "SOURCE_TRACE_CONTRACT_VALIDATION_ONLY",
        "jspace_model_runtime_credit": 0,
        "training_credit": 0,
    }
    if not path.exists():
        out["invalid"] = 1
        out["errors"].append({"line": 0, "errors": ["TRACE_FILE_MISSING"]})
        return out

    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        out["seen"] += 1
        try:
            obj = json.loads(line)
        except Exception:
            errs = ["INVALID_JSON"]
        else:
            errs = validate_trace(obj)
        if errs:
            out["invalid"] += 1
            out["errors"].append({"line": line_no, "errors": errs})
        else:
            out["valid"] += 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("trace_jsonl", type=Path)
    args = ap.parse_args()
    result = validate_jsonl(args.trace_jsonl)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["invalid"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
