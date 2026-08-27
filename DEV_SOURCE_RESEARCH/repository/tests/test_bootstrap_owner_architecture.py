import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOT = ROOT / "research_entity" / "continuity" / "BOOTSTRAP_MINIMAL.json"
STATE = ROOT / "research_entity" / "rooms" / "PROGRAM_STATE.json"


def _load():
    return json.loads(BOOT.read_text(encoding="utf-8"))


def _load_state():
    return json.loads(STATE.read_text(encoding="utf-8"))


def test_bootstrap_binds_current_owner_architecture_without_runtime_credit():
    b = _load()
    assert b["active_stage"] == "MINI_ENTITY_PIPELINE_CLAY_PLUS_BUNDLED_08B_UNIFIED_JSPACE_GWT"
    assert b["sole_owner_directive"] == "research_entity/global/ENTITYOS_FIXED_CLAUDE_ADAPTIVE_INFERENCE_INTEGRATION.md"

    source = b["owner_architecture_source"]
    assert source["status"] == "CURRENT_OWNER_ARCHITECTURE_SOURCE_AUTHORITY_ONLY"
    assert source["architecture_commit"] == "5f3c2a7cc9aeab8f851d38450fa50a3e1451d767"
    assert source["bundled_08b_exact_runtime_credit"] == 0
    assert source["jspace_runtime_credit"] == 0
    assert source["whole_gwt_production_credit"] == 0
    assert source["claude_code_adapter_runtime_credit"] == 0


def test_release_shape_keeps_bundled_core_jspace_gwt_and_claude_first_class():
    b = _load()
    release = "\n".join(b["portable_release_shape"]).lower()
    assert "bundled first-class generic approximately-0.8b" in release
    assert "fixed versioned bundled-core j-space/gwt integration contract" in release
    assert "one unified cognitive workspace fabric" in release
    assert "first-class claude code targeted-inference adapter" in release
    assert "adaptive capability-profile layer" in release
    assert "self-hosted microentity dashboard" in release
    assert "optional replaceable gguf" not in release


def test_unified_cognitive_fabric_never_promotes_uncalibrated_geometry():
    b = _load()
    fabric = b["unified_cognitive_fabric"]
    assert fabric["status"] == "OWNER_ARCHITECTURE_BOUND_SOURCE_ONLY_RUNTIME_UNVERIFIED"
    assert fabric["law"] == "JSPACE_GWT = ONE_COGNITIVE_FABRIC"
    assert set(fabric["adaptive_jspace_modes"]) == {
        "FULL_LOCAL_LATENT",
        "LOCAL_OBSERVE_ONLY",
        "COMPILED_EXTERNAL",
        "PLAIN_COMPATIBILITY",
    }
    calibration = fabric["calibration_law"].lower()
    assert "no alpha" in calibration
    assert "checkpoint/tokenizer/runtime" in calibration
    assert "measured" in calibration


def test_closed_api_and_free_only_boundaries_fail_closed():
    b = _load()
    assert "compiled_external" in b["inference_law"]["remote_api"].lower()
    assert "never claim latent access" in b["inference_law"]["remote_api"].lower()

    together = b["together_api"]
    assert together["credential_lookup_allowed_now"] is False
    assert together["provider_network_allowed_now"] is False
    assert together["job_started"] is False
    assert "FREE_ONLY" in together["training_campaign_approx1b"]


def test_current_architecture_is_not_reclassified_as_legacy():
    b = _load()
    legacy = b["legacy_scope"]
    assert "ENTITYOS_FIXED_CLAUDE_ADAPTIVE_INFERENCE_INTEGRATION" in legacy
    assert "supersede the prior optional-0.8B/loose-J-Space-GWT assumptions" in legacy


def test_program_state_matches_boot_owner_architecture_and_zero_credit():
    b = _load()
    s = _load_state()

    assert s["schema_version"] == "7.11"
    assert s["stage"] == b["active_stage"]
    assert s["owner_directive"] == b["sole_owner_directive"]

    boot_source = b["owner_architecture_source"]
    state_source = s["owner_architecture_2026_08_23"]
    assert state_source["status"] == boot_source["status"]
    assert state_source["architecture_commit"] == boot_source["architecture_commit"]
    assert state_source["bundled_08b_exact_runtime_credit"] == boot_source["bundled_08b_exact_runtime_credit"] == 0
    assert state_source["jspace_runtime_credit"] == boot_source["jspace_runtime_credit"] == 0
    assert state_source["whole_gwt_production_credit"] == boot_source["whole_gwt_production_credit"] == 0
    assert state_source["claude_code_adapter_runtime_credit"] == boot_source["claude_code_adapter_runtime_credit"] == 0

    assert s["unified_cognitive_fabric"]["law"] == b["unified_cognitive_fabric"]["law"]
    assert set(s["unified_cognitive_fabric"]["adaptive_jspace_modes"]) == set(b["unified_cognitive_fabric"]["adaptive_jspace_modes"])
    assert s["execution_policy"]["free_only"] is True
    assert s["together_api"]["credentialed_preflight_allowed_now"] is False
    assert "FREE_ONLY" in s["together_api"]["training_campaign_approx1b"]
    assert "optional replaceable" not in s["sole_target"].lower()
