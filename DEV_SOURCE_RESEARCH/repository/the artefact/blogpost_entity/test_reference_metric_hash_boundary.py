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


def _contains_name(node: ast.AST, name: str) -> bool:
    return any(isinstance(child, ast.Name) and child.id == name for child in ast.walk(node))


def _target_is_canonical_slot(target: ast.AST) -> bool:
    return (
        isinstance(target, ast.Subscript)
        and isinstance(target.value, ast.Name)
        and target.value.id == "canonical"
    )


def test_future_db_profile_reference_hash_binds_claim_authorizing_metrics() -> None:
    """The echoed canonical hash must commit to metrics later used to authorize claims.

    Current legacy main is intentionally allowed to remain unconverged. Once the DB-profile
    reference surface lands (`_pipeline_profile_read` exists), a generated answer may not be
    gated against `personality_state` metrics that sit outside `canonical_state_hash`.
    Otherwise two different claim-authorizing metric states can share the same echoed hash.
    """
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    if _function(tree, "_pipeline_profile_read") is None:
        return

    compile_fn = _function(tree, "_pipeline_compile")
    gate_fn = _function(tree, "_pipeline_gate")
    assert compile_fn is not None
    assert gate_fn is not None

    # This guard is relevant only because the deterministic gate authorizes state claims
    # against the compiled personality-state metrics.
    gate_source = ast.get_source_segment(source, gate_fn) or ""
    assert "personality_state" in gate_source
    assert "UNVERIFIED_STATE_CLAIM" in gate_source
    assert "STATE_CLAIM_OVERSHOOT" in gate_source

    metrics_bound_into_canonical = False
    canonical_raw_seen = False
    for statement in compile_fn.body:
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            value = statement.value
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]

            if any(isinstance(target, ast.Name) and target.id == "canonical" for target in targets):
                metrics_bound_into_canonical = metrics_bound_into_canonical or _contains_name(value, "metrics")

            if any(_target_is_canonical_slot(target) for target in targets):
                metrics_bound_into_canonical = metrics_bound_into_canonical or _contains_name(value, "metrics")

            if any(isinstance(target, ast.Name) and target.id == "canonical_raw" for target in targets):
                canonical_raw_seen = True
                # Direct serialization of a structure containing metrics is also valid.
                metrics_bound_into_canonical = metrics_bound_into_canonical or _contains_name(value, "metrics")
                break

    assert canonical_raw_seen, "reference compile path no longer exposes canonical_raw before hashing"
    assert metrics_bound_into_canonical, (
        "canonical_state_hash does not bind the personality/state metrics that authorize "
        "state claims; include those metrics in the hashed canonical state before promotion"
    )

    # Keep the hash echo attached to that canonical serialization rather than an unrelated digest.
    hash_bound = False
    for node in ast.walk(compile_fn):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Constant) and key.value == "canonical_state_hash":
                if _contains_name(value, "canonical_raw"):
                    hash_bound = True
    assert hash_bound, "canonical_state_hash must derive from the canonical_raw serialization"
