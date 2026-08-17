from __future__ import annotations

import ast
from pathlib import Path

import pytest

from clayverse import service


def test_final_service_required_effect_capability_is_narrow(monkeypatch):
    monkeypatch.delenv("CLAYVERSE_ACCEPTANCE_REQUIRED_EFFECT_CAPABILITY", raising=False)
    assert service._acceptance_required_effect_capability() is None

    monkeypatch.setenv("CLAYVERSE_ACCEPTANCE_REQUIRED_EFFECT_CAPABILITY", "entityos.exec")
    assert service._acceptance_required_effect_capability() == "entityos.exec"

    monkeypatch.setenv("CLAYVERSE_ACCEPTANCE_REQUIRED_EFFECT_CAPABILITY", "state.noop")
    with pytest.raises(RuntimeError, match="may only be entityos.exec"):
        service._acceptance_required_effect_capability()


def test_mistral_once_passes_required_capability_into_canonical_probe():
    source = (
        Path(__file__).resolve().parents[1] / "clayverse" / "service.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_run_mistral_once"
    )
    calls = [node for node in ast.walk(function) if isinstance(node, ast.Call)]
    probe = next(
        call
        for call in calls
        if isinstance(call.func, ast.Name)
        and call.func.id == "run_mistral_acceptance_probe"
    )
    keyword = next(
        item for item in probe.keywords if item.arg == "required_effect_capability"
    )
    assert isinstance(keyword.value, ast.Name)
    assert keyword.value.id == "required_effect_capability"
