from __future__ import annotations

import json

import pytest

from clayverse.engine import ClayVerseEngine
from clayverse.recovery import recover_incomplete_episodes
from clayverse.store import UnifiedDB


class _NoopEffectInference:
    def reason(self, world, observation):
        return {
            "text": "provider response before bounded noop",
            "selection": "request_effect",
            "effect": {
                "capability": "state.noop",
                "target": "engine-active-spine-regression",
                "argv": None,
            },
            "inference_receipt": {
                "provider": "mistral",
                "model_requested": "model-fixed",
                "model_returned": "model-fixed",
                "response_id": "cmpl-engine-active-spine",
                "finish_reason": "stop",
                "request_sha256": "1" * 64,
                "response_sha256": "2" * 64,
            },
        }


class _FailingInference:
    def reason(self, world, observation):
        raise RuntimeError("provider failed before response")


def test_engine_effect_uses_predeclared_active_causal_spine_and_retires_it(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        engine = ClayVerseEngine(
            db,
            {"subject-g": "gabriel", "subject-a": "andreas"},
            inference=_NoopEffectInference(),
        )
        result = engine.ingest("subject-g", "request bounded noop")

        assert result["outcome"]["ok"] is True
        assert result["effect_id"]
        assert result["causal_id"] == engine.effects.causal_for_effect(result["effect_id"])
        assert db.db.execute(
            "SELECT 1 FROM active_turns WHERE session_id=?", (result["session_id"],)
        ).fetchone() is None

        workspace = db.db.execute(
            "SELECT selected,state FROM workspace_episodes WHERE episode_id=?",
            (result["workspace"]["episode_id"],),
        ).fetchone()
        assert workspace["selected"] == "request_effect"
        assert workspace["state"] == "COMPLETED"

        causal = db.db.execute(
            "SELECT causal_id,effect_id,observation_turn_id,reentered FROM causal_episodes WHERE causal_id=?",
            (result["causal_id"],),
        ).fetchone()
        assert causal["effect_id"] == result["effect_id"]
        assert causal["observation_turn_id"] == result["turn_id"]
        assert causal["reentered"] == 1

        assistant = db.db.execute(
            "SELECT provenance FROM turns WHERE turn_id=?", (result["assistant_turn_id"],)
        ).fetchone()
        provenance = json.loads(assistant["provenance"])
        assert provenance["phase"] == "pre-effect-reingest"
        assert provenance["reasoning_generation"] == db.entity_generation()

        recovery = recover_incomplete_episodes(db)
        assert recovery["scanned"] == 0
        assert recovery["existing_reentries_closed"] == 0
        assert recovery["active_turns_closed"] == 0
        workspace_after_recovery = db.db.execute(
            "SELECT state FROM workspace_episodes WHERE episode_id=?",
            (result["workspace"]["episode_id"],),
        ).fetchone()
        assert workspace_after_recovery["state"] == "COMPLETED"
    finally:
        db.close()


def test_engine_no_effect_response_is_terminal_before_recovery(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        engine = ClayVerseEngine(
            db,
            {"subject-g": "gabriel", "subject-a": "andreas"},
        )
        result = engine.ingest("subject-g", "respond without an effect")

        workspace = db.db.execute(
            "SELECT selected,state FROM workspace_episodes WHERE episode_id=?",
            (result["workspace"]["episode_id"],),
        ).fetchone()
        assert workspace["selected"] == "respond"
        assert workspace["state"] == "COMPLETED"
        assert db.db.execute("SELECT COUNT(*) FROM active_turns").fetchone()[0] == 0

        recovery = recover_incomplete_episodes(db)
        assert recovery["scanned"] == 0
        assert recovery["existing_reentries_closed"] == 0
        assert recovery["active_turns_closed"] == 0
        assert db.db.execute(
            "SELECT state FROM workspace_episodes WHERE episode_id=?",
            (result["workspace"]["episode_id"],),
        ).fetchone()[0] == "COMPLETED"
    finally:
        db.close()


def test_engine_provider_failure_leaves_active_turn_for_recovery(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        engine = ClayVerseEngine(
            db,
            {"subject-g": "gabriel", "subject-a": "andreas"},
            inference=_FailingInference(),
        )
        with pytest.raises(RuntimeError, match="provider failed"):
            engine.ingest("subject-g", "provider will fail")

        active = db.db.execute("SELECT * FROM active_turns").fetchone()
        assert active is not None
        assert active["user_id"] == "gabriel"
        workspace = db.db.execute(
            "SELECT selected,state FROM workspace_episodes WHERE episode_id=?",
            (active["episode_id"],),
        ).fetchone()
        assert workspace["selected"] is None
        assert workspace["state"] == "OPEN"
    finally:
        db.close()
