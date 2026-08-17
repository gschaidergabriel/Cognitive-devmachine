from pathlib import Path

from clayverse.engine import ClayVerseEngine
from clayverse.store import UnifiedDB


class EffectInference:
    def __init__(self, executable):
        self.executable = executable
    def reason(self, world, observation):
        return {
            "text": "effect observed",
            "selection": "effect",
            "effect": {"capability": "process.exec", "target": self.executable, "argv": [self.executable]},
        }


def test_failed_effect_reenters_without_positive_credit(tmp_path):
    executable = "/bin/false"
    if not Path(executable).exists():
        return
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        result = ClayVerseEngine(
            db, {"g": "gabriel"}, inference=EffectInference(executable), allow_process=True
        ).ingest("g", "run expected failing effect")
        assert result["outcome"]["ok"] is False
        row = db.db.execute(
            "SELECT credit,reentered,outcome_hash FROM causal_episodes WHERE causal_id=?",
            (result["causal_id"],),
        ).fetchone()
        assert row["reentered"] == 1
        assert row["credit"] == 0.0
        assert row["outcome_hash"]
    finally:
        db.close()


def test_successful_effect_gets_positive_credit(tmp_path):
    executable = "/bin/true"
    if not Path(executable).exists():
        return
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        result = ClayVerseEngine(
            db, {"g": "gabriel"}, inference=EffectInference(executable), allow_process=True
        ).ingest("g", "run expected successful effect")
        assert result["outcome"]["ok"] is True
        credit = db.db.execute(
            "SELECT credit FROM causal_episodes WHERE causal_id=?", (result["causal_id"],)
        ).fetchone()[0]
        assert credit == 1.0
    finally:
        db.close()
