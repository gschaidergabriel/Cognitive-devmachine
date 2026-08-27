#!/usr/bin/env python3
"""Normalize retained intermediate receipts into JSPACE_TRACE_ABI/v1.

The normalizer is deterministic and provider-independent. It verifies existing
measurement receipts, separates replay identity from measured evidence and envelope
identity, and never mints canonical truth or raises scientific credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from jspace_execution_identity_v1 import derive_model_execution_id

TRACE_SCHEMA = "JSPACE_TRACE_ABI/v1"
SOURCE_SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1"
MANIFEST_SCHEMA = "JSPACE_TRACE_MANIFEST/v1"
REPLAY_SCHEMA = "JSPACE_EXECUTION_REPLAY_IDENTITY/v1"
MEASURED_SCHEMA = "JSPACE_MEASURED_EVIDENCE_IDENTITY/v1"
ENVELOPE_SCHEMA = "JSPACE_OBSERVATION_ENVELOPE_IDENTITY/v1"
CONTROL_FAMILY_SCHEMA = "JSPACE_CONTROL_FAMILY_IDENTITY/v1"
ALLOWED_STATUS = {"PASS", "SCIENTIFIC_NEGATIVE"}
ALLOWED_CONTROLS = {
    "BASELINE", "+VECTOR", "SIGN_FLIP", "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM", "PERMUTED_SAME_NORM",
}
ALLOWED_SPLITS = {"calibration": "CALIBRATION", "holdout": "CAUSAL_HOLDOUT"}
HEX64 = frozenset("0123456789abcdef")
RUNTIME_RECEIPT_KEYS = (
    "invocation", "prompt_sha256", "layer", "vector_layer", "gain", "control",
    "mode", "seed", "positive_label", "negative_label", "target_score", "hook_calls",
    "pre_activation_sha256", "post_activation_sha256", "applied_vector_sha256",
)


class TraceNormalizationError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _require_hex64(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in HEX64 for ch in value):
        raise TraceNormalizationError(f"{field}_MUST_BE_LOWER_HEX_SHA256")
    return value


def _require_nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TraceNormalizationError(f"{field}_MUST_BE_NONEMPTY_STRING")
    return value


def _runtime_receipt_material(row: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in RUNTIME_RECEIPT_KEYS if key not in row]
    if missing:
        raise TraceNormalizationError("ROW_RUNTIME_RECEIPT_FIELDS_MISSING:" + ",".join(missing))
    return {key: row[key] for key in RUNTIME_RECEIPT_KEYS}


def _validate_runtime_receipt(row: dict[str, Any]) -> str:
    claimed = _require_hex64(row.get("runtime_receipt_sha256"), "runtime_receipt_sha256")
    measured = canonical_sha(_runtime_receipt_material(row))
    if claimed != measured:
        raise TraceNormalizationError("RUNTIME_RECEIPT_DIGEST_MISMATCH")
    return claimed


def _validate_model_execution_id(row: dict[str, Any]) -> str:
    session_id = _require_nonempty(row.get("runtime_session_id"), "runtime_session_id")
    claimed = _require_hex64(row.get("model_execution_id"), "model_execution_id")
    measured = derive_model_execution_id(session_id, row)
    if claimed != measured:
        raise TraceNormalizationError("MODEL_EXECUTION_ID_MISMATCH")
    return claimed


def _source_identity(result: dict[str, Any]) -> dict[str, str]:
    source = result.get("source")
    if not isinstance(source, dict):
        raise TraceNormalizationError("SOURCE_IDENTITY_MISSING")
    return {
        "repo_head": _require_hex64(source.get("repo_head"), "source.repo_head"),
        "repo_tree": _require_hex64(source.get("repo_tree"), "source.repo_tree"),
    }


def _adapter_id(result: dict[str, Any], row: dict[str, Any]) -> str:
    return canonical_sha({
        "schema": "JSPACE_ADAPTER_IDENTITY/v1",
        "model_id": result["model"], "model_revision": result["model_revision"],
        "checkpoint_sha256": result["checkpoint_sha256"],
        "tokenizer_sha256": result["tokenizer_sha256"],
        "runtime_build_sha256": result["runtime_build_sha256"],
        "activation_site": f"model.model.layers[{int(row['layer'])}]:output:last_token",
        "token_position_policy": "LAST_PROMPT_TOKEN",
    })


def _causal_event_id(result: dict[str, Any], row: dict[str, Any], split_id: str) -> str:
    # All matched controls for one prompt/seed/map share the same higher-level event.
    return canonical_sha({
        "schema": "JSPACE_CAUSAL_EVENT_ID/v1",
        "source_repo_head": result["source"]["repo_head"],
        "model_id": result["model"], "model_revision": result["model_revision"],
        "prompt_sha256": row["prompt_sha256"], "seed": int(row["seed"]),
        "split_id": split_id,
        "case_id": row.get("case_id") or "CALIBRATION",
        "label_map_id": row.get("label_map_id") or "CALIBRATION_MAP",
        "positive_label": row["positive_label"], "negative_label": row["negative_label"],
    })


def _control_family_id(event_id: str, row: dict[str, Any]) -> str:
    return canonical_sha({
        "schema": CONTROL_FAMILY_SCHEMA,
        "causal_event_id": event_id,
        "selected_vector_layer": int(row["vector_layer"]),
        "gain": float(row["gain"]),
    })


def _intervention_id(event_id: str, row: dict[str, Any]) -> str | None:
    control = str(row["control"]); mode = str(row.get("mode") or "control")
    if control == "BASELINE" and mode == "control":
        return None
    return canonical_sha({
        "schema": "JSPACE_INTERVENTION_ID/v1", "causal_event_id": event_id,
        "layer": int(row["layer"]), "vector_layer": int(row["vector_layer"]),
        "gain": float(row["gain"]), "control": control, "mode": mode,
        "applied_vector_sha256": row["applied_vector_sha256"],
    })


def _replay_identity(result: dict[str, Any], row: dict[str, Any], event_id: str, adapter_id: str, intervention_id: str | None, model_execution_id: str) -> str:
    return canonical_sha({
        "schema": REPLAY_SCHEMA,
        "causal_event_id": event_id,
        "model_execution_id": model_execution_id,
        "model_id": result["model"], "model_revision": result["model_revision"],
        "checkpoint_sha256": result["checkpoint_sha256"],
        "tokenizer_sha256": result["tokenizer_sha256"],
        "runtime_build_sha256": result["runtime_build_sha256"],
        "loader_consumption_identity": "UNKNOWN",
        "jspace_adapter_id": adapter_id,
        "activation_site": {"layer": int(row["layer"]), "component": "decoder_block_output_residual"},
        "token_position_policy": "LAST_PROMPT_TOKEN",
        "observation_operator": "INTERMEDIATE_RESIDUAL_PRE_POST_PLUS_TARGET_SCORE/v1",
        "intervention_id": intervention_id or "NONE",
        "control_class": str(row["control"]) if intervention_id else "NONE",
        "gain": float(row["gain"]),
        "seed": int(row["seed"]),
        "prompt_sha256": row["prompt_sha256"],
        "producer_schema": SOURCE_SCHEMA,
    })


def _measured_evidence_identity(row: dict[str, Any]) -> str:
    return canonical_sha({
        "schema": MEASURED_SCHEMA,
        "pre_activation_sha256": row["pre_activation_sha256"],
        "post_activation_sha256": row["post_activation_sha256"],
        "applied_vector_sha256": row["applied_vector_sha256"],
        "target_score": float(row["target_score"]),
        "hook_calls": int(row["hook_calls"]),
        "runtime_observed_intervention": bool(row.get("runtime_observed_intervention")),
        "wrong_layer_delta": row.get("wrong_layer_delta"),
        "lesion_delta": row.get("lesion_delta"),
        "rescue_delta": row.get("rescue_delta"),
        "measurement_operator": "INTERMEDIATE_RESIDUAL_PRE_POST_PLUS_TARGET_SCORE/v1",
    })


def _observation_envelope_identity(result: dict[str, Any], row: dict[str, Any]) -> str:
    return canonical_sha({
        "schema": ENVELOPE_SCHEMA,
        "row": row,
        "source_status": result.get("status"),
        "result_classification": result.get("verdict", {}).get("classification"),
    })


def _row_to_trace(result: dict[str, Any], row: dict[str, Any], credit_scope: str) -> dict[str, Any]:
    split_raw = row.get("split")
    if split_raw not in ALLOWED_SPLITS:
        raise TraceNormalizationError(f"UNSUPPORTED_SPLIT:{split_raw}")
    split_id = ALLOWED_SPLITS[str(split_raw)]
    control = str(row.get("control"))
    if control not in ALLOWED_CONTROLS:
        raise TraceNormalizationError(f"UNSUPPORTED_CONTROL:{control}")
    if split_id == "CAUSAL_HOLDOUT":
        _require_nonempty(row.get("case_id"), "case_id")
        _require_nonempty(row.get("label_map_id"), "label_map_id")

    _require_hex64(row.get("prompt_sha256"), "prompt_sha256")
    pre_sha = _require_hex64(row.get("pre_activation_sha256"), "pre_activation_sha256")
    post_sha = _require_hex64(row.get("post_activation_sha256"), "post_activation_sha256")
    vector_sha = _require_hex64(row.get("applied_vector_sha256"), "applied_vector_sha256")
    runtime_receipt = _validate_runtime_receipt(row)
    model_execution_id = _validate_model_execution_id(row)

    event_id = _causal_event_id(result, row, split_id)
    control_family_id = _control_family_id(event_id, row)
    intervention_id = _intervention_id(event_id, row)
    adapter_id = _adapter_id(result, row)
    replay_id = _replay_identity(result, row, event_id, adapter_id, intervention_id, model_execution_id)
    measured_id = _measured_evidence_identity(row)
    envelope_id = _observation_envelope_identity(result, row)
    admission_id = canonical_sha({
        "schema": "JSPACE_TRACE_ADMISSION_ID/v1",
        "execution_replay_identity_sha256": replay_id,
        "observation_envelope_sha256": envelope_id,
    })

    trace = {
        "schema": TRACE_SCHEMA,
        "causal_event_id": event_id,
        "admission_id": admission_id,
        "generation": 1,
        "model_id": result["model"], "model_revision": result["model_revision"],
        "checkpoint_sha256": result["checkpoint_sha256"],
        "tokenizer_sha256": result["tokenizer_sha256"],
        "runtime_build_sha256": result["runtime_build_sha256"],
        "loader_consumption_identity": "UNKNOWN",
        "model_execution_id": model_execution_id,
        "inference_receipt_id": runtime_receipt,
        "jspace_adapter_id": adapter_id,
        "activation_site": {
            "layer": int(row["layer"]), "vector_source_layer": int(row["vector_layer"]),
            "component": "decoder_block_output_residual", "token_position": "last_prompt_token",
        },
        "token_position_policy": "LAST_PROMPT_TOKEN",
        "observation_class": "RAW_ACTIVATION_MEASUREMENT",
        "activation_or_projection_sha256": post_sha,
        "pre_activation_sha256": pre_sha,
        "applied_vector_sha256": vector_sha,
        "semantic_family_id": canonical_sha({
            "schema": "JSPACE_SEMANTIC_FAMILY/v1",
            "derivation_input_family_sha256": result.get("derivation", {}).get("label_independence", {}).get("derivation_input_family_sha256"),
            "task": "APPROVE_DISAPPROVE_STANCE",
        }),
        "task_family_id": canonical_sha({"schema": "JSPACE_TASK_FAMILY/v1", "task": "BINARY_STANCE_CONTROL"}),
        "context_polarity_id": row.get("label_map_id") or "NONE",
        "split_id": split_id,
        "intervention_id": intervention_id or "NONE",
        "control_class": control if intervention_id else "NONE",
        "control_family_id": control_family_id,
        "execution_replay_identity_sha256": replay_id,
        "measured_evidence_sha256": measured_id,
        "observation_envelope_sha256": envelope_id,
        "target_metrics": {
            "target_score": float(row["target_score"]), "gain": float(row["gain"]),
            "hook_calls": int(row["hook_calls"]),
            "wrong_layer_delta": row.get("wrong_layer_delta"),
            "lesion_delta": row.get("lesion_delta"), "rescue_delta": row.get("rescue_delta"),
        },
        "off_target_metrics": {},
        "result_classification": str(result.get("verdict", {}).get("classification") or result["status"]),
        "credit_scope": credit_scope,
        "source_identity": {"repo_head": result["source"]["repo_head"], "repo_tree": result["source"]["repo_tree"]},
        "canonical_truth": False,
        "truth_status": "CANDIDATE_MEASUREMENT_ONLY",
        "dataset_admission_eligible": False,
        "dataset_admission_blocker": "LOADER_CONSUMPTION_IDENTITY_UNKNOWN_AND_OFF_TARGET_METRICS_UNMEASURED",
    }
    trace["trace_sha256"] = canonical_sha(trace)
    return trace


def classify_reemission(existing: dict[str, Any], incoming: dict[str, Any]) -> str:
    if existing["execution_replay_identity_sha256"] != incoming["execution_replay_identity_sha256"]:
        return "NEW_EXECUTION_IDENTITY"
    if existing["measured_evidence_sha256"] != incoming["measured_evidence_sha256"]:
        return "JSPACE_REPLAY_IDENTITY_CONFLICT"
    return "DUPLICATE_REEMISSION"


def normalize_result(result: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if result.get("schema") != SOURCE_SCHEMA:
        raise TraceNormalizationError("SOURCE_SCHEMA_MISMATCH")
    status = str(result.get("status"))
    source = _source_identity(result)
    if status not in ALLOWED_STATUS:
        manifest = {
            "schema": MANIFEST_SCHEMA, "source_schema": SOURCE_SCHEMA,
            "source_identity": source, "source_status": status, "trace_count": 0,
            "normalization_status": "NO_MEASURED_TRACE_FOR_BLOCKED_SOURCE", "credit_scope": "NONE",
            "dataset_admission_eligible": False,
        }
        manifest["manifest_sha256"] = canonical_sha(manifest)
        return [], manifest

    for field in ("model", "model_revision"):
        _require_nonempty(result.get(field), field)
    for field in ("checkpoint_sha256", "tokenizer_sha256", "runtime_build_sha256"):
        _require_hex64(result.get(field), field)
    credit_scope = _require_nonempty(result.get("credit_scope"), "credit_scope")

    rows: list[dict[str, Any]] = []
    for key in ("calibration_rows", "holdout_rows"):
        value = result.get(key)
        if not isinstance(value, list):
            raise TraceNormalizationError(f"{key}_MUST_BE_LIST")
        rows.extend(value)
    traces = [_row_to_trace(result, row, credit_scope) for row in rows]
    traces.sort(key=lambda t: (t["control_family_id"], t["execution_replay_identity_sha256"], t["admission_id"]))
    if len({t["admission_id"] for t in traces}) != len(traces):
        raise TraceNormalizationError("DUPLICATE_TRACE_ADMISSION_ID")

    manifest = {
        "schema": MANIFEST_SCHEMA, "source_schema": SOURCE_SCHEMA, "source_identity": source,
        "source_result_sha256": result.get("result_sha256") or canonical_sha({k: v for k, v in result.items() if k != "result_sha256"}),
        "source_status": status, "trace_count": len(traces),
        "trace_set_sha256": canonical_sha([t["trace_sha256"] for t in traces]),
        "execution_replay_set_sha256": canonical_sha([t["execution_replay_identity_sha256"] for t in traces]),
        "measured_evidence_set_sha256": canonical_sha([t["measured_evidence_sha256"] for t in traces]),
        "normalization_status": "PASS", "credit_scope": credit_scope,
        "loader_consumption_identity_status": "UNKNOWN_PRESERVED_FAIL_CLOSED",
        "truth_status": "CANDIDATE_MEASUREMENT_ONLY",
        "off_target_metric_status": "NOT_MEASURED_BY_SOURCE_PROTOCOL",
        "dataset_admission_eligible": False,
        "dataset_admission_blocker": "LOADER_CONSUMPTION_IDENTITY_UNKNOWN_AND_OFF_TARGET_METRICS_UNMEASURED",
    }
    manifest["manifest_sha256"] = canonical_sha(manifest)
    return traces, manifest


def write_outputs(result_path: Path, output_dir: Path) -> tuple[Path, Path]:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise TraceNormalizationError("RESULT_ROOT_MUST_BE_OBJECT")
    traces, manifest = normalize_result(result)
    output_dir.mkdir(parents=True, exist_ok=True)
    trace_path = output_dir / "jspace_trace_abi_v1.jsonl"
    manifest_path = output_dir / "jspace_trace_manifest_v1.json"
    trace_path.write_text("".join(json.dumps(t, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n" for t in traces), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return trace_path, manifest_path


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--result", required=True); ap.add_argument("--output-dir", required=True)
    args = ap.parse_args(list(argv) if argv is not None else None)
    try:
        write_outputs(Path(args.result), Path(args.output_dir)); return 0
    except Exception as exc:
        out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
        blocked = {"schema": MANIFEST_SCHEMA, "normalization_status": "BLOCKED_FAIL_CLOSED", "reason": f"{type(exc).__name__}:{str(exc)[:1200]}", "trace_count": 0, "credit_scope": "NONE", "dataset_admission_eligible": False}
        blocked["manifest_sha256"] = canonical_sha(blocked)
        (out / "jspace_trace_manifest_v1.json").write_text(json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        trace_path = out / "jspace_trace_abi_v1.jsonl"
        if trace_path.exists(): trace_path.unlink()
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
