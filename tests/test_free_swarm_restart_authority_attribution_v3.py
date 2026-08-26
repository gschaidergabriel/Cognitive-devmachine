from __future__ import annotations

import importlib.util
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools" / "free_swarm_restart_authority_attribution_v3.py"
spec = importlib.util.spec_from_file_location("restart_attr_v3", TOOL)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def root(pattern="run_6000_free_swarm_supervisor.sh", cls="SYSTEMD_OR_SCOPE", pid=123, unit="clay-free-swarm.service"):
    return {
        "pid": pid,
        "ppid": 1,
        "argv": f"/bin/bash /srv/clay/{pattern}",
        "cgroup": f"0::/system.slice/{unit}",
        "pid_ns": "pid:[1]",
        "mnt_ns": "mnt:[1]",
        "matched_patterns": [pattern],
        "restart_authority": {"class": cls, "confidence": "HIGH", "evidence": [{"unit": unit}]},
    }


def test_exact_root_specific_systemd_binding_passes():
    r = root()
    got = mod.assess_root(r, systemd_lookup=lambda unit: {
        "unit": unit, "show_rc": 0, "cat_rc": 0,
        "show_sha256": "a", "cat_sha256": "b",
        "matched_patterns": ["run_6000_free_swarm_supervisor.sh"],
        "show_excerpt": "Id=clay-free-swarm.service",
    })
    assert got["actionable"] is True
    assert got["reason"] == "ROOT_SPECIFIC_SYSTEMD_AUTHORITY_BOUND"


def test_cross_root_systemd_transplant_rejected():
    r = root(pattern="run_research_distillery_local.py", unit="clay-free-swarm.service")
    got = mod.assess_root(r, systemd_lookup=lambda unit: {
        "unit": unit, "show_rc": 0, "cat_rc": 0,
        "show_sha256": "a", "cat_sha256": "b",
        "matched_patterns": ["run_6000_free_swarm_supervisor.sh"],
        "show_excerpt": "Id=clay-free-swarm.service",
    })
    assert got["actionable"] is False
    assert got["reason"] == "SYSTEMD_OBJECT_CROSS_ROOT_OR_PATTERN_MISMATCH"


def test_cgroup_must_bind_single_systemd_object():
    r = root()
    r["cgroup"] = "0::/system.slice/a.service/b.scope"
    got = mod.assess_root(r, systemd_lookup=lambda unit: {})
    assert got["actionable"] is False
    assert got["reason"] == "ROOT_CGROUP_NOT_BOUND_TO_SINGLE_SYSTEMD_OBJECT"


def test_root_argv_receipt_transplant_rejected():
    r = root()
    r["argv"] = "/usr/bin/python unrelated.py"
    got = mod.assess_root(r, systemd_lookup=lambda unit: {})
    assert got["actionable"] is False
    assert got["reason"] == "ROOT_ARGV_PATTERN_BINDING_MISMATCH"


def test_root_specific_cron_binding_passes():
    r = root(pattern="update_fabric_live.py", cls="CRON_OR_TIMER")
    got = mod.assess_root(r, cron_lookup=lambda: [{
        "source": "/etc/cron.d/clay-fabric",
        "source_sha256": "a", "line_sha256": "line-a",
        "matched_patterns": ["update_fabric_live.py"],
    }])
    assert got["actionable"] is True
    assert got["reason"] == "ROOT_SPECIFIC_SCHEDULER_AUTHORITY_BOUND"


def test_cross_root_cron_transplant_rejected():
    r = root(pattern="update_fabric_live.py", cls="CRON_OR_TIMER")
    got = mod.assess_root(r, cron_lookup=lambda: [{
        "source": "/etc/cron.d/clay-other",
        "source_sha256": "a", "line_sha256": "line-b",
        "matched_patterns": ["run_research_distillery_local.py"],
    }])
    assert got["actionable"] is False
    assert got["reason"] == "SCHEDULER_OBJECT_NOT_ROOT_SPECIFIC_OR_AMBIGUOUS"


def test_ambiguous_duplicate_cron_entries_rejected():
    r = root(pattern="update_fabric_live.py", cls="CRON_OR_TIMER")
    hit = {"source": "/etc/cron.d/a", "source_sha256": "a", "line_sha256": "x", "matched_patterns": ["update_fabric_live.py"]}
    hit2 = {"source": "/etc/cron.d/b", "source_sha256": "b", "line_sha256": "y", "matched_patterns": ["update_fabric_live.py"]}
    got = mod.assess_root(r, cron_lookup=lambda: [hit, hit2])
    assert got["actionable"] is False


def test_global_cross_root_owning_object_collision_rejected():
    a = mod.assess_root(root(pid=1), systemd_lookup=lambda unit: {
        "unit": unit, "show_rc": 0, "cat_rc": 0, "show_sha256": "a", "cat_sha256": "b",
        "matched_patterns": ["run_6000_free_swarm_supervisor.sh"], "show_excerpt": "",
    })
    b = mod.assess_root(root(pid=2), systemd_lookup=lambda unit: {
        "unit": unit, "show_rc": 0, "cat_rc": 0, "show_sha256": "a", "cat_sha256": "b",
        "matched_patterns": ["run_6000_free_swarm_supervisor.sh"], "show_excerpt": "",
    })
    assert a["actionable"] and b["actionable"]
    assert mod.cross_root_collision([a, b]) is True


def test_container_hint_remains_non_actionable():
    r = root(cls="CONTAINER_ORCHESTRATION")
    r["cgroup"] = "0::/docker/abc"
    got = mod.assess_root(r)
    assert got["actionable"] is False
    assert "ROOT_OWNING_OBJECT_NOT_BOUND" in got["reason"]
