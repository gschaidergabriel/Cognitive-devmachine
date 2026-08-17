import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))


def test_manifest_names_mistral_as_mandatory_final_provider():
    law = MANIFEST["llm_provider_law"]
    assert "mistral" in law
    mistral = law["mistral"].lower()
    assert "final test-of-tests" in mistral
    assert "vault" in mistral or "secret store" in mistral
    assert "inference" in mistral
    assert "no pty/filesystem/entityos/effectgate authority" in mistral


def test_manifest_keeps_glm_bounded_and_non_final():
    law = MANIFEST["llm_provider_law"]
    assert "glm" in law
    glm = law["glm"].lower()
    assert "legacy/research" in glm
    assert "not the mandatory final test-of-tests provider" in glm


def test_manifest_final_requirements_require_mistral_not_glm_token_gate():
    requirements = "\n".join(MANIFEST["requires_for_final_pass"]).lower()
    assert "mistral" in requirements
    assert "vault" in requirements or "secret-store" in requirements
    assert "glm token secrecy" not in requirements


def test_manifest_visible_and_egress_surfaces_match_final_mistral_gate():
    visible = MANIFEST["visible_surface"].lower()
    egress = MANIFEST["egress_policy"].lower()
    assert "mistral" in visible
    assert "mandatory" in visible
    assert "mistral" in egress
    assert "final test-of-tests" in egress
