from __future__ import annotations

import unittest

from semantic_maintenance_economics_s1 import MaintenanceEconomics
from semantic_maintenance_horizon_estimator_s1 import (
    MaintenanceLifetime,
    decide_maintenance_from_pulse_history,
    estimate_maintenance_horizon,
)


class MaintenanceHorizonEstimatorS1Tests(unittest.TestCase):
    def economics(self):
        return MaintenanceEconomics(
            expected_reads=0,
            expected_updates=0,
            online_query_us=1000.0,
            compiled_query_us=10.0,
            full_build_us=110248.0,
            full_refresh_us=109093.0,
            spm_build_us=314721.0,
            spm_local_refresh_us=23942.0,
            local_impact_probability=None,
            online_quality=1.0,
            full_quality=1.0,
            spm_quality=1.0,
            safety_factor=1.0,
        )

    def test_sparse_history_disables_spm(self):
        samples=[MaintenanceLifetime(i,5000,4,4) for i in range(4)]
        est,decision=decide_maintenance_from_pulse_history(self.economics(),samples)
        self.assertEqual(est.status,"INSUFFICIENT_HISTORY")
        self.assertIsNone(est.local_impact_probability_lower_bound)
        self.assertNotEqual(decision.mode,"SPM_S1")

    def test_stable_local_history_can_select_spm(self):
        samples=[MaintenanceLifetime(i,5000+i*10,4,4) for i in range(8)]
        est,decision=decide_maintenance_from_pulse_history(self.economics(),samples)
        self.assertGreater(est.local_impact_probability_lower_bound,0.7)
        self.assertGreaterEqual(est.expected_updates_lower_bound,4.0)
        self.assertEqual(decision.mode,"SPM_S1")

    def test_recent_locality_collapse_suppresses_spm(self):
        samples=[MaintenanceLifetime(i,5000,4,4) for i in range(5)] + [
            MaintenanceLifetime(5,5000,4,0),
            MaintenanceLifetime(6,5000,4,0),
            MaintenanceLifetime(7,5000,4,0),
        ]
        est,decision=decide_maintenance_from_pulse_history(self.economics(),samples)
        self.assertEqual(est.local_impact_probability_lower_bound,0.0)
        self.assertNotEqual(decision.mode,"SPM_S1")

    def test_no_update_trials_disables_spm(self):
        samples=[MaintenanceLifetime(i,5000,0,0) for i in range(6)]
        est,decision=decide_maintenance_from_pulse_history(self.economics(),samples)
        self.assertEqual(est.status,"NO_UPDATE_LOCALITY_EVIDENCE")
        self.assertIsNone(est.local_impact_probability_lower_bound)
        self.assertNotEqual(decision.mode,"SPM_S1")

    def test_read_churn_shock_propagates_into_maintenance_estimate(self):
        samples=[MaintenanceLifetime(i,6000,4,4) for i in range(5)] + [
            MaintenanceLifetime(5,300,4,4),
            MaintenanceLifetime(6,250,4,4),
            MaintenanceLifetime(7,200,4,4),
        ]
        est=estimate_maintenance_horizon(samples)
        self.assertTrue(est.churn_shock)
        self.assertEqual(est.status,"CHURN_SHOCK_BOUND")
        self.assertLessEqual(est.expected_reads_lower_bound,200.0)

    def test_fault_boundary_is_kept_as_real_sample(self):
        samples=[MaintenanceLifetime(i,5000,4,4) for i in range(5)] + [
            MaintenanceLifetime(5,50,1,0,recovery_or_fault_boundary=True)
        ]
        est=estimate_maintenance_horizon(samples)
        self.assertEqual(est.completed_samples,6)
        self.assertLess(est.expected_reads_lower_bound,5000)

    def test_invalid_local_count_rejected(self):
        with self.assertRaises(ValueError):
            estimate_maintenance_horizon([MaintenanceLifetime(0,1,1,2)]*5)


if __name__=="__main__":
    unittest.main(verbosity=2)
