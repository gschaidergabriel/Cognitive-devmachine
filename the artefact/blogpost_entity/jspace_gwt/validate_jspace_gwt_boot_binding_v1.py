#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MINI_COGNITION = HERE.parent / "mini_cognition"
CANONICAL_SOURCE_LOCK_PATH = MINI_COGNITION / "bundled_cognition_source_lock_v1.json"
if str(MINI_COGNITION) not in sys.path:
    sys.path.insert(0, str(MINI_COGNITION))

from bundled_cognition_manifest_v1 import (  # noqa: E402
    ManifestError as BundledManifestError,
    SCHEMA as BUNDLED_MANIFEST_SCHEMA,
    load_and_validate as load_bundled_manifest,
)

SCHEMA = "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1"
SOURCE_LOCK_SCHEMA = "BUNDLED_COGNITION_SOURCE_LOCK/v1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ACTION_ORIGINS = {"ZERO", "HOOK_TIMER", "CLAUDE_CODE", "PROXY_SANDBOX_CONTROLLER", "OTHER"}


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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_source_lock(lock: dict) -> None:
    if lock.get("schema") != SOURCE_LOCK_SCHEMA:
        fail("SOURCE_LOCK_SCHEMA_MISMATCH")
    allowed = {
        "schema",
        "status",
        "authority",
        "manifest_file_sha256",
        "manifest_identity_sha256",
        "integration_identity_sha256",
        "note",
    }
    unknown = sorted(set(lock) - allowed)
    if unknown:
        fail("SOURCE_LOCK_UNKNOWN_FIELDS:" + ",".join(unknown))
    if req_str(lock, "status") != "BOUND":
        fail("SOURCE_LOCK_NOT_BOUND")
    if req_str(lock, "authority") != "repository_source_tree":
        fail("SOURCE_LOCK_AUTHORITY_INVALID")
    req_sha(lock, "manifest_file_sha256")
    req_sha(lock, "manifest_identity_sha256")
    req_sha(lock, "integration_identity_sha256")
    if "note" in lock:
        req_str(lock, "note")


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
    if "quantization_runtime_identity" in core:
        req_str(core, "quantization_runtime_identity")
    if not req_bool(core, "exact_bytes_verified"):
        fail("BUNDLED_CORE_BYTES_UNVERIFIED")

    jspace = req_obj(data, "jspace")
    req_sha(jspace, "jlens_upstream_commit", 40)
    req_sha(jspace, "jspace_profile_sha256")
    req_sha(jspace, "lens_file_sha256")
    req_sha(jspace, "lens_profile_sha256")
    req_sha(jspace, "fit_corpus_sha256")
    if "steering_calibration_sha256" in jspace:
        req_sha(jspace, "steering_calibration_sha256")
    req_int(jspace, "n_prompts", minimum=1)
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
    if req_str(gwt, "calibration_status") not in {
        "MEASURED_EXACT_BUNDLE",
        "UNMEASURED_SOURCE_ONLY",
    }:
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
    if req_str(inference, "first_engine_choice") not in {
        "BUNDLED_LOCAL_08B",
        "CLAUDE_CODE",
        "NO_MODEL_REQUIRED",
        "OTHER_ADMITTED",
    }:
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

    authority = req_obj(data, "authority")
    for key in {
        "miniunifieddb_is_truth_authority",
        "claude_result_is_candidate_only",
        "jspace_measurement_is_not_truth",
        "gwt_workspace_is_not_truth",
        "effect_gate_required",
    }:
        if not req_bool(authority, key):
            fail(f"AUTHORITY_LAW_FALSE:{key}")

    claims = req_obj(data, "claims")
    if req_str(claims, "whole_gwt_credit") != "ZERO":
        fail("BOOT_RECEIPT_CANNOT_GRANT_WHOLE_GWT_CREDIT")
    if req_str(claims, "whole_product") != "IN_PROGRESS":
        fail("BOOT_RECEIPT_CANNOT_GRANT_WHOLE_PRODUCT_PASS")


def validate_manifest_binding(data: dict, manifest_path: Path, source_lock: dict) -> None:
    validate_source_lock(source_lock)
    try:
        validated = load_bundled_manifest(manifest_path)
    except BundledManifestError as exc:
        fail(f"BUNDLED_MANIFEST_INVALID:{exc}")

    raw_sha = sha256_file(manifest_path)
    if raw_sha != req_sha(source_lock, "manifest_file_sha256"):
        fail("SOURCE_LOCK_MANIFEST_FILE_MISMATCH")
    if validated.manifest_identity_sha256 != req_sha(source_lock, "manifest_identity_sha256"):
        fail("SOURCE_LOCK_MANIFEST_IDENTITY_MISMATCH")
    if validated.integration_identity_sha256 != req_sha(source_lock, "integration_identity_sha256"):
        fail("SOURCE_LOCK_INTEGRATION_IDENTITY_MISMATCH")

    manifest = validated.manifest
    core = req_obj(data, "bundled_core")
    if req_str(core, "manifest_version") != BUNDLED_MANIFEST_SCHEMA:
        fail("BUNDLED_MANIFEST_VERSION_MISMATCH")
    if req_sha(core, "manifest_sha256") != raw_sha:
        fail("BOOT_MANIFEST_FILE_MISMATCH")
    if req_str(core, "engine_id") != manifest["engine_id"]:
        fail("BOOT_ENGINE_ID_MISMATCH")
    if req_str(core, "model_family") != manifest["model_family"]:
        fail("BOOT_MODEL_FAMILY_MISMATCH")
    if req_sha(core, "checkpoint_sha256") != manifest["checkpoint_digest"]:
        fail("BOOT_CHECKPOINT_MISMATCH")
    if req_sha(core, "tokenizer_sha256") != manifest["tokenizer_digest"]:
        fail("BOOT_TOKENIZER_MISMATCH")

    expected_runtime_identity = manifest.get("quantization_runtime_identity")
    observed_runtime_identity = core.get("quantization_runtime_identity")
    if expected_runtime_identity is None:
        if observed_runtime_identity is not None:
            fail("BOOT_UNEXPECTED_QUANTIZATION_RUNTIME_IDENTITY")
    elif observed_runtime_identity != expected_runtime_identity:
        fail("BOOT_QUANTIZATION_RUNTIME_IDENTITY_MISMATCH")

    jspace = req_obj(data, "jspace")
    if req_sha(jspace, "jspace_profile_sha256") != manifest["jspace_profile_digest"]:
        fail("BOOT_JSPACE_PROFILE_MISMATCH")
    if req_sha(jspace, "lens_profile_sha256") != manifest["lens_profile_digest"]:
        fail("BOOT_LENS_PROFILE_MISMATCH")

    expected_steering = manifest.get("steering_calibration_digest")
    observed_steering = jspace.get("steering_calibration_sha256")
    if expected_steering is None:
        if observed_steering is not None:
            fail("BOOT_UNEXPECTED_STEERING_CALIBRATION")
    elif observed_steering != expected_steering:
        fail("BOOT_STEERING_CALIBRATION_MISMATCH")

    gwt = req_obj(data, "gwt")
    if req_sha(gwt, "calibration_sha256") != manifest["workspace_calibration_digest"]:
        fail("BOOT_WORKSPACE_CALIBRATION_MISMATCH")


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "usage: validate_jspace_gwt_boot_binding_v1.py RECEIPT.json BUNDLED_MANIFEST.json",
            file=sys.stderr,
        )
        return 2
    try:
        receipt_path = Path(sys.argv[1])
        manifest_path = Path(sys.argv[2])
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
        source_lock = json.loads(CANONICAL_SOURCE_LOCK_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            fail("TOP_LEVEL_NOT_OBJECT")
        if not isinstance(source_lock, dict):
            fail("SOURCE_LOCK_TOP_LEVEL_NOT_OBJECT")
        validate(data)
        validate_manifest_binding(data, manifest_path, source_lock)
    except (OSError, json.JSONDecodeError, ValidationError, BundledManifestError) as exc:
        print(f"FAIL {exc}")
        return 1
    print("PASS JSPACE_GWT_BOOT_BINDING_RECEIPT/v1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
