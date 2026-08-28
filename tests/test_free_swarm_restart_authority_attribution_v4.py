from __future__ import annotations

import importlib.util
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools" / "free_swarm_restart_authority_attribution_v4.py"
spec = importlib.util.spec_from_file_location("restart_attr_v4", TOOL)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def root(path="/srv/clay/run_6000_free_swarm_supervisor.sh", cls="SYSTEMD_OR_SCOPE", pid=123):
    pat = "run_6000_free_swarm_supervisor.sh"
    return {"pid": pid, "ppid": 1, "argv": f"/bin/bash {path}",
            "cgroup": "0::/system.slice/clay-free-swarm.service",
            "pid_ns": "pid:[1]", "mnt_ns": "mnt:[1]", "matched_patterns": [pat],
            "restart_authority": {"class": cls, "confidence": "HIGH"}}


def sd(command_text):
    return lambda unit: {"unit": unit, "show_rc": 0, "cat_rc": 0,
                         "show_sha256": "a", "cat_sha256": "b",
                         "matched_patterns": ["run_6000_free_swarm_supervisor.sh"],
                         "command_text": command_text}


def test_exact_same_systemd_entrypoint_path_passes():
    got = mod.assess_root(root(), systemd_lookup=sd("ExecStart=/bin/bash /srv/clay/run_6000_free_swarm_supervisor.sh"))
    assert got["actionable"] is True
    assert got["reason"].endswith("EXACT_COMMAND_BOUND")


def test_same_basename_different_tree_is_rejected():
    got = mod.assess_root(root("/srv/clay-A/run_6000_free_swarm_supervisor.sh"),
                          systemd_lookup=sd("ExecStart=/bin/bash /srv/clay-B/run_6000_free_swarm_supervisor.sh"))
    assert got["actionable"] is False
    assert got["reason"] == "OWNING_OBJECT_EXACT_COMMAND_PATH_MISMATCH"


def test_object_with_two_same_pattern_paths_is_ambiguous():
    got = mod.assess_root(root(), systemd_lookup=sd(
        "ExecStart=/bin/bash /srv/clay/run_6000_free_swarm_supervisor.sh ; "
        "/bin/bash /srv/other/run_6000_free_swarm_supervisor.sh"))
    assert got["actionable"] is False


def test_cron_same_basename_different_tree_is_rejected():
    r = root("/srv/clay-A/run_6000_free_swarm_supervisor.sh", cls="CRON_OR_TIMER")
    got = mod.assess_root(r, cron_lookup=lambda: [{
        "source": "/etc/cron.d/clay", "source_sha256": "a", "line_sha256": "x",
        "matched_patterns": ["run_6000_free_swarm_supervisor.sh"],
        "command_text": "* * * * * root /bin/bash /srv/clay-B/run_6000_free_swarm_supervisor.sh"}])
    assert got["actionable"] is False
    assert got["reason"] == "OWNING_OBJECT_EXACT_COMMAND_PATH_MISMATCH"


def test_command_binding_requires_exactly_one_root_path():
    ok, _ = mod.exact_command_binding(
        "/bin/bash /a/run_6000_free_swarm_supervisor.sh /b/run_6000_free_swarm_supervisor.sh",
        "/bin/bash /a/run_6000_free_swarm_supervisor.sh",
        ["run_6000_free_swarm_supervisor.sh"])
    assert ok is False
