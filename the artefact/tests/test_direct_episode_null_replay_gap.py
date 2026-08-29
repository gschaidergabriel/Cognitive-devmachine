from __future__ import annotations

from pathlib import Path

import pytest

from clayverse.effects import EffectGate, EffectRequest
from clayverse.store import UnifiedDB


class HarmlessAmbiguousMarkerBridge:
    """Local marker only: proves boundary entry without any external real effect."""

    sha256 = "a" * 64

    def __init__(self, marker_path: Path):
        self.marker_path = marker_path

    def run(self, argv):
        prior = int(self.marker_path.read_text() or "0") if self.marker_path.exists() else 0
        self.marker_path.write_text(str(prior + 1))
        raise RuntimeError("simulated_post_start_ambiguity")


def test_current_exact_source_reopens_and_redispatches_episode_null_direct_effect(tmp_path):
    db_path = tmp_path / "unified.db"
    marker = tmp_path / "child-start-count.txt"

    db = UnifiedDB(db_path)
    db.ensure_user("user-direct-A", "Direct User")
    session_id = db.ensure_session("user-direct-A", "terminal-direct-A")
    request = EffectRequest(
        user_id="user-direct-A",
        session_id=session_id,
        capability="entityos.exec",
        target="wp105-direct-episode-null-replay-probe",
        argv=["harmless-marker", "same-logical-operation"],
        expected_generation=db.session_generation(session_id),
    )

    first_gate = EffectGate(db, entityos_bridge=HarmlessAmbiguousMarkerBridge(marker))
    with pytest.raises(RuntimeError, match="simulated_post_start_ambiguity"):
        first_gate.execute(request, episode_id=None)
    first_rows = db.db.execute(
        "SELECT effect_id,episode_id,status FROM effects ORDER BY ts,effect_id"
    ).fetchall()
    assert len(first_rows) == 1
    assert first_rows[0]["episode_id"] is None
    assert first_rows[0]["status"] == "FAILED"
    assert marker.read_text() == "1"
    first_effect_id = first_rows[0]["effect_id"]
    db.close()

    reopened = UnifiedDB(db_path)
    second_gate = EffectGate(reopened, entityos_bridge=HarmlessAmbiguousMarkerBridge(marker))
    with pytest.raises(RuntimeError, match="simulated_post_start_ambiguity"):
        second_gate.execute(request, episode_id=None)

    rows = reopened.db.execute(
        "SELECT effect_id,episode_id,status FROM effects ORDER BY ts,effect_id"
    ).fetchall()
    assert marker.read_text() == "2"
    assert len(rows) == 2
    assert rows[1]["effect_id"] != first_effect_id
    assert rows[1]["episode_id"] is None
    assert [row["status"] for row in rows] == ["FAILED", "FAILED"]
    reopened.close()
