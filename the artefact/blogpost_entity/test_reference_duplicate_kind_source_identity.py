from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import PipelineFault, ProfilePipelineRuntime


def _contract() -> dict:
    return {
        "title_field": "title",
        "intro_field": "intro",
        "sections_field": "sections",
        "section_text_field": "text",
        "section_evidence_field": "evidence",
        "section_claims_field": "claims",
        "continuity_field": "thread",
        "autobiographical_hypotheses_field": "hypotheses",
    }


def _profile() -> dict:
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "same-kind-distinct-logical-sources",
        "inference": {"kind": "mock", "secret_names": []},
        "personality": {
            "system_prompt": "",
            "public_style": "",
            "output_contract": _contract(),
        },
        "sources": [
            {
                "kind": "events",
                "source_namespace": "feed:a",
                "adapter": "sqlite_query",
                "db": "source",
                "query": "SELECT source_id,payload FROM events_a",
                "id_field": "source_id",
                "required_for_quiet": True,
                "evidence_prefix": "event:a:",
            },
            {
                "kind": "events",
                "source_namespace": "feed:b",
                "adapter": "sqlite_query",
                "db": "source",
                "query": "SELECT source_id,payload FROM events_b",
                "id_field": "source_id",
                "required_for_quiet": True,
                "evidence_prefix": "event:b:",
            },
        ],
        "canonical_probes": [],
        "state_metrics": [],
        "gate": {"require_hash_echo": True, "require_evidence_per_section": True},
    }


def _row_count(sources: dict) -> int:
    return sum(len(source.get("rows", [])) for source in sources.values())


def test_same_kind_distinct_logical_sources_must_not_silently_overwrite(tmp_path: Path) -> None:
    """A logical source identity repair must cover the collector representation itself.

    Acceptable contracts are deliberately implementation-neutral:
    1. reject an unaddressable same-kind configuration before collection, or
    2. preserve both logical source instances in the collected representation.

    It is never acceptable to report source_count=2 / two exactly-once namespaces while
    materializing only one source entry because sources/sensors are keyed by kind.
    """
    source_db = tmp_path / "source.db"
    entity_db = tmp_path / "entity.db"
    with sqlite3.connect(source_db) as db:
        db.execute("CREATE TABLE events_a(source_id INTEGER PRIMARY KEY,payload TEXT NOT NULL)")
        db.execute("CREATE TABLE events_b(source_id INTEGER PRIMARY KEY,payload TEXT NOT NULL)")
        db.execute("INSERT INTO events_a(source_id,payload) VALUES(1,'a')")
        db.execute("INSERT INTO events_b(source_id,payload) VALUES(1,'b')")

    runtime = ProfilePipelineRuntime(root=tmp_path)
    profile = _profile()

    try:
        runtime.import_profile(str(entity_db), profile)
    except PipelineFault as exc:
        text = str(exc)
        assert (
            "DUPLICATE_SOURCE_KIND" in text
            or "SOURCE_IDENTITY_AMBIGUOUS" in text
            or "SOURCE_ADDRESSING_AMBIGUOUS" in text
        ), text
        return

    loaded = runtime.effect("pipeline_profile_read", {"entity_db": str(entity_db)})
    assert loaded["ok"] is True
    collected = runtime.effect(
        "pipeline_collect",
        {
            "entity_db": str(entity_db),
            "source_db": str(source_db),
            "profile": loaded["profile"],
            "previous": {"cursors": {}},
        },
    )

    if collected.get("ok") is False:
        text = str(collected.get("error", ""))
        assert (
            "DUPLICATE_SOURCE_KIND" in text
            or "SOURCE_IDENTITY_AMBIGUOUS" in text
            or "SOURCE_ADDRESSING_AMBIGUOUS" in text
        ), text
        return

    assert collected["source_count"] == 2
    assert {item["namespace"] for item in collected["consume"]} == {"feed:a", "feed:b"}
    assert _row_count(collected["sources"]) == 2, (
        "collector counted both logical sources but silently overwrote one in its "
        "kind-keyed sources representation"
    )
    assert len(collected["sources"]) >= 2, (
        "distinct logical sources must remain separately addressable or the profile must fail closed"
    )
