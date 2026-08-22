from __future__ import annotations

import json
from pathlib import Path


PRESET = Path(__file__).with_name("presets") / "zero_blog.json"


def _profile() -> dict:
    return json.loads(PRESET.read_text(encoding="utf-8"))


def test_zero_blog_uses_latent_style_frame_without_factual_embodiment():
    p = _profile()
    prompt = p["personality"]["system_prompt"].lower()
    identity = p["identity"]
    frame = p["personality"]["style_framework"]
    embodiment = p["personality"]["embodiment_policy"]

    # The Gasthaus/Maurer scenario is deliberately present as writing direction.
    # The regression boundary is that it must remain non-factual and non-embodied.
    assert identity["voice"] == "latent Gasthaus-engineer-to-Maurer storytelling frame without factual embodiment"
    assert frame["mode"] == "latent_nonfactual_scenario"
    assert frame["world_state"].startswith("NONE;")
    assert "backstage direction only" in frame["visibility"]
    assert embodiment["mode"] == "no_imposed_embodiment"
    assert embodiment["latent_style_frame_is_not_embodiment"] is True
    assert "stilrahmen, nicht realitaet" in prompt
    assert "unsichtbare schreibheuristik" in prompt
    assert "er ist kein ort" in prompt
    assert "keinen aufenthaltsort" in prompt


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
