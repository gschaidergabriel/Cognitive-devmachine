import sqlite3

from clayverse.microclay_retrieval import MicroClayRetrieval


class _SelectionDB:
    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE retrieval_episodes(
                retrieval_id TEXT PRIMARY KEY,
                causal_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                generation INTEGER NOT NULL,
                ts REAL NOT NULL
            );
            CREATE TABLE causal_episodes(
                causal_id TEXT PRIMARY KEY,
                effect_id TEXT NOT NULL,
                credit REAL NOT NULL,
                reentered INTEGER NOT NULL
            );
            CREATE TABLE effects(
                effect_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                capability TEXT NOT NULL
            );
            CREATE TABLE retrieval_feedback(
                retrieval_id TEXT NOT NULL,
                signal_class TEXT NOT NULL
            );
            """
        )

    def assert_live_generation(self, session_id, generation):
        assert session_id == "session:gabriel"
        assert generation == 7


def _add(db, name, *, status, capability, credit=0.0, ts=1.0):
    db.db.execute(
        "INSERT INTO retrieval_episodes(retrieval_id,causal_id,session_id,generation,ts) VALUES(?,?,?,?,?)",
        (f"r:{name}", f"c:{name}", "session:gabriel", 7, ts),
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,effect_id,credit,reentered) VALUES(?,?,?,1)",
        (f"c:{name}", f"e:{name}", credit),
    )
    db.db.execute(
        "INSERT INTO effects(effect_id,status,capability) VALUES(?,?,?)",
        (f"e:{name}", status, capability),
    )


def test_automatic_effect_learning_accepts_only_known_reward_eligible_outcomes():
    db = _SelectionDB()
    _add(db, "verified", status="VERIFIED", capability="entityos.exec", credit=1.0, ts=1.0)
    _add(db, "failed", status="FAILED", capability="entityos.exec", credit=0.0, ts=2.0)
    _add(db, "denied", status="DENIED", capability="entityos.exec", credit=0.0, ts=3.0)
    _add(db, "unknown-live", status="UNKNOWN_OUTCOME", capability="entityos.exec", ts=4.0)
    _add(db, "unknown-restart", status="UNKNOWN_AFTER_RESTART", capability="entityos.exec", ts=5.0)
    _add(db, "stale", status="STALE_OUTCOME", capability="entityos.exec", ts=6.0)
    _add(db, "noop", status="VERIFIED", capability="state.noop", credit=0.0, ts=7.0)

    organ = MicroClayRetrieval(db)
    calls = []

    def fake_credit(**kwargs):
        calls.append(kwargs)
        return {"applied": True}

    organ.credit = fake_credit
    result = organ.learn_from_verified_outcomes(session_id="session:gabriel", generation=7)

    assert result == {"eligible": 3, "applied": 3}
    assert [call["signal_class"] for call in calls] == [
        "effect_outcome:VERIFIED",
        "effect_outcome:FAILED",
        "effect_outcome:DENIED",
    ]
    assert {call["causal_id"] for call in calls} == {
        "c:verified",
        "c:failed",
        "c:denied",
    }
    db.db.close()
