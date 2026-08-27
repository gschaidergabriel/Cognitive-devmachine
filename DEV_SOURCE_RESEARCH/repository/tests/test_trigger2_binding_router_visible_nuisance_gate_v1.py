from __future__ import annotations

import copy
import unittest

from tools import trigger2_binding_router_blueprint_generator_v2 as gen
from tools import trigger2_binding_router_visible_nuisance_gate_v1 as gate


class Trigger2BindingRouterVisibleNuisanceGateTests(unittest.TestCase):
    def test_current_v22_blueprint_passes_model_visible_ablation_gate(self):
        rows = list(gen.rows())
        audit = gate.analyze(rows)
        self.assertEqual(11664, len(rows))
        self.assertTrue(audit["pass"], audit["failures"])
        self.assertEqual(3888, audit["ablated_prompt_groups"])
        self.assertAlmostEqual(1.0 / 3.0, audit["semantic_ablated_lookup_accuracy"], places=12)
        self.assertAlmostEqual(1.0 / 3.0, audit["episode_local_chance_accuracy"], places=12)
        self.assertTrue(audit["model_visible_only"])
        self.assertFalse(audit["hidden_audit_metadata_used"])

    def test_visible_target_leak_is_rejected(self):
        all_rows = list(gen.rows())
        groups = {}
        for row in all_rows:
            key = gate.ablate_semantic_scene(row["prompt"])
            groups.setdefault(key, []).append(row)
        trio = next(group for group in groups.values() if len(group) == 3)
        bad = copy.deepcopy(trio)
        for row in bad:
            row["prompt"] = row["prompt"].replace(
                "END_QUERY\n", f"END_QUERY\nVISIBLE_NUISANCE_HINT={row['target']}\n", 1
            )
        audit = gate.analyze(bad)
        self.assertFalse(audit["pass"])
        self.assertGreater(audit["semantic_ablated_lookup_accuracy"], 1.0 / 3.0)
        self.assertTrue(any("MODEL_VISIBLE_NUISANCE_DECODER_ABOVE_CHANCE" in x for x in audit["failures"]))

    def test_hidden_audit_metadata_cannot_change_gate_result(self):
        all_rows = list(gen.rows())
        groups = {}
        for row in all_rows:
            key = gate.ablate_semantic_scene(row["prompt"])
            groups.setdefault(key, []).append(row)
        trio = copy.deepcopy(next(group for group in groups.values() if len(group) == 3))
        baseline = gate.analyze(trio)
        for i, row in enumerate(trio):
            row["base_state_class"] = f"HIDDEN_LIE_{i}"
            row["audit_semantic_class"] = f"HIDDEN_LIE_{2-i}"
            row["s3_permutation_id"] = f"HIDDEN_LIE_{i}"
        mutated = gate.analyze(trio)
        self.assertEqual(baseline["pass"], mutated["pass"])
        self.assertEqual(
            baseline["semantic_ablated_lookup_accuracy"],
            mutated["semantic_ablated_lookup_accuracy"],
        )

    def test_missing_semantic_record_fails_closed(self):
        row = copy.deepcopy(next(gen.rows()))
        row["prompt"] = row["prompt"].replace("R3:", "RX:", 1)
        audit = gate.analyze([row])
        self.assertFalse(audit["pass"])
        self.assertTrue(any(x.startswith("ROW_PARSE_FAILURE:0") for x in audit["failures"]))


if __name__ == "__main__":
    unittest.main()
