"""Authority-bound tests for the canonical Bugfix-Frankenstein entrypoint."""
import sys
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parents[1] / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept"
sys.path.insert(0, str(PKG_DIR))

import frankenstein_authority_gate_v1 as gate
import frankenstein_bugfix_v1 as bugfix


def test_current_bugfix_entrypoint_is_hardoff_bound():
    state = bugfix.authority_status()
    assert state["provider_routes_admitted"] is False
    assert state["provider_calls_performed"] == 0
    assert state["secret_lookups_performed"] == 0


def test_current_bugfix_refuses_before_quarantined_execution(monkeypatch):
    called = []
    monkeypatch.setattr(sys, "argv", ["frankenstein_bugfix_v1.py"])
    monkeypatch.setattr(bugfix.runpy, "run_path", lambda *a, **k: called.append((a, k)))
    try:
        bugfix.main()
        assert False, "HARD_OFF must block bugfix provider loop"
    except gate.ProviderAuthorityBlocked:
        pass
    assert called == []
