import hashlib
import json

from clayverse.effects import EffectGate, EffectRequest
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB


def test_effect_target_is_redacted_at_rest_but_live_semantics_are_preserved(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    user_id, session_id = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    secret_target = "TARGET_SECRET_19"
    try:
        effect_id, outcome = EffectGate(db).execute(
            EffectRequest(user_id, session_id, "state.noop", secret_target)
        )
        assert outcome["target"] == secret_target
        row = db.db.execute(
            "SELECT target,outcome FROM effects WHERE effect_id=?", (effect_id,)
        ).fetchone()
        assert secret_target not in row["target"]
        assert secret_target not in row["outcome"]
        receipt = json.loads(row["target"])
        raw = secret_target.encode("utf-8")
        assert receipt == {
            "audit": "redacted-target-v1",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
    finally:
        db.close()
