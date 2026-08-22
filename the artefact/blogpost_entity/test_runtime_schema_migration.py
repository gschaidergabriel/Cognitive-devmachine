from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


def test_old_packet_hash_primary_key_migrates_without_losing_history(tmp_path):
    entity_db = tmp_path / "entity.db"
    db = sqlite3.connect(entity_db)
    db.executescript(
        """
        CREATE TABLE eos_pipeline_packets(
          packet_hash TEXT PRIMARY KEY,
          output_id TEXT NOT NULL,
          ts REAL NOT NULL,
          generation INTEGER NOT NULL,
          profile_id TEXT NOT NULL,
          source_count INTEGER NOT NULL,
          canonical_hash TEXT NOT NULL);
        INSERT INTO eos_pipeline_packets VALUES(
          'same-content-hash','old-output',1.0,7,'legacy-profile',0,'canonical-old');
        """
    )
    db.commit()
    db.close()

    runtime = ProfilePipelineRuntime(root=tmp_path)
    initialized = runtime.effect("pipeline_init", {"entity_db": str(entity_db)})
    assert initialized["ok"] is True

    db = sqlite3.connect(entity_db)
    info = db.execute("PRAGMA table_info(eos_pipeline_packets)").fetchall()
    primary = [row[1] for row in info if row[5] > 0]
    assert primary == ["output_id"]
    old = db.execute(
        "SELECT output_id,packet_hash,generation FROM eos_pipeline_packets WHERE output_id='old-output'"
    ).fetchone()
    assert old == ("old-output", "same-content-hash", 7)

    # Same content identity is legal in another ledger generation; row identity is output_id.
    db.execute(
        """INSERT INTO eos_pipeline_packets(
           output_id,packet_hash,ts,generation,profile_id,source_count,canonical_hash)
           VALUES(?,?,?,?,?,?,?)""",
        ("new-output", "same-content-hash", 2.0, 8, "legacy-profile", 0, "canonical-new"),
    )
    db.commit()
    assert db.execute(
        "SELECT COUNT(*) FROM eos_pipeline_packets WHERE packet_hash='same-content-hash'"
    ).fetchone()[0] == 2
    db.close()
