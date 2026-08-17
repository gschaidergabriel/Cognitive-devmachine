from __future__ import annotations

import ast
from pathlib import Path


def test_final_acceptance_probe_binds_validated_fixed_model_to_canonical_adapter():
    source = (
        Path(__file__).resolve().parents[1]
        / "clayverse"
        / "final_acceptance_probe.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_mistral_acceptance_probe"
    )
    validate_assign = next(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "fixed_model" for target in node.targets)
    )
    assert isinstance(validate_assign.value, ast.Call)
    assert isinstance(validate_assign.value.func, ast.Name)
    assert validate_assign.value.func.id == "validate_final_mistral_runtime_config"

    adapter_assign = next(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "adapter" for target in node.targets)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "MistralInference"
    )
    model_keywords = [kw for kw in adapter_assign.value.keywords if kw.arg == "model"]
    assert len(model_keywords) == 1
    assert isinstance(model_keywords[0].value, ast.Name)
    assert model_keywords[0].value.id == "fixed_model"
