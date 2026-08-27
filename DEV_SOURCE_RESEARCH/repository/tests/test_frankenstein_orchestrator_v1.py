"""Authority-bound tests for the canonical Frankenstein Bauleiter entrypoint."""
import sys
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parents[1] / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept"
sys.path.insert(0, str(PKG_DIR))

import frankenstein_authority_gate_v1 as gate
import frankenstein_orchestrator_v1 as orch


def test_current_orchestrator_entrypoint_is_hardoff_bound():
    state = orch.authority_status()
    assert state["provider_routes_admitted"] is False
    assert state["provider_calls_performed"] == 0
    assert state["secret_lookups_performed"] == 0


def test_current_orchestrator_refuses_before_quarantined_execution(monkeypatch):
    called = []
    monkeypatch.setattr(sys, "argv", ["frankenstein_orchestrator_v1.py"])
    monkeypatch.setattr(orch.runpy, "run_path", lambda *a, **k: called.append((a, k)))
    try:
        orch.main()
        assert False, "HARD_OFF must block orchestration"
    except gate.ProviderAuthorityBlocked:
        pass
    assert called == []
