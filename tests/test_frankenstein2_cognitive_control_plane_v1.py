from pathlib import Path
import tempfile
import unittest

from tools.frankenstein2_cognitive_control_plane_v1 import (
    CognitiveControlPlane,
    ControlError,
    ControlMode,
)


class ControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "u.db"
        self.p = CognitiveControlPlane(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_defaults_snapshot(self):
        s = self.p.snapshot()
        self.assertEqual(s.control_epoch, 0)
        self.assertEqual(s.mode("grid.orientation.mode"), ControlMode.ON)
        self.assertEqual(s.int("delegation.max_parallel"), 4)
        self.assertTrue(s.snapshot_digest)

    def test_atomic_batch_and_restart(self):
        s0 = self.p.snapshot()
        patch = self.p.build_patch(
            patch_id="p1",
            writer="human",
            writer_kind="HUMAN",
            reason="test",
            changes={
                "grid.hypothesis.gain": 1.7,
                "grid.microlab.mode": "COMPUTE_OFF",
            },
            base=s0,
        )
        r = self.p.apply_patch(patch)
        self.assertEqual(r.control_epoch, 1)
        s1 = self.p.snapshot()
        self.assertAlmostEqual(s1.float("grid.hypothesis.gain"), 1.7)
        self.assertEqual(s1.mode("grid.microlab.mode"), ControlMode.COMPUTE_OFF)
        self.assertNotEqual(s0.snapshot_digest, s1.snapshot_digest)

        reopened = CognitiveControlPlane(self.db)
        self.assertEqual(reopened.snapshot().snapshot_digest, s1.snapshot_digest)

    def test_stale_snapshot_rejected(self):
        s0 = self.p.snapshot()
        a = self.p.build_patch(
            patch_id="a",
            writer="h",
            writer_kind="HUMAN",
            reason="a",
            changes={"voice.initiative_gain": 0.5},
            base=s0,
        )
        b = self.p.build_patch(
            patch_id="b",
            writer="h",
            writer_kind="HUMAN",
            reason="b",
            changes={"memory.max_items": 32},
            base=s0,
        )
        self.p.apply_patch(a)
        with self.assertRaisesRegex(ControlError, "STALE_CONTROL_SNAPSHOT"):
            self.p.apply_patch(b)
        self.assertEqual(self.p.snapshot().int("memory.max_items"), 64)

    def test_invalid_batch_is_atomic(self):
        s0 = self.p.snapshot()
        patch = self.p.build_patch(
            patch_id="bad",
            writer="h",
            writer_kind="HUMAN",
            reason="bad",
            changes={
                "voice.initiative_gain": 0.5,
                "grid.world.mode": "NOT_A_MODE",
            },
            base=s0,
        )
        with self.assertRaisesRegex(ControlError, "INVALID_MODE"):
            self.p.apply_patch(patch)
        self.assertEqual(self.p.snapshot().snapshot_digest, s0.snapshot_digest)

    def test_human_pin_blocks_auto(self):
        s0 = self.p.snapshot()
        human = self.p.build_patch(
            patch_id="hpin",
            writer="human",
            writer_kind="HUMAN",
            reason="pin",
            changes={"grid.counterhypothesis_pressure": 0.9},
            base=s0,
            pin_seconds=60,
        )
        self.p.apply_patch(human)
        s1 = self.p.snapshot()
        auto = self.p.build_patch(
            patch_id="auto",
            writer="homeostat",
            writer_kind="AUTO",
            reason="auto",
            changes={"grid.counterhypothesis_pressure": 0.4},
            base=s1,
        )
        with self.assertRaisesRegex(ControlError, "HUMAN_PIN_ACTIVE"):
            self.p.apply_patch(auto)
        self.assertAlmostEqual(
            self.p.snapshot().float("grid.counterhypothesis_pressure"), 0.9
        )

    def test_idempotent_patch_replay(self):
        s0 = self.p.snapshot()
        patch = self.p.build_patch(
            patch_id="same",
            writer="human",
            writer_kind="HUMAN",
            reason="same",
            changes={"world.physics.gain": 1.4},
            base=s0,
        )
        r1 = self.p.apply_patch(patch)
        r2 = self.p.apply_patch(patch)
        self.assertEqual(r1.control_epoch, r2.control_epoch)
        self.assertEqual(r2.reason, "IDEMPOTENT_REPLAY_ALREADY_COMMITTED")
        self.assertEqual(len(self.p.revision_rows()), 1)


if __name__ == "__main__":
    unittest.main()
