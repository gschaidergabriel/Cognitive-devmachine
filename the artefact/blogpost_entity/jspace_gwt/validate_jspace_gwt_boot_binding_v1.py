#!/usr/bin/env python3
import hashlib
import json
import math
import re
import struct
import sys
from pathlib import Path

SCHEMA = "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1"
SEMANTIC_DIGEST_METHOD = "ordered-fp32-finite-v1"
SEMANTIC_DIGEST_DOMAIN = b"CLAY/JSPACE_LENS_SEMANTIC/ordered-fp32-finite-v1\x00"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ACTION_ORIGINS = {
    "ZERO",
    "HOOK_TIMER",
    "CLAUDE_CODE",
    "PROXY_SANDBOX_CONTROLLER",
    "OTHER",
}


class ValidationError(ValueError):
    pass


def fail(code: str) -> None:
    raise ValidationError(code)


def req_obj(parent: dict, key: str) -> dict:
    value = parent.get(key)
    if not isinstance(value, dict):
        fail(f"MISSING_OBJECT:{key}")
    return value


def req_str(parent: dict, key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f"MISSING_STRING:{key}")
    return value


def req_bool(parent: dict, key: str) -> bool:
    value = parent.get(key)
    if not isinstance(value, bool):
        fail(f"MISSING_BOOL:{key}")
    return value


def req_int(parent: dict, key: str, *, minimum: int = 0) -> int:
    value = parent.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        fail(f"INVALID_INT:{key}")
    return value


def req_finite_number(parent: dict, key: str, *, minimum: float | None = None) -> float:
    value = parent.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(f"INVALID_NUMBER:{key}")
    value = float(value)
    if not math.isfinite(value):
        fail(f"NONFINITE_NUMBER:{key}")
    if minimum is not None and value < minimum:
        fail(f"NUMBER_BELOW_MIN:{key}")
    return value


def req_sha(parent: dict, key: str, length: int = 64) -> str:
    value = req_str(parent, key)
    regex = HEX64 if length == 64 else HEX40
    if regex.fullmatch(value) is None:
        fail(f"INVALID_SHA{length}:{key}")
    return value


def req_source_layers(parent: dict, key: str = "source_layers") -> list[int]:
    value = parent.get(key)
    if (
        not isinstance(value, list)
        or not value
        or any(isinstance(layer, bool) or not isinstance(layer, int) or layer < 0 for layer in value)
    ):
        fail("INVALID_SOURCE_LAYERS")
    if value != sorted(set(value)):
        fail("SOURCE_LAYERS_NOT_CANONICAL")
    return value


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def semantic_digest_from_lens_checkpoint(path: str | Path) -> dict:
    """Hash persisted JacobianLens semantics independently of torch-save container bytes."""
    try:
        import torch
    except ImportError as exc:
        raise ValidationError("TORCH_REQUIRED_FOR_LENS_SEMANTIC_DIGEST") from exc

    try:
        checkpoint = torch.load(str(path), map_location="cpu", weights_only=True)
    except Exception as exc:
        raise ValidationError(f"LENS_LOAD_FAILED:{exc.__class__.__name__}") from exc

    if not isinstance(checkpoint, dict):
        fail("LENS_CHECKPOINT_NOT_OBJECT")
    required = {"J", "n_prompts", "source_layers", "d_model"}
    if not required.issubset(checkpoint):
        fail("LENS_CHECKPOINT_FIELDS_MISSING")

    n_prompts = checkpoint["n_prompts"]
    d_model = checkpoint["d_model"]
    if isinstance(n_prompts, bool) or not isinstance(n_prompts, int) or n_prompts <= 0:
        fail("BAD_LENS_N_PROMPTS")
    if isinstance(d_model, bool) or not isinstance(d_model, int) or d_model <= 0:
        fail("BAD_LENS_D_MODEL")

    source_layers = req_source_layers({"source_layers": checkpoint["source_layers"]})
    matrices = checkpoint["J"]
    if not isinstance(matrices, dict) or set(matrices) != set(source_layers):
        fail("LENS_MATRIX_LAYER_SET_MISMATCH")

    digest = hashlib.sha256()
    digest.update(SEMANTIC_DIGEST_DOMAIN)
    digest.update(struct.pack("<qqq", n_prompts, d_model, len(source_layers)))

    for layer in source_layers:
        matrix = matrices[layer]
        if not isinstance(matrix, torch.Tensor):
            fail("LENS_MATRIX_NOT_TENSOR")
        matrix = matrix.detach().to(device="cpu", dtype=torch.float32).contiguous()
        if matrix.ndim != 2 or tuple(matrix.shape) != (d_model, d_model):
            fail("LENS_MATRIX_SHAPE_MISMATCH")
        if not bool(torch.isfinite(matrix).all().item()):
            fail("LENS_POST_LOAD_NONFINITE")
        digest.update(struct.pack("<qqq", layer, matrix.shape[0], matrix.shape[1]))
        payload = matrix.numpy().astype("<f4", copy=False).tobytes(order="C")
        digest.update(payload)

    return {
        "artifact_sha256": sha256_file(path),
        "semantic_sha256": digest.hexdigest(),
        "semantic_digest_method": SEMANTIC_DIGEST_METHOD,
        "n_prompts": n_prompts,
        "d_model": d_model,
        "source_layers": source_layers,
    }


def validate(data: dict) -> None:
    if data.get("schema") != SCHEMA:
        fail("SCHEMA_MISMATCH")

    source = req_obj(data, "source")
    req_sha(source, "main_sha", 40)
    req_sha(source, "tree_sha", 40)
    dirty = req_bool(source, "dirty")
    if dirty:
        req_sha(source, "dirty_diff_sha256")

    executor = req_obj(data, "executor")
    if req_str(executor, "host_class") != "UBUNTU":
        fail("EXECUTOR_NOT_UBUNTU")
    req_sha(executor, "host_identity_sha256")
    req_str(executor, "kernel")

    core = req_obj(data, "bundled_core")
    req_str(core, "manifest_version")
    req_str(core, "engine_id")
    req_str(core, "model_family")
    req_sha(core, "checkpoint_sha256")
    req_sha(core, "tokenizer_sha256")
    req_sha(core, "runtime_sha256")
    req_sha(core, "manifest_sha256")
    if not req_bool(core, "exact_bytes_verified"):
        fail("BUNDLED_CORE_BYTES_UNVERIFIED")

    jspace = req_obj(data, "jspace")
    req_sha(jspace, "jlens_upstream_commit", 40)
    req_sha(jspace, "lens_file_sha256")
    req_sha(jspace, "lens_semantic_sha256")
    if req_str(jspace, "lens_semantic_digest_method") != SEMANTIC_DIGEST_METHOD:
        fail("UNSUPPORTED_LENS_SEMANTIC_DIGEST_METHOD")
    req_sha(jspace, "lens_profile_sha256")
    req_sha(jspace, "fit_corpus_sha256")
    req_int(jspace, "n_prompts", minimum=1)
    req_int(jspace, "d_model", minimum=1)
    req_source_layers(jspace)
    req_int(jspace, "sparsity_k", minimum=1)
    skip_first = req_int(jspace, "skip_first_positions", minimum=0)
    req_str(jspace, "storage_dtype")

    numeric = req_obj(jspace, "numeric_integrity")
    if not req_bool(numeric, "pre_save_all_finite"):
        fail("LENS_PRE_SAVE_NONFINITE")
    if not req_bool(numeric, "post_load_all_finite"):
        fail("LENS_POST_LOAD_NONFINITE")
    req_finite_number(numeric, "max_abs_pre_save", minimum=0.0)
    req_finite_number(numeric, "max_abs_post_load", minimum=0.0)

    measurement = req_obj(jspace, "measurement_policy")
    min_pos = req_int(measurement, "minimum_readout_position", minimum=0)
    if min_pos < skip_first:
        fail("JSPACE_UNFITTED_POSITION_POLICY")
    positions = measurement.get("observed_readout_positions")
    if not isinstance(positions, list) or not positions:
        fail("MISSING_READOUT_POSITIONS")
    for position in positions:
        if isinstance(position, bool) or not isinstance(position, int) or position < min_pos:
            fail("JSPACE_UNFITTED_POSITION")
    if not req_bool(measurement, "prompt_copy_confound_guard_enabled"):
        fail("PROMPT_COPY_CONFOUND_GUARD_DISABLED")

    gwt = req_obj(data, "gwt")
    req_sha(gwt, "workspace_policy_sha256")
    req_sha(gwt, "calibration_sha256")
    req_int(gwt, "slot_count", minimum=1)
    if req_str(gwt, "calibration_status") not in {"MEASURED_EXACT_BUNDLE", "UNMEASURED_SOURCE_ONLY"}:
        fail("INVALID_GWT_CALIBRATION_STATUS")

    zero = req_obj(data, "zero_grf")
    req_sha(zero, "zero_identity_sha256")
    req_sha(zero, "grf_sha256")
    req_sha(zero, "projection_policy_sha256")

    claude = req_obj(data, "claude_adapter")
    req_str(claude, "adapter_version")
    req_sha(claude, "capability_profile_sha256")
    req_bool(claude, "enabled")

    inference = req_obj(data, "inference")
    if req_str(inference, "first_engine_choice") not in {"BUNDLED_LOCAL_08B", "CLAUDE_CODE", "NO_MODEL_REQUIRED", "OTHER_ADMITTED"}:
        fail("INVALID_FIRST_ENGINE_CHOICE")
    req_str(inference, "origin_attribution")
    first_actions = inference.get("first_actions")
    if not isinstance(first_actions, list) or not first_actions:
        fail("MISSING_FIRST_ACTIONS")
    seen_action_ids: set[str] = set()
    for action in first_actions:
        if not isinstance(action, dict):
            fail("FIRST_ACTION_NOT_OBJECT")
        action_id = req_str(action, "action_id")
        if action_id in seen_action_ids:
            fail("DUPLICATE_FIRST_ACTION_ID")
        seen_action_ids.add(action_id)
        origin = req_str(action, "origin")
        if origin not in ACTION_ORIGINS:
            fail("INVALID_FIRST_ACTION_ORIGIN")
        if origin == "OTHER":
            req_str(action, "origin_detail")
        req_bool(action, "effect_requested")

    policy = req_obj(data, "policy")
    free_only = req_bool(policy, "free_only")
    paid_network = req_int(policy, "paid_or_unknown_network_attempts", minimum=0)
    secret_lookups = req_int(policy, "paid_or_unknown_secret_lookups", minimum=0)
    if free_only and (paid_network != 0 or secret_lookups != 0):
        fail("FREE_ONLY_BOUNDARY_BREACH")

    authority = req_obj(data, "authority")
    required_true = {
        "miniunifieddb_is_truth_authority",
        "claude_result_is_candidate_only",
        "jspace_measurement_is_not_truth",
        "gwt_workspace_is_not_truth",
        "effect_gate_required",
    }
    for key in required_true:
        if not req_bool(authority, key):
            fail(f"AUTHORITY_LAW_FALSE:{key}")

    claims = req_obj(data, "claims")
    if req_str(claims, "whole_gwt_credit") != "ZERO":
        fail("BOOT_RECEIPT_CANNOT_GRANT_WHOLE_GWT_CREDIT")
    if req_str(claims, "whole_product") != "IN_PROGRESS":
        fail("BOOT_RECEIPT_CANNOT_GRANT_WHOLE_PRODUCT_PASS")


def verify_lens_artifact(data: dict, lens_path: str | Path) -> None:
    validate(data)
    observed = semantic_digest_from_lens_checkpoint(lens_path)
    jspace = data["jspace"]
    if observed["artifact_sha256"] != jspace["lens_file_sha256"]:
        fail("LENS_FILE_HASH_MISMATCH")
    if observed["semantic_sha256"] != jspace["lens_semantic_sha256"]:
        fail("LENS_SEMANTIC_HASH_MISMATCH")
    if observed["semantic_digest_method"] != jspace["lens_semantic_digest_method"]:
        fail("LENS_SEMANTIC_METHOD_MISMATCH")
    if observed["n_prompts"] != jspace["n_prompts"]:
        fail("LENS_PROMPT_COUNT_MISMATCH")
    if observed["d_model"] != jspace["d_model"]:
        fail("LENS_D_MODEL_MISMATCH")
    if observed["source_layers"] != jspace["source_layers"]:
        fail("LENS_SOURCE_LAYERS_MISMATCH")


def reject_nonfinite_json(_: str):
    fail("NONFINITE_JSON")


def main() -> int:
    if len(sys.argv) not in {2, 3}:
        print("usage: validate_jspace_gwt_boot_binding_v1.py RECEIPT.json [LENS.pt]", file=sys.stderr)
        return 2
    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"), parse_constant=reject_nonfinite_json)
        if not isinstance(data, dict):
            fail("TOP_LEVEL_NOT_OBJECT")
        if len(sys.argv) == 3:
            verify_lens_artifact(data, sys.argv[2])
        else:
            validate(data)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"FAIL {exc}")
        return 1
    suffix = " EXACT_LENS_ARTIFACT_VERIFIED" if len(sys.argv) == 3 else " STRUCTURAL_ONLY"
    print("PASS JSPACE_GWT_BOOT_BINDING_RECEIPT/v1" + suffix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
