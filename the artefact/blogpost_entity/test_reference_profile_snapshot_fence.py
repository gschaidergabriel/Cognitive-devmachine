from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import PROFILE_SCHEMA, PipelineFault, ProfilePipelineRuntime


def _profile(profile_id: str) -> dict:
    return {
        "schema": PROFILE_SCHEMA,
        "profile_id": profile_id,
        "identity": {"entity_name": "fixture"},
        "inference": {"kind": "local_exec"},
        "personality": {
            "output_contract": {
                "title_field": "title",
                "intro_field": "intro",
                "sections_field": "sections",
                "section_text_field": "text",
                "section_evidence_field": "evidence",
                "section_claims_field": "claims",
                "continuity_field": "thread",
                "autobiographical_hypotheses_field": "hypotheses",
            }
        },
        "sources": [],
        "state_metrics": [],
        "gate": {},
    }


def _commit_payload(profile: dict) -> dict:
    return {
        "entity_db": "entity.db",
        "profile": profile,
        "previous": {"generation": 0},
        "data": {
            "collected": {"consume": [], "next_cursors": {}},
            "compiled": {
                "packet_hash": "packet",
                "canonical_state_hash": "canonical",
                "source_count": 0,
                "canonical": {},
            },
            "generated": {"provider_kind": "fixture", "model": "fixture"},
            "gated": {
                "payload": {
                    "title": "fixture",
                    "intro": "fixture",
                    "sections": [],
                    "thread": "fixture",
                    "hypotheses": "fixture",
                }
            },
        },
    }


def test_profile_integrity_hash_binds_exact_persisted_text_bytes(tmp_path: Path) -> None:
    runtime = ProfilePipelineRuntime(root=tmp_path)
    entity_db = tmp_path / "entity.db"
    runtime.install_profile(str(entity_db), _profile("a"))

    with sqlite3.connect(entity_db) as db:
        raw = db.execute("SELECT profile_json FROM profiles WHERE profile_id='a'").fetchone()[0]
        obj = json.loads(raw)
        semantically_equal_but_different_bytes = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)
        assert semantically_equal_but_different_bytes != raw
        db.execute(
            "UPDATE profiles SET profile_json=? WHERE profile_id='a'",
            (semantically_equal_but_different_bytes,),
        )

    loaded = runtime.effect("pipeline_profile_read", {"entity_db": str(entity_db)})
    assert loaded["ok"] is False
    assert loaded["error"] == "PROFILE_HASH_MISMATCH"


def test_commit_fails_closed_if_active_profile_changes_after_profile_read(tmp_path: Path) -> None:
    runtime = ProfilePipelineRuntime(root=tmp_path)
    entity_db = tmp_path / "entity.db"
    runtime.install_profile(str(entity_db), _profile("a"))

    loaded = runtime.effect("pipeline_profile_read", {"entity_db": str(entity_db)})
    assert loaded["ok"] is True
    turn_profile = loaded["profile"]

    runtime.install_profile(str(entity_db), _profile("b"))
    payload = _commit_payload(turn_profile)
    payload["entity_db"] = str(entity_db)
    result = runtime.effect("pipeline_commit", payload)

    assert result["ok"] is False
    assert result["error"] == "PROFILE_SNAPSHOT_STALE"
    with sqlite3.connect(entity_db) as db:
        assert db.execute("SELECT COUNT(*) FROM eos_pipeline_outputs").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM eos_pipeline_packets").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM eos_pipeline_consumed").fetchone()[0] == 0
        assert db.execute("SELECT generation FROM eos_pipeline_state WHERE singleton=1").fetchone()[0] == 0


@pytest.mark.parametrize("secret_field", ["private_key", "client_secret"])
def test_profile_persistence_rejects_additional_literal_secret_aliases(
    tmp_path: Path, secret_field: str
) -> None:
    runtime = ProfilePipelineRuntime(root=tmp_path)
    profile = _profile("secret-test")
    profile["inference"] = {"kind": "remote_api", secret_field: "literal-secret"}
    with pytest.raises(PipelineFault, match="EMBEDDED_SECRET_VALUE_FORBIDDEN"):
        runtime.install_profile(str(tmp_path / "entity.db"), profile)
