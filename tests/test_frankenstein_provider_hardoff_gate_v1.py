"""Regression tests for the Frankenstein external-caller authority boundary.

These tests are deliberately non-networked.  They prove ordering: canonical
admission is consulted before provider helper import/secret enumeration,
network-capable client import, Aider subprocess dispatch, or retry/backoff.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
PKG_DIR = Path(__file__).resolve().parents[1] / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(PKG_DIR))

import frankenstein_bugfix_v1 as bugfix  # noqa: E402
import frankenstein_orchestrator_v1 as orch  # noqa: E402


def test_bauleiter_provider_call_hardoff_precedes_provider_import(monkeypatch):
    imports = []
    monkeypatch.setattr(orch, "provider_is_admitted_free", lambda _provider: False)

    def forbidden_import(name):
        imports.append(name)
        raise AssertionError(f"must not import downstream provider/network client: {name}")

    monkeypatch.setattr(orch.importlib, "import_module", forbidden_import)
    with pytest.raises(orch.TierUnavailable, match="HARD_OFF_OR_UNADMITTED"):
        orch.call_specific_tier("nvidia", [{"role": "user", "content": "x"}])
    assert imports == []


def test_bauleiter_hardoff_precedes_aider_subprocess(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(orch, "admitted_provider_names", lambda: ())

    def forbidden_subprocess(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("Aider subprocess must not start under HARD_OFF")

    monkeypatch.setattr(orch.subprocess, "run", forbidden_subprocess)
    result = orch.dispatch_helper_task("small package", "test", tmp_path / "gate.log")
    assert result["ok"] is False
    assert result["blocked"] == "CANONICAL_PROVIDER_HARD_OFF_OR_PARTIAL_ADMISSION"
    assert result["provider_calls"] == 0
    assert result["secret_lookups"] == 0
    assert result["aider_calls"] == 0
    assert calls == []


def test_bugfix_hardoff_precedes_provider_import(monkeypatch):
    imports = []
    monkeypatch.setattr(bugfix, "provider_is_admitted_free", lambda _provider: False)

    def forbidden_import(name):
        imports.append(name)
        raise AssertionError(f"must not import downstream provider/network client: {name}")

    monkeypatch.setattr(bugfix.importlib, "import_module", forbidden_import)
    with pytest.raises(bugfix.ProviderHardOff, match="HARD_OFF_OR_UNADMITTED"):
        bugfix._call_one_tier("nvidia", [{"role": "user", "content": "x"}])
    assert imports == []


def test_bugfix_authority_denial_is_not_retried_as_rate_limit(monkeypatch, tmp_path):
    sleeps = []

    def blocked(*args, **kwargs):
        raise bugfix.ProviderHardOff("canonical hard off")

    monkeypatch.setattr(bugfix, "call_with_explicit_fallback", blocked)
    monkeypatch.setattr(bugfix.time, "sleep", lambda seconds: sleeps.append(seconds))

    log_path = tmp_path / "bugfix.log"
    with pytest.raises(bugfix.ProviderHardOff, match="canonical hard off"):
        bugfix.wait_for_any_tier_available([{"role": "user", "content": "x"}], log_path)
    assert sleeps == []
    log = log_path.read_text()
    assert "provider_calls=0" in log
    assert "secret_lookups=0" in log
    assert "network_calls=0" in log
