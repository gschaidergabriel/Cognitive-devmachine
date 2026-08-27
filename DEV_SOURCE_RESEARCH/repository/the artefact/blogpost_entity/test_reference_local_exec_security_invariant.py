from __future__ import annotations

import ast
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNTIME_PATH = ROOT / "tools" / "clay_profile_pipeline_runtime.py"


def _function(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def test_future_reference_local_exec_never_inherits_unbounded_parent_environment() -> None:
    """Once local_exec is admitted, subprocess execution must carry an explicit child env."""
    tree = ast.parse(RUNTIME_PATH.read_text(encoding="utf-8"))
    local_exec = _function(tree, "_inference_local_exec")

    # Current main has not yet converged the generic local_exec reference handler.
    # This guard becomes active automatically when the narrow convergence adds it.
    if local_exec is None:
        return

    subprocess_runs = [
        node
        for node in ast.walk(local_exec)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "run"
    ]
    assert subprocess_runs, "local_exec must execute its configured runner through subprocess.run"

    for call in subprocess_runs:
        keyword_names = {kw.arg for kw in call.keywords if kw.arg is not None}
        assert "shell" in keyword_names, "local_exec must bind shell behavior explicitly"
        assert "env" in keyword_names, (
            "local_exec must pass an explicit child environment; omitting env makes Python inherit "
            "the complete parent process environment, including unrelated provider secrets"
        )
