import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOT = ROOT / "research_entity" / "continuity" / "BOOTSTRAP_MINIMAL.json"

def _load():
    return json.loads(BOOT.read_text(encoding="utf-8"))

def test_bootstrap_binds_current_owner_architecture():
    b = _load()
    assert b["sole_owner_directive"] == "research_entity/global/ENTITYOS_FIXED_CLAUDE_ADAPTIVE_INFERENCE_INTEGRATION.md"
    assert b["supporting_training_directive"] == "research_entity/global/MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md"
    a = b["owner_architecture"]
    assert a["status"] == "CURRENT_OWNER_ARCHITECTURE_SOURCE_ONLY"
    assert a["bundled_08b_core_required"] is True
    assert a["jspace_gwt_fixed_integration_required"] is True
    assert a["claude_code_first_class_adapter_required"] is True
    assert a["runtime_credit"] == 0
    assert a["whole_gwt_credit"] == 0
    assert a["claude_adapter_runtime_credit"] == 0

def test_bundled_core_is_not_optional_attachment():
    b = _load()
    release = "\n".join(b["portable_release_shape"]).lower()
    assert "bundled first-class approximately-0.8b" in release
    assert "fixed versioned unified j-space/gwt" in release
    assert "first-class claude code" in release
    assert "optional replaceable local model attachment" not in release
    cognition = b["claycog_approx1b"]
    assert cognition["product_requirement"] == "BUNDLED_FIRST_CLASS_GENERIC_COGNITION_CORE"
    assert cognition["integration_contract"] == "FIXED_VERSIONED_UNIFIED_JSPACE_GWT"

def test_current_entityos_jspace_gwt_are_not_blanket_legacy():
    b = _load()
    legacy = b["legacy_scope"].lower()
    assert "current entityos + mini entity" in legacy
    assert "source architecture does not create runtime or semantic pass" in legacy

def test_free_only_still_blocks_provider_execution():
    b = _load()
    together = b["together_api"]["training_campaign_approx1b"]
    assert "CURRENT_FREE_ONLY_BLOCKS_PROVIDER_EXECUTION" in together
    assert b["owner_architecture"]["runtime_credit"] == 0
