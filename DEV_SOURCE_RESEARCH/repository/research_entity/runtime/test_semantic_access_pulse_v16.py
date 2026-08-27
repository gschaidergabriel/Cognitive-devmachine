from __future__ import annotations

import unittest

from semantic_access_pulse_v12 import PulseInvariantError
from semantic_access_pulse_v16 import SegmentedPulseProjectionV16
from test_semantic_access_pulse_v12 import SegmentedPulseTests, VERSIONS, seed_ids, paths_for


class SegmentedPulseV16Tests(SegmentedPulseTests):
    """Run all provisional segmented-Pulse guards against the V16 successor."""

    def make(self):
        x = SegmentedPulseProjectionV16()
        x.bootstrap(
            event_id="boot",
            source_epoch=1,
            graph_epoch=1,
            seeds=seed_ids(),
            recompute_seed=paths_for,
        )
        return x

    def test_deep_audit_accepts_clean_generation_and_detects_physical_corruption(self):
        x = self.make()
        clean = x.audit_current_generation()
        self.assertTrue(clean["pass"])
        self.assertEqual(clean["segments_audited"], 20)
        self.assertEqual(clean["paths_audited"], 40)

        head = x.head_basis()
        self.assertIsNotNone(head)
        generation_id = head[2]
        segment_id = x.con.execute(
            "SELECT segment_id FROM access_generation_seed WHERE generation_id=? ORDER BY seed_id LIMIT 1",
            (generation_id,),
        ).fetchone()[0]
        x.con.execute(
            "UPDATE access_segment_path SET path_weight=path_weight+0.125 WHERE segment_id=? AND path_rank=1",
            (segment_id,),
        )
        x.con.commit()
        with self.assertRaises(PulseInvariantError):
            x.audit_current_generation()
        x.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
