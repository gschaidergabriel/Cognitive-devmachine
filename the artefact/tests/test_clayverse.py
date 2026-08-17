import subprocess
import sys
import time

import pytest

from clayverse.effects import EffectGate, EffectRequest
from clayverse.engine import ClayVerseEngine
from clayverse.identity import IdentityRouter
from clayverse.memory import MemoryManager
from clayverse.store import StaleGeneration, UnifiedDB


@pytest.fixture
def db(tmp_path):
    d = UnifiedDB(tmp_path / "unified.db")
    yield d
    d.close()


def engine(db):
    return ClayVerseEngine(db, {"clerk-g": "gabriel", "clerk-a": "andreas"})


def test_two_equal_users_one_db(db):
    r = IdentityRouter(db, {"g": "gabriel", "a": "andreas"})
    assert r.resolve("g")[0] == "gabriel" and r.resolve("a")[0] == "andreas"
    assert {x["rights"] for x in db.db.execute("select * from users")} == {"equal"}


def test_unmapped_identity_fails_closed(db):
    with pytest.raises(PermissionError):
        IdentityRouter(db, {}).resolve("unknown")


def test_last_20_remain_full_and_older_compress(db):
    r = IdentityRouter(db, {"g": "gabriel"})
    uid, sid = r.resolve("g")
    mm = MemoryManager(db)
    for i in range(45):
        db.append_turn(sid, uid, "user", f"turn {i} " + ("x " * 50))
    mm.compact(sid)
    rows = db.all_turns(sid)
    assert all(x["fidelity"] == "full" for x in rows[-20:])
    assert any(x["fidelity"] != "full" for x in rows[:-20])


def test_explicit_durable_memory_only(db):
    e = engine(db)
    e.ingest("clerk-g", "FACT: alpha is beta\nnormal sentence")
    mem = db.memories()
    assert len(mem) == 1 and mem[0]["value"] == "alpha is beta"


def test_collision_triggers_cross_session_retrieval(db):
    e = engine(db)
    e.ingest("clerk-g", "editing resource", resources=["repo:file.txt"])
    assert (
        e.ingest("clerk-a", "also editing", resources=["repo:file.txt"])["collision_count"]
        >= 1
    )
    assert (
        e.ingest("clerk-a", "unrelated", resources=["repo:other.txt"])["collision_count"]
        == 0
    )


def test_claygraph_is_rebuildable_projection(db):
    e = engine(db)
    e.ingest("clerk-g", "FACT: graph source")
    counts = e.graph.counts()
    db.db.execute("delete from graph_nodes")
    db.db.execute("delete from graph_edges")
    assert e.graph.rebuild() == counts and counts["nodes"] > 0


def test_stale_lease_is_rejected_aba(db):
    IdentityRouter(db, {"g": "gabriel"})
    l1 = db.acquire_lease("repo:x", "worker-A", ttl=0.01)
    time.sleep(0.02)
    l2 = db.acquire_lease("repo:x", "worker-B", ttl=10)
    with pytest.raises(StaleGeneration):
        db.assert_lease(l1)
    db.assert_lease(l2)


def test_process_gate_no_shell_and_disabled_by_default(db):
    r = IdentityRouter(db, {"g": "gabriel"})
    uid, sid = r.resolve("g")
    gate = EffectGate(db, allow_process=False)
    with pytest.raises(PermissionError):
        gate.execute(EffectRequest(uid, sid, "process.exec", "echo", ["/bin/echo", "ok"]))

    eid, out = EffectGate(db, allow_process=True).execute(
        EffectRequest(
            uid,
            sid,
            "process.exec",
            "echo",
            ["/bin/echo", "ok"],
            request_key="gabriel:req-process:effect:0",
        )
    )
    assert eid and out["ok"] and out["stdout"].strip() == "ok"

    with pytest.raises(PermissionError):
        EffectGate(db, allow_process=True).execute(
            EffectRequest(uid, sid, "process.exec", "shell", ["/bin/sh", "-c", "echo forbidden"])
        )
    with pytest.raises(ValueError):
        EffectGate(db, allow_process=True).execute(
            EffectRequest(uid, sid, "process.exec", "nul", ["/bin/echo", "bad\x00arg"])
        )


def test_effect_exact_retry_is_idempotent(db):
    uid, sid = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    gate = EffectGate(db, allow_process=True)
    req = EffectRequest(
        uid,
        sid,
        "process.exec",
        "echo",
        ["/bin/echo", "once"],
        request_key="gabriel:req-idempotent:effect:0",
    )
    eid1, out1 = gate.execute(req)
    eid2, out2 = gate.execute(req)
    assert eid1 == eid2
    assert out1 == out2
    assert db.db.execute("select count(*) from effects").fetchone()[0] == 1


def test_consumed_unusual_collision_regression_blocks_second_intent(db, tmp_path):
    # Regression of this go's already-consumed EFFECT_ID_INTENT_COLLISION
    # intervention; this is not a second unusual experiment.
    uid, sid = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    gate = EffectGate(db, allow_process=True)
    key = "gabriel:req-collision:effect:0"
    gate.execute(
        EffectRequest(uid, sid, "process.exec", "echo", ["/bin/echo", "first"], request_key=key)
    )
    marker = tmp_path / "must-not-exist"
    with pytest.raises(RuntimeError, match="EFFECT_REQUEST_CONFLICT"):
        gate.execute(
            EffectRequest(
                uid,
                sid,
                "process.exec",
                "different-intent",
                [sys.executable, "-c", f"open({str(marker)!r},'w').write('BAD')"],
                request_key=key,
            )
        )
    assert not marker.exists()
    assert db.db.execute("select count(*) from effects").fetchone()[0] == 1


def test_pending_effect_after_crash_fails_closed_on_restart(tmp_path, monkeypatch):
    path = tmp_path / "state.db"
    d = UnifiedDB(path)
    uid, sid = IdentityRouter(d, {"g": "gabriel"}).resolve("g")
    req = EffectRequest(
        uid,
        sid,
        "process.exec",
        "echo",
        ["/bin/echo", "once"],
        request_key="gabriel:req-crash-window:effect:0",
    )
    gate = EffectGate(d, allow_process=True)

    def simulated_process_death(*args, **kwargs):
        raise SystemExit(99)

    monkeypatch.setattr(subprocess, "run", simulated_process_death)
    with pytest.raises(SystemExit):
        gate.execute(req)
    assert d.db.execute("select status from effects").fetchone()[0] == "PENDING"
    d.close()

    d = UnifiedDB(path)
    gate = EffectGate(d, allow_process=True)
    with pytest.raises(RuntimeError, match="EFFECT_RECOVERY_REQUIRED"):
        gate.execute(req)
    assert d.db.execute("select count(*) from effects").fetchone()[0] == 1
    d.close()


class FailingProcessInference:
    def reason(self, world, observation):
        return {
            "text": "attempted",
            "selection": "respond",
            "effect": {
                "capability": "process.exec",
                "target": "false",
                "argv": ["/bin/false"],
            },
        }


def test_verified_negative_outcome_reenters_without_positive_credit(db):
    e = ClayVerseEngine(
        db,
        {"g": "gabriel"},
        inference=FailingProcessInference(),
        allow_process=True,
    )
    result = e.ingest("g", "try", request_id="req-negative-outcome")
    assert result["outcome"]["ok"] is False
    row = db.db.execute(
        "select credit,reentered from causal_episodes where causal_id=?",
        (result["causal_id"],),
    ).fetchone()
    assert float(row["credit"]) == 0.0
    assert int(row["reentered"]) == 1
    assert db.db.execute(
        "select status from effects where effect_id=?", (result["effect_id"],)
    ).fetchone()[0] == "VERIFIED"


def test_causal_reentry_and_restart_continuity(tmp_path):
    path = tmp_path / "state.db"
    d = UnifiedDB(path)
    ClayVerseEngine(d, {"g": "gabriel"}).ingest("g", "FACT: persistent")
    d.close()
    d = UnifiedDB(path)
    assert d.db.execute(
        "select count(*) from causal_episodes where reentered=1"
    ).fetchone()[0] == 1
    assert d.db.execute("select value from durable_memory").fetchone()[0] == "persistent"
    assert d.db.execute("select value from meta where key='schema_version'").fetchone()[0] == "2"
    d.close()


def test_checkpoint_hash_changes_on_canonical_state(db):
    r = IdentityRouter(db, {"g": "gabriel"})
    _, h1 = db.checkpoint("before")
    uid, sid = r.resolve("g")
    db.append_turn(sid, uid, "user", "x")
    _, h2 = db.checkpoint("after")
    assert h1 != h2
