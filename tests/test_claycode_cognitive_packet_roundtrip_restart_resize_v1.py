from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from claycode_cognitive_packet_roundtrip_restart_resize_v1 import (
    run_roundtrip_smoke,
    validate_protocol_binding,
)


class ClayCodeCognitivePacketRoundtripRestartResizeTests(unittest.TestCase):
    def run_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            return run_roundtrip_smoke(Path(td) / "s0.sqlite3")

    def test_protocol_is_exact_v18_hash_bound(self):
        binding = validate_protocol_binding()
        self.assertTrue(all(binding["checks"].values()))
        self.assertEqual("BASE_D_V18_REWARD_RELATIONS", binding["surface"])

    def test_full_component_roundtrip_gate(self):
        receipt = self.run_receipt()
        self.assertEqual("PASS_CLAYCODE_COGNITIVE_PROTOCOL_COMPONENT_ONLY", receipt["status"])
        self.assertEqual(receipt["counts"]["total"], receipt["counts"]["passed"])

    def test_work_and_result_packets_roundtrip_without_identity_drift(self):
        checks = self.run_receipt()["checks"]
        self.assertTrue(checks["work_packet_json_roundtrip_identity"])
        self.assertTrue(checks["result_packet_json_roundtrip_identity"])
        self.assertTrue(checks["claude_bridge_packet_roundtrip_identity"])

    def test_n_change_preserves_semantic_work_and_process_identity(self):
        checks = self.run_receipt()["checks"]
        self.assertTrue(checks["semantic_core_stable_across_n_change"])
        self.assertTrue(checks["runtime_semantic_identity_stable_across_n_change"])
        self.assertTrue(checks["process_identity_stable_across_n_change"])
        self.assertTrue(checks["physical_binding_reflects_n_change"])

    def test_restart_drops_s1_and_preserves_s0_reference(self):
        checks = self.run_receipt()["checks"]
        self.assertTrue(checks["s1_restart_is_empty"])
        self.assertTrue(checks["state_ref_stable_across_n_change"])
        self.assertTrue(checks["s0_stable_after_restart_resize_candidates"])

    def test_db_and_effect_authority_remain_fail_closed(self):
        checks = self.run_receipt()["checks"]
        self.assertTrue(checks["direct_s0_write_rejected_n1"])
        self.assertTrue(checks["direct_s0_write_rejected_n20"])
        self.assertTrue(checks["candidate_paths_do_not_mutate_s0"])
        self.assertTrue(checks["effect_is_candidate_only"])
        self.assertTrue(checks["result_candidate_only_n1"])
        self.assertTrue(checks["result_candidate_only_n20"])

    def test_claude_bridge_does_not_claim_activation_or_runtime(self):
        receipt = self.run_receipt()
        self.assertTrue(receipt["checks"]["claude_bridge_has_no_activation_or_runtime_claim"])
        self.assertEqual(0, receipt["execution"]["claude_code_calls"])
        self.assertEqual(0, receipt["credit_boundary"]["claude_code_bridge_runtime"])

    def test_broad_runtime_and_training_credit_stay_zero(self):
        credit = self.run_receipt()["credit_boundary"]
        self.assertEqual(0, credit["trained_08b_variable_grid_runtime"])
        self.assertEqual(0, credit["global_jspace_causal_runtime"])
        self.assertEqual(0, credit["whole_entityos_hcu_runtime"])
        self.assertEqual(0, credit["training"])
        self.assertFalse(credit["whole_product_pass"])


if __name__ == "__main__":
    unittest.main()
