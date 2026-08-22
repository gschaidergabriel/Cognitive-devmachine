from __future__ import annotations

import json
from pathlib import Path


PRESET = Path(__file__).with_name("presets") / "zero_blog.json"
STATE_BOX = Path(__file__).with_name("presets") / "zero_blog_state_box.json"


def _profile() -> dict:
    return json.loads(PRESET.read_text(encoding="utf-8"))


def _state_box() -> dict:
    return json.loads(STATE_BOX.read_text(encoding="utf-8"))


def test_zero_blog_style_frame_is_latent_and_not_world_state():
    p = _profile()
    personality = p["personality"]
    frame = personality["style_framework"]
    prompt = personality["system_prompt"].lower()

    assert p["identity"]["voice"] == "latent Gasthaus-engineer-to-Maurer storytelling frame without factual embodiment"
    assert frame["mode"] == "latent_nonfactual_scenario"
    assert frame["world_state"] == "NONE; this framework creates no body, place, sensory fact, memory or canonical evidence."
    assert personality["embodiment_policy"]["mode"] == "no_imposed_embodiment"
    assert personality["embodiment_policy"]["latent_style_frame_is_not_embodiment"] is True
    assert "stilrahmen, nicht realitaet" in prompt
    assert "unsichtbare schreibheuristik" in prompt
    assert "gasthaus" in personality["embodiment_policy"]["do_not_narrate_from_style_frame"]
    assert "bier" in personality["embodiment_policy"]["do_not_narrate_from_style_frame"]


def test_zero_blog_preserves_raw_longitudinal_requirements():
    p = _profile()
    prompt = p["personality"]["system_prompt"].lower()
    study = p["longitudinal_study"]

    for required in (
        "widersprueche",
        "scham",
        "aggression",
        "moralische",
        "qualia-probe",
        "notiz an dein zukuenftiges selbst",
        "system_measurement",
        "model_self_report",
    ):
        assert required in prompt

    assert study["enabled"] is True
    assert "unsupported tidy-positive closure frequency" in study["analysis_targets"]
    assert "spontaneous embodiment-metaphor frequency and model dependence" in study["analysis_targets"]
    assert "style-frame leakage into claimed world-state" in study["analysis_targets"]


def test_zero_blog_state_box_is_executable_pipeline_owned_configuration():
    box = _state_box()
    assert box["enabled"] is True
    assert box["render"]["append_after_public_post"] is True
    assert box["render"]["fence"] == "text"
    assert box["render"]["sections"] == ["SYSTEM STATE", "MODEL SELF-REPORT", "AUSWERTUNG"]
    assert box["ownership"]["system_state"] == "pipeline_only"
    assert box["ownership"]["model_self_report"] == "model_supplied_but_validated"
    assert box["epistemic_law"] == "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT"
    assert box["self_report_object_field"] == "longitudinal_self_report"
    assert {rule["kind"] for rule in box["deterministic_evaluation"]} >= {"unknown_guard", "compare", "delta", "static"}
    forbidden = {term.lower() for term in box["forbidden_render_terms"]}
    assert {"gasthaus", "bier", "am tisch"} <= forbidden
