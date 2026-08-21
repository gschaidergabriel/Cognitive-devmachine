from __future__ import annotations

import pytest

from clayverse.autonomy import AutonomyController
from clayverse.autonomy_dispatch import (
    AutonomyDispatchError,
    consume_dispatch_prompt,
    reserve_dispatch,
)
from clayverse.autonomy_planner import AutonomyPlanner
from clayverse.autonomy_pulse import AutonomyPulse
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.terminal_hooks import user_prompt


def _prepared_dispatch(state_root):
    db = UnifiedDB(state_root / "unified.db")
    IdentityRouter(db, {})
    controller = AutonomyController(db)
    source = db.append_turn(
        "session:gabriel",
        "gabriel",
        "user",
        "Continue this durable detached goal.",
    )
    goal = controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        source,
        completion_mode="user_ack",
    )
    prepared = AutonomyPlanner(db).prepare_next("gabriel")
    dispatch = reserve_dispatch(
        db,
        user_id="gabriel",
        goal_id=goal["goal_id"],
        step_id=prepared["step_id"],
        instruction=prepared["prompt"],
    )
    db.close()
    return dispatch


def _canonical_counts(db):
    return {
        "turns": db.db.execute("SELECT COUNT(*) FROM turns").fetchone()[0],
        "workspace": db.db.execute("SELECT COUNT(*) FROM workspace_episodes").fetchone()[0],
        "causal": db.db.execute("SELECT COUNT(*) FROM causal_episodes").fetchone()[0],
    }


def _hook_payload(prompt):
    return {
        "hook_event_name": "UserPromptSubmit",
        "session_id": "claude-session-rejected-dispatch",
        "prompt": prompt,
    }


@pytest.mark.parametrize("mode", ["malformed", "wrong", "expired", "replayed"])
def test_rejected_reserved_dispatch_never_becomes_human_attestation(tmp_path, monkeypatch, mode):
    state_root = tmp_path / "state"
    state_root.mkdir()
    dispatch = _prepared_dispatch(state_root)

    db = UnifiedDB(state_root / "unified.db")
    before = _canonical_counts(db)
    if mode == "malformed":
        terminal_prompt = "__CLAY_AUTONOMY_DISPATCH__:not-a-valid-nonce"
        expected = "prompt malformed"
    elif mode == "wrong":
        wrong_nonce = "0" * 32 if dispatch.nonce != "0" * 32 else "1" * 32
        terminal_prompt = f"__CLAY_AUTONOMY_DISPATCH__:{wrong_nonce}"
        expected = "nonce mismatch"
    elif mode == "expired":
        db.db.execute(
            "UPDATE leases SET expires_at=0 WHERE resource=?",
            ("autonomy-dispatch:session:gabriel",),
        )
        db.db.commit()
        terminal_prompt = dispatch.terminal_prompt
        expected = "lease expired"
    else:
        claimed = consume_dispatch_prompt(
            db,
            user_id="gabriel",
            session_id="session:gabriel",
            prompt=dispatch.terminal_prompt,
        )
        assert claimed is not None
        terminal_prompt = dispatch.terminal_prompt
        expected = "lease missing"
    db.close()

    monkeypatch.setenv("CLAYVERSE_USER_ID", "gabriel")
    monkeypatch.setenv("CLAYVERSE_SESSION_ID", "session:gabriel")
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(state_root))

    with pytest.raises(AutonomyDispatchError, match=expected):
        user_prompt(_hook_payload(terminal_prompt))

    db = UnifiedDB(state_root / "unified.db")
    try:
        assert _canonical_counts(db) == before
        assert AutonomyPulse._has_human_roundtrip_after(db, "gabriel", 0.0) is False
        if mode == "wrong":
            lease = db.db.execute(
                "SELECT nonce FROM leases WHERE resource=?",
                ("autonomy-dispatch:session:gabriel",),
            ).fetchone()
            assert lease is not None
            assert lease["nonce"] == dispatch.nonce
    finally:
        db.close()
