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


def test_profile_file_amputation_after_db_import(tmp_path: Path) -> None:
    """Unusual discriminator: runtime must survive deletion of the import preset."""
    source_db = tmp_path / "source.db"
    with sqlite3.connect(source_db) as db:
        db.execute("CREATE TABLE events(id TEXT PRIMARY KEY, note TEXT)")
        db.execute("INSERT INTO events VALUES('e1','measured')")

    profile = {
        "schema": PROFILE_SCHEMA,
        "profile_id": "amputation_probe",
        "identity": {"entity_name": "replaceable"},
        "inference": {
            "kind": "mock",
            "model": "fixture",
            "contract_id": "amputation",
            "secret_names": [],
        },
        "personality": {
            "system_prompt": "Report only admitted evidence.",
            "public_style": "short",
            "output_contract": {
                "title_field": "title",
                "intro_field": "intro",
                "sections_field": "sections",
                "section_text_field": "text",
                "section_evidence_field": "evidence",
                "section_claims_field": "claims",
                "continuity_field": "thread",
                "autobiographical_hypotheses_field": "hypotheses",
            },
        },
        "sources": [
            {
                "kind": "events",
                "adapter": "sqlite_query",
                "required_for_quiet": True,
                "db": "source",
                "query": "SELECT id AS source_id,note FROM events ORDER BY id",
                "id_field": "source_id",
                "evidence_prefix": "event:",
            }
        ],
        "canonical_probes": [],
        "state_metrics": [],
        "gate": {
            "require_hash_echo": True,
            "require_evidence_per_section": True,
            "max_claim_overshoot": 0.0,
            "leak_patterns": [],
        },
    }

    preset = tmp_path / "import-only-profile.json"
    preset.write_text(json.dumps(profile), encoding="utf-8")
    imported = json.loads(preset.read_text(encoding="utf-8"))

    entity_db = tmp_path / "entity.db"

    def provider(req: dict) -> dict:
        state = json.loads(req["user"])
        evidence = [ref for ref in state["ALLOWED_EVIDENCE_REFS"] if ref.startswith("event:")]
        return {
            "canonical_state_hash_seen": state["CANONICAL_STATE_HASH"],
            "packet_hash_seen": state["PACKET_HASH"],
            "title": "DB resident",
            "intro": "Preset file is no longer required.",
            "sections": [
                {
                    "text": "The imported profile remained usable after file deletion.",
                    "evidence": evidence[:1],
                    "claims": {},
                }
            ],
            "thread": "continue",
            "hypotheses": "none promoted",
        }

    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=provider)
    runtime.install_profile(str(entity_db), imported, activate=True)
    preset.unlink()
    assert not preset.exists()

    result, _ = execute_source(
        SRC,
        "run",
        [str(entity_db), str(source_db), ""],
        runtime,
    )
    assert result["ok"] is True
    assert result["profile_id"] == "amputation_probe"
    assert result["generation"] == 1
