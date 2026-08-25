import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import time

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


def budget_obj(signature="b", zero_leases=True):
    return {
        "counter_sha256": signature,
        "zero_unexpired_leases": zero_leases,
    }


def make_budget_db(path: Path, *, requests=1, lease_expires_at=None):
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE provider_state(
          provider TEXT PRIMARY KEY,
          max_inflight INTEGER NOT NULL,
          min_interval_s REAL NOT NULL DEFAULT 0,
          cooldown_until REAL NOT NULL DEFAULT 0,
          last_start REAL NOT NULL DEFAULT 0,
          total_requests INTEGER NOT NULL DEFAULT 0,
          total_success INTEGER NOT NULL DEFAULT 0,
          total_429 INTEGER NOT NULL DEFAULT 0,
          total_errors INTEGER NOT NULL DEFAULT 0,
          last_status TEXT,
          last_observed_at TEXT
        );
        CREATE TABLE leases(
          lease_id TEXT PRIMARY KEY,
          provider TEXT NOT NULL,
          owner TEXT NOT NULL,
          acquired_at REAL NOT NULL,
          expires_at REAL NOT NULL
        );
        """
    )
    con.execute(
        "INSERT INTO provider_state(provider,max_inflight,total_requests,total_success,total_429,total_errors) "
        "VALUES('openrouter',3,?,?,?,?)",
        (requests, 1, 0, 0),
    )
    con.execute(
        "INSERT INTO provider_state(provider,max_inflight,total_requests,total_success,total_429,total_errors) "
        "VALUES('github',1,5,5,0,0)"
    )
    if lease_expires_at is not None:
        con.execute(
            "INSERT INTO leases(lease_id,provider,owner,acquired_at,expires_at) VALUES(?,?,?,?,?)",
            ("lease-1", "openrouter", "worker", time.time(), lease_expires_at),
        )
    con.commit()
    con.close()


def test_file_sha256_returns_exact_hex_digest(tmp_path):
    p = tmp_path / "hash-source.bin"
    payload = b"trigger2-quiescence-hash-regression"
    p.write_bytes(payload)
    assert probe.file_sha256(p) == hashlib.sha256(payload).hexdigest()


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


def test_shared_budget_snapshot_detects_direct_counter_change(tmp_path):
    db = tmp_path / "budget.sqlite3"
    make_budget_db(db, requests=7)
    before = probe.provider_budget_snapshot(db, now=time.time(), providers=["openrouter"])
    con = sqlite3.connect(db)
    con.execute("UPDATE provider_state SET total_requests=total_requests+1 WHERE provider='openrouter'")
    con.commit(); con.close()
    after = probe.provider_budget_snapshot(db, now=time.time(), providers=["openrouter"])
    assert before["counter_sha256"] != after["counter_sha256"]
    assert before["counters"]["providers"]["openrouter"]["total_requests"] == 7
    assert after["counters"]["providers"]["openrouter"]["total_requests"] == 8


def test_shared_budget_filter_ignores_noncanonical_tool_lane_change(tmp_path):
    db = tmp_path / "budget.sqlite3"
    make_budget_db(db, requests=7)
    before = probe.provider_budget_snapshot(db, now=time.time(), providers=["openrouter"])
    con = sqlite3.connect(db)
    con.execute("UPDATE provider_state SET total_requests=total_requests+1 WHERE provider='github'")
    con.commit(); con.close()
    after = probe.provider_budget_snapshot(db, now=time.time(), providers=["openrouter"])
    assert before["counter_sha256"] == after["counter_sha256"]
    assert before["provider_filter"] == ["openrouter"]
    assert "github" not in before["counters"]["providers"]


def test_shared_budget_snapshot_reports_unexpired_lease(tmp_path):
    db = tmp_path / "budget.sqlite3"
    make_budget_db(db, requests=1, lease_expires_at=time.time() + 60)
    snap = probe.provider_budget_snapshot(db, now=time.time(), providers=["openrouter"])
    assert snap["zero_unexpired_leases"] is False
    assert snap["unexpired_leases"][0]["provider"] == "openrouter"


def test_shared_budget_missing_fails_closed(tmp_path):
    with pytest.raises(probe.ProbeError, match="shared provider budget DB unavailable"):
        probe.provider_budget_snapshot(tmp_path / "missing.sqlite3")


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
        budget_obj("b", True),
        budget_obj("b", True),
    )
    assert out["status"] == "PASS_COMPONENT_ONLY"
    assert out["failure_reasons"] == []


def test_evaluate_fails_live_process_even_with_stable_counters():
    out = probe.evaluate(
        {"hard_off": True},
        {"usage_sha256": "x"},
        {"usage_sha256": "x"},
        [{"zero_forbidden": True}, {"zero_forbidden": False}],
        budget_obj("b", True),
        budget_obj("b", True),
    )
    assert out["status"] == "FAIL_CLOSED"
    assert "FORBIDDEN_FREE_SWARM_PROCESS_OBSERVED" in out["failure_reasons"]


def test_evaluate_fails_usage_change_even_with_zero_processes():
    out = probe.evaluate(
        {"hard_off": True},
        {"usage_sha256": "x"},
        {"usage_sha256": "y"},
        [{"zero_forbidden": True}],
        budget_obj("b", True),
        budget_obj("b", True),
    )
    assert out["status"] == "FAIL_CLOSED"
    assert "PROVIDER_USAGE_CHANGED_DURING_WINDOW" in out["failure_reasons"]


def test_evaluate_fails_direct_budget_change_even_when_live_metrics_static():
    out = probe.evaluate(
        {"hard_off": True},
        {"usage_sha256": "same-derived-worker-view"},
        {"usage_sha256": "same-derived-worker-view"},
        [{"zero_forbidden": True}],
        budget_obj("before", True),
        budget_obj("after", True),
    )
    assert out["status"] == "FAIL_CLOSED"
    assert "SHARED_PROVIDER_BUDGET_COUNTER_CHANGED_DURING_WINDOW" in out["failure_reasons"]


def test_evaluate_fails_unexpired_budget_lease():
    out = probe.evaluate(
        {"hard_off": True},
        {"usage_sha256": "x"},
        {"usage_sha256": "x"},
        [{"zero_forbidden": True}],
        budget_obj("b", False),
        budget_obj("b", True),
    )
    assert out["status"] == "FAIL_CLOSED"
    assert "UNEXPIRED_SHARED_PROVIDER_BUDGET_LEASE_OBSERVED" in out["failure_reasons"]


def test_evaluate_fails_without_direct_budget_evidence():
    out = probe.evaluate(
        {"hard_off": True},
        {"usage_sha256": "x"},
        {"usage_sha256": "x"},
        [{"zero_forbidden": True}],
    )
    assert out["status"] == "FAIL_CLOSED"
    assert "NO_SHARED_PROVIDER_BUDGET_EVIDENCE" in out["failure_reasons"]


def test_metrics_missing_aggregate_fails_closed(tmp_path):
    p = tmp_path / "m.json"
    obj = metrics_obj(); del obj["workers"]["exact_usage_rows"]
    write_json(p, obj)
    with pytest.raises(probe.ProbeError):
        probe.provider_usage_snapshot(p)
