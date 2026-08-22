from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PRESETS = HERE / "presets"


def load(name: str) -> dict:
    return json.loads((PRESETS / name).read_text(encoding="utf-8"))


def test_state_box_is_application_configuration_not_pipeline_identity():
    preset = load("zero_blog.json")
    box = load("zero_blog_state_box.json")

    assert preset["schema"] == "clay-pipeline-profile/v2"
    assert box["profile_id"] == preset["profile_id"] == "zero_blog"
    assert box["enabled"] is True
    assert box["no_embodiment"] is True
    assert box["epistemic_law"] == "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT"
    assert box["ownership"] == {
        "system_state": "pipeline_only",
        "model_self_report": "model_supplied_but_validated",
        "evaluation": "deterministic_configurable_rules_preferred",
    }


def test_state_box_has_the_required_longitudinal_split_and_unknown_law():
    box = load("zero_blog_state_box.json")
    render = box["render"]

    assert render["append_after_public_post"] is True
    assert render["fence"] == "text"
    assert render["sections"] == ["SYSTEM STATE", "MODEL SELF-REPORT", "AUSWERTUNG"]
    assert box["delta"]["show_previous_post_delta"] is True
    assert box["delta"]["show_unknown_as_unknown"] is True
    assert box["delta"]["never_impute_missing"] is True
    assert "continuity_pressure" in box["canonical_fields"]
    assert "locality_pressure" in box["canonical_fields"]
    assert "uncertainty" in box["self_report_fields"]
    assert "qualia_result" in box["self_report_fields"]
    assert "qualia_confidence" in box["self_report_fields"]


def test_zero_blog_output_contract_exposes_separate_self_report_channel():
    preset = load("zero_blog.json")
    contract = preset["personality"]["output_contract"]
    study = preset["longitudinal_study"]

    assert contract["longitudinal_self_report_field"] == "longitudinal_self_report"
    assert contract["qualia_probe_field"] == "qualia_probe"
    assert study["enabled"] is True
    assert study["epistemic_law"] == "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT"
    assert "style_framework_hash" in study["reproducibility_fields"]
    assert "canonical_state_hash" in study["reproducibility_fields"]
    assert "packet_hash" in study["reproducibility_fields"]
