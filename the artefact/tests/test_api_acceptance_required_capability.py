import pytest

from clayverse.api_acceptance_probe import run_api_acceptance_probe
from clayverse.store import UnifiedDB


class _NoopProvider:
    def reason(self, world, observation):
        return {
            "text": "proposal",
            "selection": "request_effect",
            "effect": {"capability": "state.noop", "target": "acceptance", "argv": None},
            "inference_receipt": {
                "provider": "test-provider",
                "protocol": "chat-completions-json-v1",
                "model_requested": "model-x",
                "model_returned": "model-x",
                "response_id": "cmpl-noop",
                "finish_reason": "stop",
                "endpoint_identity_sha256": "0" * 64,
                "request_sha256": "1" * 64,
                "response_sha256": "2" * 64,
            },
        }


def test_final_generic_api_probe_does_not_accept_noop_as_entityos_round_trip(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        with pytest.raises(RuntimeError, match="entityos.exec"):
            run_api_acceptance_probe(
                db,
                {"subject-g": "gabriel", "subject-a": "andreas"},
                "subject-g",
                "final generic API acceptance must exercise EntityOS",
                inference=_NoopProvider(),
                require_effect=True,
                required_effect_capability="entityos.exec",
            )
    finally:
        db.close()
