import importlib.util
import json
from pathlib import Path

import pytest

SRC = Path(__file__).parents[1] / "tools" / "free_swarm_runtime_quiescence_probe_v1.py"
spec = importlib.util.spec_from_file_location("probe", SRC)
probe = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(probe)


def write_json(path: Path, obj):
    path.write_text(json.dumps(obj), encoding="utf-8")


def admission_obj(admitted=False):
    return {
        "authority_epoch": "8.78",
        "mode": "FREE_ONLY",
        "execution_state": probe.REQUIRED_EXECUTION_STATE,
        "providers": {"groq": {"admitted": admitted}, "nvidia": {"admitted": False}},
    }


def metrics_obj(tokens=10, corpus_chars=100):
    return {
        "generated_at": "x",
        "workers": {
            "exact_usage_rows": 1,
            "input_tokens": tokens,
            "output_tokens": 2,
            "total_tokens": tokens + 2,
            "models": [
                {
                    "provider": "groq", "model": "m", "requests": 1, "success": 1,
                    "rate_limits": 0, "errors": 0, "input_tokens": tokens,
                    "output_tokens": 2, "total_tokens": tokens + 2,
                }
            ],
        },
        "corpus": {"characters": corpus_chars},
    }


def test_admission_hard_off_passes(tmp_path):
    p = tmp_path / "admission.json"
    write_json(p, admission_obj(False))
    state = probe.admission_state(p)
    assert state["hard_off"] is True
    assert state["provider_admitted"] == {"groq": False, "nvidia": False}


def test_admission_any_provider_true_fails(tmp_path):
    p = tmp_path / "admission.json"
    write_json(p, admission_obj(True))
    assert probe.admission_state(p)["hard_off"] is False


def test_usage_signature_ignores_nonprovider_corpus_churn(tmp_path):
    a = tmp_path / "a.json"; b = tmp_path / "b.json"
    write_json(a, metrics_obj(tokens=10, corpus_chars=100))
    write_json(b, metrics_obj(tokens=10, corpus_chars=999))
    assert probe.provider_usage_snapshot(a)["usage_sha256"] == probe.provider_usage_snapshot(b)["usage_sha256"]


def test_usage_signature_detects_provider_change(tmp_path):
    a = tmp_path / "a.json"; b = tmp_path / "b.json"
    write_json(a, metrics_obj(tokens=10)); write_json(b, metrics_obj(tokens=11))
    assert probe.provider_usage_snapshot(a)["usage_sha256"] != probe.provider_usage_snapshot(b)["usage_sha256"]


def test_scan_processes_detects_forbidden(tmp_path):
    proc = tmp_path / "proc"; cmd = proc / "123" / "cmdline"; cmd.parent.mkdir(parents=True)
    cmd.write_bytes(b"bash\0tools/run_free_evidence_forge.py\0")
    result = probe.scan_processes(proc, ["run_free_evidence_forge.py"])
    assert result["zero_forbidden"] is False
    assert result["matches"][0]["pid"] == 123


def test_evaluate_pass_component_only():
    out = probe.evaluate(
        {"hard_off": True},
        {"usage_sha256": "x"},
        {"usage_sha256": "x"},
        [{"zero_forbidden": True}, {"zero_forbidden": True}],
    )
    assert out["status"] == "PASS_COMPONENT_ONLY"
    assert out["failure_reasons"] == []


def test_evaluate_fails_live_process_even_with_stable_usage():
    out = probe.evaluate(
        {"hard_off": True},
        {"usage_sha256": "x"},
        {"usage_sha256": "x"},
        [{"zero_forbidden": True}, {"zero_forbidden": False}],
    )
    assert out["status"] == "FAIL_CLOSED"
    assert "FORBIDDEN_FREE_SWARM_PROCESS_OBSERVED" in out["failure_reasons"]


def test_evaluate_fails_usage_change_even_with_zero_processes():
    out = probe.evaluate(
        {"hard_off": True},
        {"usage_sha256": "x"},
        {"usage_sha256": "y"},
        [{"zero_forbidden": True}],
    )
    assert out["status"] == "FAIL_CLOSED"
    assert "PROVIDER_USAGE_CHANGED_DURING_WINDOW" in out["failure_reasons"]


def test_metrics_missing_aggregate_fails_closed(tmp_path):
    p = tmp_path / "m.json"
    obj = metrics_obj(); del obj["workers"]["exact_usage_rows"]
    write_json(p, obj)
    with pytest.raises(probe.ProbeError):
        probe.provider_usage_snapshot(p)
