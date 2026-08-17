import json

import pytest

from clayverse.api_acceptance_probe import run_api_acceptance_probe
from clayverse.store import StaleGeneration, UnifiedDB


class FakeApiProvider:
    def __init__(self, *, effect=None, extra_receipt=None):
        self.effect = effect
        self.extra_receipt = extra_receipt or {}

    def reason(self, world, observation):
        receipt = {
            "provider": "test-provider",
            "protocol": "chat-completions-json-v1",
            "model_requested": "model-x",
            "model_returned": "model-x",
            "response_id": "cmpl-probe",
            "finish_reason": "stop",
            "endpoint_identity_sha256": "0" * 64,
            "request_sha256": "1" * 64,
            "response_sha256": "2" * 64,
            **self.extra_receipt,
        }
        return {
            "text": "provider response persisted inside UnifiedDB",
            "selection": "request_effect" if self.effect else "respond",
            "effect": self.effect,
            "inference_receipt": receipt,
        }


def test_probe_uses_canonical_engine_and_returns_only_sanitized_receipt(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        payload = run_api_acceptance_probe(
            db,
            {"subject-g": "gabriel", "subject-a": "andreas"},
            "subject-g",
            "acceptance prompt that must not be echoed in probe output",
            inference=FakeApiProvider(),
        )
        assert payload["status"] == "api_canonical_turn_pass"
        assert payload["auth_credit"] is False
        assert payload["whole_product_pass"] is False
        assert payload["user_id"] == "gabriel"
        assert payload["reasoning_generation"] == payload["session_generation"]
        assert payload["session_generation"] == payload["entity_generation"]
        assert payload["entity_generation"] == db.entity_generation()
        assert payload["workspace_episode_id"]
        assert payload["effect"] == {
            "required": False,
            "effect_id": None,
            "present": False,
            "verified_ok": False,
        }
        assert payload["inference_receipt"]["provider"] == "test-provider"
        serialised = json.dumps(payload, sort_keys=True)
        assert "acceptance prompt" not in serialised
        assert "provider response persisted inside UnifiedDB" not in serialised
        assert len(payload["assistant_content_sha256"]) == 64
        assert payload["assistant_content_bytes"] > 0

        assistant = db.db.execute(
            "SELECT content,provenance FROM turns WHERE turn_id=?",
            (payload["assistant_turn_id"],),
        ).fetchone()
        assert assistant["content"] == "provider response persisted inside UnifiedDB"
        provenance = json.loads(assistant["provenance"])
        assert provenance["phase"] == "pre-effect-reingest"
        assert provenance["inference_receipt"]["response_id"] == "cmpl-probe"
        assert provenance["reasoning_generation"] == payload["reasoning_generation"]
        assert provenance["workspace_episode_id"] == payload["workspace_episode_id"]
    finally:
        db.close()


def test_probe_can_require_verified_effect_through_effectgate(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        payload = run_api_acceptance_probe(
            db,
            {"subject-g": "gabriel", "subject-a": "andreas"},
            "subject-g",
            "request the bounded noop",
            inference=FakeApiProvider(
                effect={"capability": "state.noop", "target": "acceptance", "argv": None}
            ),
            require_effect=True,
        )
        assert payload["effect"]["required"] is True
        assert payload["effect"]["present"] is True
        assert payload["effect"]["verified_ok"] is True
        assert payload["effect"]["effect_id"]
    finally:
        db.close()


def test_probe_can_require_exact_effect_capability(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        payload = run_api_acceptance_probe(
            db,
            {"subject-g": "gabriel", "subject-a": "andreas"},
            "subject-g",
            "request the bounded noop",
            inference=FakeApiProvider(
                effect={"capability": "state.noop", "target": "acceptance", "argv": None}
            ),
            required_effect_capability="state.noop",
        )
        assert payload["effect"]["required"] is True
        assert payload["effect"]["present"] is True
        assert payload["effect"]["verified_ok"] is True
    finally:
        db.close()


def test_probe_rejects_wrong_successful_effect_capability(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        with pytest.raises(
            RuntimeError,
            match="required entityos.exec but observed state.noop",
        ):
            run_api_acceptance_probe(
                db,
                {"subject-g": "gabriel", "subject-a": "andreas"},
                "subject-g",
                "request the bounded noop",
                inference=FakeApiProvider(
                    effect={"capability": "state.noop", "target": "acceptance", "argv": None}
                ),
                required_effect_capability="entityos.exec",
            )
    finally:
        db.close()


def test_probe_rejects_unadmitted_required_effect_capability(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        with pytest.raises(RuntimeError, match="required API effect capability is not admitted"):
            run_api_acceptance_probe(
                db,
                {"subject-g": "gabriel", "subject-a": "andreas"},
                "subject-g",
                "probe",
                inference=FakeApiProvider(),
                required_effect_capability="process.exec",
            )
    finally:
        db.close()


def test_probe_fails_closed_when_required_effect_is_missing(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        with pytest.raises(RuntimeError, match="required an effect but none was requested"):
            run_api_acceptance_probe(
                db,
                {"subject-g": "gabriel", "subject-a": "andreas"},
                "subject-g",
                "no effect",
                inference=FakeApiProvider(),
                require_effect=True,
            )
    finally:
        db.close()


def test_probe_fails_closed_when_reasoning_generation_is_stale(tmp_path, monkeypatch):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        def reject_generation(session_id, generation):
            raise StaleGeneration("forced stale probe generation")

        monkeypatch.setattr(db, "assert_live_generation", reject_generation)
        with pytest.raises(RuntimeError, match="reasoning generation is stale"):
            run_api_acceptance_probe(
                db,
                {"subject-g": "gabriel", "subject-a": "andreas"},
                "subject-g",
                "probe stale generation",
                inference=FakeApiProvider(),
            )
    finally:
        db.close()


def test_probe_fails_closed_on_unmapped_subject_or_unexpected_receipt_fields(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        with pytest.raises(PermissionError, match="canonical mapping"):
            run_api_acceptance_probe(
                db,
                {"subject-g": "gabriel", "subject-a": "andreas"},
                "unknown-subject",
                "probe",
                inference=FakeApiProvider(),
            )

        with pytest.raises(RuntimeError, match="missing or malformed"):
            run_api_acceptance_probe(
                db,
                {"subject-g": "gabriel", "subject-a": "andreas"},
                "subject-g",
                "probe",
                inference=FakeApiProvider(extra_receipt={"secret_like": "must-not-pass"}),
            )
    finally:
        db.close()
