from __future__ import annotations

import unittest

from semantic_access_segmented_maintenance_s1 import SegmentedPulseMaintenanceS1
from test_semantic_access_pulse_v16 import SegmentedPulseV16Tests, seed_ids, paths_for


class SegmentedPulseMaintenanceS1Tests(SegmentedPulseV16Tests):
    def make(self):
        x = SegmentedPulseMaintenanceS1()
        x.bootstrap(
            event_id="boot",
            source_epoch=1,
            graph_epoch=1,
            seeds=seed_ids(),
            recompute_seed=paths_for,
        )
        return x

    def test_collision_free_implementation_identity(self):
        x = self.make()
        audit = x.audit_current_generation()
        self.assertEqual(
            audit["implementation"], "UNIFIEDDB_SEGMENTED_PULSE_MAINTENANCE_S1"
        )
        x.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
