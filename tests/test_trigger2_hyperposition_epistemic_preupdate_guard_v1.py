from __future__ import annotations

from tools import trigger2_hyperposition_epistemic_preupdate_guard_v1 as guard


def _minimal_row(epistemic_type: str):
    return {
        "synthetic_event_history_evaluator_only": [],
        "synthetic_test_event_evaluator_only": {
            "event_id": "e-current",
            "epistemic_type": epistemic_type,
        },
    }


def test_nonobservational_epistemic_types_fail_before_u_state_path():
    for epistemic_type in (
        "HYPOTHESIS",
        "PREDICTION",
        "UNKNOWN",
        "MEASUREMENT_ERROR",
        "COUNTERHYPOTHESIS",
        "CONTRADICTION",
    ):
        result = guard.adjudicate(_minimal_row(epistemic_type))
        assert not result["pass"]
        assert result["underlying_gate_called"] is False
        assert any(
            x == f"EPISTEMIC_TYPE_NOT_EVIDENCE_ADMISSIBLE:e-current:{epistemic_type}"
            for x in result["failures"]
        )


def test_nonobservational_history_event_also_fails_before_base_gate():
    row = _minimal_row("SYNTHETIC_PROOF")
    row["synthetic_event_history_evaluator_only"] = [
        {"event_id": "e-history", "epistemic_type": "HYPOTHESIS"}
    ]
    result = guard.adjudicate(row)
    assert not result["pass"]
    assert result["underlying_gate_called"] is False
    assert "EPISTEMIC_TYPE_NOT_EVIDENCE_ADMISSIBLE:e-history:HYPOTHESIS" in result["failures"]


def test_missing_epistemic_type_fails_closed_before_base_gate():
    row = _minimal_row("SYNTHETIC_PROOF")
    row["synthetic_test_event_evaluator_only"] = {"event_id": "e-current"}
    result = guard.adjudicate(row)
    assert not result["pass"]
    assert result["underlying_gate_called"] is False
    assert "EPISTEMIC_TYPE_REQUIRED:e-current" in result["failures"]


def test_evidence_admissible_type_reaches_retained_state_history_gate_but_cannot_false_pass():
    for epistemic_type in ("OBSERVED", "SYNTHETIC_PROOF"):
        result = guard.adjudicate(_minimal_row(epistemic_type))
        assert not result["pass"]
        assert result["underlying_gate_called"] is True
        assert result["positive_D_E_promotion_ready"] is False
        assert any(x.startswith("STATE_HISTORY:") for x in result["failures"])


def test_arbitrary_new_epistemic_string_is_not_auto_admitted():
    result = guard.adjudicate(_minimal_row("FUTURE_NEW_TYPE"))
    assert not result["pass"]
    assert result["underlying_gate_called"] is False
    assert "EPISTEMIC_TYPE_NOT_EVIDENCE_ADMISSIBLE:e-current:FUTURE_NEW_TYPE" in result["failures"]
