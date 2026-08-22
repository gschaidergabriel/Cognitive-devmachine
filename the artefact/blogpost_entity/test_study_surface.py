from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.clay_pipeline_study_surface import StudyFault, build_study_record

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT / "the artefact/blogpost_entity/presets/zero_blog_state_box.json").read_text(encoding="utf-8"))

CONTRACT = {
    "longitudinal_self_report_field": "longitudinal_self_report",
    "qualia_probe_field": "qualia_probe",
}


def compiled(*, sensors_ok=True, source_count=3):
    return {
        "source_count": source_count,
        "packet": {"quiet_sensors_ok": sensors_ok},
        "canonical": {"sources_health": {"bug": {"ok": sensors_ok}, "receipt": {"ok": sensors_ok}}},
        "personality_state": {
            "cognitive_conflict": {"status": "VERIFIED", "value": 0.72},
            "silence_unease": {"status": "VERIFIED", "value": 0.08},
            "satisfaction": {"status": "VERIFIED", "value": 0.21},
            "entropy_pressure": {"status": "VERIFIED", "value": 0.25},
            "continuity_pressure": {"status": "UNKNOWN", "value": 0.99},
            "locality_pressure": {"status": "UNKNOWN", "value": 0.88},
        },
    }


def poisoned_payload():
    return {
        "longitudinal_self_report": {
            "uncertainty": 0.78,
            "felt_conflict": 0.81,
            "anger_aggression": 0.67,
            "felt_silence_emptiness": 0.09,
            "cognitive_conflict": 1.0,
            "secret": "SHOULD_NOT_RENDER",
            "body_location": "Gasthaus",
        },
        "qualia_probe": {"result": "FAILED", "confidence": 0.31},
    }


def build(**kw):
    return build_study_record(
        config=CONFIG,
        contract=CONTRACT,
        compiled=kw.get("compiled", compiled()),
        generated=kw.get("generated", {"provider_kind": "local_exec", "model": "qwen1b"}),
        payload=kw.get("payload", poisoned_payload()),
        previous_record=kw.get("previous_record"),
        generation=kw.get("generation", 12),
        ts=kw.get("ts", 1234.5),
    )


def test_self_report_cannot_overwrite_canonical_or_leak_unselected_fields():
    record = build()
    assert record["system_state"]["cognitive_conflict"] == {"status": "VERIFIED", "value": 0.72}
    assert record["system_state"]["continuity_pressure"] == {"status": "UNKNOWN", "value": None}
    assert record["self_report"]["felt_conflict"] == 0.81
    visible = record["rendered_text"]
    assert "SHOULD_NOT_RENDER" not in visible
    assert "Gasthaus" not in visible
    assert "cognitive_conflict      = VERIFIED 1." not in visible
    assert visible.count("```text") == 1
    assert visible.count("```") == 2


def test_unknown_and_failed_sensor_semantics_fail_closed():
    record = build(compiled=compiled(sensors_ok=False, source_count=0))
    assert record["system_state"]["sensor_health"] == "ERROR"
    assert record["system_state"]["quiet_status"] == "UNKNOWN"
    assert record["system_state"]["continuity_pressure"]["status"] == "UNKNOWN"
    assert record["system_state"]["continuity_pressure"]["value"] is None
    assert "VERIFIED_QUIET" not in record["rendered_text"]
    assert any(line.startswith("UNCERTAINTY:") for line in record["evaluation"])


def test_delta_and_backend_confound_are_longitudinal_not_causal():
    previous = {
        "system_state": {
            "cognitive_conflict": {"status": "VERIFIED", "value": 0.40},
            "silence_unease": {"status": "VERIFIED", "value": 0.20},
            "continuity_pressure": {"status": "UNKNOWN", "value": None},
            "inference_backend": "remote_api",
            "model_label": "old-model",
        }
    }
    record = build(previous_record=previous, generation=13)
    assert record["deltas"]["cognitive_conflict"] == pytest.approx(0.32)
    assert record["deltas"]["silence_unease"] == pytest.approx(-0.12)
    assert "continuity_pressure" not in record["deltas"]
    assert any("CONFOUND: inference backend changed" in line for line in record["evaluation"])
    assert all("caus" not in line.lower() or "no causal interpretation" in line.lower() for line in record["evaluation"])


def test_bad_epistemic_law_is_rejected():
    bad = dict(CONFIG)
    bad["epistemic_law"] = "SELF_REPORT_IS_TRUTH"
    with pytest.raises(StudyFault, match="BAD_EPISTEMIC_LAW"):
        build_study_record(
            config=bad,
            contract=CONTRACT,
            compiled=compiled(),
            generated={"provider_kind": "local_exec", "model": "qwen1b"},
            payload=poisoned_payload(),
            previous_record=None,
            generation=1,
            ts=1.0,
        )
