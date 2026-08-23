from __future__ import annotations

import ast
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNTIME_PATH = ROOT / "tools" / "clay_profile_pipeline_runtime.py"
NATIVE_PART00 = HERE / "native" / "mini_entity_part00.inc"
NATIVE_PART01 = HERE / "native" / "mini_entity_part01.inc"
NATIVE_PART03 = HERE / "native" / "mini_entity_part03.inc"
CONTRACT_PATH = HERE / "native" / "NATIVE_PROFILE_V2_PARITY_CONTRACT.json"


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


def _flat(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _assert_reference_uses_native_generation_authority(source: str) -> None:
    tree = ast.parse(source)
    init = _function(tree, "_pipeline_init")
    ensure = _function(tree, "_ensure_schema")
    state_read = _function(tree, "_pipeline_state_read")
    commit = _function(tree, "_pipeline_commit")
    assert init is not None
    assert state_read is not None
    assert commit is not None

    init_body = _body(source, init)
    ensure_body = _body(source, ensure)
    schema_body = init_body + "\n" + ensure_body
    read_body = _body(source, state_read)
    commit_body = _body(source, commit)
    flat_schema = _flat(schema_body)
    flat_read = _flat(read_body)
    flat_commit = _flat(commit_body)

    assert "CREATE TABLE IF NOT EXISTS entity_state" in flat_schema, (
        "reference init/schema helper has not adopted native MiniUnifiedDB entity_state"
    )
    assert "entity_state" in read_body and "generation" in read_body, (
        "reference state read must source the live generation from entity_state"
    )
    assert "eos_pipeline_state.generation" not in flat_read, (
        "reference state read may not source live generation from the projection table"
    )
    assert "UPDATE entity_state SET generation" in flat_commit, (
        "reference commit must advance the native entity_state generation"
    )
    assert "WHERE id=1 AND generation=?" in flat_commit, (
        "reference generation update must preserve stale-writer CAS semantics"
    )

    eos_state_ddl = re.search(
        r"CREATE TABLE IF NOT EXISTS eos_pipeline_state\((.*?)\)",
        schema_body,
        flags=re.S,
    )
    if eos_state_ddl is not None:
        assert not re.search(r"\bgeneration\b", eos_state_ddl.group(1)), (
            "eos_pipeline_state may retain continuity/cursors but not a second generation authority"
        )

    combined = flat_read + " " + flat_commit
    for forbidden in (
        "SELECT * FROM eos_pipeline_state WHERE singleton=1",
        "UPDATE eos_pipeline_state SET generation=",
        "WHERE singleton=1 AND generation=?",
    ):
        assert forbidden not in combined, (
            "reference runtime still uses eos_pipeline_state as an independent generation/CAS authority: "
            + forbidden
        )


def _assert_bootstrap_cannot_promote_legacy_generation_mirror(source: str) -> None:
    """A compatibility projection may never write its counter back into canonical generation.

    This guard is deliberately separate from the live read/commit checks above because a
    refactor can move schema/migration logic behind `_ensure_schema()` while `_pipeline_init`
    merely calls that helper. A legacy table may be structurally rebuilt, but its historical
    generation value may not be read as input that can advance `entity_state.generation`.
    """
    tree = ast.parse(source)
    ensure = _function(tree, "_ensure_schema")
    if ensure is None:
        return
    ensure_body = _body(source, ensure)
    flat_ensure = _flat(ensure_body)
    assert "SELECT generation FROM eos_pipeline_state" not in flat_ensure, (
        "legacy eos_pipeline_state generation may not be read as bootstrap/migration authority"
    )
    assert not (
        "eos_pipeline_state" in ensure_body
        and "UPDATE entity_state SET generation" in flat_ensure
    ), "schema/bootstrap logic may not promote a legacy mirror into canonical generation"


def test_native_miniunifieddb_is_the_bound_generation_and_cas_authority() -> None:
    native00 = NATIVE_PART00.read_text(encoding="utf-8")
    native01 = NATIVE_PART01.read_text(encoding="utf-8")
    native03 = NATIVE_PART03.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS entity_state" in native00
    assert "generation INTEGER NOT NULL" in native00
    assert 'SELECT generation FROM entity_state WHERE id=1' in native01
    assert "UPDATE entity_state SET generation=?,updated_at=? WHERE id=1 AND generation=?" in native03


def test_future_current_reference_must_reuse_one_generation_authority() -> None:
    """Activate when DB-profile/current-effect reference convergence actually begins.

    Legacy current main is allowed to remain explicitly unconverged. Once
    `_pipeline_profile_read` appears, the new reference path may not carry forward the
    legacy eos_pipeline_state generation as a second live entity/CAS authority.
    """
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    if _function(tree, "_pipeline_profile_read") is None:
        return
    _assert_reference_uses_native_generation_authority(source)
    _assert_bootstrap_cannot_promote_legacy_generation_mirror(source)


def test_reference_parity_cannot_turn_green_with_parallel_generation_authority() -> None:
    """Prevent Goodhart: effect/profile parity cannot hide a forked live generation."""
    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    if '"status": "PARITY"' not in contract:
        return
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    _assert_reference_uses_native_generation_authority(source)
    _assert_bootstrap_cannot_promote_legacy_generation_mirror(source)
