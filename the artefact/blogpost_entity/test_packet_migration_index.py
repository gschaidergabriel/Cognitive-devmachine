from __future__ import annotations

from pathlib import Path

from tools.clay_profile_pipeline_runtime import ProfilePipelineRuntime


def test_legacy_packet_migration_retains_named_packet_hash_index(tmp_path: Path):
    """Legacy PK migration must not silently drop the packet-hash lookup index."""
    runtime = ProfilePipelineRuntime(root=tmp_path)
    db_path = str(tmp_path / "entity.db")

    with runtime._db(db_path) as db:
        db.execute(
            """CREATE TABLE eos_pipeline_packets(
                 packet_hash TEXT PRIMARY KEY,
                 output_id TEXT NOT NULL,
                 ts REAL NOT NULL,
                 generation INTEGER NOT NULL,
                 profile_id TEXT NOT NULL,
                 source_count INTEGER NOT NULL,
                 canonical_hash TEXT NOT NULL)"""
        )
        db.execute(
            "CREATE INDEX eos_pipeline_packets_hash_idx "
            "ON eos_pipeline_packets(packet_hash)"
        )
        db.execute(
            """INSERT INTO eos_pipeline_packets(
                   packet_hash,output_id,ts,generation,profile_id,source_count,canonical_hash)
               VALUES(?,?,?,?,?,?,?)""",
            ("packet-1", "output-1", 1.0, 1, "fixture", 0, "canonical-1"),
        )
        db.commit()

        runtime._ensure_schema(db)

        indexes = {
            row["name"]
            for row in db.execute("PRAGMA index_list('eos_pipeline_packets')").fetchall()
        }
        migrated = db.execute(
            "SELECT output_id,packet_hash,canonical_hash FROM eos_pipeline_packets"
        ).fetchall()

    assert "eos_pipeline_packets_hash_idx" in indexes
    assert [tuple(row) for row in migrated] == [
        ("output-1", "packet-1", "canonical-1")
    ]
