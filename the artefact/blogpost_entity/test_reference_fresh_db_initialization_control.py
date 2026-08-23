from __future__ import annotations

import ast
import importlib
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = ROOT / "tools"
RUNTIME_PATH = TOOLS / "clay_profile_pipeline_runtime.py"


def _has_db_profile_reference(source: str) -> bool:
    tree = ast.parse(source)
    return any(
        isinstance(node, ast.FunctionDef) and node.name == "_pipeline_profile_read"
        for node in ast.walk(tree)
    )


def _runtime_module():
    sys.path.insert(0, str(TOOLS))
    try:
        return importlib.import_module("clay_profile_pipeline_runtime")
    finally:
        if sys.path and sys.path[0] == str(TOOLS):
            sys.path.pop(0)


def test_future_reference_fresh_db_still_initializes_generation_zero(tmp_path: Path) -> None:
    """Legacy migration hardening must not turn an empty DB into migration debt."""

    source = RUNTIME_PATH.read_text(encoding="utf-8")
    if not _has_db_profile_reference(source):
        return

    runtime_module = _runtime_module()
    entity_db = tmp_path / "fresh_entity.db"
    assert not entity_db.exists()

    runtime = runtime_module.ProfilePipelineRuntime(root=tmp_path)
    result = runtime.effect("pipeline_init", {"entity_db": str(entity_db)})
    assert result.get("ok") is True, (
        "a database with no legacy generation evidence must remain normally initializable"
    )

    db = sqlite3.connect(entity_db)
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
        assert row is not None, "fresh init must materialize the canonical entity_state row"
        assert int(row[0]) == 0, "fresh canonical generation must start at zero"
    finally:
        db.close()
