"""Tests for frankenstein_orchestrator_v1.py's non-networked logic. Real
tmp Fabric (same discipline as every other GRID10 fabric test), but every
call that would hit a real network (call_specific_tier / dispatch_helper_task's
subprocess) is monkeypatched -- this suite verifies the ORCHESTRATION logic
(continuity framing, package-dispenser integration, respawn bookkeeping),
not third-party API behavior.
"""
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
PKG_DIR = Path(__file__).resolve().parents[1] / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(PKG_DIR))

from grid10_fabric import Fabric  # noqa: E402
import frankenstein_orchestrator_v1 as orch  # noqa: E402
import frankenstein_packages_v1 as packages  # noqa: E402


def test_continuation_opening_message_first_activation_has_no_continuity_claim():
    msg = orch.continuation_opening_message(None)
    assert "first activation" in msg
    assert "continuing your own prior work" not in msg


def test_continuation_opening_message_with_context_frames_as_own_prior_work():
    msg = orch.continuation_opening_message("I was halfway through package A2.")
    assert "continuing your own prior work" in msg
    assert "I was halfway through package A2." in msg
    assert "not reading a summary of someone else's work" in msg


def test_ensure_scope_is_idempotent(tmp_path):
    f = Fabric(tmp_path / "s1.sqlite")
    orch._ensure_scope(f)
    snap1 = f.snapshot()
    orch._ensure_scope(f)
    snap2 = f.snapshot()
    assert snap1.epoch == snap2.epoch, "calling _ensure_scope twice must not re-seed/reset the scope"


def test_record_build_event_commits_a_real_packet(tmp_path):
    f = Fabric(tmp_path / "s1.sqlite")
    orch._ensure_scope(f)
    log_path = tmp_path / "log.txt"
    result = orch.record_build_event(f, "test-node", {"event": "TEST", "x": 1}, log_path)
    assert result.get("ok") is True
    snap = f.snapshot()
    scope_row = [s for s in snap.scopes if s["scope"] == orch.BUILD_SCOPE][0]
    assert scope_row["evidence_count"] >= 1


def test_run_bauleiter_instance_claims_and_dispatches_a_real_package(tmp_path, monkeypatch):
    """No real network: dispatch_helper_task and call_specific_tier (used only
    for the end-of-activation narrative) are monkeypatched. Verifies the
    package-dispenser integration is actually wired into the main loop --
    Gabriel's core requirement that packages, not freeform monolith tasks,
    drive dispatch."""
    fabric_path = tmp_path / "s1.sqlite"
    sandbox_dir = tmp_path / "sandbox"
    log_path = sandbox_dir / "log.txt"

    dispatched_descriptions = []

    def fake_dispatch(task_description, reason, log_path_arg, max_retries=4):
        dispatched_descriptions.append(task_description)
        return {"ok": True}

    def fake_call_specific_tier(tier_label, messages, **kwargs):
        return "Fake narrative summary for testing."

    monkeypatch.setattr(orch, "dispatch_helper_task", fake_dispatch)
    monkeypatch.setattr(orch, "call_specific_tier", fake_call_specific_tier)

    result = orch.run_bauleiter_instance(None, str(fabric_path), sandbox_dir, log_path,
                                          max_actions=2, max_seconds=30.0)

    assert result["real_actions_taken"] == 2
    assert len(dispatched_descriptions) == 2
    # The dispatched text must be the PACKAGE's own self-contained
    # description, never a placeholder/freeform planning string.
    all_descriptions = "\n".join(p["description"] for phase in packages.PHASES for p in phase["packages"])
    for d in dispatched_descriptions:
        assert d in all_descriptions

    summary_path = Path(result["continuation_summary_path"])
    assert summary_path.exists()
    assert summary_path.read_text() == "Fake narrative summary for testing."

    fabric = Fabric(fabric_path)
    progress = packages.progress_summary(fabric)
    assert progress["done"] == 2


def test_run_bauleiter_instance_ends_cleanly_when_all_packages_already_done(tmp_path, monkeypatch):
    fabric_path = tmp_path / "s1.sqlite"
    sandbox_dir = tmp_path / "sandbox"
    log_path = sandbox_dir / "log.txt"

    fabric = Fabric(fabric_path)
    packages.seed_all_packages(fabric)
    for pid in packages._all_package_ids():
        packages.mark_package_done(fabric, pid, ok=True, node_id="pre-seeded")

    calls = []
    monkeypatch.setattr(orch, "dispatch_helper_task", lambda *a, **k: calls.append(1) or {"ok": True})
    monkeypatch.setattr(orch, "call_specific_tier", lambda *a, **k: "done narrative")

    result = orch.run_bauleiter_instance(None, str(fabric_path), sandbox_dir, log_path)
    assert result["real_actions_taken"] == 0
    assert result["ended_reason"] == "checkpoint"
    assert calls == [], "must never dispatch anything once every package is already done"


def test_run_bauleiter_instance_respects_training_marker(tmp_path, monkeypatch):
    fabric_path = tmp_path / "s1.sqlite"
    sandbox_dir = tmp_path / "sandbox"
    sandbox_dir.mkdir(parents=True)
    log_path = sandbox_dir / "log.txt"
    (sandbox_dir / "TRAINING_RUN_READY_FOR_LAUNCH.json").write_text("{}")

    calls = []
    monkeypatch.setattr(orch, "dispatch_helper_task", lambda *a, **k: calls.append(1) or {"ok": True})
    monkeypatch.setattr(orch, "call_specific_tier", lambda *a, **k: "narrative")

    result = orch.run_bauleiter_instance(None, str(fabric_path), sandbox_dir, log_path)
    assert result["ended_reason"] == "training_marker_present"
    assert calls == [], "must never dispatch further work once the training marker is present"
