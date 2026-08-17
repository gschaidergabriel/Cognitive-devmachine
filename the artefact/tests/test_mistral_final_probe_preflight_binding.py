import ast
from pathlib import Path


def test_final_mistral_probe_runs_strict_preflight_before_default_adapter():
    source = (
        Path(__file__).resolve().parents[1] / "clayverse" / "final_acceptance_probe.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module == "final_acceptance_mistral_config"
        for alias in node.names
    }
    assert "validate_final_mistral_runtime_config" in imported

    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_mistral_acceptance_probe"
    )
    strict_if = next(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "inference"
        and len(node.test.ops) == 1
        and isinstance(node.test.ops[0], ast.Is)
        and len(node.test.comparators) == 1
        and isinstance(node.test.comparators[0], ast.Constant)
        and node.test.comparators[0].value is None
    )

    calls = [node for statement in strict_if.body for node in ast.walk(statement) if isinstance(node, ast.Call)]
    assert any(
        isinstance(call.func, ast.Name)
        and call.func.id == "validate_final_mistral_runtime_config"
        for call in calls
    )
    constructors = [
        call
        for call in calls
        if isinstance(call.func, ast.Name) and call.func.id == "MistralInference"
    ]
    assert len(constructors) == 1
    assert any(
        keyword.arg == "model"
        and isinstance(keyword.value, ast.Name)
        and keyword.value.id == "fixed_model"
        for keyword in constructors[0].keywords
    )
