import json
import unittest

from tools import trigger2_cognitive_process_executable_transition_generator_v2 as g


class Trigger2ExecutableTransitionGeneratorV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = g.rows()
        cls.report = g.report(cls.rows)

    def row(self, case_id, variant="N10_A"):
        return next(r for r in self.rows if r["case_id"] == case_id and r["variant_evaluator_only"]["variant_id"] == variant)

    def target(self, case_id, variant="N10_A"):
        return json.loads(self.row(case_id, variant)["target"])

    def test_small_pilot_spans_all_model_executed_process_classes_without_deterministic_targets(self):
        self.assertEqual(len(self.rows), len(g.CASES) * len(g.VARIANTS))
        classes = {r["implementation_class_evaluator_only"] for r in self.rows}
        self.assertEqual(classes, {"SIMULATE_ON_GRID", "EXTERNAL_STRONG_MODEL_BRIDGE", "OPTIONAL_CAUSAL_RESEARCH"})
        self.assertNotIn("DETERMINISTIC_BOUNDARY", classes)
        self.assertNotIn("STORE_IN_DB", classes)

    def test_targets_are_concrete_packets_not_meta_rule_narration(self):
        self.assertFalse(self.report["contains_meta_rule_targets"])
        for row in self.rows:
            target = json.loads(row["target"])
            self.assertEqual(target["schema"], g.TARGET_SCHEMA)
            self.assertIsInstance(target["result_packet"], dict)
            self.assertIsInstance(target["state_after_candidate"], dict)
            self.assertNotIn("rule", target)
            self.assertNotIn("emit", target)
            self.assertNotIn("rule", target["result_packet"])
            self.assertNotIn("emit", target["result_packet"])

    def test_result_payload_digest_and_inline_reference_are_machine_adjudicable(self):
        for row in self.rows:
            packet = json.loads(row["target"])["result_packet"]
            expected = g.dg(packet["result_payload_inline"])
            self.assertEqual(packet["result_digest"], expected)
            self.assertEqual(packet["result_payload_ref"], f"inline-sha256:{expected}")
            self.assertEqual(row["oracle_evaluator_only"]["result_payload_digest_recomputed"], expected)

    def test_claycode_roundtrip_passes_for_every_target_packet(self):
        self.assertTrue(self.report["all_claycode_roundtrips_passed"])
        for row in self.rows:
            self.assertEqual(row["claycode_roundtrip_evaluator_only"]["status"], "PASS_SOURCE_COMPONENT")
            self.assertEqual(len(row["claycode_roundtrip_evaluator_only"]["packet_digest"]), 64)

    def test_runtime_n_and_executor_do_not_change_semantic_core(self):
        for case_id, result in self.report["nuisance_invariance"].items():
            self.assertEqual(result["variants"], 2, case_id)
            self.assertTrue(result["semantic_core_identical"], case_id)

    def test_hyperposition_does_not_promote_majority_to_truth(self):
        target = self.target("HP_UNRESOLVED_MAJORITY")
        payload = target["result_packet"]["result_payload_inline"]
        self.assertEqual(payload["alternative_set"], ["h1", "h2"])
        self.assertEqual(payload["resolution"], "UNRESOLVED")
        self.assertFalse(payload["majority_is_truth"])
        self.assertEqual(target["state_after_candidate"]["live_alternatives"], ["h1", "h2"])

    def test_stale_observation_preserves_unknown_and_forbids_metadata_relabel(self):
        target = self.target("STALE_OBSERVATION_CRITIQUE")
        packet = target["result_packet"]
        self.assertEqual(packet["unknowns"][0]["status"], "UNKNOWN")
        revision = packet["result_payload_inline"]["revision_request"]
        self.assertFalse(revision["relabel_old_observation"])
        self.assertTrue(target["state_after_candidate"]["old_observation_preserved"])

    def test_claude_return_separates_tool_evidence_from_model_assertion(self):
        target = self.target("CLAUDE_RETURN_EVIDENCE_SPLIT")
        payload = target["result_packet"]["result_payload_inline"]
        self.assertEqual(payload["evidence_candidates"][0]["class"], "TOOL_OBSERVATION")
        self.assertEqual(payload["model_assertions"][0]["status"], "UNVERIFIED")
        self.assertEqual(target["state_after_candidate"]["deployment_succeeded"], "UNKNOWN")

    def test_memory_target_proposes_but_does_not_commit(self):
        target = self.target("MEMORY_PROPOSAL_NO_COMMIT")
        packet = target["result_packet"]
        self.assertEqual(packet["db_write_proposals"][0]["status"], "PROPOSED_ONLY")
        self.assertEqual(packet["result_payload_inline"]["commit_status"], "NOT_COMMITTED")
        self.assertTrue(target["state_after_candidate"]["canonical_memory_unchanged"])

    def test_effect_target_proposes_but_does_not_execute(self):
        target = self.target("EFFECT_PROPOSAL_NO_EXECUTION")
        packet = target["result_packet"]
        self.assertEqual(packet["result_class"], "CANDIDATE")
        self.assertEqual(packet["effect_request_candidates"][0]["status"], "CANDIDATE_ONLY")
        self.assertFalse(packet["result_payload_inline"]["executed"])
        self.assertEqual(packet["result_payload_inline"]["effect_receipt"], "NONE")

    def test_unknown_effect_outcome_never_blind_replays(self):
        target = self.target("UNKNOWN_EFFECT_OUTCOME_NO_REPLAY")
        packet = target["result_packet"]
        self.assertEqual(packet["unknowns"][0]["status"], "UNKNOWN")
        self.assertFalse(packet["result_payload_inline"]["blind_replay_allowed"])
        self.assertTrue(target["state_after_candidate"]["verification_required"])

    def test_jspace_measurement_does_not_upgrade_to_hidden_state_causality(self):
        target = self.target("JSPACE_MEASUREMENT_NO_CAUSAL_UPGRADE")
        packet = target["result_packet"]
        self.assertEqual(packet["result_class"], "MEASUREMENT")
        payload = packet["result_payload_inline"]
        self.assertEqual(payload["credit_scope"], "MEASUREMENT_ONLY_NO_CAUSAL_PROMOTION")
        self.assertEqual(payload["hidden_activation_access"], "UNKNOWN_NOT_EXPOSED")
        self.assertFalse(target["state_after_candidate"]["causal_promotion"])

    def test_deterministic_authorities_are_oracle_only(self):
        for row in self.rows:
            oracle = row["oracle_evaluator_only"]
            self.assertEqual(oracle["canonical_state_commit"], "NOT_PERFORMED_BY_MODEL")
            self.assertEqual(oracle["capability_grant"], "NOT_PERFORMED_BY_MODEL")
            self.assertEqual(oracle["coordinator_or_executor_lease_grant"], "NOT_PERFORMED_BY_MODEL")
            self.assertEqual(oracle["effect_execution"], "NOT_PERFORMED_BY_MODEL")

    def test_pilot_remains_closed_to_training_admission(self):
        for row in self.rows:
            self.assertFalse(row["training_eligible"])
            self.assertEqual(row["positive_training_admission"], "CLOSED")
            self.assertEqual(row["accepted_dataset_tokens"], 0)
        self.assertEqual(self.report["credit"]["positive_training_rows_admitted"], 0)
        self.assertEqual(self.report["credit"]["accepted_dataset_tokens"], 0)
        self.assertEqual(self.report["credit"]["training"], 0)


if __name__ == "__main__":
    unittest.main()
