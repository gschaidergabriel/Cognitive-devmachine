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


def _body(source: str, node: ast.FunctionDef | None) -> str:
    if node is None:
        return ""
    segment = ast.get_source_segment(source, node)
    assert segment is not None
    return segment


def test_future_reference_commit_does_not_bootstrap_schema_outside_atomic_commit() -> None:
    """Canonical run initializes schema before reads; commit must not bootstrap again.

    A converged reference runtime receives `pipeline_init` first on the canonical Clay path.
    Re-entering `_ensure_schema()` inside `_pipeline_commit()` creates a second pre-CAS write
    phase. If that helper is committed before `BEGIN IMMEDIATE`, a later profile-snapshot or
    generation failure can return `ok=false` after schema/canonical bootstrap state was already
    durably changed. Commit must therefore assume successful init and keep all admitted state
    mutation inside its explicit transaction.
    """

    source = RUNTIME_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    if _function(tree, "_pipeline_profile_read") is None:
        return

    init = _function(tree, "_pipeline_init")
    commit = _function(tree, "_pipeline_commit")
    assert init is not None
    assert commit is not None

    init_body = _body(source, init)
    commit_body = _body(source, commit)
    assert "_ensure_schema" in init_body or "CREATE TABLE" in init_body, (
        "pipeline_init must retain schema/bootstrap responsibility"
    )

    assert "_ensure_schema(" not in commit_body, (
        "pipeline_commit re-enters schema/migration responsibility after canonical pipeline_init"
    )
    for token in ("CREATE TABLE", "ALTER TABLE", "DROP TABLE"):
        assert token not in commit_body, (
            "pipeline_commit contains schema mutation outside the dedicated init phase: " + token
        )

    begin = commit_body.find('BEGIN IMMEDIATE')
    assert begin >= 0, "pipeline_commit must establish one explicit SQLite write transaction"
    assert ".commit()" not in commit_body[:begin], (
        "pipeline_commit durably commits a pre-CAS/pre-snapshot phase before BEGIN IMMEDIATE"
    )
