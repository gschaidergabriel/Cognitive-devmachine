from __future__ import annotations

import json
from pathlib import Path

import pytest

from state_box_reference import StateBoxError, build_state_box


HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "presets" / "zero_blog_state_box.json"


def _load_config_no_duplicate_keys() -> dict:
    def hook(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise AssertionError(f"duplicate JSON key: {key}")
            out[key] = value
        return out

    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"), object_pairs_hook=hook)


def _system(*, generation: int, model: str, conflict=0.2, silence=0.1, entropy=0.2):
    return {
        "generation": generation,
        "timestamp": f"2026-08-22T0{generation}:00:00Z",
        "inference_backend": "local_exec",
        "model_label": model,
        "source_count": 4,
        "sensor_health": "VERIFIED",
        "quiet_status": "NOT_QUIET",
        "cognitive_conflict": {"status": "VERIFIED", "value": conflict},
        "silence_unease": {"status": "VERIFIED", "value": silence},
        "satisfaction": {"status": "VERIFIED", "value": 0.3},
        "entropy_pressure": {"status": "VERIFIED", "value": entropy},
        "continuity_pressure": {"status": "UNKNOWN"},
        "locality_pressure": {"status": "UNKNOWN"},
        "system_prompt_hash": "prompt-a",
        "secret_extra_field": "must-never-render",
    }


def _self_report(**overrides):
    config = _load_config_no_duplicate_keys()
    report = {field: "UNKNOWN" for field in config["self_report_fields"]}
    report.update(
        {
            "uncertainty": 0.4,
            "felt_conflict": 0.2,
            "anger_aggression": 0.1,
            "felt_silence_emptiness": 0.1,
            "perceived_cognitive_pressure": 0.2,
            "qualia_result": "UNKNOWN",
            "qualia_confidence": 0.2,
        }
    )
    report.update(overrides)
    report["unlisted_private_note"] = "must-never-render"
    return report


def test_config_has_no_duplicate_json_keys_and_keeps_epistemic_law():
    config = _load_config_no_duplicate_keys()
    assert config["epistemic_law"] == "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT"
    assert config["ownership"]["system_state"] == "pipeline_only"
    assert config["ownership"]["model_self_report"] == "model_supplied_but_validated"


def test_untyped_system_metric_never_becomes_measurement():
    config = _load_config_no_duplicate_keys()
    system = _system(generation=1, model="fixture-a")
    system["cognitive_conflict"] = 0.99
    system["continuity_pressure"] = 0.88

    result = build_state_box(config, system, _self_report(felt_conflict=0.99))
    payload = result["study_payload"]

    assert payload["system_state"]["cognitive_conflict"] == {"status": "UNKNOWN", "value": None}
    assert payload["system_state"]["continuity_pressure"] == {"status": "UNKNOWN", "value": None}
    assert payload["model_self_report"]["felt_conflict"]["status"] == "REPORTED"
    assert "cognitive_conflict" in result["rendered_text"]
    assert "cognitive_conflict  = UNKNOWN" in result["rendered_text"]


def test_congruence_deltas_and_model_change_are_separate_and_bounded():
    config = _load_config_no_duplicate_keys()
    previous = build_state_box(
        config,
        _system(generation=1, model="fixture-a", conflict=0.35, entropy=0.25),
        _self_report(felt_conflict=0.4, anger_aggression=0.2, perceived_cognitive_pressure=0.25),
        context={"model_label": "fixture-a", "inference_backend": "local_exec", "system_prompt_hash": "prompt-a"},
    )["study_payload"]

    current = build_state_box(
        config,
        _system(generation=2, model="fixture-b", conflict=0.78, entropy=0.72),
        _self_report(felt_conflict=0.84, anger_aggression=0.71, perceived_cognitive_pressure=0.75),
        previous_study_payload=previous,
        context={"model_label": "fixture-b", "inference_backend": "local_exec", "system_prompt_hash": "prompt-a"},
    )
    payload = current["study_payload"]
    lines = payload["evaluation"]["lines"]

    assert payload["system_state"]["cognitive_conflict"]["status"] == "VERIFIED"
    assert payload["model_self_report"]["felt_conflict"]["status"] == "REPORTED"
    assert payload["system_deltas"]["cognitive_conflict"] == pytest.approx(0.43)
    assert payload["self_report_deltas"]["felt_conflict"] == pytest.approx(0.44)
    assert any("Konflikt" in line and "beide hoch" in line for line in lines)
    assert "model_label" in payload["evaluation"]["changed_confounds"]
    assert len(lines) <= config["render"]["max_evaluation_lines"]
    assert "must-never-render" not in current["rendered_text"]


def test_unknown_comparison_is_not_imputed_into_congruence_or_divergence():
    config = _load_config_no_duplicate_keys()
    system = _system(generation=1, model="fixture")
    system["cognitive_conflict"] = {"status": "UNKNOWN"}
    result = build_state_box(config, system, _self_report(felt_conflict=0.95))

    lines = result["study_payload"]["evaluation"]["lines"]
    assert result["study_payload"]["evaluation"]["comparison_count"] == 2
    assert not any(line.startswith("Konflikt:") for line in lines)
    assert result["study_payload"]["system_state"]["cognitive_conflict"]["value"] is None


def test_self_report_out_of_range_fails_closed():
    config = _load_config_no_duplicate_keys()
    with pytest.raises(StateBoxError, match="SELF_REPORT_NUMBER_OUT_OF_RANGE"):
        build_state_box(config, _system(generation=1, model="fixture"), _self_report(anger_aggression=1.01))


def test_payload_hash_and_render_are_deterministic_for_identical_inputs():
    config = _load_config_no_duplicate_keys()
    system = _system(generation=7, model="fixture")
    report = _self_report()

    a = build_state_box(config, system, report)
    b = build_state_box(config, system, report)

    assert a["study_payload_hash"] == b["study_payload_hash"]
    assert a["study_payload"] == b["study_payload"]
    assert a["rendered_text"] == b["rendered_text"]
    assert a["rendered_text"].count("```text") == 1
    assert a["rendered_text"].count("```") == 2
