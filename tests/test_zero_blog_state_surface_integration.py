from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from clay_study_surface import build_record, render_state_box

CFG = ROOT / "the artefact" / "blogpost_entity" / "presets" / "zero_blog_state_box.json"


def test_current_zero_blog_state_box_profile_is_accepted_without_special_case():
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    canonical = {
        "generation": 12,
        "timestamp": "2026-08-22T10:05:00+07:00",
        "inference_backend": "local_exec",
        "model_label": "fixture",
        "source_count": 4,
        "sensor_health": "VERIFIED",
        "quiet_status": "NOT_QUIET",
        "cognitive_conflict": {"status": "VERIFIED", "value": 0.72},
        "silence_unease": {"status": "VERIFIED", "value": 0.08},
        "satisfaction": {"status": "VERIFIED", "value": 0.21},
        "entropy_pressure": {"status": "VERIFIED", "value": 0.55},
        "continuity_pressure": {"status": "UNKNOWN", "value": 0.99},
        "locality_pressure": {"status": "UNKNOWN", "value": 0.99},
        "internal_secretish": "NO",
    }
    self_report = {name: 0.5 for name in cfg["self_report_fields"] if name != "qualia_result"}
    self_report["qualia_result"] = "FAILED"
    self_report["generation"] = 999999
    rec = build_record(
        config=cfg,
        canonical_values=canonical,
        self_report_values=self_report,
        context={"inference_backend": "local_exec", "model_label": "fixture"},
    )
    text = render_state_box(cfg, rec)
    assert "ZERO STATE" in text
    assert "SYSTEM STATE" in text and "MODEL SELF-REPORT" in text and "AUSWERTUNG" in text
    assert "continuity_pressure     = UNKNOWN" in text
    assert "locality_pressure       = UNKNOWN" in text
    assert "999999" not in text
    assert "internal_secretish" not in text


def test_current_profile_never_relabels_self_report_as_system_measurement():
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    rec = build_record(
        config=cfg,
        canonical_values={"cognitive_conflict": {"status": "UNKNOWN", "value": 1.0}},
        self_report_values={"felt_conflict": 1.0, "qualia_result": "REPORTED"},
        context={},
    )
    assert rec["canonical"]["cognitive_conflict"] == {"status": "UNKNOWN", "value": None}
    assert rec["self_report"]["felt_conflict"] == 1.0
