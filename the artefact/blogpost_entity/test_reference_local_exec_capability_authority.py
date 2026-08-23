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


def test_future_local_exec_runner_authority_is_not_owned_by_db_profile() -> None:
    """A cognition profile may select model/inference arguments, not mint process capability.

    `local_exec` is intended to be a replaceable local cognition backend. If the DB-resident
    profile supplies the complete argv, including argv[0], any admitted profile can instead
    select an arbitrary host executable while merely pointing `local_model_path` at any
    readable decoy file. Explicit child `env=` prevents ambient-secret inheritance but does
    not close that process-capability boundary.

    The executable runner therefore has to enter from trusted runtime admission outside the
    profile. This guard intentionally does not prescribe one runner implementation; it binds
    the responsibility boundary: constructor/runtime policy owns the runner, profile data may
    only parameterize the already-admitted runner.
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
    init_src = _source(source, init)
    local_src = _source(source, local_exec)

    # A fail-closed admission state must exist before any subprocess can be reached.
    assert "LOCAL_EXEC_NOT_ADMITTED" in local_src, (
        "local_exec needs an explicit fail-closed runtime-admission state before process execution"
    )

    # Runner authority must be supplied to the Runtime itself, not read from the DB profile.
    trusted_runner_tokens = (
        "local_exec_runner",
        "local_runner",
        "allowed_local_exec_runner",
        "admitted_local_exec_runner",
    )
    bound = [token for token in trusted_runner_tokens if token in init_src and f"self.{token}" in local_src]
    assert bound, (
        "local_exec runner/executable authority must be injected into the runtime and consumed "
        "from runtime state; the DB profile cannot own argv[0]"
    )

    # The known unsafe donor shape gives profile data the complete command vector. Profile
    # arguments may be supported under a narrower key, but these full-command keys are not an
    # admissible authority surface once local_exec exists.
    for forbidden in ('inference.get("local_argv_json"', "inference.get('local_argv_json'", 'inference.get("argv"', "inference.get('argv'"):
        assert forbidden not in local_src, (
            "DB profile still selects the complete local process argv; split trusted runner "
            "authority from profile-supplied cognition arguments"
        )

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
