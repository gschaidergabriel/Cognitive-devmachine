from __future__ import annotations

import json
import pathlib
import sqlite3
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from clay_study_surface import (
    StudySurfaceError,
    append_state_box,
    build_record,
    ensure_study_schema,
    extract_self_report,
    insert_study_record,
    normalize_canonical,
    normalize_self_report,
    render_state_box,
    stable_record_json,
)


def config() -> dict:
    return {
        "enabled": True,
        "render": {
            "fence": "text",
            "title": "ENTITY STATE",
            "sections": ["SYSTEM STATE", "MODEL SELF-REPORT", "EVALUATION"],
            "max_evaluation_lines": 5,
        },
        "epistemic_law": "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT",
        "canonical_fields": [
            "generation",
            "backend",
            "model",
            "source_count",
            "conflict",
            "locality_pressure",
        ],
        "self_report_fields": ["felt_conflict", "uncertainty", "qualia_result", "qualia_confidence"],
        "deterministic_evaluation": {
            "confound_fields": ["profile_hash", "prompt_hash", "backend", "model"],
            "uncertainty_template": "Unknown/degraded system fields: {fields}.",
            "comparisons": [
                {
                    "system": "conflict",
                    "report": "felt_conflict",
                    "high": 0.65,
                    "low": 0.35,
                    "both_high": "System conflict and reported conflict are jointly high.",
                    "divergent": "System conflict and reported conflict diverge.",
                }
            ],
            "delta_threshold": 0.05,
            "delta_template": "Measured change: {changes}.",
            "confound_template": "Context changed: {fields}.",
            "calibration_line": "Self-report is not canonical measurement.",
        },
    }


def canonical(conflict_status="VERIFIED", conflict_value=0.72):
    return {
        "generation": 2,
        "backend": "local_exec",
        "model": "fixture-model",
        "source_count": 3,
        "conflict": {"status": conflict_status, "value": conflict_value},
        # Deliberately carries an internal numeric placeholder despite UNKNOWN.
        "locality_pressure": {"status": "UNKNOWN", "value": 0.99},
        "private_internal_id": "must-not-leak",
    }


def report():
    return {
        "felt_conflict": 0.81,
        "uncertainty": 0.55,
        "qualia_result": "FAILED",
        "qualia_confidence": 0.31,
        "model_attempt_to_write_generation": 999,
    }


def test_unknown_numeric_placeholder_is_erased_and_private_field_is_allowlisted_out():
    out = normalize_canonical(canonical(), config()["canonical_fields"])
    assert out["locality_pressure"] == {"status": "UNKNOWN", "value": None}
    assert "private_internal_id" not in out


def test_self_report_is_separate_allowlisted_and_bounded():
    out = normalize_self_report(report(), config()["self_report_fields"])
    assert out["felt_conflict"] == pytest.approx(0.81)
    assert out["qualia_result"] == "FAILED"
    assert "model_attempt_to_write_generation" not in out
    with pytest.raises(StudySurfaceError):
        normalize_self_report({"felt_conflict": 1.2}, ["felt_conflict"])


def test_record_deltas_require_verified_on_both_sides_and_context_change_is_flagged():
    old = build_record(
        config=config(),
        canonical_values={**canonical(conflict_value=0.40), "generation": 1},
        self_report_values={**report(), "felt_conflict": 0.45},
        context={"profile_hash": "a", "prompt_hash": "a", "backend": "api", "model": "m1"},
    )
    new = build_record(
        config=config(),
        canonical_values=canonical(conflict_value=0.72),
        self_report_values=report(),
        context={"profile_hash": "a", "prompt_hash": "b", "backend": "local_exec", "model": "m2"},
        previous_record=old,
    )
    assert new["deltas"] == {"conflict": pytest.approx(0.32)}
    assert set(new["confounds"]) == {"prompt_hash", "backend", "model"}
    assert any("jointly high" in line for line in new["evaluation"])
    assert any("Context changed" in line for line in new["evaluation"])


def test_unknown_current_measurement_suppresses_delta_and_pair_interpretation():
    old = build_record(
        config=config(),
        canonical_values={**canonical(conflict_value=0.4), "generation": 1},
        self_report_values=report(),
        context={},
    )
    new = build_record(
        config=config(),
        canonical_values=canonical(conflict_status="UNKNOWN", conflict_value=0.95),
        self_report_values=report(),
        context={},
        previous_record=old,
    )
    assert "conflict" not in new["deltas"]
    assert not any("jointly high" in line for line in new["evaluation"])
    assert any("conflict" in line for line in new["evaluation"])


def test_counterfactual_swap_attack_cannot_promote_model_report_to_system_state():
    # Adversarial regression: the model supplies a near-perfect imitation of canonical
    # field names/values inside self-report. Only configured self-report fields survive;
    # system generation/conflict remain solely pipeline supplied.
    attack = {
        **report(),
        "generation": 999999,
        "conflict": 1.0,
        "backend": "attacker",
        "model": "attacker",
    }
    rec = build_record(
        config=config(),
        canonical_values=canonical(conflict_value=0.22),
        self_report_values=attack,
        context={"backend": "local_exec", "model": "fixture-model"},
    )
    assert rec["canonical"]["generation"] == 2
    assert rec["canonical"]["conflict"]["value"] == pytest.approx(0.22)
    assert rec["canonical"]["backend"] == "local_exec"
    assert "generation" not in rec["self_report"]
    assert "conflict" not in rec["self_report"]


def test_render_is_deterministic_public_safe_and_appends_after_prose():
    rec = build_record(
        config=config(),
        canonical_values=canonical(),
        self_report_values=report(),
        context={"backend": "local_exec", "model": "fixture-model"},
    )
    box1 = render_state_box(config(), rec)
    box2 = render_state_box(config(), json.loads(stable_record_json(rec)))
    assert box1 == box2
    assert "must-not-leak" not in box1
    assert "UNKNOWN 0.99" not in box1
    assert "locality_pressure" in box1 and "UNKNOWN" in box1
    final = append_state_box("Validated prose.", box1)
    assert final.startswith("Validated prose.\n\n```text")
    assert final.count("```text") == 1


def test_missing_epistemic_law_fails_closed():
    bad = config()
    bad["epistemic_law"] = "reports are measurements"
    with pytest.raises(StudySurfaceError):
        build_record(
            config=bad,
            canonical_values=canonical(),
            self_report_values=report(),
            context={},
        )


def test_profile_named_self_report_extraction_is_typed():
    assert extract_self_report({"report": {"uncertainty": 0.4}}, "report") == {"uncertainty": 0.4}
    assert extract_self_report({}, "report") == {}
    with pytest.raises(StudySurfaceError):
        extract_self_report({"report": "I can overwrite system state"}, "report")


def test_study_insert_participates_in_caller_transaction_and_rolls_back_atomically():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE output_stub(output_id TEXT PRIMARY KEY)")
    ensure_study_schema(db)
    db.commit()
    rec = build_record(
        config=config(), canonical_values=canonical(), self_report_values=report(), context={}
    )
    box = render_state_box(config(), rec)

    db.execute("BEGIN IMMEDIATE")
    db.execute("INSERT INTO output_stub VALUES(?)", ("o1",))
    insert_study_record(
        db, output_id="o1", ts=1.0, generation=2, profile_id="p", record=rec,
        rendered_box=box, canonical_hash="c", packet_hash="q"
    )
    db.rollback()
    assert db.execute("SELECT COUNT(*) FROM output_stub").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_study_records").fetchone()[0] == 0

    db.execute("BEGIN IMMEDIATE")
    db.execute("INSERT INTO output_stub VALUES(?)", ("o1",))
    h = insert_study_record(
        db, output_id="o1", ts=1.0, generation=2, profile_id="p", record=rec,
        rendered_box=box, canonical_hash="c", packet_hash="q"
    )
    assert len(h) == 64
    db.commit()
    assert db.execute("SELECT COUNT(*) FROM output_stub").fetchone()[0] == 1
    row = db.execute(
        "SELECT generation,profile_id,record_hash,canonical_hash,packet_hash FROM eos_pipeline_study_records"
    ).fetchone()
    assert row == (2, "p", h, "c", "q")


def test_duplicate_study_output_binding_fails_closed():
    db = sqlite3.connect(":memory:")
    ensure_study_schema(db)
    rec = build_record(config=config(), canonical_values=canonical(), self_report_values=report(), context={})
    kwargs = dict(
        output_id="same", ts=1.0, generation=2, profile_id="p", record=rec, rendered_box="box",
        canonical_hash="c", packet_hash="q"
    )
    insert_study_record(db, **kwargs)
    with pytest.raises(sqlite3.IntegrityError):
        insert_study_record(db, **kwargs)
