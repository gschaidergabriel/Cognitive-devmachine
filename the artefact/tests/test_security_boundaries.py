import hashlib
import json
from pathlib import Path

from clayverse.effects import EffectGate, EffectRequest
from clayverse.identity import IdentityRouter
from clayverse.service import healthcheck
from clayverse.store import UnifiedDB


def test_health_missing_fails_closed_without_creating_state(tmp_path):
    assert healthcheck(str(tmp_path)) == 1
    assert not (tmp_path / "unified.db").exists()


def test_health_probe_is_read_only(tmp_path):
    path = tmp_path / "unified.db"
    db = UnifiedDB(path)
    IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    db.checkpoint("before-health")
    before_count = db.db.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0]
    db.close()
    before_hash = hashlib.sha256(path.read_bytes()).hexdigest()

    assert healthcheck(str(tmp_path)) == 0

    after_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    db = UnifiedDB(path)
    after_count = db.db.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0]
    db.close()
    assert after_hash == before_hash
    assert after_count == before_count


def test_effect_audit_does_not_persist_raw_argv_or_output(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    uid, sid = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    secret = "SENSITIVE_ARG_VALUE"
    eid, outcome = EffectGate(db, allow_process=True).execute(
        EffectRequest(uid, sid, "process.exec", "printf-test", ["/usr/bin/printf", secret])
    )
    assert secret in outcome["stdout"]
    row = db.db.execute("SELECT argv,outcome FROM effects WHERE effect_id=?", (eid,)).fetchone()
    persisted_argv = json.loads(row["argv"])
    persisted_outcome = json.loads(row["outcome"])
    assert secret not in row["argv"]
    assert secret not in row["outcome"]
    assert persisted_argv["argc"] == 2
    assert len(persisted_argv["argv_sha256"]) == 64
    assert "stdout" not in persisted_outcome
    assert "stderr" not in persisted_outcome
    assert len(persisted_outcome["stdout_sha256"]) == 64
    db.close()
