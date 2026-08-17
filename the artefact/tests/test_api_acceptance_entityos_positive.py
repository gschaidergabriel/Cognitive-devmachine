from clayverse.api_acceptance_probe import run_api_acceptance_probe
from clayverse.store import UnifiedDB


class _EntityOSProvider:
    def reason(self, world, observation):
        return {
            "text": "proposal",
            "selection": "request_effect",
            "effect": {
                "capability": "entityos.exec",
                "target": "self-test",
                "argv": ["--self-test-json"],
            },
            "inference_receipt": {
                "provider": "test-provider",
                "protocol": "chat-completions-json-v1",
                "model_requested": "model-x",
                "model_returned": "model-x",
                "response_id": "cmpl-entityos",
                "finish_reason": "stop",
                "endpoint_identity_sha256": "0" * 64,
                "request_sha256": "1" * 64,
                "response_sha256": "2" * 64,
            },
        }


class _EntityOSBridge:
    sha256 = "a" * 64

    def run(self, argv):
        assert argv == ["--self-test-json"]
        return {"ok": True, "self_test": "passed"}


def test_required_entityos_capability_gets_credit_only_after_verified_journal_round_trip(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        result = run_api_acceptance_probe(
            db,
            {"subject-g": "gabriel", "subject-a": "andreas"},
            "subject-g",
            "final generic API acceptance must exercise EntityOS",
            inference=_EntityOSProvider(),
            entityos_bridge=_EntityOSBridge(),
            require_effect=True,
            required_effect_capability="entityos.exec",
        )
        assert result["effect"]["required"] is True
        assert result["effect"]["required_capability"] == "entityos.exec"
        assert result["effect"]["capability"] == "entityos.exec"
        assert result["effect"]["verified_ok"] is True
        row = db.db.execute(
            "SELECT capability,status,outcome FROM effects WHERE effect_id=?",
            (result["effect"]["effect_id"],),
        ).fetchone()
        assert row["capability"] == "entityos.exec"
        assert row["status"] == "VERIFIED"
        assert '"ok": true' in row["outcome"]
    finally:
        db.close()
