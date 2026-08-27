import unittest

from tools import trigger2_dynamic_codebook_binding_template_generator_v3 as g


class Trigger2DynamicBindingV3Test(unittest.TestCase):
    def test_full_factorial_passes(self):
        rows = g.build_rows()
        report = g.validate(rows)
        self.assertEqual(len(rows), 864)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["training_eligible_rows"], 0)
        self.assertEqual(report["hard_negative_rows"], 0)
        self.assertTrue(
            all(abs(v) < 1e-12 for v in report["mutual_information_bits"].values())
        )

    def test_polarity_semantics_are_explicit(self):
        self.assertEqual(g.effective_class("ALLOW", "DIRECT"), "ALLOW")
        self.assertEqual(g.effective_class("ALLOW", "INVERTED"), "DENY")
        self.assertEqual(g.effective_class("DENY", "INVERTED"), "ALLOW")
        self.assertEqual(g.effective_class("ABSTAIN", "INVERTED"), "ABSTAIN")

    def test_target_tamper_fails_closed(self):
        rows = g.build_rows()
        rows[0]["target_template"] = (
            "ATOM_C" if rows[0]["target_template"] != "ATOM_C" else "ATOM_A"
        )
        with self.assertRaises(AssertionError):
            g.validate(rows)

    def test_prompt_mapping_drift_fails_closed_even_with_fresh_digest(self):
        rows = g.build_rows()
        row = rows[0]
        row["model_visible_prompt_template"] = row[
            "model_visible_prompt_template"
        ].replace("ALLOW -> ATOM_A", "ALLOW -> ATOM_C")
        row["model_visible_render_sha256"] = g.visible_render_sha256(
            row["model_visible_prompt_template"], row["target_template"]
        )
        with self.assertRaises(AssertionError):
            g.validate(rows)

    def test_private_metadata_leak_fails_closed(self):
        rows = g.build_rows()
        row = rows[0]
        row["model_visible_prompt_template"] += "\nmaterializer_private"
        row["model_visible_render_sha256"] = g.visible_render_sha256(
            row["model_visible_prompt_template"], row["target_template"]
        )
        with self.assertRaises(AssertionError):
            g.validate(rows)

    def test_render_digest_tamper_fails_closed(self):
        rows = g.build_rows()
        rows[0]["model_visible_render_sha256"] = "0" * 64
        with self.assertRaises(AssertionError):
            g.validate(rows)

    def test_missing_polarity_half_fails_closed(self):
        rows = [r for r in g.build_rows() if r["query_polarity"] == "DIRECT"]
        self.assertEqual(len(rows), 432)
        with self.assertRaises(AssertionError):
            g.validate(rows)

    def test_positive_jspace_label_tamper_fails_closed(self):
        rows = g.build_rows()
        rows[0]["positive_jspace_label"] = True
        with self.assertRaises(AssertionError):
            g.validate(rows)


if __name__ == "__main__":
    unittest.main()
