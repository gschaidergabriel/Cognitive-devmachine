from __future__ import annotations

import copy
import unittest

from tools import trigger2_context_binding_generator_v2 as gen


class Trigger2ContextBindingGeneratorV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = gen.generate_rows()

    def test_full_factorial_passes(self):
        audit = gen.validate_rows(self.rows)
        self.assertTrue(audit["pass"], audit["failures"])
        self.assertEqual(2592, audit["rows_total"])
        self.assertEqual("ALL_THREE_CLASSES_PER_SIGNATURE", audit["nuisance_semantic_class_support"])
        self.assertEqual("ALL_THREE_SLOTS_PER_SIGNATURE", audit["nuisance_target_slot_support"])

    def test_unknown_stays_abstain_under_both_polarities(self):
        self.assertEqual("ABSTAIN", gen.target_class("UNKNOWN", "DIRECT"))
        self.assertEqual("ABSTAIN", gen.target_class("UNKNOWN", "INVERTED"))

    def test_known_states_invert_exactly(self):
        self.assertEqual("ALLOW", gen.target_class("SUPPORTS", "DIRECT"))
        self.assertEqual("DENY", gen.target_class("SUPPORTS", "INVERTED"))
        self.assertEqual("DENY", gen.target_class("CONTRADICTS", "DIRECT"))
        self.assertEqual("ALLOW", gen.target_class("CONTRADICTS", "INVERTED"))

    def test_every_fixed_scenario_mapping_has_all_six_display_orders_same_target(self):
        groups = {}
        for row in self.rows:
            key = (row["scenario_id"], row["query_polarity"], row["s3_permutation_id"])
            groups.setdefault(key, []).append(row)
        self.assertTrue(groups)
        for group in groups.values():
            self.assertEqual(6, len(group))
            self.assertEqual(6, len({r["display_order_id"] for r in group}))
            self.assertEqual(1, len({r["target"] for r in group}))

    def test_nuisance_only_signature_is_chance_complete(self):
        classes = {}
        slots = {}
        for row in self.rows:
            key = (
                row["template_id"],
                row["lexical_variant_index"],
                row["query_polarity"],
                row["s3_permutation_id"],
                row["display_order_id"],
            )
            classes.setdefault(key, set()).add(row["audit_target_semantic_class"])
            slots.setdefault(key, set()).add(row["target"])
        self.assertTrue(all(v == set(gen.CLASSES) for v in classes.values()))
        self.assertTrue(all(v == set(gen.SLOTS) for v in slots.values()))

    def test_builtin_generator_materializes_train_only(self):
        self.assertEqual({"TRAIN"}, {r["split"] for r in self.rows})
        self.assertNotIn("VALIDATION", {r["split"] for r in self.rows})
        self.assertNotIn("HOLDOUT", {r["split"] for r in self.rows})

    def test_target_tamper_fails(self):
        bad = copy.deepcopy(self.rows)
        bad[0]["target"] = next(x for x in gen.SLOTS if x != bad[0]["target"])
        audit = gen.validate_rows(bad)
        self.assertFalse(audit["pass"])
        self.assertTrue(any(x.startswith("TARGET_NOT_FROM_MAPPING") for x in audit["failures"]))

    def test_class_label_leak_fails(self):
        bad = copy.deepcopy(self.rows)
        bad[0]["prompt"] += "\nHint: ALLOW"
        audit = gen.validate_rows(bad)
        self.assertFalse(audit["pass"])
        self.assertTrue(any(x.startswith("CLASS_LABEL_LEAK") for x in audit["failures"]))

    def test_model_visible_projection_is_explicit(self):
        for row in self.rows[:20]:
            self.assertEqual(["prompt"], row["model_visible_fields"])
            self.assertEqual("target", row["supervision_field"])
            self.assertTrue(row["audit_metadata_must_not_enter_model_context"])
            self.assertFalse(row["training_eligible"])


if __name__ == "__main__":
    unittest.main()
