import pytest

from clayverse.store import UnifiedDB


def test_direct_unifieddb_effect_persistence_is_retired(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        with pytest.raises(RuntimeError, match="use EffectJournal"):
            db.record_effect(
                None,
                "gabriel",
                "entityos.exec",
                "RAW_TARGET_SECRET",
                db.entity_generation(),
                "VERIFIED",
                argv=["RAW_ARG_SECRET"],
                outcome={"stdout": "RAW_OUTPUT_SECRET"},
            )
        assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0
    finally:
        db.close()
