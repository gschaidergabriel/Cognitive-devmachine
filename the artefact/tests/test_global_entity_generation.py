import pytest

from clayverse.effects import EffectGate, EffectRequest
from clayverse.identity import IdentityRouter
from clayverse.store import StaleGeneration, UnifiedDB


def test_entity_generation_is_live_and_equal_across_both_sessions(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        IdentityRouter(db, {})
        assert db.entity_generation() == 1
        assert db.session_generation("session:gabriel") == 1
        assert db.session_generation("session:andreas") == 1
        generation = db.advance_entity_generation()
        assert generation == 2
        assert db.session_generation("session:gabriel") == 2
        assert db.session_generation("session:andreas") == 2
        db.assert_live_generation("session:gabriel", 2)
        db.assert_live_generation("session:andreas", 2)
    finally:
        db.close()


def test_global_generation_advance_fences_effect_reasoned_before_other_session_advanced_entity(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        IdentityRouter(db, {})
        stale = db.session_generation("session:gabriel")
        db.advance_entity_generation()
        gate = EffectGate(db, allow_process=False, entityos_bridge=None)
        with pytest.raises(StaleGeneration):
            gate.execute(
                EffectRequest(
                    "gabriel",
                    "session:gabriel",
                    "state.noop",
                    "must-not-run",
                    None,
                    stale,
                )
            )
        assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0
    finally:
        db.close()
