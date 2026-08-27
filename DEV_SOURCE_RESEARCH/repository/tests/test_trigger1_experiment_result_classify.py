from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_experiment_result_classify as classify


class Trigger1ExperimentResultClassificationTests(unittest.TestCase):
    def gate(self, *, mechanism=True, scientific=True, owner=True, schema=None):
        return {
            "schema": schema or classify.PROMOTION_GATE_SCHEMA,
            "mechanism_runtime_vector_credit_candidate": mechanism,
            "scientifically_independent_vector_candidate": scientific,
            "owner_trigger1_goal_credit_candidate": owner,
        }

    def test_blocked_runtime_is_blocked(self):
        self.assertEqual(
            "BLOCKED",
            classify.classify({"status": "BLOCKED_LOCAL_MIDLAYER_FASTPATH"}, self.gate(), 3),
        )

    def test_missing_result_is_blocked(self):
        self.assertEqual("BLOCKED", classify.classify({}, self.gate(), None))

    def test_nonzero_process_exit_is_fail(self):
        self.assertEqual("FAIL", classify.classify({"status": "PASS"}, self.gate(), 2))

    def test_scientific_negative_is_fail(self):
        self.assertEqual("FAIL", classify.classify({"status": "SCIENTIFIC_NEGATIVE"}, self.gate(), 0))

    def test_mechanism_only_candidate_is_not_full_experiment_pass(self):
        gate = self.gate(mechanism=True, scientific=False, owner=False)
        self.assertEqual("FAIL", classify.classify({"status": "PASS"}, gate, 0))
        self.assertEqual(
            {
                "mechanism_runtime_vector_credit_candidate": True,
                "scientifically_independent_vector_candidate": False,
                "owner_trigger1_goal_credit_candidate": False,
            },
            classify.evidence_summary(gate),
        )

    def test_stale_or_unknown_gate_schema_fails_closed(self):
        gate = self.gate(schema="CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v2")
        self.assertEqual("FAIL", classify.classify({"status": "PASS"}, gate, 0))

    def test_full_current_goal_gate_can_pass(self):
        self.assertEqual("PASS", classify.classify({"status": "PASS"}, self.gate(), 0))


if __name__ == "__main__":
    unittest.main()
