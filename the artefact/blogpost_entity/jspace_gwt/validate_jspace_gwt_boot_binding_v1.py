#!/usr/bin/env python3
import hashlib
import json
import math
import re
import sys
from pathlib import Path

SCHEMA = "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_ARTIFACT_BINDINGS = {
    "bundled_manifest": ("bundled_core", "manifest_sha256"),
    "checkpoint": ("bundled_core", "checkpoint_sha256"),
    "tokenizer": ("bundled_core", "tokenizer_sha256"),
    "runtime": ("bundled_core", "runtime_sha256"),
    "lens_file": ("jspace", "lens_file_sha256"),
    "lens_profile": ("jspace", "lens_profile_sha256"),
    "fit_corpus": ("jspace", "fit_corpus_sha256"),
    "workspace_policy": ("gwt", "workspace_policy_sha256"),
    "gwt_calibration": ("gwt", "calibration_sha256"),
    "zero_identity": ("zero_grf", "zero_identity_sha256"),
    "grf": ("zero_grf", "grf_sha256"),
    "projection_policy": ("zero_grf", "projection_policy_sha256"),
    "claude_capability_profile": ("claude_adapter", "capability_profile_sha256"),
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_artifact_binding(root: Path, role: str, binding: dict, expected_sha256: str) -> None:
    relative = req_str(binding, "path")
    if Path(relative).is_absolute():
        fail(f"ARTIFACT_ABSOLUTE_PATH:{role}")
    declared_sha = req_sha(binding, "sha256")
    if declared_sha != expected_sha256:
        fail(f"ARTIFACT_DECLARED_DIGEST_MISMATCH:{role}")
    size_bytes = req_int(binding, "size_bytes", minimum=0)
    try:
        resolved = (root / relative).resolve(strict=True)
        resolved.relative_to(root)
    except (FileNotFoundError, OSError, ValueError):
        fail(f"ARTIFACT_PATH_OUTSIDE_ROOT_OR_MISSING:{role}")
    if not resolved.is_file():
        fail(f"ARTIFACT_NOT_FILE:{role}")
    if resolved.stat().st_size != size_bytes:
        fail(f"ARTIFACT_SIZE_MISMATCH:{role}")
    if sha256_file(resolved) != expected_sha256:
        fail(f"ARTIFACT_DIGEST_MISMATCH:{role}")


def validate(data: dict, artifact_root: Path) -> None:
    if data.get("schema") != SCHEMA:
        fail("SCHEMA_MISMATCH")

    source = req_obj(data, "source")
    req_sha(source, "main_sha", 40)
    req_sha(source, "tree_sha", 40)
    req_bool(source, "dirty")

    executor = req_obj(data, "executor")
    if req_str(executor, "host_class") != "UBUNTU":
        fail("EXECUTOR_NOT_UBUNTU")
    req_sha(executor, "host_identity_sha256")
    req_str(executor, "kernel")

    core = req_obj(data, "bundled_core")
    req_str(core, "manifest_version")
    req_str(core, "engine_id")
    req_str(core, "model_family")
    checkpoint_sha = req_sha(core, "checkpoint_sha256")
    tokenizer_sha = req_sha(core, "tokenizer_sha256")
    req_sha(core, "runtime_sha256")
    req_sha(core, "manifest_sha256")
    layer_count = req_int(core, "layer_count", minimum=1)
    d_model = req_int(core, "d_model", minimum=1)
    if not req_bool(core, "exact_bytes_verified"):
        fail("BUNDLED_CORE_BYTES_UNVERIFIED")

    jspace = req_obj(data, "jspace")
    req_sha(jspace, "jlens_upstream_commit", 40)
    req_sha(jspace, "lens_file_sha256")
    req_sha(jspace, "lens_profile_sha256")
    req_sha(jspace, "fit_corpus_sha256")
    if req_sha(jspace, "source_checkpoint_sha256") != checkpoint_sha:
        fail("JSPACE_CHECKPOINT_PROVENANCE_MISMATCH")
    if req_sha(jspace, "source_tokenizer_sha256") != tokenizer_sha:
        fail("JSPACE_TOKENIZER_PROVENANCE_MISMATCH")
    if req_int(jspace, "d_model", minimum=1) != d_model:
        fail("JSPACE_D_MODEL_MISMATCH")
    source_layers = jspace.get("source_layers")
    if not isinstance(source_layers, list) or not source_layers:
        fail("JSPACE_SOURCE_LAYERS_REQUIRED")
    if any(isinstance(layer, bool) or not isinstance(layer, int) for layer in source_layers):
        fail("JSPACE_SOURCE_LAYER_INVALID")
    if source_layers != sorted(set(source_layers)):
        fail("JSPACE_SOURCE_LAYERS_NOT_UNIQUE_SORTED")
    if any(layer < 0 or layer >= layer_count for layer in source_layers):
        fail("JSPACE_SOURCE_LAYER_OUT_OF_RANGE")
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
    req_sha(inference, "inference_packet_sha256")

    control = req_obj(data, "control")
    if not req_bool(control, "free_only"):
        fail("FREE_ONLY_NOT_BOUND")
    if req_bool(control, "paid_or_unknown_provider_network_attempted"):
        fail("PAID_OR_UNKNOWN_PROVIDER_NETWORK_ATTEMPTED")

    artifacts = req_obj(data, "artifact_bindings")
    sections = {
        "bundled_core": core,
        "jspace": jspace,
        "gwt": gwt,
        "zero_grf": zero,
        "claude_adapter": claude,
    }
    for role, (section_name, digest_key) in REQUIRED_ARTIFACT_BINDINGS.items():
        binding = req_obj(artifacts, role)
        expected_sha = req_sha(sections[section_name], digest_key)
        verify_artifact_binding(artifact_root, role, binding, expected_sha)

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
    if len(sys.argv) != 3:
        print("usage: validate_jspace_gwt_boot_binding_v1.py RECEIPT.json ARTIFACT_ROOT", file=sys.stderr)
        return 2
    try:
        receipt_path = Path(sys.argv[1])
        artifact_root = Path(sys.argv[2]).resolve(strict=True)
        if not artifact_root.is_dir():
            fail("ARTIFACT_ROOT_NOT_DIRECTORY")
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            fail("TOP_LEVEL_NOT_OBJECT")
        validate(data, artifact_root)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"FAIL {exc}")
        return 1
    print("PASS JSPACE_GWT_BOOT_BINDING_RECEIPT/v1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
