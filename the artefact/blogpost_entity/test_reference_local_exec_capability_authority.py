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


def _source(source: str, node: ast.AST | None) -> str:
    if node is None:
        return ""
    return ast.get_source_segment(source, node) or ""


def _self_attr_names(node: ast.AST) -> set[str]:
    return {
        child.attr
        for child in ast.walk(node)
        if isinstance(child, ast.Attribute)
        and isinstance(child.value, ast.Name)
        and child.value.id == "self"
    }


def _plain_names(node: ast.AST) -> set[str]:
    return {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}


def _assigned_plain_names(node: ast.Assign | ast.AnnAssign) -> set[str]:
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    return {
        child.id
        for target in targets
        for child in ast.walk(target)
        if isinstance(child, ast.Name)
    }


def _trusted_runner_attrs(init: ast.FunctionDef) -> set[str]:
    params = {
        arg.arg
        for arg in [*init.args.posonlyargs, *init.args.args, *init.args.kwonlyargs]
        if arg.arg != "self"
    }
    markers = ("runner", "executor", "exec_capability", "process_capability")
    trusted: set[str] = set()
    for node in ast.walk(init):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        if not isinstance(value, ast.Name) or value.id not in params:
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
                and any(marker in target.attr.lower() for marker in markers)
            ):
                trusted.add(target.attr)
    return trusted


def test_future_local_exec_runner_authority_is_not_owned_by_db_profile() -> None:
    """A cognition profile may parameterize an admitted runner, not mint process capability.

    A readable `local_model_path` plus `shell=False` and explicit child `env=` does not prove
    that the executed command is a model runner when DB profile data still owns the complete
    command vector. The process owner therefore has to enter through trusted Runtime admission
    outside the profile. This guard binds that responsibility without naming one runner binary.
    """
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    local_exec = _function(tree, "_inference_local_exec")

    # Legacy current main has no generic local_exec handler yet. Activate exactly when the
    # reference convergence introduces that capability.
    if local_exec is None:
        return

    init = _function(tree, "__init__")
    assert init is not None
    local_src = _source(source, local_exec)

    # Capability admission must fail closed before process execution is reachable.
    assert "LOCAL_EXEC_NOT_ADMITTED" in local_src, (
        "local_exec needs an explicit fail-closed runtime-admission state before process execution"
    )

    trusted_attrs = _trusted_runner_attrs(init)
    assert trusted_attrs, (
        "local_exec runner/executor authority must be injected into Runtime construction; "
        "DB profile data cannot be the sole source of process authority"
    )

    # Track local command-building variables that actually depend on trusted Runtime state.
    trusted_vars: set[str] = set()
    assignments = [
        node
        for node in ast.walk(local_exec)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
    ]
    changed = True
    while changed:
        changed = False
        for node in assignments:
            value = node.value
            depends_on_trusted_attr = bool(_self_attr_names(value) & trusted_attrs)
            depends_on_trusted_var = bool(_plain_names(value) & trusted_vars)
            if not (depends_on_trusted_attr or depends_on_trusted_var):
                continue
            for name in _assigned_plain_names(node):
                if name not in trusted_vars:
                    trusted_vars.add(name)
                    changed = True

    subprocess_runs = [
        node
        for node in ast.walk(local_exec)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "run"
    ]
    assert subprocess_runs, "local_exec must still have an explicit bounded execution point"

    for call in subprocess_runs:
        assert call.args, "subprocess.run must receive an explicit command expression"
        command = call.args[0]
        command_is_runtime_bound = bool(_self_attr_names(command) & trusted_attrs) or bool(
            _plain_names(command) & trusted_vars
        )
        assert command_is_runtime_bound, (
            "subprocess command is not derived from trusted Runtime runner/executor admission; "
            "profile data must not own the executable process capability"
        )
