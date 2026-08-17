import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))


def test_manifest_has_provider_agnostic_api_boundary():
    law = MANIFEST["llm_provider_law"]
    assert "generic_api" in law
    generic = law["generic_api"].lower()
    assert "inference" in generic
    assert "adapter" in generic
    assert "re-ingest" in generic or "reingest" in generic
    assert "no pty/filesystem/entityos/effectgate authority" in generic


def test_manifest_keeps_mistral_as_first_profile_not_unique_authority():
    law = MANIFEST["llm_provider_law"]
    assert "mistral" in law
    mistral = law["mistral"].lower()
    assert "first" in mistral
    assert "acceptance" in mistral or "test profile" in mistral
    assert "not unique" in mistral or "not a unique" in mistral
    assert "mistral_api_key" in mistral


def test_manifest_keeps_provider_switching_inside_one_entity_generation():
    law = MANIFEST["llm_provider_law"]
    switching = law["provider_switching"].lower()
    assert "unifieddb" in switching
    assert "generation" in switching
    assert "never forks" in switching or "never fork" in switching


def test_manifest_final_requirements_require_generic_api_acceptance_not_unique_mistral():
    requirements = "\n".join(MANIFEST["requires_for_final_pass"]).lower()
    assert "generic" in requirements
    assert "api" in requirements
    assert "stage-1" in requirements or "stage 1" in requirements
    assert "stage-2" in requirements or "stage 2" in requirements
    assert "mistral" in requirements
    assert "first" in requirements
    assert "unique mandatory" not in requirements


def test_manifest_visible_and_egress_surfaces_preserve_native_claude_and_bounded_api_inference():
    visible = MANIFEST["visible_surface"].lower()
    egress = MANIFEST["egress_policy"].lower()
    assert "claude code" in visible
    assert "api" in visible
    assert "inference" in visible
    assert "token/api" in egress or "api inference" in egress
    assert "mistral" not in egress or "first" in egress
