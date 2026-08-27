from __future__ import annotations

import ast
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNTIME_PATH = ROOT / "tools" / "clay_profile_pipeline_runtime.py"
PRESET_PATH = HERE / "presets" / "zero_blog.json"


def _function(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"missing function: {name}")


def _string_keys(node: ast.Dict) -> set[str]:
    return {
        key.value
        for key in node.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }


def _collect_refs(value: object) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        ref = value.get("ref")
        if isinstance(ref, str):
            refs.add(ref)
        for child in value.values():
            refs.update(_collect_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.update(_collect_refs(child))
    return refs


def test_reference_convergence_preserves_shipped_derived_expression_inputs() -> None:
    """DB-profile/effect convergence must not amputate inputs used by the shipped preset."""
    runtime = RUNTIME_PATH.read_text(encoding="utf-8")
    tree = ast.parse(runtime)
    compile_fn = _function(tree, "_pipeline_compile")

    derived_keys: set[str] | None = None
    for node in ast.walk(compile_fn):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        if not isinstance(value, ast.Dict):
            continue
        keys = list(value.keys)
        for index, key in enumerate(keys):
            if isinstance(key, ast.Constant) and key.value == "derived":
                nested = value.values[index]
                if isinstance(nested, ast.Dict):
                    derived_keys = _string_keys(nested)

    preset = json.loads(PRESET_PATH.read_text(encoding="utf-8"))
    required = {ref.removeprefix("derived.") for ref in _collect_refs(preset) if ref.startswith("derived.")}

    assert required == {"source_count", "quiet_sensors_ok"}
    assert derived_keys is not None
    assert required <= derived_keys


def test_reference_convergence_preserves_recursive_value_only_persistence_gate() -> None:
    """Future inference/profile fusion must retain the newer all-persisted-value leak gate."""
    runtime = RUNTIME_PATH.read_text(encoding="utf-8")
    tree = ast.parse(runtime)
    helper = _function(tree, "_iter_persisted_string_leaves")
    gate = _function(tree, "_pipeline_gate")

    helper_attrs = {
        node.attr
        for node in ast.walk(helper)
        if isinstance(node, ast.Attribute)
    }
    gate_calls = {
        node.func.attr
        for node in ast.walk(gate)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    # Persisted object values are scanned recursively; object keys stay policy-neutral.
    assert "values" in helper_attrs
    assert "keys" not in helper_attrs
    assert "_iter_persisted_string_leaves" in gate_calls


def test_reference_convergence_guard_does_not_reintroduce_a_second_runtime() -> None:
    """The repair target remains the one canonical runtime module named by PROGRAM_STATE."""
    runtime = RUNTIME_PATH.read_text(encoding="utf-8")
    assert "class ProfilePipelineRuntime" in runtime
    assert not (ROOT / "tools" / "clay_profile_pipeline_runtime_v2.py").exists()
    assert not (ROOT / "tools" / "clay_profile_pipeline_runtime_legacy.py").exists()
