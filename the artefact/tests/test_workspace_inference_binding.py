import hashlib
import json

from clayverse.engine import ClayVerseEngine
from clayverse.store import UnifiedDB


class CaptureInference:
    def __init__(self):
        self.world = None

    def reason(self, world, observation):
        self.world = json.loads(json.dumps(world))
        return {"text": "ok", "selection": "respond", "effect": None}


def test_workspace_episode_is_bound_into_inference_and_canonical_provenance(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        capture = CaptureInference()
        engine = ClayVerseEngine(db, {"g": "gabriel"}, inference=capture)
        result = engine.ingest("g", "probe")

        binding = capture.world["cognitive_workspace_binding"]
        assert binding["schema"] == "COGNITIVE_WORKSPACE_BINDING/v1"
        assert binding["binding_class"] == "DETERMINISTIC_WORKSPACE_EPISODE"
        assert binding["jspace_status"] == "JSPACE_UNAVAILABLE"
        assert binding["jspace_reason"] == "EXACT_LATENT_WORKSPACE_NOT_BOUND"
        assert binding["session_id"] == result["session_id"]
        assert binding["observation_turn_id"] == result["turn_id"]
        assert binding["episode_id"] == result["workspace"]["episode_id"]
        assert binding["generation"] == db.session_generation(result["session_id"])
        assert binding["alternatives"] == result["workspace"]["alternatives"]
        assert binding["truth_authority"] is False
        assert binding["effect_authority"] is False

        raw = json.dumps(
            binding,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        assert result["workspace_binding_sha256"] == digest

        row = db.db.execute(
            "SELECT provenance FROM turns WHERE turn_id=?",
            (result["assistant_turn_id"],),
        ).fetchone()
        provenance = json.loads(row["provenance"])
        assert provenance["workspace_episode_id"] == binding["episode_id"]
        assert provenance["reasoning_generation"] == binding["generation"]
        assert provenance["workspace_binding_sha256"] == digest
    finally:
        db.close()
