from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL = Path(__file__).resolve().parents[1] / "tools" / "free_swarm_restart_authority_attribution_v2.py"
spec = importlib.util.spec_from_file_location("restart_attr_v2", TOOL)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def root(cls: str, confidence: str = "HIGH"):
    return {
        "pid": 123,
        "matched_patterns": ["run_6000_free_swarm_supervisor.sh"],
        "restart_authority": {"class": cls, "confidence": confidence, "evidence": []},
    }


def test_unknown_is_not_actionable():
    got = mod.assess_root(root("UNKNOWN", "NONE"))
    assert got["actionable"] is False
    assert got["reason"] == "UNKNOWN_RESTART_AUTHORITY"


def test_medium_container_hint_is_not_actionable():
    got = mod.assess_root(root("CONTAINER_ORCHESTRATION", "MEDIUM"))
    assert got["actionable"] is False
    assert "OWNING_OBJECT_NOT_BOUND" in got["reason"]


def test_systemd_requires_exact_bound_unit(monkeypatch):
    r = root("SYSTEMD_OR_SCOPE")
    r["restart_authority"]["evidence"] = [{"unit": "clay-free-swarm.service"}]
    monkeypatch.setattr(mod, "systemd_unit_evidence", lambda unit: {
        "unit": unit, "show_rc": 0, "cat_rc": 0,
        "show_sha256": "a", "cat_sha256": "b", "legacy_pattern_bound": True,
        "show_excerpt": "Id=clay-free-swarm.service",
    })
    got = mod.assess_root(r)
    assert got["actionable"] is True
    assert got["action"]["kind"] == "DISABLE_SYSTEMD_UNIT_FIRST"
    assert got["action"]["unit"] == "clay-free-swarm.service"


def test_systemd_without_legacy_binding_fails_closed(monkeypatch):
    r = root("SYSTEMD_OR_SCOPE")
    r["restart_authority"]["evidence"] = [{"unit": "unrelated.service"}]
    monkeypatch.setattr(mod, "systemd_unit_evidence", lambda unit: {
        "unit": unit, "show_rc": 0, "cat_rc": 0,
        "show_sha256": "a", "cat_sha256": "b", "legacy_pattern_bound": False,
        "show_excerpt": "Id=unrelated.service",
    })
    got = mod.assess_root(r)
    assert got["actionable"] is False
    assert got["reason"] == "SYSTEMD_UNIT_NOT_UNAMBIGUOUSLY_BOUND"


def test_cron_requires_single_exact_source_and_entry(monkeypatch):
    monkeypatch.setattr(mod, "cron_evidence", lambda: [{
        "source": "/etc/cron.d/clay", "matched_count": 1,
        "source_sha256": "a", "matching_line_hashes": ["b"],
    }])
    got = mod.assess_root(root("CRON_OR_TIMER"))
    assert got["actionable"] is True
    assert got["action"]["kind"] == "DISABLE_SCHEDULER_ENTRY_FIRST"


def test_no_process_binding_never_actionable():
    r = root("SYSTEMD_OR_SCOPE")
    r["matched_patterns"] = []
    got = mod.assess_root(r)
    assert got["actionable"] is False
    assert got["reason"] == "NO_CLAY_LEGACY_PROCESS_BINDING"
