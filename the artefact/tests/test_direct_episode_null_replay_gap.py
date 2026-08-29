from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

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


class DirectEpisodeNullReplayGapTests(unittest.TestCase):
    def test_current_exact_source_reopens_and_redispatches_episode_null_direct_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "unified.db"
            marker = root / "child-start-count.txt"

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
            with self.assertRaisesRegex(RuntimeError, "simulated_post_start_ambiguity"):
                first_gate.execute(request, episode_id=None)
            first_rows = db.db.execute(
                "SELECT effect_id,episode_id,status FROM effects ORDER BY ts,effect_id"
            ).fetchall()
            self.assertEqual(len(first_rows), 1)
            self.assertIsNone(first_rows[0]["episode_id"])
            self.assertEqual(first_rows[0]["status"], "FAILED")
            self.assertEqual(marker.read_text(), "1")
            first_effect_id = first_rows[0]["effect_id"]
            db.close()

            reopened = UnifiedDB(db_path)
            second_gate = EffectGate(
                reopened, entityos_bridge=HarmlessAmbiguousMarkerBridge(marker)
            )
            with self.assertRaisesRegex(RuntimeError, "simulated_post_start_ambiguity"):
                second_gate.execute(request, episode_id=None)

            rows = reopened.db.execute(
                "SELECT effect_id,episode_id,status FROM effects ORDER BY ts,effect_id"
            ).fetchall()
            self.assertEqual(marker.read_text(), "2")
            self.assertEqual(len(rows), 2)
            self.assertNotEqual(rows[1]["effect_id"], first_effect_id)
            self.assertIsNone(rows[1]["episode_id"])
            self.assertEqual([row["status"] for row in rows], ["FAILED", "FAILED"])
            reopened.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
