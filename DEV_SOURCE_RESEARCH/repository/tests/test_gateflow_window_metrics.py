import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "gateflow_window_metrics", ROOT / "tools" / "gateflow_window_metrics.py"
)
window_metrics = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(window_metrics)


def test_missing_window_counts_remain_null():
    metrics = window_metrics.compile_window_metrics({})
    assert metrics["stale_evidence_rate"] is None
    assert metrics["duplicate_superseded_ratio"] is None
    assert metrics["target_queue_yield"] is None
    assert metrics["e2e_causal_chain_supported_fraction"] is None


def test_measured_quality_ratios_are_deterministic():
    window = {
        "window_counts": {
            "stale_evidence_count": 2,
            "evidence_items_count": 10,
            "duplicate_superseded_count": 3,
            "work_items_count": 12,
            "target_jobs_pass": 7,
            "target_jobs_completed": 10,
        },
        "e2e_causal_chain": [
            {"name": "candidate", "status": "SUPPORTED"},
            {"name": "verified_outcome", "status": "SUPPORTED"},
            {"name": "reentry", "status": "TERMINAL_ACCEPTED"},
            {"name": "causal_credit", "status": "OPEN"},
            {"name": "learning", "status": "UNMEASURED"},
        ],
    }
    metrics = window_metrics.compile_window_metrics(window)
    assert metrics["stale_evidence_rate"] == 0.2
    assert metrics["duplicate_superseded_ratio"] == 0.25
    assert metrics["target_queue_yield"] == 0.7
    assert metrics["e2e_causal_chain_supported_fraction"] == 0.6
    assert metrics["e2e_causal_chain_terminal_fraction"] == 0.2
    assert metrics["e2e_causal_chain_measured_fraction"] == 0.8


def test_impossible_ratio_is_rejected():
    try:
        window_metrics.safe_ratio(5, 4)
    except ValueError:
        pass
    else:
        raise AssertionError("numerator > denominator must fail")


def test_unknown_causal_status_is_rejected():
    try:
        window_metrics.compile_window_metrics(
            {"e2e_causal_chain": [{"name": "x", "status": "GUESSED"}]}
        )
    except ValueError:
        pass
    else:
        raise AssertionError("unknown causal status must fail")
