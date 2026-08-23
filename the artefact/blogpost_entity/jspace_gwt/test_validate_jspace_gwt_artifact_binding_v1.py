from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from validate_jspace_gwt_boot_binding_v1 import ValidationError, validate  # noqa: E402

H40 = "a" * 40

ROLES = {
    "bundled_manifest": ("bundled_core", "manifest_sha256"),
    "checkpoint": ("bundled_core", "checkpoint_sha256"),
    "tokenizer": ("bundled_core", "tokenizer_sha256"),
    "runtime": ("bundled_core", "runtime_sha256"),
    "jspace_profile": ("jspace", "jspace_profile_sha256"),
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


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _receipt(root: Path) -> dict:
    payloads = {role: f"artifact:{role}".encode() for role in ROLES}
    digests = {role: _sha(data) for role, data in payloads.items()}
    bindings = {}
    for role, data in payloads.items():
        path = root / "artifacts" / f"{role}.bin"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        bindings[role] = {
            "path": str(path.relative_to(root)),
            "sha256": digests[role],
            "size_bytes": len(data),
        }

    return {
        "schema": "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1",
        "source": {"main_sha": H40, "tree_sha": H40, "dirty": False},
        "executor": {
            "host_class": "UBUNTU",
            "host_identity_sha256": _sha(b"host"),
            "kernel": "test-kernel",
        },
        "bundled_core": {
            "manifest_version": "mini-entity-bundled-cognition-manifest/v1",
            "engine_id": "bundled-qwen35-08b",
            "model_family": "Qwen3.5-0.8B",
            "checkpoint_sha256": digests["checkpoint"],
            "tokenizer_sha256": digests["tokenizer"],
            "runtime_sha256": digests["runtime"],
            "manifest_sha256": digests["bundled_manifest"],
            "layer_count": 24,
            "d_model": 2048,
            "exact_bytes_verified": True,
        },
        "jspace": {
            "jlens_upstream_commit": H40,
            "jspace_profile_sha256": digests["jspace_profile"],
            "lens_file_sha256": digests["lens_file"],
            "lens_profile_sha256": digests["lens_profile"],
            "fit_corpus_sha256": digests["fit_corpus"],
            "source_checkpoint_sha256": digests["checkpoint"],
            "source_tokenizer_sha256": digests["tokenizer"],
            "d_model": 2048,
            "source_layers": [4, 8, 12, 16, 20],
            "n_prompts": 100,
            "skip_first_positions": 16,
            "storage_dtype": "float32",
            "numeric_integrity": {
                "pre_save_all_finite": True,
                "post_load_all_finite": True,
                "max_abs_pre_save": 1.0,
                "max_abs_post_load": 1.0,
            },
            "measurement_policy": {
                "minimum_readout_position": 16,
                "observed_readout_positions": [16, 17],
                "prompt_copy_confound_guard_enabled": True,
            },
        },
        "gwt": {
            "workspace_policy_sha256": digests["workspace_policy"],
            "calibration_sha256": digests["gwt_calibration"],
            "slot_count": None,
            "calibration_status": "UNMEASURED_SOURCE_ONLY",
        },
        "zero_grf": {
            "zero_identity_sha256": digests["zero_identity"],
            "grf_sha256": digests["grf"],
            "projection_policy_sha256": digests["projection_policy"],
        },
        "claude_adapter": {
            "adapter_version": "1",
            "capability_profile_sha256": digests["claude_capability_profile"],
            "enabled": False,
        },
        "inference": {
            "first_engine_choice": "BUNDLED_LOCAL_08B",
            "origin_attribution": "boot-probe",
            "inference_packet_sha256": _sha(b"packet"),
            "first_actions": [
                {"action_id": "boot-1", "origin": "ZERO", "effect_requested": False}
            ],
        },
        "control": {
            "free_only": True,
            "paid_or_unknown_provider_network_attempted": False,
        },
        "artifact_bindings": bindings,
        "authority": {
            "miniunifieddb_is_truth_authority": True,
            "claude_result_is_candidate_only": True,
            "jspace_measurement_is_not_truth": True,
            "gwt_workspace_is_not_truth": True,
            "effect_gate_required": True,
        },
        "claims": {"whole_gwt_credit": "ZERO", "whole_product": "IN_PROGRESS"},
    }


def _fails(data: dict, root: Path, code: str) -> None:
    with pytest.raises(ValidationError, match=code):
        validate(data, root)


def test_combined_provenance_contract_accepts_bound_source_candidate(tmp_path: Path):
    validate(_receipt(tmp_path), tmp_path)


def test_actual_checkpoint_substitution_fails_closed(tmp_path: Path):
    data = _receipt(tmp_path)
    checkpoint = tmp_path / data["artifact_bindings"]["checkpoint"]["path"]
    checkpoint.write_bytes(b"substituted")
    _fails(data, tmp_path, "ARTIFACT_SIZE_MISMATCH:checkpoint|ARTIFACT_DIGEST_MISMATCH:checkpoint")


def test_jspace_cross_checkpoint_provenance_fails_closed(tmp_path: Path):
    data = _receipt(tmp_path)
    data["jspace"]["source_checkpoint_sha256"] = _sha(b"foreign-checkpoint")
    _fails(data, tmp_path, "JSPACE_CHECKPOINT_PROVENANCE_MISMATCH")


def test_jspace_profile_bytes_are_independently_bound(tmp_path: Path):
    data = _receipt(tmp_path)
    profile = tmp_path / data["artifact_bindings"]["jspace_profile"]["path"]
    profile.write_bytes(b"different-jspace-profile")
    _fails(data, tmp_path, "ARTIFACT_SIZE_MISMATCH:jspace_profile|ARTIFACT_DIGEST_MISMATCH:jspace_profile")


def test_residual_width_mismatch_fails_closed(tmp_path: Path):
    data = _receipt(tmp_path)
    data["jspace"]["d_model"] = 4096
    _fails(data, tmp_path, "JSPACE_D_MODEL_MISMATCH")


def test_source_layer_out_of_range_fails_closed(tmp_path: Path):
    data = _receipt(tmp_path)
    data["jspace"]["source_layers"] = [4, 24]
    _fails(data, tmp_path, "JSPACE_SOURCE_LAYER_OUT_OF_RANGE")


def test_missing_inference_packet_identity_fails_closed(tmp_path: Path):
    data = _receipt(tmp_path)
    del data["inference"]["inference_packet_sha256"]
    _fails(data, tmp_path, "MISSING_STRING:inference_packet_sha256")


def test_free_only_false_fails_closed_before_runtime_credit(tmp_path: Path):
    data = _receipt(tmp_path)
    data["control"]["free_only"] = False
    _fails(data, tmp_path, "FREE_ONLY_NOT_BOUND")


def test_paid_or_unknown_provider_attempt_fails_closed(tmp_path: Path):
    data = _receipt(tmp_path)
    data["control"]["paid_or_unknown_provider_network_attempted"] = True
    _fails(data, tmp_path, "PAID_OR_UNKNOWN_PROVIDER_NETWORK_ATTEMPTED")


def test_new_guards_do_not_relax_unmeasured_gwt_slot_rule(tmp_path: Path):
    data = _receipt(tmp_path)
    data["gwt"]["slot_count"] = 3
    _fails(data, tmp_path, "UNMEASURED_GWT_SLOT_COUNT_MUST_BE_NULL")


def test_new_guards_do_not_relax_first_action_provenance(tmp_path: Path):
    data = _receipt(tmp_path)
    data["inference"]["first_actions"] = [
        {"action_id": "dup", "origin": "ZERO", "effect_requested": False},
        {"action_id": "dup", "origin": "CLAUDE_CODE", "effect_requested": False},
    ]
    _fails(data, tmp_path, "DUPLICATE_FIRST_ACTION_ID")
