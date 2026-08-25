from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import run_restart_resize_db_boundary_smoke_v1 as mod


class RestartResizeDbBoundarySmokeTests(unittest.TestCase):
    def setUp(self):
        self.receipt = mod.run_smoke()
        self.checks = self.receipt["checks"]

    def test_smoke_passes_all_declared_checks(self):
        self.assertEqual(self.receipt["status"], "PASS_DB_SIMULATION_BOUNDARY_COMPONENT_ONLY")
        self.assertEqual(self.receipt["declared_boundary_schema"], "DB_VS_SIMULATION_BOUNDARY/v1")
        self.assertEqual(self.receipt["counts"]["passed"], self.receipt["counts"]["total"])

    def test_restart_resize_preserves_s0(self):
        self.assertTrue(self.checks["s0_stable_across_restart_and_resize"])
        self.assertTrue(self.checks["post_admission_s0_stable_across_second_resize"])

    def test_s1_rebuild_and_s2_loss(self):
        self.assertTrue(self.checks["s1_rebuilt_from_s0"])
        self.assertTrue(self.checks["s2_loss_tolerated"])

    def test_direct_model_write_rejected(self):
        self.assertTrue(self.checks["direct_model_to_s0_rejected"])
        self.assertTrue(self.checks["negative_paths_do_not_mutate_s0"])

    def test_stale_generation_and_cache_recovery_rejected(self):
        self.assertTrue(self.checks["stale_generation_write_rejected"])
        self.assertTrue(self.checks["s1_cache_recovery_authority_rejected"])

    def test_direct_effect_rejected(self):
        self.assertTrue(self.checks["direct_effect_rejected"])

    def test_claude_bridge_is_candidate_only(self):
        self.assertTrue(self.checks["claude_reentry_candidate_only"])
        self.assertEqual(self.receipt["credit"]["claude_code_runtime"], 0)

    def test_typed_write_and_variable_process_placement(self):
        self.assertTrue(self.checks["typed_durable_proposal_admitted_once"])
        self.assertTrue(self.checks["duplicate_proposal_rejected"])
        self.assertTrue(self.checks["process_identity_not_fixed_to_module_or_n"])
        self.assertEqual(self.receipt["credit"]["whole_product_pass"], False)


if __name__ == "__main__":
    unittest.main()
