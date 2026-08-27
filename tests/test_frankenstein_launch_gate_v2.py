from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "research_entity"
    / "topic_packets"
    / "frankenstein-master-cognition-concept"
    / "frankenstein_launch_gate_v2.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("frankenstein_launch_gate_v2", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_only_literal_true_admits():
    m = _load_module()
    assert m.evaluate_decision({"admitted": True}, "bauleiter")["admitted"] is True
    for value in (False, None, 1, "true", "True", [], {}):
        assert m.evaluate_decision({"admitted": value}, "bauleiter")["admitted"] is False


def test_unknown_role_fails_closed_without_target():
    m = _load_module()
    out = m.evaluate_decision({"admitted": True}, "unknown")
    assert out["admitted"] is False
    assert out["reason"] == "UNKNOWN_ROLE"
    assert out["provider_calls"] == 0
    assert out["secret_lookups_by_launcher"] == 0


def test_blocked_main_never_execs_retained_role():
    m = _load_module()
    blocked = {
        "schema": "FREEPOOL_FALLBACK_PROVIDER_GATE/v1",
        "admitted": False,
        "reason": "HARD_OFF",
        "authority_schema_version": "9.13",
        "runtime_provider_authority": "HARD_OFF",
    }
    with mock.patch.object(m, "_load_gate_decision", return_value=blocked), mock.patch.object(
        m.os, "execv"
    ) as execv:
        rc = m.main(["--role", "bauleiter"])
    assert rc == 77
    execv.assert_not_called()


def test_probe_never_execs_even_if_gate_admits():
    m = _load_module()
    admitted = {
        "schema": "FREEPOOL_FALLBACK_PROVIDER_GATE/v1",
        "admitted": True,
        "reason": "TEST_ADMITTED",
    }
    with mock.patch.object(m, "_load_gate_decision", return_value=admitted), mock.patch.object(
        m.os, "execv"
    ) as execv:
        rc = m.main(["--role", "bugfix", "--probe"])
    assert rc == 0
    execv.assert_not_called()


def test_admitted_path_execs_exact_python_and_role_target_only():
    m = _load_module()
    admitted = {
        "schema": "FREEPOOL_FALLBACK_PROVIDER_GATE/v1",
        "admitted": True,
        "reason": "TEST_ADMITTED",
    }
    expected = m.ROLE_TARGETS["bauleiter"].resolve(strict=True)
    with mock.patch.object(m, "_load_gate_decision", return_value=admitted), mock.patch.object(
        m.os, "execv", side_effect=RuntimeError("exec intercepted")
    ) as execv:
        try:
            m.main(["--role", "bauleiter", "--", "--help"])
        except RuntimeError as exc:
            assert str(exc) == "exec intercepted"
        else:
            raise AssertionError("expected intercepted exec")
    execv.assert_called_once_with(m.sys.executable, [m.sys.executable, str(expected), "--help"])


def test_launcher_module_has_no_provider_or_aider_imports():
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden = {"requests", "llm", "openai", "anthropic", "aider", "harness_aider"}
    assert imported.isdisjoint(forbidden)


def test_gate_is_called_before_exec_in_main_source_order():
    source = MODULE_PATH.read_text(encoding="utf-8")
    main_start = source.index("def main(")
    main_source = source[main_start:]
    assert main_source.index("_load_gate_decision()") < main_source.index("os.execv(")
    assert "provider_calls\": 0" in source
    assert "secret_lookups_by_launcher\": 0" in source
