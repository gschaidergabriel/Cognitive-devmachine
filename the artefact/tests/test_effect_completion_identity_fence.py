import pytest

from clayverse.effect_journal import EffectJournal
from clayverse.identity import IdentityRouter
from clayverse.store import StaleGeneration, UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def test_verified_completion_rejects_cross_user_rebinding_without_consuming_pending_effect(tmp_path):
    db = _db(tmp_path)
    journal = EffectJournal(db)
    generation = db.session_generation("session:gabriel")
    effect_id = journal.begin(
        None,
        "session:gabriel",
        "gabriel",
        "state.noop",
        "checkpoint",
        generation,
    )

    with pytest.raises(PermissionError, match="effect owner mismatch"):
        journal.complete_verified(
            effect_id,
            {"ok": True, "boundary": "internal"},
            "session:andreas",
            "andreas",
            db.session_generation("session:andreas"),
        )

    row = db.db.execute(
        "SELECT status,outcome FROM effects WHERE effect_id=?", (effect_id,)
    ).fetchone()
    assert tuple(row) == ("PENDING", None)
    assert journal.causal_for(effect_id) is None

    journal.complete_verified(
        effect_id,
        {"ok": True, "boundary": "internal"},
        "session:gabriel",
        "gabriel",
        generation,
    )
    assert db.db.execute(
        "SELECT status FROM effects WHERE effect_id=?", (effect_id,)
    ).fetchone()[0] == "VERIFIED"
    db.close()


def test_verified_completion_cannot_rebind_old_effect_to_new_live_generation(tmp_path):
    db = _db(tmp_path)
    journal = EffectJournal(db)
    generation = db.session_generation("session:gabriel")
    effect_id = journal.begin(
        None,
        "session:gabriel",
        "gabriel",
        "state.noop",
        "checkpoint",
        generation,
    )

    new_generation = db.advance_entity_generation()
    assert new_generation != generation
    assert db.session_generation("session:gabriel") == new_generation

    with pytest.raises(StaleGeneration):
        journal.complete_verified(
            effect_id,
            {"ok": True, "boundary": "internal"},
            "session:gabriel",
            "gabriel",
            new_generation,
        )

    row = db.db.execute(
        "SELECT status,outcome FROM effects WHERE effect_id=?", (effect_id,)
    ).fetchone()
    assert row["status"] == "STALE_OUTCOME"
    assert row["outcome"] is not None
    causal = db.db.execute(
        "SELECT credit,reentered FROM causal_episodes WHERE effect_id=?", (effect_id,)
    ).fetchone()
    assert tuple(causal) == (0.0, 1)
    db.close()
