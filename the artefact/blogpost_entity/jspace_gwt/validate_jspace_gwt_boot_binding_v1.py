#!/usr/bin/env python3
import hashlib
import json
import math
import re
import sys
from pathlib import Path

SCHEMA = "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1"
SOURCE_LOCK_SCHEMA = "mini-entity-bundled-cognition-source-lock/v1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ACTION_ORIGINS = {
    "ZERO",
    "HOOK_TIMER",
    "CLAUDE_CODE",
    "PROXY_SANDBOX_CONTROLLER",
    "OTHER",
}
LOCAL_JSPACE_MODES = {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY"}
SOURCE_LOCK_PATH = (
    Path(__file__).resolve().parents[1]
    / "mini_cognition"
    / "BUNDLED_COGNITION_SOURCE_LOCK_V1.json"
)
SOURCE_LOCK_KEYS = {
    "schema",
    "status",
    "lock_revision",
    "engine_id",
    "model_family",
    "manifest_version",
    "checkpoint_sha256",
    "tokenizer_sha256",
    "runtime_sha256",
    "manifest_identity_sha256",
    "integration_identity_sha256",
    "local_jspace_mode",
    "jlens_upstream_commit",
    "jspace_profile_sha256",
    "lens_file_sha256",
    "lens_profile_sha256",
    "fit_corpus_sha256",
    "measurement_policy_sha256",
    "workspace_policy_sha256",
    "workspace_calibration_sha256",
    "admission_evidence_receipt_sha256",
    "note",
}
SOURCE_LOCK_BOUND_FIELDS = SOURCE_LOCK_KEYS - {"schema", "status", "lock_revision", "note"}


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


def canonical_json_sha256(value: object) -> str:
    try:
        raw = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        fail("NONCANONICAL_JSON_VALUE")
    return hashlib.sha256(raw).hexdigest()


def _load_source_lock() -> tuple[dict, str]:
    try:
        raw = SOURCE_LOCK_PATH.read_bytes()
        data = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        fail("SOURCE_LOCK_READ_OR_JSON_ERROR")
    if not isinstance(data, dict):
        fail("SOURCE_LOCK_OBJECT_REQUIRED")
    keys = set(data)
    if keys != SOURCE_LOCK_KEYS:
        missing = sorted(SOURCE_LOCK_KEYS - keys)
        unknown = sorted(keys - SOURCE_LOCK_KEYS)
        if missing:
            fail("SOURCE_LOCK_MISSING_FIELDS:" + ",".join(missing))
        fail("SOURCE_LOCK_UNKNOWN_FIELDS:" + ",".join(unknown))
    if data.get("schema") != SOURCE_LOCK_SCHEMA:
        fail("SOURCE_LOCK_SCHEMA_MISMATCH")
    revision = data.get("lock_revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        fail("SOURCE_LOCK_REVISION_INVALID")
    status = data.get("status")
    if status not in {"BOUND", "UNBOUND"}:
        fail("SOURCE_LOCK_STATUS_INVALID")
    note = data.get("note")
    if not isinstance(note, str) or not note.strip():
        fail("SOURCE_LOCK_NOTE_REQUIRED")
    if status == "UNBOUND":
        if any(data.get(key) is not None for key in SOURCE_LOCK_BOUND_FIELDS):
            fail("SOURCE_LOCK_UNBOUND_CONTAINS_IDENTITY")
    else:
        for key in (
            "engine_id",
            "model_family",
            "manifest_version",
            "local_jspace_mode",
        ):
            req_str(data, key)
        if data["local_jspace_mode"] not in LOCAL_JSPACE_MODES:
            fail("SOURCE_LOCK_LOCAL_JSPACE_MODE_INVALID")
        req_sha(data, "jlens_upstream_commit", 40)
        for key in (
            "checkpoint_sha256",
            "tokenizer_sha256",
            "runtime_sha256",
            "manifest_identity_sha256",
            "integration_identity_sha256",
            "jspace_profile_sha256",
            "lens_file_sha256",
            "lens_profile_sha256",
            "fit_corpus_sha256",
            "measurement_policy_sha256",
            "workspace_policy_sha256",
            "workspace_calibration_sha256",
            "admission_evidence_receipt_sha256",
        ):
            req_sha(data, key)
    return data, hashlib.sha256(raw).hexdigest()


def _require_expected(observed: str, expected_lock: dict, lock_key: str) -> None:
    expected = expected_lock.get(lock_key)
    if observed != expected:
        fail(f"EXPECTED_BUNDLE_MISMATCH:{lock_key}")


def validate(data: dict) -> None:
    if data.get("schema") != SCHEMA:
        fail("SCHEMA_MISMATCH")

    expected_lock, source_lock_sha256 = _load_source_lock()
    if expected_lock["status"] != "BOUND":
        fail("SOURCE_LOCK_UNBOUND")

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
    manifest_version = req_str(core, "manifest_version")
    engine_id = req_str(core, "engine_id")
    model_family = req_str(core, "model_family")
    checkpoint_sha256 = req_sha(core, "checkpoint_sha256")
    tokenizer_sha256 = req_sha(core, "tokenizer_sha256")
    runtime_sha256 = req_sha(core, "runtime_sha256")
    manifest_sha256 = req_sha(core, "manifest_sha256")
    integration_identity_sha256 = req_sha(core, "integration_identity_sha256")
    observed_source_lock_sha256 = req_sha(core, "source_lock_sha256")
    if observed_source_lock_sha256 != source_lock_sha256:
        fail("SOURCE_LOCK_BYTE_IDENTITY_MISMATCH")
    if not req_bool(core, "exact_bytes_verified"):
        fail("BUNDLED_CORE_BYTES_UNVERIFIED")

    jspace = req_obj(data, "jspace")
    local_jspace_mode = req_str(jspace, "local_mode")
    if local_jspace_mode not in LOCAL_JSPACE_MODES:
        fail("INVALID_LOCAL_JSPACE_MODE")
    jlens_upstream_commit = req_sha(jspace, "jlens_upstream_commit", 40)
    jspace_profile_sha256 = req_sha(jspace, "profile_sha256")
    lens_file_sha256 = req_sha(jspace, "lens_file_sha256")
    lens_profile_sha256 = req_sha(jspace, "lens_profile_sha256")
    fit_corpus_sha256 = req_sha(jspace, "fit_corpus_sha256")
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
    measurement_policy_sha256 = req_sha(jspace, "measurement_policy_sha256")
    if measurement_policy_sha256 != canonical_json_sha256(measurement):
        fail("MEASUREMENT_POLICY_DIGEST_MISMATCH")

    gwt = req_obj(data, "gwt")
    workspace_policy_sha256 = req_sha(gwt, "workspace_policy_sha256")
    workspace_calibration_sha256 = req_sha(gwt, "calibration_sha256")
    req_int(gwt, "slot_count", minimum=1)
    calibration_status = req_str(gwt, "calibration_status")
    if calibration_status not in {
        "MEASURED_EXACT_BUNDLE",
        "UNMEASURED_SOURCE_ONLY",
    }:
        fail("INVALID_GWT_CALIBRATION_STATUS")
    if calibration_status != "MEASURED_EXACT_BUNDLE":
        fail("BOUND_SOURCE_LOCK_REQUIRES_MEASURED_GWT_CALIBRATION")

    # Repository-owned expected identity. The receipt reports observations only;
    # it cannot author the values on the right-hand side of these comparisons.
    for observed, lock_key in (
        (manifest_version, "manifest_version"),
        (engine_id, "engine_id"),
        (model_family, "model_family"),
        (checkpoint_sha256, "checkpoint_sha256"),
        (tokenizer_sha256, "tokenizer_sha256"),
        (runtime_sha256, "runtime_sha256"),
        (manifest_sha256, "manifest_identity_sha256"),
        (integration_identity_sha256, "integration_identity_sha256"),
        (local_jspace_mode, "local_jspace_mode"),
        (jlens_upstream_commit, "jlens_upstream_commit"),
        (jspace_profile_sha256, "jspace_profile_sha256"),
        (lens_file_sha256, "lens_file_sha256"),
        (lens_profile_sha256, "lens_profile_sha256"),
        (fit_corpus_sha256, "fit_corpus_sha256"),
        (measurement_policy_sha256, "measurement_policy_sha256"),
        (workspace_policy_sha256, "workspace_policy_sha256"),
        (workspace_calibration_sha256, "workspace_calibration_sha256"),
    ):
        _require_expected(observed, expected_lock, lock_key)

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


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_jspace_gwt_boot_binding_v1.py RECEIPT.json", file=sys.stderr)
        return 2
    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            fail("TOP_LEVEL_NOT_OBJECT")
        validate(data)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"FAIL {exc}")
        return 1
    print("PASS JSPACE_GWT_BOOT_BINDING_RECEIPT/v1 SOURCE_LOCK_BOUND")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
