#!/usr/bin/env python3
import argparse
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MINI_COGNITION = HERE.parent / "mini_cognition"
if str(MINI_COGNITION) not in sys.path:
    sys.path.insert(0, str(MINI_COGNITION))

from bundled_cognition_manifest_v1 import ManifestError, ValidatedManifest, load_and_validate

SCHEMA = "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_ORIGINS = {"ZERO", "HOOK_TIMER", "CLAUDE_CODE", "PROXY_SANDBOX_CONTROLLER", "OTHER"}
ZERO_CREDIT_FIELDS = {
    "bundled_08b_exact_runtime_credit",
    "jspace_runtime_credit",
    "whole_gwt_credit",
    "claude_code_adapter_runtime_credit",
    "canonical_semantics_credit",
}


class ValidationError(ValueError):
    pass


def fail(code: str) -> None:
    raise ValidationError(code)


def req_obj(parent: dict, key: str) -> dict:
    value = parent.get(key)
    if type(value) is not dict:
        fail(f"MISSING_OBJECT:{key}")
    return value


def req_str(parent: dict, key: str) -> str:
    value = parent.get(key)
    if type(value) is not str or not value.strip():
        fail(f"MISSING_STRING:{key}")
    return value


def req_bool(parent: dict, key: str) -> bool:
    value = parent.get(key)
    if type(value) is not bool:
        fail(f"MISSING_BOOL:{key}")
    return value


def req_int(parent: dict, key: str, *, minimum: int = 0) -> int:
    value = parent.get(key)
    if type(value) is not int or value < minimum:
        fail(f"INVALID_INT:{key}")
    return value


def req_finite_number(parent: dict, key: str, *, minimum: float | None = None) -> float:
    value = parent.get(key)
    if type(value) not in {int, float}:
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


def bind_actual_manifest(data: dict, manifest: ValidatedManifest, expected_manifest_sha256: str) -> None:
    if HEX64.fullmatch(expected_manifest_sha256) is None:
        fail("EXPECTED_MANIFEST_SHA256_INVALID")
    if manifest.manifest_identity_sha256 != expected_manifest_sha256:
        fail("SOURCE_LOCK_MANIFEST_MISMATCH")

    m = manifest.manifest
    core = req_obj(data, "bundled_core")
    if req_sha(core, "manifest_sha256") != manifest.manifest_identity_sha256:
        fail("RECEIPT_MANIFEST_MISMATCH")
    if req_sha(core, "integration_identity_sha256") != manifest.integration_identity_sha256:
        fail("RECEIPT_INTEGRATION_IDENTITY_MISMATCH")
    if req_str(core, "engine_id") != m["engine_id"]:
        fail("MANIFEST_COMPONENT_MISMATCH:engine_id")
    if req_str(core, "model_family") != m["model_family"]:
        fail("MANIFEST_COMPONENT_MISMATCH:model_family")
    if req_sha(core, "checkpoint_sha256") != m["checkpoint_digest"]:
        fail("MANIFEST_COMPONENT_MISMATCH:checkpoint_digest")
    if req_sha(core, "tokenizer_sha256") != m["tokenizer_digest"]:
        fail("MANIFEST_COMPONENT_MISMATCH:tokenizer_digest")

    runtime_digest = m.get("runtime_digest")
    if runtime_digest is None:
        fail("BOOT_MANIFEST_RUNTIME_DIGEST_REQUIRED")
    if req_sha(core, "runtime_sha256") != runtime_digest:
        fail("MANIFEST_COMPONENT_MISMATCH:runtime_digest")

    runtime_identity = m.get("quantization_runtime_identity")
    if runtime_identity is None:
        fail("BOOT_MANIFEST_RUNTIME_IDENTITY_REQUIRED")
    if req_str(core, "runtime_identity") != runtime_identity:
        fail("MANIFEST_COMPONENT_MISMATCH:quantization_runtime_identity")

    jspace = req_obj(data, "jspace")
    if req_sha(jspace, "jspace_profile_sha256") != m["jspace_profile_digest"]:
        fail("MANIFEST_COMPONENT_MISMATCH:jspace_profile_digest")
    if req_sha(jspace, "lens_profile_sha256") != m["lens_profile_digest"]:
        fail("MANIFEST_COMPONENT_MISMATCH:lens_profile_digest")
    gwt = req_obj(data, "gwt")
    if req_sha(gwt, "calibration_sha256") != m["workspace_calibration_digest"]:
        fail("MANIFEST_COMPONENT_MISMATCH:workspace_calibration_digest")


def validate(
    data: dict,
    *,
    manifest: ValidatedManifest,
    expected_manifest_sha256: str,
    expected_main_sha: str,
    expected_tree_sha: str,
) -> None:
    if data.get("schema") != SCHEMA:
        fail("SCHEMA_MISMATCH")

    source = req_obj(data, "source")
    main_sha = req_sha(source, "main_sha", 40)
    tree_sha = req_sha(source, "tree_sha", 40)
    if main_sha != expected_main_sha:
        fail("SOURCE_MAIN_SHA_MISMATCH")
    if tree_sha != expected_tree_sha:
        fail("SOURCE_TREE_SHA_MISMATCH")
    dirty = req_bool(source, "dirty")
    if dirty:
        req_sha(source, "dirty_diff_sha256")
    elif source.get("dirty_diff_sha256") is not None:
        fail("DIRTY_DIFF_PRESENT_FOR_CLEAN_SOURCE")

    executor = req_obj(data, "executor")
    if req_str(executor, "host_class") != "UBUNTU":
        fail("EXECUTOR_NOT_UBUNTU")
    req_sha(executor, "host_identity_sha256")
    req_str(executor, "kernel")

    core = req_obj(data, "bundled_core")
    req_str(core, "manifest_version")
    req_str(core, "engine_id")
    req_str(core, "model_family")
    req_str(core, "runtime_identity")
    req_sha(core, "checkpoint_sha256")
    req_sha(core, "tokenizer_sha256")
    req_sha(core, "runtime_sha256")
    req_sha(core, "manifest_sha256")
    req_sha(core, "integration_identity_sha256")
    if not req_bool(core, "exact_bytes_verified"):
        fail("BUNDLED_CORE_BYTES_UNVERIFIED")

    jspace = req_obj(data, "jspace")
    req_sha(jspace, "jlens_upstream_commit", 40)
    req_sha(jspace, "jspace_profile_sha256")
    req_sha(jspace, "lens_file_sha256")
    req_sha(jspace, "lens_profile_sha256")
    req_sha(jspace, "fit_corpus_sha256")
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
    if type(positions) is not list or not positions:
        fail("MISSING_READOUT_POSITIONS")
    for position in positions:
        if type(position) is not int or position < min_pos:
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
    origin = req_str(inference, "origin_attribution")
    if origin not in ALLOWED_ORIGINS:
        fail("INVALID_ORIGIN_ATTRIBUTION")
    if origin == "OTHER":
        req_str(inference, "origin_detail")

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
    for key in ZERO_CREDIT_FIELDS:
        if req_str(claims, key) != "ZERO":
            fail(f"BOOT_RECEIPT_CANNOT_GRANT_CREDIT:{key}")
    if req_str(claims, "whole_product") != "IN_PROGRESS":
        fail("BOOT_RECEIPT_CANNOT_GRANT_WHOLE_PRODUCT_PASS")

    bind_actual_manifest(data, manifest, expected_manifest_sha256)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--expected-main-sha", required=True)
    parser.add_argument("--expected-tree-sha", required=True)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.receipt.read_text(encoding="utf-8"))
        if type(data) is not dict:
            fail("TOP_LEVEL_NOT_OBJECT")
        manifest = load_and_validate(args.manifest)
        validate(
            data,
            manifest=manifest,
            expected_manifest_sha256=args.expected_manifest_sha256,
            expected_main_sha=args.expected_main_sha,
            expected_tree_sha=args.expected_tree_sha,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ManifestError, ValidationError) as exc:
        print(f"FAIL {exc}")
        return 1
    print("PASS JSPACE_GWT_BOOT_BINDING_RECEIPT/v1 SOURCE_LOCKED_MANIFEST")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
