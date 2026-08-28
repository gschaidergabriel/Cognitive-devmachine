"""Split-brain regression tests for Frankenstein provider authority."""
import json
import sys
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parents[1] / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept"
sys.path.insert(0, str(PKG_DIR))

import frankenstein_authority_gate_v1 as gate
import frankenstein_orchestrator_v1 as orch
import frankenstein_bugfix_v1 as bugfix


def _write_authority(repo_root: Path, *, inbox_routes: bool, canonical_routes: bool,
                     emergency_stop: bool | None = None, together_forbidden: bool = True,
                     remaining_paid: int = 0, canonical_together: bool = False) -> None:
    inbox_path = repo_root / gate.INBOX_RELATIVE_PATH
    canonical_path = repo_root / gate.PROVIDER_ADMISSION_RELATIVE_PATH
    inbox_path.parent.mkdir(parents=True, exist_ok=True)
    if emergency_stop is None:
        emergency_stop = not inbox_routes
    inbox_path.write_text(json.dumps({
        "free_only": {
            "enabled": True,
            "no_paid_fallback": True,
            "provider_routes_admitted": inbox_routes,
            "free_swarm_owner_emergency_stop": emergency_stop,
            "together_forbidden": together_forbidden,
            "remaining_together_paid_runs_authorized": remaining_paid,
        }
    }))
    providers = {name: {"admitted": canonical_routes} for name in ("groq", "mistral", "nvidia", "openrouter")}
    canonical = {
        "authority_epoch": "test",
        "mode": "FREE_ONLY",
        "execution_state": (
            "PROVIDER_ROUTES_ADMITTED" if canonical_routes
            else "OWNER_EMERGENCY_STOP_FREE_SWARM_HARD_OFF"
        ),
        "providers": providers,
    }
    if canonical_together:
        canonical["together"] = {"admitted": True}
    canonical_path.write_text(json.dumps(canonical))


def test_missing_either_authority_fails_closed(tmp_path):
    assert gate.provider_authority_state(tmp_path)["provider_routes_admitted"] is False
    inbox = tmp_path / gate.INBOX_RELATIVE_PATH
    inbox.parent.mkdir(parents=True, exist_ok=True)
    inbox.write_text(json.dumps({"free_only": {"enabled": True, "provider_routes_admitted": True,
                                               "free_swarm_owner_emergency_stop": False}}))
    assert gate.provider_authority_state(tmp_path)["provider_routes_admitted"] is False


def test_inbox_open_canonical_hardoff_split_brain_fails_closed(tmp_path):
    _write_authority(tmp_path, inbox_routes=True, canonical_routes=False, emergency_stop=False)
    state = gate.provider_authority_state(tmp_path)
    assert state["authority_readable"] is True
    assert state["authority_coherent"] is False
    assert state["provider_routes_admitted"] is False
    assert state["together_admitted"] is False
    assert state["reason"] == "AUTHORITY_SPLIT_BRAIN_FAIL_CLOSED"


def test_inbox_closed_canonical_open_still_fails_closed(tmp_path):
    _write_authority(tmp_path, inbox_routes=False, canonical_routes=True, emergency_stop=True)
    state = gate.provider_authority_state(tmp_path)
    assert state["provider_routes_admitted"] is False


def test_both_provider_authorities_must_explicitly_admit(tmp_path):
    _write_authority(tmp_path, inbox_routes=True, canonical_routes=True, emergency_stop=False)
    state = gate.provider_authority_state(tmp_path)
    assert state["authority_coherent"] is True
    assert state["provider_routes_admitted"] is True
    assert set(state["admitted_provider_names"]) == {"groq", "mistral", "nvidia", "openrouter"}


def test_together_cannot_be_minted_by_inbox_only(tmp_path):
    _write_authority(tmp_path, inbox_routes=True, canonical_routes=True, emergency_stop=False,
                     together_forbidden=False, remaining_paid=1, canonical_together=False)
    assert gate.provider_authority_state(tmp_path)["together_admitted"] is False


def test_no_paid_fallback_keeps_together_closed_even_with_explicit_canonical_object(tmp_path):
    _write_authority(tmp_path, inbox_routes=True, canonical_routes=True, emergency_stop=False,
                     together_forbidden=False, remaining_paid=1, canonical_together=True)
    assert gate.provider_authority_state(tmp_path)["together_admitted"] is False


def test_require_provider_routes_raises_on_split_brain(tmp_path):
    _write_authority(tmp_path, inbox_routes=True, canonical_routes=False, emergency_stop=False)
    try:
        gate.require_provider_routes("test", tmp_path)
        assert False, "split-brain must raise"
    except gate.ProviderAuthorityBlocked as exc:
        assert "blocked before provider import/secret lookup/network" in str(exc)


def test_canonical_entrypoints_have_no_eager_provider_imports():
    for module in (orch, bugfix):
        source = Path(module.__file__).read_text()
        assert "import requests" not in source
        assert "import llm" not in source


def test_entrypoints_never_execute_quarantined_donor_on_split_brain(tmp_path, monkeypatch):
    _write_authority(tmp_path, inbox_routes=True, canonical_routes=False, emergency_stop=False)
    for module, argv0 in ((orch, "frankenstein_orchestrator_v1.py"), (bugfix, "frankenstein_bugfix_v1.py")):
        monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
        called = []
        monkeypatch.setattr(sys, "argv", [argv0])
        monkeypatch.setattr(module.runpy, "run_path", lambda *a, **k: called.append((a, k)))
        try:
            module.main()
            assert False, "split-brain authority must raise"
        except gate.ProviderAuthorityBlocked:
            pass
        assert called == []
