from __future__ import annotations

import unittest

from semantic_maintenance_economics_s1 import (
    MaintenanceEconomics,
    decide_maintenance,
    spm_local_update_break_even,
)


class MaintenanceEconomicsS1Tests(unittest.TestCase):
    def fixture(self, **overrides):
        base = dict(
            expected_reads=10000,
            expected_updates=3,
            online_query_us=1000.0,
            compiled_query_us=10.0,
            full_build_us=110248.0,
            full_refresh_us=109093.0,
            spm_build_us=314721.0,
            spm_local_refresh_us=23942.0,
            local_impact_probability=1.0,
            online_quality=1.0,
            full_quality=1.0,
            spm_quality=1.0,
            safety_factor=1.0,
        )
        base.update(overrides)
        return MaintenanceEconomics(**base)

    def test_measured_spm_fixture_break_even_is_about_2_4_local_updates(self):
        b = spm_local_update_break_even(
            full_build_us=110248.0,
            spm_build_us=314721.0,
            full_refresh_us=109093.0,
            spm_local_refresh_us=23942.0,
        )
        self.assertIsNotNone(b)
        self.assertAlmostEqual(b, 2.4013, places=4)

    def test_three_local_updates_select_spm(self):
        d = decide_maintenance(self.fixture(expected_updates=3))
        self.assertEqual(d.mode, "SPM_S1")
        self.assertGreater(d.expected_savings_vs_full_us, 0)

    def test_two_local_updates_keep_simpler_full_generation(self):
        d = decide_maintenance(self.fixture(expected_updates=2))
        self.assertEqual(d.mode, "FULL_GENERATION")

    def test_unknown_locality_fails_conservatively_away_from_spm(self):
        d = decide_maintenance(self.fixture(local_impact_probability=None))
        self.assertEqual(d.mode, "FULL_GENERATION")
        self.assertIsNone(d.spm_total_us)

    def test_low_locality_can_make_full_generation_cheaper(self):
        d = decide_maintenance(self.fixture(expected_updates=10, local_impact_probability=0.1))
        self.assertEqual(d.mode, "FULL_GENERATION")

    def test_spm_quality_regression_disqualifies_spm(self):
        d = decide_maintenance(self.fixture(spm_quality=0.99))
        self.assertNotEqual(d.mode, "SPM_S1")

    def test_full_and_spm_quality_regression_selects_online(self):
        d = decide_maintenance(self.fixture(full_quality=0.99, spm_quality=0.99))
        self.assertEqual(d.mode, "ONLINE")

    def test_short_read_lifetime_can_select_online(self):
        d = decide_maintenance(self.fixture(expected_reads=1, expected_updates=0))
        self.assertEqual(d.mode, "ONLINE")

    def test_no_per_update_saving_has_no_spm_break_even(self):
        b = spm_local_update_break_even(
            full_build_us=100.0,
            spm_build_us=200.0,
            full_refresh_us=10.0,
            spm_local_refresh_us=10.0,
        )
        self.assertIsNone(b)

    def test_invalid_locality_rejected(self):
        with self.assertRaises(ValueError):
            decide_maintenance(self.fixture(local_impact_probability=1.1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
