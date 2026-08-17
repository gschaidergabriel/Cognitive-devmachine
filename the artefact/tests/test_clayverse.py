import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clayverse import CLAYVERSE_ID, ClayVerse, selftest


class ClayVerseCoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_first_two_sessions_share_identity_and_memory_across_restart(self):
        with ClayVerse(self.root) as cv:
            a = cv.open_session("A")
            cv.put_memory("A", "fact", {"n": 7})
        with ClayVerse(self.root) as cv:
            b = cv.open_session("B")
            self.assertEqual(a["clayverse_id"], CLAYVERSE_ID)
            self.assertEqual(b["clayverse_id"], CLAYVERSE_ID)
            self.assertEqual(a["core_fingerprint"], b["core_fingerprint"])
            self.assertEqual(cv.get_memory("fact"), {"n": 7})

    def test_graph_is_rebuildable_projection_of_unifieddb(self):
        with ClayVerse(self.root) as cv:
            cv.link("a", "CAUSES", "b")
            cv.link("b", "SUPPORTS", "c")
            expected = cv.graph_edges()
            cv.db.execute("DELETE FROM graph_edges")
            self.assertEqual(cv.graph_edges(), [])
            self.assertEqual(cv.rebuild_graph_projection(), 2)
            self.assertEqual(cv.graph_edges(), expected)

    def test_event_tamper_fails_closed(self):
        with ClayVerse(self.root) as cv:
            cv.open_session("A")
            cv.db.execute("UPDATE events SET payload_json='{}' WHERE seq=2")
            with self.assertRaisesRegex(RuntimeError, "EVENT_HASH_MISMATCH"):
                cv.verify_event_stream()

    def test_causal_effect_requires_verified_reentry_before_credit(self):
        with ClayVerse(self.root) as cv:
            result = cv.run_process_effect(
                "echo.1", ["/bin/echo", "ok"],
                verifier=lambda p: p.returncode == 0 and p.stdout.strip() == "ok",
            )
            self.assertTrue(result.verified)
            types = [row[0] for row in cv.db.execute(
                "SELECT event_type FROM events WHERE object_id IN ('echo.1','credit:echo.1') ORDER BY seq"
            )]
            self.assertEqual(types, [
                "EFFECT_REQUEST", "EFFECT_OUTCOME", "EFFECT_VERIFIED", "CAUSAL_REENTRY", "CREDIT_UPDATE"
            ])

    def test_pending_effect_after_restart_fails_closed_instead_of_reexecuting(self):
        # Regression discriminator for the crash window discovered after the
        # first green run. This is regression-only, not a second unusual experiment.
        request = {"kind": "process", "argv": ["/bin/echo", "once"], "timeout": 5.0}
        from clayverse import canonical_json
        import hashlib
        request_hash = hashlib.sha256(canonical_json(request).encode()).hexdigest()
        with ClayVerse(self.root) as cv:
            cv.db.execute("BEGIN IMMEDIATE")
            epoch = cv._next_epoch()
            cv._append_event("EFFECT_REQUEST", "crash-window", request, epoch=epoch)
            cv.db.execute(
                "INSERT INTO effects(effect_id,request_hash,request_json,status,result_json,verified,request_epoch,terminal_epoch) "
                "VALUES(?,?,?,?,NULL,0,?,NULL)",
                ("crash-window", request_hash, canonical_json(request), "PENDING", epoch),
            )
            cv.db.execute("COMMIT")
        with ClayVerse(self.root) as cv:
            before = cv.epoch()
            with self.assertRaisesRegex(RuntimeError, "EFFECT_RECOVERY_REQUIRED"):
                cv.run_process_effect(
                    "crash-window", ["/bin/echo", "once"], verifier=lambda p: True
                )
            self.assertEqual(cv.epoch(), before)

    def test_manager_tick_keeps_integrity_contract_live(self):
        with ClayVerse(self.root) as cv:
            cv.open_session("A")
            snap = cv.manager_tick()
            self.assertEqual(snap["identity"], CLAYVERSE_ID)
            self.assertTrue(snap["event_head"])

    def test_failed_effect_verification_gets_no_credit(self):
        with ClayVerse(self.root) as cv:
            with self.assertRaisesRegex(RuntimeError, "EFFECT_VERIFICATION_FAILED"):
                cv.run_process_effect(
                    "echo.bad", ["/bin/echo", "wrong"], verifier=lambda p: False
                )
            credit = cv.db.execute(
                "SELECT 1 FROM objects WHERE object_id='credit:echo.bad'"
            ).fetchone()
            self.assertIsNone(credit)

    def test_unusual_effect_id_collision_fails_closed_without_second_execution(self):
        # Exactly one unusual experiment for this go: identical authority key,
        # conflicting process intent. The second intent must never execute.
        marker = self.root / "should-not-exist"
        with ClayVerse(self.root) as cv:
            first = cv.run_process_effect(
                "collision", ["/bin/echo", "first"],
                verifier=lambda p: p.stdout.strip() == "first"
            )
            self.assertTrue(first.verified)
            before = cv.epoch()
            with self.assertRaisesRegex(RuntimeError, "EFFECT_ID_CONFLICT"):
                cv.run_process_effect(
                    "collision", [sys.executable, "-c", f"open({str(marker)!r},'w').write('BAD')"],
                    verifier=lambda p: True,
                )
            self.assertFalse(marker.exists())
            self.assertEqual(cv.epoch(), before)

    def test_builtin_selftest(self):
        report = selftest(self.root)
        self.assertTrue(report["ok"])
        self.assertEqual(report["identity"], CLAYVERSE_ID)


if __name__ == "__main__":
    unittest.main()
