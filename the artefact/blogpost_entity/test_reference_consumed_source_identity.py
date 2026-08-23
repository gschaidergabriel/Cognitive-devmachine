from __future__ import annotations

import ast
import importlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = ROOT / "tools"
RUNTIME_PATH = TOOLS / "clay_profile_pipeline_runtime.py"
CLAY_PATH = HERE / "BLOGPOST_ENTITY.clay"


def _reference_is_converged() -> bool:
    source = RUNTIME_PATH.read_text(encoding="utf-8")
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


def _source_db(path: Path, value: str) -> None:
    db = sqlite3.connect(path)
    try:
        db.execute("CREATE TABLE events(id INTEGER PRIMARY KEY,payload TEXT NOT NULL)")
        db.execute("INSERT INTO events(id,payload) VALUES(1,?)", (value,))
        db.commit()
    finally:
        db.close()


def _profile(profile_id: str, source_namespace: str) -> dict:
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": profile_id,
        "inference": {
            "kind": "mock",
            "model": "identity-test",
            "secret_names": [],
        },
        "personality": {
            "system_prompt": "Transform only admitted evidence.",
            "public_style": "test",
            "output_contract": {
                "title_field": "title",
                "intro_field": "intro",
                "sections_field": "sections",
                "section_text_field": "text",
                "section_evidence_field": "refs",
                "section_claims_field": "claims",
                "continuity_field": "continuity",
                "autobiographical_hypotheses_field": "hypotheses",
            },
        },
        "sources": [
            {
                "kind": "event",
                "source_namespace": source_namespace,
                "adapter": "sqlite_query",
                "required_for_quiet": True,
                "db": "source",
                "query": "SELECT id AS source_id,payload FROM events ORDER BY id",
                "id_field": "source_id",
                "evidence_prefix": "event:",
            }
        ],
        "state_metrics": [],
        "gate": {
            "require_hash_echo": True,
            "require_evidence_per_section": True,
            "max_claim_overshoot": 0.0,
            "leak_patterns": [],
        },
    }


def _provider(req: dict) -> dict:
    state = json.loads(req["user"])
    refs = list(state["ALLOWED_EVIDENCE_REFS"])
    evidence = refs[:1]
    return {
        "canonical_state_hash_seen": state["CANONICAL_STATE_HASH"],
        "packet_hash_seen": state["PACKET_HASH"],
        "title": "t",
        "intro": "i",
        "sections": [{"text": "x", "refs": evidence, "claims": {}}],
        "continuity": "c",
        "hypotheses": "h",
    }


def _run(runtime_module, root: Path, entity_db: Path, source_db: Path, profile: dict) -> dict:
    runtime = runtime_module.ProfilePipelineRuntime(root=root, provider_override=_provider)
    runtime.import_profile(str(entity_db), profile)
    source = CLAY_PATH.read_text(encoding="utf-8")
    result, _ = runtime_module.execute_source(
        source,
        "run",
        [str(entity_db), str(source_db), ""],
        runtime,
    )
    return result


@pytest.mark.skipif(not _reference_is_converged(), reason="activates with DB-profile reference convergence")
def test_distinct_source_namespaces_cannot_alias_the_same_kind_and_source_id(tmp_path: Path) -> None:
    """Exactly-once identity must distinguish different logical sources after profile swaps.

    Profile/application replacement is required to preserve the same MiniUnifiedDB history.
    Therefore `(source_kind, source_id)` alone is not a sufficient durable event identity:
    two admitted sources can legitimately reuse the same local id. `source_namespace` is the
    stable logical-source identity carried by the profile; an equivalent implementation may
    derive the same semantic identity differently, but it must preserve this behavior.
    """
    runtime_module = _runtime_module()
    entity_db = tmp_path / "entity.db"
    source_a = tmp_path / "source_a.db"
    source_b = tmp_path / "source_b.db"
    _source_db(source_a, "A")
    _source_db(source_b, "B")

    first = _run(runtime_module, tmp_path, entity_db, source_a, _profile("profile-a", "source-A"))
    second = _run(runtime_module, tmp_path, entity_db, source_b, _profile("profile-b", "source-B"))

    assert first["source_count"] == 1
    assert second["source_count"] == 1, (
        "new evidence from a distinct logical source was silently suppressed by a consumed-id collision"
    )
    assert second["generation"] == 2


@pytest.mark.skipif(not _reference_is_converged(), reason="activates with DB-profile reference convergence")
def test_profile_swap_does_not_reconsume_the_same_logical_source(tmp_path: Path) -> None:
    """Counterbalance: source identity must not be reduced to profile identity either."""
    runtime_module = _runtime_module()
    entity_db = tmp_path / "entity.db"
    source = tmp_path / "shared.db"
    _source_db(source, "shared")

    first = _run(runtime_module, tmp_path, entity_db, source, _profile("profile-a", "shared-source"))
    second = _run(runtime_module, tmp_path, entity_db, source, _profile("profile-b", "shared-source"))

    assert first["source_count"] == 1
    assert second["source_count"] == 0, (
        "changing only the application profile caused already-consumed evidence to be consumed again"
    )
    assert second["generation"] == 2
