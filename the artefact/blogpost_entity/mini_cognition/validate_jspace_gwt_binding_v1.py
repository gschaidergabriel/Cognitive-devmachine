#!/usr/bin/env python3
"""Fail-closed validator for Mini Entity J-Space/GWT binding manifests.

This validates identity/provenance/calibration boundaries only. It does not
establish Jacobian-Lens runtime compatibility or GWT effectiveness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import re
import sys
from typing import Any

SCHEMA_VERSION = "jspace-gwt-binding/v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_MODES = {"OBSERVE_ONLY", "RESEARCH_INTERVENTION"}
ALLOWED_CAL = {"UNMEASURED", "MEASURED"}


def _err(errors: list[str], code: str, detail: str) -> None:
    errors.append(f"{code}:{detail}")


def _require_dict(obj: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(obj, dict):
        _err(errors, "TYPE", f"{name} must be object")
        return {}
    return obj


def _require_str(obj: dict[str, Any], key: str, errors: list[str]) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        _err(errors, "FIELD", f"{key} must be non-empty string")
        return ""
    return value


def _digest(obj: dict[str, Any], key: str, errors: list[str]) -> str:
    value = _require_str(obj, key, errors)
    if value and not HEX64.fullmatch(value):
        _err(errors, "DIGEST", f"{key} must be lowercase sha256")
    if value in {"0" * 64, "f" * 64}:
        _err(errors, "DIGEST_PLACEHOLDER", key)
    return value


def validate(data: Any) -> list[str]:
    errors: list[str] = []
    root = _require_dict(data, "root", errors)
    if root.get("schema_version") != SCHEMA_VERSION:
        _err(errors, "SCHEMA", f"schema_version must be {SCHEMA_VERSION}")
    if root.get("program") != "MINI_ENTITY_PIPELINE_ALL_IN_ONE":
        _err(errors, "PROGRAM", "unexpected program")

    provenance = _require_dict(root.get("provenance"), "provenance", errors)
    source_sha = _require_str(provenance, "source_main_sha", errors)
    if source_sha and not GIT_SHA.fullmatch(source_sha):
        _err(errors, "SOURCE_SHA", "source_main_sha must be 40 lowercase hex")
    _require_str(provenance, "owner_architecture_commit", errors)

    model = _require_dict(root.get("model"), "model", errors)
    _require_str(model, "model_id", errors)
    _require_str(model, "architecture", errors)
    _require_str(model, "runtime_class", errors)
    _digest(model, "checkpoint_digest", errors)
    _digest(model, "tokenizer_digest", errors)
    n_layers = model.get("n_layers")
    d_model = model.get("d_model")
    if not isinstance(n_layers, int) or isinstance(n_layers, bool) or n_layers < 2:
        _err(errors, "MODEL_SHAPE", "n_layers must be integer >=2")
    if not isinstance(d_model, int) or isinstance(d_model, bool) or d_model < 1:
        _err(errors, "MODEL_SHAPE", "d_model must be positive integer")

    lens = _require_dict(root.get("lens"), "lens", errors)
    _require_str(lens, "implementation", errors)
    _require_str(lens, "implementation_revision", errors)
    _digest(lens, "lens_digest", errors)
    _digest(lens, "fitting_corpus_digest", errors)
    prompt_count = lens.get("prompt_count")
    if not isinstance(prompt_count, int) or isinstance(prompt_count, bool) or prompt_count < 1:
        _err(errors, "LENS_FIT", "prompt_count must be positive integer")
    source_layers = lens.get("source_layers")
    if not isinstance(source_layers, list) or not source_layers:
        _err(errors, "LENS_LAYERS", "source_layers must be non-empty array")
        source_layers = []
    elif any(not isinstance(x, int) or isinstance(x, bool) or x < 0 for x in source_layers):
        _err(errors, "LENS_LAYERS", "source_layers must contain non-negative integers")
    elif len(source_layers) != len(set(source_layers)):
        _err(errors, "LENS_LAYERS", "source_layers must be unique")
    target_layer = lens.get("target_layer")
    if not isinstance(target_layer, int) or isinstance(target_layer, bool) or target_layer < 1:
        _err(errors, "LENS_LAYERS", "target_layer must be integer >=1")
    else:
        if isinstance(n_layers, int) and not isinstance(n_layers, bool) and target_layer >= n_layers:
            _err(errors, "LENS_LAYERS", "target_layer outside model")
        for layer in source_layers:
            if isinstance(layer, int) and layer >= target_layer:
                _err(errors, "LENS_LAYERS", "every source layer must be < target_layer")
    for key in ("dim_batch", "max_seq_len"):
        value = lens.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            _err(errors, "LENS_FIT", f"{key} must be positive integer")

    workspace = _require_dict(root.get("workspace"), "workspace", errors)
    _digest(workspace, "policy_digest", errors)
    cal = _require_dict(workspace.get("slot_calibration"), "slot_calibration", errors)
    status = cal.get("status")
    if status not in ALLOWED_CAL:
        _err(errors, "CALIBRATION", f"status must be one of {sorted(ALLOWED_CAL)}")
    selected = cal.get("selected_max_slots")
    receipt = cal.get("calibration_receipt_digest")
    if status == "UNMEASURED":
        if selected is not None or receipt is not None:
            _err(errors, "CALIBRATION", "unmeasured calibration cannot select slots or bind receipt")
    elif status == "MEASURED":
        if not isinstance(selected, int) or isinstance(selected, bool) or selected < 1:
            _err(errors, "CALIBRATION", "measured selected_max_slots must be positive integer")
        if not isinstance(receipt, str) or not HEX64.fullmatch(receipt):
            _err(errors, "CALIBRATION", "measured calibration requires sha256 receipt")

    authority = _require_dict(root.get("authority"), "authority", errors)
    expected = {
        "canonical_truth": "MiniUnifiedDB",
        "jspace_measurement": "MEASURED_INTERPRETABILITY_NOT_TRUTH",
        "model_output": "CANDIDATE_INFERENCE_ONLY",
        "effect_authority": "DETERMINISTIC_PIPELINE_GATES",
    }
    for key, value in expected.items():
        if authority.get(key) != value:
            _err(errors, "AUTHORITY", f"{key} must equal {value}")

    mode = root.get("mode")
    if mode not in ALLOWED_MODES:
        _err(errors, "MODE", f"mode must be one of {sorted(ALLOWED_MODES)}")
    intervention = root.get("intervention")
    if mode == "OBSERVE_ONLY":
        if intervention not in (None, {}):
            _err(errors, "INTERVENTION", "observe-only manifest cannot carry intervention")
    elif mode == "RESEARCH_INTERVENTION":
        iv = _require_dict(intervention, "intervention", errors)
        _digest(iv, "receipt_digest", errors)
        alpha = iv.get("alpha")
        if not isinstance(alpha, (int, float)) or isinstance(alpha, bool) or not math.isfinite(float(alpha)):
            _err(errors, "INTERVENTION", "alpha must be finite numeric")
        elif float(alpha) == 0.0:
            _err(errors, "INTERVENTION", "research intervention alpha cannot be zero")
        if iv.get("canonical_write_allowed") is not False:
            _err(errors, "INTERVENTION", "canonical_write_allowed must be false")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=pathlib.Path)
    args = parser.parse_args()
    try:
        raw = args.manifest.read_bytes()
        data = json.loads(raw)
    except Exception as exc:
        print(json.dumps({"ok": False, "errors": [f"LOAD:{exc}"]}, sort_keys=True))
        return 2
    errors = validate(data)
    report = {
        "ok": not errors,
        "schema_version": SCHEMA_VERSION,
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "errors": errors,
        "runtime_credit": "ZERO_SOURCE_BINDING_VALIDATION_ONLY",
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
