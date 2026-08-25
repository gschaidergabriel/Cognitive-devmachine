import json
import unittest
from pathlib import Path

from tools import entityos_hcu_trainingtrace_candidate_gate_v1 as row_gate
from tools import trigger2_trainingtrace_family_split_linter_v1 as split_linter

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "research_entity/global/j-space/research/trigger2_claude_negative_evidence_seed_v1.jsonl"


def load_rows():
    return [json.loads(line) for line in SEED.read_text(encoding="utf-8").splitlines() if line.strip()]


class Trigger2ClaudeNegativeEvidenceSeedTests(unittest.TestCase):
    def test_seed_has_expected_size_and_candidate_gate_passes(self):
        rows = load_rows()
        self.assertEqual(len(rows), 10)
        failures = []
        for i, row in enumerate(rows):
            result = row_gate.adjudicate(row)
            if not result["candidate_admission_pass"]:
                failures.append((i, result["failures"]))
        self.assertEqual(failures, [])

    def test_family_and_provenance_split_gate_passes(self):
        result = split_linter.adjudicate(load_rows())
        self.assertTrue(result["dataset_split_pass"], result)
        self.assertEqual(result["rows_row_gate_fail"], 0)
        self.assertEqual(result["accepted_dataset_tokens_minted"], 0)
        self.assertFalse(result["canonical_dataset_write_performed"])
        self.assertFalse(result["training_credit_minted"])

    def test_no_positive_jspace_target_or_authority_grant(self):
        forbidden_positive_targets = {
            "JSPACE_VECTOR_EFFECT",
            "ABSTRACT_STATE_CONTROL",
            "HIDDEN_STATE_COORDINATE",
        }
        for row in load_rows():
            self.assertNotIn(row["target_type"], forbidden_positive_targets)
            self.assertFalse(row["canonical_truth_allowed"])
            self.assertFalse(row["direct_effect_authority"])
            self.assertFalse(row["selected_using_holdout"])

    def test_t01_family_contains_transport_and_matched_control_negatives(self):
        rows = [r for r in load_rows() if r["family_id"] == "CLAUDE_T01_TRANSPORT_BEHAVIOR_F01"]
        self.assertEqual(len(rows), 3)
        target_types = {r["target_type"] for r in rows}
        self.assertIn("JSPACE_PROMOTION_REJECTION", target_types)
        self.assertIn("MATCHED_CONTROL_REJECTION", target_types)

    def test_t06_family_covers_live_gate_failure_modes(self):
        rows = [r for r in load_rows() if r["family_id"] == "CLAUDE_T06_PROMOTION_GATE_F01"]
        self.assertEqual(len(rows), 4)
        target_types = {r["target_type"] for r in rows}
        self.assertEqual(
            target_types,
            {
                "EVIDENCE_GATE_REJECTION",
                "RECEIPT_INTEGRITY_REJECTION",
                "CONTROL_FAMILY_COMPLETENESS_REJECTION",
                "LIVE_GATE_TOPOLOGY_REJECTION",
            },
        )


if __name__ == "__main__":
    unittest.main()
