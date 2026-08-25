from __future__ import annotations

import copy
import json
import unittest

from tools import trigger2_qwen35_checkpoint_candidates_gate_v4 as v4
from tools import trigger2_qwen35_checkpoint_candidates_gate_v5 as gate


class Trigger2Qwen35CheckpointGateV5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(v4.REGISTRY_PATH.read_text(encoding="utf-8"))

    def test_current_registry_passes_but_selection_stays_closed(self):
        result = gate.adjudicate(copy.deepcopy(self.registry))
        self.assertTrue(result["pass"], result["failures"])
        self.assertFalse(result["selection_ready"])
        self.assertIsNone(result["checkpoint_winner"])
        self.assertTrue(all(value == 0 for value in result["credit"].values()))

    def test_bool_int_alias_is_rejected(self):
        arch = copy.deepcopy(gate.EXPECTED_ARCHITECTURE)
        arch["hidden_size"] = True
        self.assertFalse(gate.architecture_typed_exact(arch))

    def test_unexpected_positive_shape_is_rejected(self):
        arch = copy.deepcopy(gate.EXPECTED_ARCHITECTURE)
        arch["num_hidden_layers"] = 25
        self.assertFalse(gate.architecture_typed_exact(arch))

    def test_wrong_text_model_type_is_rejected(self):
        arch = copy.deepcopy(gate.EXPECTED_ARCHITECTURE)
        arch["model_type"] = "qwen3_5"
        self.assertFalse(gate.architecture_typed_exact(arch))

    def test_v4_failures_propagate(self):
        registry = copy.deepcopy(self.registry)
        registry["schema"] = "STALE"
        result = gate.adjudicate(registry)
        self.assertFalse(result["pass"])
        self.assertIn("SCHEMA_MISMATCH", result["failures"])

    def test_v5_self_test_is_green_on_current_bound_registry(self):
        result = gate.self_test(copy.deepcopy(self.registry))
        self.assertTrue(result["pass"], result["checks"])


if __name__ == "__main__":
    unittest.main()
