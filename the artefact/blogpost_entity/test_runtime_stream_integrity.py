from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import PROFILE_SCHEMA, ProfilePipelineRuntime, execute_source

SRC = Path(__file__).with_name("BLOGPOST_ENTITY.clay").read_text(encoding="utf-8")


def contract() -> dict:
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


def profile(source: dict) -> dict:
    return {
        "schema": PROFILE_SCHEMA,
        "profile_id": "stream_integrity",
        "identity": {"entity_name": "Stream Integrity Fixture"},
        "inference": {"kind": "mock", "model": "fixture", "secret_names": []},
        "personality": {
            "system_prompt": "Return only the evidence-bound fixture response.",
            "public_style": "fixture",
            "output_contract": contract(),
        },
        "sources": [source],
        "canonical_probes": [],
        "state_metrics": [],
        "gate": {
            "require_hash_echo": True,
            "require_evidence_per_section": False,
            "max_claim_overshoot": 0.0,
            "leak_patterns": [],
        },
    }


def provider(seen: list[dict] | None = None):
    def _provider(req: dict) -> dict:
        state = json.loads(req["user"])
        if seen is not None:
            seen.append(state)
        refs = state["ALLOWED_EVIDENCE_REFS"]
        evidence = [r for r in refs if r.startswith("event:")][:1]
        return {
            "canonical_state_hash_seen": state["CANONICAL_STATE_HASH"],
            "packet_hash_seen": state["PACKET_HASH"],
            "title": "fixture",
            "intro": "fixture",
            "sections": [{"text": "fixture", "evidence": evidence, "claims": {}}],
            "thread": "continue",
            "hypotheses": "none",
        }
    return _provider


def run(runtime: ProfilePipelineRuntime, entity_db: Path, source_db: Path):
    result, _ = execute_source(SRC, "run", [str(entity_db), str(source_db), ""], runtime)
    return result


def make_sqlite_events(path: Path, count: int) -> None:
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE events(id INTEGER PRIMARY KEY, note TEXT)")
    db.executemany("INSERT INTO events(id,note) VALUES(?,?)", [(i, f"e{i}") for i in range(1, count + 1)])
    db.commit()
    db.close()


def test_repeated_identical_quiet_packets_are_distinct_ledger_rows(tmp_path):
    """Content hash is not row identity: multiple generations may legitimately share one packet hash."""
    source_db = tmp_path / "source.db"
    entity_db = tmp_path / "entity.db"
    make_sqlite_events(source_db, 1)
    source = {
        "kind": "event",
        "adapter": "sqlite_query",
        "required_for_quiet": True,
        "db": "source",
        "query": "SELECT id AS source_id,note FROM events ORDER BY id",
        "id_field": "source_id",
        "evidence_prefix": "event:",
    }
    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=provider())
    runtime.install_profile(str(entity_db), profile(source))

    first = run(runtime, entity_db, source_db)
    second = run(runtime, entity_db, source_db)
    third = run(runtime, entity_db, source_db)

    assert first["generation"] == 1
    assert second["generation"] == 2
    assert third["generation"] == 3
    assert second["packet_hash"] == third["packet_hash"]
    db = sqlite3.connect(entity_db)
    rows = db.execute("SELECT output_id,packet_hash,generation FROM eos_pipeline_packets ORDER BY generation").fetchall()
    db.close()
    assert len(rows) == 3
    assert len({row[0] for row in rows}) == 3


def test_sql_limit_is_delivery_budget_after_consumed_filter(tmp_path):
    """A terminal LIMIT must not pin later generations forever to already-consumed head rows."""
    source_db = tmp_path / "source.db"
    entity_db = tmp_path / "entity.db"
    make_sqlite_events(source_db, 4)
    source = {
        "kind": "event",
        "adapter": "sqlite_query",
        "required_for_quiet": True,
        "db": "source",
        "query": "SELECT id AS source_id,note FROM events ORDER BY id LIMIT 2",
        "id_field": "source_id",
        "evidence_prefix": "event:",
    }
    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=provider())
    runtime.install_profile(str(entity_db), profile(source))

    first = run(runtime, entity_db, source_db)
    second = run(runtime, entity_db, source_db)
    third = run(runtime, entity_db, source_db)

    assert first["source_count"] == 2
    assert second["source_count"] == 2
    assert third["source_count"] == 0
    db = sqlite3.connect(entity_db)
    consumed = [row[0] for row in db.execute("SELECT source_id FROM eos_pipeline_consumed WHERE source_kind='event' ORDER BY CAST(source_id AS INTEGER)")]
    db.close()
    assert consumed == ["1", "2", "3", "4"]


def test_jsonl_cursor_advances_only_through_lines_visited_under_limit(tmp_path):
    """Per-run limits must defer unvisited complete lines, not advance the cursor past them."""
    source_db = tmp_path / "unused.db"
    source_db.touch()
    entity_db = tmp_path / "entity.db"
    stream = tmp_path / "events.jsonl"
    stream.write_text("".join(json.dumps({"source_id": i, "note": f"e{i}"}) + "\n" for i in range(1, 5)), encoding="utf-8")
    source = {
        "kind": "event",
        "adapter": "jsonl_cursor",
        "required_for_quiet": True,
        "path": "events.jsonl",
        "limit": 2,
        "evidence_prefix": "event:",
    }
    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=provider())
    runtime.install_profile(str(entity_db), profile(source))

    first = run(runtime, entity_db, source_db)
    second = run(runtime, entity_db, source_db)
    third = run(runtime, entity_db, source_db)

    assert first["source_count"] == 2
    assert second["source_count"] == 2
    assert third["source_count"] == 0


def test_no_required_quiet_sensors_cannot_mint_verified_quiet(tmp_path):
    """Avoid the all([])==True epistemic bug for profiles with no quiet-required sources."""
    source_db = tmp_path / "source.db"
    entity_db = tmp_path / "entity.db"
    make_sqlite_events(source_db, 0)
    source = {
        "kind": "event",
        "adapter": "sqlite_query",
        "required_for_quiet": False,
        "db": "source",
        "query": "SELECT id AS source_id,note FROM events ORDER BY id",
        "id_field": "source_id",
        "evidence_prefix": "event:",
    }
    seen: list[dict] = []
    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=provider(seen))
    runtime.install_profile(str(entity_db), profile(source))

    result = run(runtime, entity_db, source_db)
    assert result["source_count"] == 0
    assert seen[0]["NEW_EVENT_PACKET"]["quiet_sensors_ok"] is False
    assert "quiet:verified" not in seen[0]["ALLOWED_EVIDENCE_REFS"]
