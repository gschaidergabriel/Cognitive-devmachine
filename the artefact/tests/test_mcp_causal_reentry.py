from clayverse.identity import IdentityRouter
from clayverse.mcp_server import ClayVerseBridge
from clayverse.store import UnifiedDB


def _bridge(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    return db, ClayVerseBridge(db, "gabriel", "session:gabriel")


def test_mcp_effect_reuses_journal_causal_reentry(tmp_path):
    db, bridge = _bridge(tmp_path)
    bridge.begin_turn("do bounded noop")
    effect = bridge.request_effect("state.noop", "probe")
    result = bridge.complete_turn("done")

    rows = db.db.execute(
        "SELECT causal_id,credit,reentered FROM causal_episodes WHERE effect_id=?",
        (effect["effect_id"],),
    ).fetchall()
    assert len(rows) == 1
    assert rows[0]["causal_id"] == effect["causal_id"] == result["causal_id"]
    assert rows[0]["credit"] == 1.0
    assert rows[0]["reentered"] == 1
    db.close()


def test_mcp_denied_entityos_effect_still_has_one_causal_reentry(tmp_path):
    db, bridge = _bridge(tmp_path)
    bridge.begin_turn("request unavailable EntityOS")
    effect = bridge.request_effect("entityos.exec", "probe", ["status"])
    assert effect["outcome"]["denied"] is True
    result = bridge.complete_turn("not executed")

    rows = db.db.execute(
        "SELECT causal_id,credit FROM causal_episodes WHERE effect_id=?",
        (effect["effect_id"],),
    ).fetchall()
    assert len(rows) == 1
    assert rows[0]["causal_id"] == result["causal_id"]
    assert rows[0]["credit"] == 0.0
    db.close()


def test_mcp_no_effect_turn_creates_one_normal_causal_reentry(tmp_path):
    db, bridge = _bridge(tmp_path)
    opened = bridge.begin_turn("just answer")
    result = bridge.complete_turn("answer")

    rows = db.db.execute(
        "SELECT causal_id,effect_id,credit,reentered FROM causal_episodes WHERE causal_id=?",
        (opened["causal_id"],),
    ).fetchall()
    assert len(rows) == 1
    assert result["causal_id"] == opened["causal_id"]
    assert rows[0]["effect_id"] is None
    assert rows[0]["credit"] == 0.0
    assert rows[0]["reentered"] == 1
    db.close()
