from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("qv2", ROOT / "tools/free_swarm_runtime_quiescence_probe_v2.py")
assert SPEC and SPEC.loader
qv2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qv2)


def binding(head="a"*40, tree="b"*40, epoch="9.13", clean=True, passed=True):
    return {
        "pass": passed,
        "dirty": not clean,
        "local_head": head,
        "remote_main_head": head,
        "tree": tree,
        "authority_epoch": epoch,
        "supervisor_schema_version": epoch,
        "source_sha256": {"x": "c"*64},
        "provider_calls": 0,
        "secret_lookups": 0,
    }


def inner(duration=90.1, status="PASS_COMPONENT_ONLY"):
    return {"decision": {"status": status}, "observation": {"duration_seconds": duration}}


def test_pass_requires_stable_current_binding_and_90s():
    r = qv2.evaluate(binding(), inner(), binding(), 90.0)
    assert r["pass"] is True
    assert r["status"] == "PASS_SCOPED_RUNTIME_QUIESCENCE"


def test_rejects_short_requested_window_even_if_inner_claims_pass():
    r = qv2.evaluate(binding(), inner(90.1), binding(), 89.9)
    assert r["pass"] is False
    assert "requested_window_below_90s" in r["errors"]


def test_rejects_short_observed_duration():
    r = qv2.evaluate(binding(), inner(89.99), binding(), 90.0)
    assert r["pass"] is False
    assert "observed_duration_below_90s" in r["errors"]


def test_rejects_remote_main_move_during_observation():
    pre = binding(head="a"*40)
    post = binding(head="d"*40)
    r = qv2.evaluate(pre, inner(), post, 90.0)
    assert r["pass"] is False
    assert "binding_changed:local_head" in r["errors"]
    assert "binding_changed:remote_main_head" in r["errors"]


def test_rejects_authority_epoch_change():
    r = qv2.evaluate(binding(epoch="9.13"), inner(), binding(epoch="9.14"), 90.0)
    assert r["pass"] is False
    assert "binding_changed:authority_epoch" in r["errors"]


def test_rejects_source_hash_change():
    post = binding()
    post["source_sha256"] = {"x": "d"*64}
    r = qv2.evaluate(binding(), inner(), post, 90.0)
    assert r["pass"] is False
    assert "binding_changed:source_sha256" in r["errors"]


def test_rejects_dirty_or_failed_control_sync():
    r = qv2.evaluate(binding(clean=False, passed=False), inner(), binding(), 90.0)
    assert r["pass"] is False
    assert "pre_control_sync_not_pass" in r["errors"]
    assert "pre_working_tree_not_clean" in r["errors"]


def test_rejects_inner_process_or_counter_failure():
    r = qv2.evaluate(binding(), inner(status="FAIL_CLOSED"), binding(), 90.0)
    assert r["pass"] is False
    assert "v1_quiescence_not_pass" in r["errors"]
