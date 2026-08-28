import pytest

from clayverse.final_acceptance_probe import run_mistral_acceptance_probe
from clayverse.store import UnifiedDB


CLERK_MAP = {"clerk-g": "gabriel", "clerk-a": "andreas"}


def _receipt():
    return {
        "provider": "mistral",
        "model_requested": "model-x",
        "model_returned": "model-x",
        "response_id": "cmpl-generation-test",
        "finish_reason": "stop",
        "request_sha256": "a" * 64,
        "response_sha256": "b" * 64,
    }


class _MistralDecision:
    def reason(self, world, observation):
        return {
            "text": "bounded answer",
            "selection": "respond",
            "effect": None,
            "inference_receipt": _receipt(),
        }


class _GenerationDriftDecision:
    def __init__(self, db):
        self.db = db

    def reason(self, world, observation):
        # ClayVerseEngine captures the reasoning generation immediately before this
        # call. Advancing the global generation here models a restart/fence race in
        # which the provider response belongs to the now-stale generation.
        self.db.advance_entity_generation()
        return {
            "text": "stale answer",
            "selection": "respond",
            "effect": None,
            "inference_receipt": _receipt(),
        }


def test_final_mistral_probe_binds_workspace_and_live_global_generation(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        result = run_mistral_acceptance_probe(
            db,
            CLERK_MAP,
            "clerk-g",
            "probe",
            inference=_MistralDecision(),
        )
        assert result["workspace_episode_id"]
        assert result["reasoning_generation"] == result["session_generation"]
        assert result["reasoning_generation"] == result["entity_generation"]
        assert result["entity_generation"] == db.entity_generation()
        assert result["status"] == "mistral_canonical_turn_pass"
        assert result["whole_product_pass"] is False
    finally:
        db.close()


def test_final_mistral_probe_rejects_generation_advanced_during_inference(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        with pytest.raises(RuntimeError, match="reasoning generation is stale"):
            run_mistral_acceptance_probe(
                db,
                CLERK_MAP,
                "clerk-g",
                "probe",
                inference=_GenerationDriftDecision(db),
            )
    finally:
        db.close()
