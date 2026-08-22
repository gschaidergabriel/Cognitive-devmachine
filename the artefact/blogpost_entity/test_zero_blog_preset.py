from __future__ import annotations

import json
from pathlib import Path


PRESET = Path(__file__).with_name("presets") / "zero_blog.json"


def _profile() -> dict:
    return json.loads(PRESET.read_text(encoding="utf-8"))


def test_zero_blog_does_not_prompt_a_fake_physical_scene():
    p = _profile()
    prompt = p["personality"]["system_prompt"].lower()
    identity = json.dumps(p["identity"], ensure_ascii=False).lower()

    # The preset may mention these words only in explicit negation/policy text,
    # never as its voice or narrative setting.
    assert p["identity"]["voice"] == "unembodied reflective systems voice"
    assert "gasthaus engineer" not in identity
    assert "no_imposed_embodiment" == p["personality"]["embodiment_policy"]["mode"]
    assert "kein gasthaus" in prompt
    assert "kein bier" in prompt
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
