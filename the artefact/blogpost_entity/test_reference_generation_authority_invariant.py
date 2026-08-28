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
    schema_body = _body(source, ensure) if ensure is not None else init_body
    read_body = _body(source, state_read)
    commit_body = _body(source, commit)

    if ensure is not None:
        assert "_ensure_schema" in init_body, (
            "reference schema helper exists but pipeline_init does not own/call it"
        )
    assert "CREATE TABLE IF NOT EXISTS entity_state" in schema_body, (
        "reference init/schema owner has not adopted native MiniUnifiedDB entity_state"
    )
    assert "SELECT generation FROM entity_state WHERE id=1" in read_body, (
        "reference state read must source the live generation from entity_state"
    )
    assert "UPDATE entity_state SET generation" in commit_body, (
        "reference commit must advance the native entity_state generation"
    )
    assert "WHERE id=1 AND generation=?" in commit_body, (
        "reference generation update must preserve stale-writer CAS semantics"
    )

    eos_state_ddl = re.search(
        r"CREATE TABLE IF NOT EXISTS eos_pipeline_state\((.*?)\);",
        schema_body,
        flags=re.S,
    )
    if eos_state_ddl is not None:
        assert not re.search(r"\bgeneration\b", eos_state_ddl.group(1)), (
            "eos_pipeline_state may retain continuity/cursors but not a second generation authority"
        )

    combined = read_body + commit_body
    for forbidden in (
        'SELECT * FROM eos_pipeline_state WHERE singleton=1',
        'UPDATE eos_pipeline_state SET generation=',
        'WHERE singleton=1 AND generation=?',
    ):
        assert forbidden not in combined, (
            "reference runtime still uses eos_pipeline_state as an independent generation/CAS authority: "
            + forbidden
        )


def _assert_bootstrap_cannot_promote_legacy_generation_mirror(source: str) -> None:
    """Schema admission may inspect a legacy mirror, but may never promote it.

    A read-only mirror check is useful for explicit divergence detection and fail-closed
    migration decisions. What must never happen in recurrent `_ensure_schema()` admission
    is a write to canonical `entity_state.generation`: canonical generation can advance only
    through the normal CAS commit path (or a separately admitted one-shot migration path).
    """
    tree = ast.parse(source)
    ensure = _function(tree, "_ensure_schema")
    if ensure is None:
        return
    ensure_body = _body(source, ensure)
    assert "UPDATE entity_state SET generation" not in ensure_body, (
        "schema/bootstrap logic may inspect a legacy mirror but may not write canonical generation"
    )


def test_generation_guard_accepts_init_owned_schema_helper_without_duplicate_ddl() -> None:
    source = '''
def _ensure_schema(db):
    db.execute("CREATE TABLE IF NOT EXISTS entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS eos_pipeline_state(singleton INTEGER PRIMARY KEY, continuity_json TEXT NOT NULL)")

def _pipeline_init(p):
    db = p["db"]
    _ensure_schema(db)

def _pipeline_state_read(p):
    return p["db"].execute("SELECT generation FROM entity_state WHERE id=1").fetchone()

def _pipeline_commit(p):
    return p["db"].execute("UPDATE entity_state SET generation=? WHERE id=1 AND generation=?", (2, 1))
'''
    _assert_reference_uses_native_generation_authority(source)


def test_generation_guard_rejects_orphan_schema_helper_not_owned_by_init() -> None:
    source = '''
def _ensure_schema(db):
    db.execute("CREATE TABLE IF NOT EXISTS entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")

def _pipeline_init(p):
    return True

def _pipeline_state_read(p):
    return p["db"].execute("SELECT generation FROM entity_state WHERE id=1").fetchone()

def _pipeline_commit(p):
    return p["db"].execute("UPDATE entity_state SET generation=? WHERE id=1 AND generation=?", (2, 1))
'''
    try:
        _assert_reference_uses_native_generation_authority(source)
    except AssertionError:
        return
    raise AssertionError("guard accepted an orphan schema helper not owned by pipeline_init")


def test_generation_guard_allows_read_only_fail_closed_mirror_divergence_check() -> None:
    source = '''
def _ensure_schema(db):
    native = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    mirror = db.execute("SELECT generation FROM eos_pipeline_state WHERE singleton=1").fetchone()
    if native is not None and mirror is not None and int(mirror[0]) > int(native[0]):
        raise RuntimeError("LEGACY_GENERATION_DIVERGENCE")
    if native is not None and mirror is not None and int(mirror[0]) < int(native[0]):
        db.execute("UPDATE eos_pipeline_state SET generation=? WHERE singleton=1", (int(native[0]),))
'''
    _assert_bootstrap_cannot_promote_legacy_generation_mirror(source)


def test_generation_guard_rejects_bootstrap_write_to_canonical_generation() -> None:
    source = '''
def _ensure_schema(db):
    native = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    mirror = db.execute("SELECT generation FROM eos_pipeline_state WHERE singleton=1").fetchone()
    migrated = max(int(native[0]), int(mirror[0]))
    db.execute("UPDATE entity_state SET generation=? WHERE id=1", (migrated,))
'''
    try:
        _assert_bootstrap_cannot_promote_legacy_generation_mirror(source)
    except AssertionError:
        return
    raise AssertionError("guard accepted a bootstrap write to canonical generation")


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
