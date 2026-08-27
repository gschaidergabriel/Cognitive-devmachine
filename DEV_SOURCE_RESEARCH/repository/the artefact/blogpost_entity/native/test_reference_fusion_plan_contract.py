from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CONTRACT_PATH = HERE / "NATIVE_PROFILE_V2_PARITY_CONTRACT.json"
PROFILE_PATH = HERE.parent / "presets" / "zero_blog.json"


def test_fresh_main_fusion_plan_is_donor_only_and_fail_closed() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert contract["schema"] == "mini-entity-native-profile-v2-parity-contract/v4"

    fusion = contract["reference_runtime_fresh_main_fusion"]
    assert fusion["status"] == "NARROW_FRESH_MAIN_EXTRACTION_REQUIRED"
    donors = {int(item["pull_request"]): item for item in fusion["donors"]}
    assert set(donors) == {727, 728}
    assert donors[727]["role"] == "PREFERRED_MECHANISM_DONOR_ONLY"
    assert donors[728]["role"] == "SECONDARY_MECHANISM_DONOR_ONLY"
    assert all(str(item["whole_branch_merge"]).startswith("FORBIDDEN") for item in donors.values())

    assert contract["admission"]["status"] == "FAIL_CLOSED_UNTIL_EXACT_PARITY"
    assert contract["admission"]["runtime_receipt"] is None
    assert any("preservation_matrix" in item for item in contract["admission"]["promotion_requires"])


def test_preservation_matrix_points_at_real_current_guard_sources() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    matrix = contract["reference_runtime_fresh_main_fusion"]["preservation_matrix"]
    invariants = {item["invariant"] for item in matrix}
    required = {
        "neutral_db_init_before_profile_read",
        "syntax_bound_effect_surface_admission",
        "effect_responsibility_semantics",
        "rfc6901_response_pointer_semantics",
        "shipped_derived_expression_inputs_and_recursive_value_only_leak_gate",
        "local_exec_parent_environment_isolation",
        "profile_integrity_and_active_secret_rejection",
        "exactly_once_generation_cas_atomic_commit",
        "single_canonical_runtime_no_v2_or_legacy_side_module",
        "fail_closed_native_v2_until_exact_runtime_receipt",
    }
    assert required <= invariants

    for item in matrix:
        relative = item["bound_source"].split("#", 1)[0]
        assert (ROOT / relative).is_file(), f"missing bound fusion guard source: {relative}"


def test_pointer_profile_integrity_and_secret_invariants_are_bound_to_current_contract() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))

    assert profile["schema"] == "clay-pipeline-profile/v2"
    assert profile["inference"]["response_pointer"] == "/choices/0/message/content"

    profile_read = contract["required_reference_effect_semantics"]["pipeline_profile_read"]
    assert profile_read["method"] == "_pipeline_profile_read"
    assert "profile_hash" in profile_read["required_method_body_tokens"]
    assert "PROFILE_HASH_MISMATCH" in profile_read["required_method_body_tokens"]
    assert "active_secret_rejection" in contract["required_gate_contract"]


def test_donor_mechanisms_cannot_replace_current_authority_boundaries() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    fusion = contract["reference_runtime_fresh_main_fusion"]
    forbidden = set(fusion["must_not_introduce"])
    assert {
        "second_profile_state_authority",
        "external_profile_file_as_mandatory_runtime_state",
        "provider_or_application_identity_in_executable",
        "generic_host_shell_effect_path",
        "study_or_presentation_side_path_required_for_reference_convergence",
    } <= forbidden
