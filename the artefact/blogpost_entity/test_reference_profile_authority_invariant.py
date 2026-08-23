from __future__ import annotations

import ast
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNTIME_PATH = ROOT / "tools" / "clay_profile_pipeline_runtime.py"
NATIVE_PART00 = HERE / "native" / "mini_entity_part00.inc"
NATIVE_PART01 = HERE / "native" / "mini_entity_part01.inc"


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


def test_native_miniunifieddb_is_the_bound_profile_authority() -> None:
    native = NATIVE_PART00.read_text(encoding="utf-8") + NATIVE_PART01.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS entity_state" in native
    assert "CREATE TABLE IF NOT EXISTS profiles" in native
    assert "active_profile" in native
    assert "profile_sha256" in native
    assert "JOIN profiles" in native
    assert "PROFILE_HASH_MISMATCH" in native


def test_reference_convergence_cannot_create_a_parallel_profile_authority() -> None:
    """Reference convergence must reuse the one MiniUnifiedDB active-profile authority."""
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    assert "eos_pipeline_profile" not in source
    assert "eos_pipeline_profiles" not in source


def test_future_db_profile_reference_must_bind_native_authority_and_preservation_gates() -> None:
    """Once DB-profile convergence lands, all profile-sensitive paths bind one authority.

    Current main is intentionally allowed to remain unconverged. The guard activates when
    `_pipeline_profile_read` appears; then a name-only/current-effect repair is insufficient.
    """
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    profile_read = _function(tree, "_pipeline_profile_read")
    if profile_read is None:
        return

    importer = _function(tree, "import_profile") or _function(tree, "install_profile")
    commit = _function(tree, "_pipeline_commit")
    query = _function(tree, "_query")
    assert importer is not None, "DB-profile convergence needs an explicit configuration/import path"
    assert commit is not None
    assert query is not None

    read_body = _body(source, profile_read)
    import_body = _body(source, importer)
    commit_body = _body(source, commit)
    query_body = _body(source, query)

    for token in ("entity_state", "profiles", "active_profile", "profile_sha256"):
        assert token in read_body, f"profile read is not bound to canonical authority token: {token}"
        assert token in import_body, f"profile import is not bound to canonical authority token: {token}"
    for token in ("entity_state", "profiles", "active_profile", "profile_sha256", "PROFILE_SNAPSHOT_STALE"):
        assert token in commit_body, f"commit-time profile fence missing canonical token: {token}"

    assert "PROFILE_HASH_MISMATCH" in read_body
    assert "PROFILE_CONTAINS_SECRET_VALUE" in source

    # Evidence adapters are observation-only. Donor extraction may not retain writable
    # arbitrary SQL against source/entity evidence databases.
    assert "_read_only_db" in query_body or "query_only" in query_body or "mode=ro" in query_body


def test_future_commit_snapshot_fence_rehashes_current_profile_bytes() -> None:
    """Hash metadata alone cannot fence a mid-turn profile_json byte mutation.

    Native MiniUnifiedDB defines profile integrity as SHA-256 over the persisted
    profile_json text bytes. A converged reference commit therefore has to fetch the
    current profile_json bytes and recompute their digest before accepting the snapshot;
    comparing only the stored profile_sha256 column to the turn snapshot leaves a TOCTOU
    gap when profile_json changes but stale hash metadata does not.
    """
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    profile_read = _function(tree, "_pipeline_profile_read")
    if profile_read is None:
        return

    commit = _function(tree, "_pipeline_commit")
    assert commit is not None
    commit_body = _body(source, commit)

    assert "profile_json" in commit_body, (
        "commit snapshot fence must fetch current persisted profile_json bytes, not only hash metadata"
    )
    assert "profile_sha256" in commit_body
    assert "PROFILE_SNAPSHOT_STALE" in commit_body
    assert "_sha256_text" in commit_body or "hashlib.sha256" in commit_body, (
        "commit snapshot fence must recompute SHA-256 from current profile_json bytes"
    )


def test_parity_metadata_may_not_turn_green_while_profile_authority_is_parallel() -> None:
    """Prevent Goodhart: contract PARITY cannot coexist with a second profile table."""
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    contract = (HERE / "native" / "NATIVE_PROFILE_V2_PARITY_CONTRACT.json").read_text(encoding="utf-8")
    if '"status": "PARITY"' in contract:
        assert "eos_pipeline_profile" not in source
        assert "eos_pipeline_profiles" not in source
