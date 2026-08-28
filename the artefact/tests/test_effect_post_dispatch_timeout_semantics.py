import hashlib
import json
import subprocess

import pytest

from clayverse.effects import EffectGate, EffectRequest
from clayverse.entityos_bridge import EntityOSBridge
from clayverse.store import UnifiedDB


def _write_harmless_timeout_fixture(path):
    payload = b"#!/bin/sh\nprintf 'entered\\n' > \"$1\"\nsleep 5\nprintf 'completed\\n'\n"
    path.write_bytes(payload)
    path.chmod(0o500)
    return hashlib.sha256(payload).hexdigest()


def test_post_start_timeout_is_currently_finalized_failed_counterexample(tmp_path, capsys):
    """Executable counterexample for the current post-dispatch UNKNOWN-outcome gap.

    This is intentionally a diagnostic regression, not the desired final semantics.
    The exact current EntityOSBridge executes a sealed copy of a harmless local fixture.
    The fixture first writes an isolated tmp_path marker proving process start, then sleeps
    long enough for subprocess.run() to time out.  The current EffectGate catches that
    post-start exception and finalizes the canonical journal row as FAILED.

    Passing this test therefore confirms the negative evidence: FAILED currently means
    more than the execution evidence can justify for this path.  No production/external
    effect is performed; the only effect is a temporary local marker inside pytest tmp_path.
    """

    db = UnifiedDB(tmp_path / "unified.db")
    try:
        user_id = "trigger4-fault-injection"
        session_id = db.ensure_session(user_id, "trigger4-local-test")
        generation = int(
            db.db.execute(
                "SELECT generation FROM sessions WHERE session_id=? AND user_id=?",
                (session_id, user_id),
            ).fetchone()[0]
        )

        fixture = tmp_path / "harmless-entityos-fixture.sh"
        fixture_sha256 = _write_harmless_timeout_fixture(fixture)
        marker = tmp_path / "dispatch-entered.marker"

        bridge = EntityOSBridge(
            path=str(fixture),
            sha256=fixture_sha256,
            timeout=0.5,
        )
        gate = EffectGate(db, entityos_bridge=bridge)
        request = EffectRequest(
            user_id=user_id,
            session_id=session_id,
            capability="entityos.exec",
            target="trigger4.zero-real-effect.timeout-counterexample",
            argv=[str(marker)],
            expected_generation=generation,
        )

        with pytest.raises(subprocess.TimeoutExpired):
            gate.execute(request)

        assert marker.read_text() == "entered\n", (
            "timeout occurred without proving that the child crossed the execution boundary"
        )

        row = db.db.execute(
            "SELECT effect_id,status,outcome FROM effects ORDER BY ts DESC,effect_id DESC LIMIT 1"
        ).fetchone()
        assert row is not None
        outcome = json.loads(row["outcome"])
        assert row["status"] == "FAILED"
        assert outcome["error"] == "TimeoutExpired"
        assert outcome["boundary"] == "EntityOS"

        # The automatic lease must still be cleaned up even though world outcome is ambiguous.
        remaining_leases = db.db.execute(
            "SELECT COUNT(*) FROM leases WHERE resource=?",
            (EffectGate.ENTITYOS_EFFECT_RESOURCE,),
        ).fetchone()[0]
        assert remaining_leases == 0

        print(
            json.dumps(
                {
                    "schema": "ENTITYOS_EFFECT_POST_DISPATCH_TIMEOUT_COUNTEREXAMPLE/v1",
                    "classification": "ZERO_REAL_EFFECT_EXECUTABLE_COUNTEREVIDENCE",
                    "process_start_proven": True,
                    "local_marker": "entered",
                    "bridge_exception": "TimeoutExpired",
                    "canonical_journal_status": row["status"],
                    "canonical_outcome_error": outcome["error"],
                    "blind_replay_safety_conclusion": "FAILED_IS_TOO_STRONG_FOR_AMBIGUOUS_POST_START_TIMEOUT",
                    "real_external_effect": False,
                },
                sort_keys=True,
            )
        )
        captured = capsys.readouterr()
        assert "ZERO_REAL_EFFECT_EXECUTABLE_COUNTEREVIDENCE" in captured.out
    finally:
        db.close()
