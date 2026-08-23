from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


def _profile() -> dict:
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "raw-byte-hash-fixture",
        "identity": {"entity_name": "Raw Byte Hash Fixture"},
        "inference": {"kind": "json_chat", "model": "fixture", "secret_names": []},
        "personality": {
            "system_prompt": "fixture",
            "public_style": "fixture",
            "output_contract": {
                "title_field": "title",
                "intro_field": "intro",
                "sections_field": "sections",
                "section_text_field": "text",
                "section_evidence_field": "evidence_refs",
                "section_claims_field": "state_claims",
                "continuity_field": "thread",
                "autobiographical_hypotheses_field": "hypotheses",
            },
        },
        "sources": [],
        "canonical_probes": [],
        "state_metrics": [],
        "gate": {
            "require_hash_echo": True,
            "require_evidence_per_section": False,
            "max_claim_overshoot": 0.0,
            "leak_patterns": [],
        },
    }


def _install_noncanonical_raw_profile(runtime: ProfilePipelineRuntime, entity_db: Path) -> tuple[str, str]:
    initialized = runtime.effect("pipeline_init", {"entity_db": str(entity_db)})
    assert initialized["ok"] is True

    # Deliberately preserve whitespace and insertion order that differ from the runtime's
    # canonical JSON serializer. Native MiniUnifiedDB hashes the exact persisted profile_json
    # text bytes, so reference verification must hash this raw text before JSON normalization.
    raw = json.dumps(_profile(), ensure_ascii=False, sort_keys=False, indent=2) + "\n"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    with sqlite3.connect(entity_db) as db:
        db.execute(
            """INSERT INTO profiles(profile_id,profile_json,profile_sha256,updated_at)
               VALUES(?,?,?,?)""",
            ("raw-byte-hash-fixture", raw, digest, "2026-08-23T00:00:00Z"),
        )
        db.execute(
            "UPDATE entity_state SET active_profile=?,updated_at=? WHERE id=1",
            ("raw-byte-hash-fixture", "2026-08-23T00:00:00Z"),
        )
        db.commit()
    return raw, digest


def test_profile_read_hashes_exact_persisted_text_before_json_normalization(tmp_path: Path) -> None:
    entity_db = tmp_path / "entity.db"
    runtime = ProfilePipelineRuntime(root=tmp_path)
    _, digest = _install_noncanonical_raw_profile(runtime, entity_db)

    loaded = runtime.effect("pipeline_profile_read", {"entity_db": str(entity_db)})

    assert loaded["ok"] is True
    assert loaded["profile_hash"] == digest
    assert loaded["profile"]["profile_id"] == "raw-byte-hash-fixture"


def test_semantically_equivalent_byte_mutation_without_digest_update_fails_closed(tmp_path: Path) -> None:
    entity_db = tmp_path / "entity.db"
    runtime = ProfilePipelineRuntime(root=tmp_path)
    raw, digest = _install_noncanonical_raw_profile(runtime, entity_db)

    # One extra whitespace byte leaves the parsed JSON meaning unchanged but changes the
    # canonical native artifact bytes. A parse/re-canonicalize verifier would miss this class.
    with sqlite3.connect(entity_db) as db:
        db.execute(
            "UPDATE profiles SET profile_json=? WHERE profile_id=?",
            (raw + " ", "raw-byte-hash-fixture"),
        )
        db.commit()

    loaded = runtime.effect("pipeline_profile_read", {"entity_db": str(entity_db)})

    assert loaded["ok"] is False
    assert "PROFILE_HASH_MISMATCH" in str(loaded.get("error", ""))
    with sqlite3.connect(entity_db) as db:
        stored_digest = db.execute(
            "SELECT profile_sha256 FROM profiles WHERE profile_id=?",
            ("raw-byte-hash-fixture",),
        ).fetchone()[0]
    assert stored_digest == digest
