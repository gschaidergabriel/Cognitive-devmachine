import pytest

from clayverse.effects import EffectGate, EffectRequest
from clayverse.identity import IdentityRouter
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


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


def test_both_human_sessions_can_hold_and_finish_live_turns_in_same_entity_generation(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        IdentityRouter(db, {})
        gabriel = TurnLifecycle(db, "gabriel", "session:gabriel", entityos_bridge=None)
        andreas = TurnLifecycle(db, "andreas", "session:andreas", entityos_bridge=None)

        g_turn = gabriel.begin("Gabriel reasons concurrently")
        a_turn = andreas.begin("Andreas reasons concurrently")

        assert g_turn["generation"] == a_turn["generation"] == db.entity_generation() == 1
        active = db.db.execute(
            "SELECT session_id,generation FROM active_turns ORDER BY session_id"
        ).fetchall()
        assert [(row["session_id"], row["generation"]) for row in active] == [
            ("session:andreas", 1),
            ("session:gabriel", 1),
        ]

        g_effect = gabriel.request_effect("state.noop", "gabriel-concurrent-probe")
        a_effect = andreas.request_effect("state.noop", "andreas-concurrent-probe")
        assert g_effect["verified"] is True
        assert a_effect["verified"] is True
        assert db.entity_generation() == 1

        assert gabriel.complete("Gabriel complete")["completed"] is True
        assert andreas.complete("Andreas complete")["completed"] is True
        assert db.db.execute("SELECT COUNT(*) FROM active_turns").fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 2
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
