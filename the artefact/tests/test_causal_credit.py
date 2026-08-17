import hashlib
from pathlib import Path

from clayverse.engine import ClayVerseEngine
from clayverse.entityos_bridge import EntityOSBridge
from clayverse.store import UnifiedDB


class EffectInference:
    def __init__(self, target): self.target = target
    def reason(self, world, observation):
        return {"text":"effect observed","selection":"effect","effect":{"capability":"entityos.exec","target":self.target,"argv":["test"]}}


def engine_for(db, executable):
    digest=hashlib.sha256(Path(executable).read_bytes()).hexdigest()
    return ClayVerseEngine(db,{"g":"gabriel"},inference=EffectInference(executable),entityos_bridge=EntityOSBridge(executable,digest))


def test_verified_failed_effect_reenters_without_positive_credit(tmp_path):
    executable="/bin/false"
    if not Path(executable).exists(): return
    db=UnifiedDB(tmp_path/"unified.db")
    try:
        result=engine_for(db,executable).ingest("g","run expected failing effect")
        assert result["outcome"]["ok"] is False
        row=db.db.execute("SELECT credit,reentered,outcome_hash FROM causal_episodes WHERE causal_id=?",(result["causal_id"],)).fetchone()
        assert row["reentered"]==1 and row["credit"]==0.0 and row["outcome_hash"]
    finally: db.close()


def test_verified_successful_effect_gets_positive_credit(tmp_path):
    executable="/bin/true"
    if not Path(executable).exists(): return
    db=UnifiedDB(tmp_path/"unified.db")
    try:
        result=engine_for(db,executable).ingest("g","run expected successful effect")
        assert result["outcome"]["ok"] is True
        row=db.db.execute("SELECT credit,reentered FROM causal_episodes WHERE causal_id=?",(result["causal_id"],)).fetchone()
        assert row["reentered"]==1 and row["credit"]==1.0
    finally: db.close()
