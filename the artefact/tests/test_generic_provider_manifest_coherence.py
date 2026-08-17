import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))


def test_manifest_generic_api_is_inference_only_and_reingested():
    generic = MANIFEST["llm_provider_law"]["generic_api"].lower()
    assert "inference authority only" in generic
    assert "re-ingest" in generic or "reingest" in generic
    assert "no pty/filesystem/entityos/effectgate authority" in generic


def test_manifest_mistral_is_first_profile_not_unique_authority():
    mistral = MANIFEST["llm_provider_law"]["mistral"].lower()
    assert "first concrete" in mistral
    assert "mistral_api_key" in mistral
    assert "not unique" in mistral


def test_manifest_provider_switching_preserves_one_entity_generation():
    switching = MANIFEST["llm_provider_law"]["provider_switching"].lower()
    assert "unifieddb" in switching
    assert "generation" in switching
    assert "never forks" in switching


def test_final_pass_requires_generic_stage1_stage2_and_keeps_mistral_first_profile():
    requirements = "\n".join(MANIFEST["requires_for_final_pass"]).lower()
    assert "generic token/api provider" in requirements
    assert "stage-1" in requirements
    assert "stage-2" in requirements
    assert "mistral is the current first concrete acceptance profile" in requirements
