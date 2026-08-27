"""Tests for the real Frankenstein Bauleiter logic (the "quarantined donor"
implementation frankenstein_orchestrator_v1_PROVIDER_QUARANTINED_854f6bc.py,
which is exactly the original, non-networked-logic-tested implementation --
same content as frankenstein-master-cognition-concept/historical_tests/
frankenstein_orchestrator_v1_tests_854f6bc.py, just loaded via importlib by
explicit file path instead of `import frankenstein_orchestrator_v1`, because
that module name now resolves to the thin canonical authority-gate
entrypoint (frankenstein_orchestrator_v1.py) that trigger3 built on top of
this same, unmodified real logic -- see frankenstein_authority_gate_v1.py.

Every call that would hit a real network (call_specific_tier /
dispatch_helper_task's subprocess) is monkeypatched -- this suite verifies
the ORCHESTRATION logic (continuity framing, package-dispenser integration,
respawn bookkeeping, training-gate wiring), not third-party API behavior.

A separate, small suite at the bottom tests the canonical entrypoint's
authority-gate behavior itself, using an INJECTED tmp repo_root fixture for
both the blocked and admitted states -- deliberately NOT depending on the
live, shared, concurrently-modified SUPERVISOR_INBOX.json, so this test
never goes stale just because the project's real authority state changes.
"""
import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
PKG_DIR = REPO_ROOT / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(PKG_DIR))


def _load(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


from grid10_fabric import Fabric  # noqa: E402
import frankenstein_packages_v1 as packages  # noqa: E402
import frankenstein_authority_gate_v1 as authority_gate  # noqa: E402

orch = _load("frankenstein_orchestrator_v1_real", PKG_DIR / "frankenstein_orchestrator_v1_PROVIDER_QUARANTINED_854f6bc.py")
entrypoint = _load("frankenstein_orchestrator_v1_entrypoint", PKG_DIR / "frankenstein_orchestrator_v1.py")


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


def test_run_bauleiter_instance_stays_closed_without_example_ids_file(tmp_path, monkeypatch):
    """Gabriel's 2026-08-28 hard training-run precondition: with no
    TRAINING_EXAMPLE_IDS.json present (the honest, no-fabricated-examples
    starting state), the gate must never write the marker, even across
    activations, even once GRID10 is fully done."""
    fabric_path = tmp_path / "s1.sqlite"
    sandbox_dir = tmp_path / "sandbox"
    log_path = sandbox_dir / "log.txt"

    fabric = Fabric(fabric_path)
    packages.seed_all_packages(fabric)
    for pid in packages._all_package_ids():
        packages.mark_package_done(fabric, pid, ok=True, node_id="pre-seeded")

    monkeypatch.setattr(orch, "dispatch_helper_task", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(orch, "call_specific_tier", lambda *a, **k: "narrative")

    result = orch.run_bauleiter_instance(None, str(fabric_path), sandbox_dir, log_path)
    assert not (sandbox_dir / "TRAINING_RUN_READY_FOR_LAUNCH.json").exists()
    assert result["ended_reason"] == "checkpoint"


def test_run_bauleiter_instance_writes_marker_once_gate_genuinely_satisfied(tmp_path, monkeypatch):
    """The positive case: GRID10 fully done (packages all marked done) AND
    a real, fully-revised example is named -- the gate must then let the
    marker through, using the SAME real training_gate module (not mocked)."""
    import frankenstein_training_gate_v1 as training_gate

    fabric_path = tmp_path / "s1.sqlite"
    sandbox_dir = tmp_path / "sandbox"
    sandbox_dir.mkdir(parents=True)
    log_path = sandbox_dir / "log.txt"

    fabric = Fabric(fabric_path)
    packages.seed_all_packages(fabric)
    for pid in packages._all_package_ids():
        packages.mark_package_done(fabric, pid, ok=True, node_id="pre-seeded")

    import time as time_module
    revision_db = sandbox_dir / "training_data_revisions.sqlite3"
    for i in range(training_gate.REQUIRED_REVISIONS_PER_EXAMPLE):
        training_gate.record_revision(revision_db, "ex-1", "reviewer",
                                       f"real careful revision pass number {i+1} of this example",
                                       before_text=f"before-{i}", after_text=f"after-{i}")
        time_module.sleep(training_gate.MIN_SECONDS_BETWEEN_REVISIONS)
    (sandbox_dir / "TRAINING_EXAMPLE_IDS.json").write_text(json.dumps(["ex-1"]))

    monkeypatch.setattr(orch, "dispatch_helper_task", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(orch, "call_specific_tier", lambda *a, **k: "narrative")

    result = orch.run_bauleiter_instance(None, str(fabric_path), sandbox_dir, log_path)
    assert result["ended_reason"] == "training_marker_present"
    marker = sandbox_dir / "TRAINING_RUN_READY_FOR_LAUNCH.json"
    assert marker.exists()
    payload = json.loads(marker.read_text())
    assert payload["example_ids"] == ["ex-1"]


# ---- canonical entrypoint authority-gate behavior, injected fixture (not live global state) ----

def _write_inbox(repo_root: Path, provider_routes_admitted: bool) -> None:
    inbox_path = repo_root / authority_gate.INBOX_RELATIVE_PATH
    inbox_path.parent.mkdir(parents=True, exist_ok=True)
    inbox_path.write_text(json.dumps({
        "free_only": {
            "enabled": True,
            "provider_routes_admitted": provider_routes_admitted,
            "free_swarm_owner_emergency_stop": not provider_routes_admitted,
            "together_forbidden": True,
            "remaining_together_paid_runs_authorized": 0,
        }
    }))


def test_entrypoint_blocks_when_authority_denies(tmp_path, monkeypatch):
    _write_inbox(tmp_path, provider_routes_admitted=False)
    monkeypatch.setattr(entrypoint, "REPO_ROOT", tmp_path)
    try:
        authority_gate.require_provider_routes("test", tmp_path)
        assert False, "must raise when provider_routes_admitted is False"
    except authority_gate.ProviderAuthorityBlocked:
        pass


def test_entrypoint_admits_when_authority_allows(tmp_path):
    _write_inbox(tmp_path, provider_routes_admitted=True)
    state = authority_gate.require_provider_routes("test", tmp_path)
    assert state["provider_routes_admitted"] is True
