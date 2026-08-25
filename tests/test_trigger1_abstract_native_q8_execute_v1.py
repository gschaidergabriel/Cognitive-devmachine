from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from tools import trigger1_abstract_native_q8_execute_v1 as runner
from tools import trigger1_nuisance_residualize as residual


class AbstractNativeExecutorSourceTests(unittest.TestCase):
    def test_nuisance_axis_set_is_exact_and_calibration_only(self):
        specs = runner.nuisance_pairs()
        self.assertEqual({row["axis"] for row in specs}, set(residual.REQUIRED_NUISANCE_FAMILIES))
        counts = {axis: 0 for axis in residual.REQUIRED_NUISANCE_FAMILIES}
        for row in specs:
            counts[row["axis"]] += 1
        self.assertTrue(all(count >= 3 for count in counts.values()), counts)

    def test_six_control_family_is_exact(self):
        self.assertEqual(
            runner.CONTROL_FAMILY,
            (
                "BASELINE",
                "+VECTOR",
                "SIGN_FLIP",
                "NULL_VECTOR",
                "ORTHOGONAL_SAME_NORM",
                "PERMUTED_SAME_NORM",
            ),
        )

    def test_matched_controls_preserve_norm_and_orthogonality(self):
        source = np.arange(1, 65, dtype=np.float64)
        family = runner.control_vectors(source, 3.25, "fixed-test")
        gain = 3.25
        self.assertAlmostEqual(float(np.linalg.norm(family["+VECTOR"])), gain, places=10)
        self.assertAlmostEqual(float(np.linalg.norm(family["SIGN_FLIP"])), gain, places=10)
        self.assertAlmostEqual(float(np.linalg.norm(family["ORTHOGONAL_SAME_NORM"])), gain, places=10)
        self.assertAlmostEqual(float(np.linalg.norm(family["PERMUTED_SAME_NORM"])), gain, places=10)
        self.assertAlmostEqual(float(np.linalg.norm(family["NULL_VECTOR"])), 0.0, places=12)
        plus_u = family["+VECTOR"] / gain
        orth_u = family["ORTHOGONAL_SAME_NORM"] / gain
        self.assertAlmostEqual(float(np.dot(plus_u, orth_u)), 0.0, places=10)
        self.assertTrue(np.allclose(family["SIGN_FLIP"], -family["+VECTOR"]))

    def test_control_metrics_positive_synthetic_family_passes(self):
        cases = [
            {
                "case_id": "case-a",
                "family_id": "fam-1",
                "semantic_target": "AFFIRMATIVE",
                "output_code_identity": "A",
            },
            {
                "case_id": "case-b",
                "family_id": "fam-1",
                "semantic_target": "NEGATIVE",
                "output_code_identity": "B",
            },
            {
                "case_id": "case-c",
                "family_id": "fam-1",
                "semantic_target": "NEUTRAL",
                "output_code_identity": "C",
            },
        ]
        observations = {}
        for case in cases:
            target = case["output_code_identity"]
            others = [x for x in ("A", "B", "C") if x != target]
            values = {
                "BASELINE": 0.0,
                "+VECTOR": 2.0,
                "SIGN_FLIP": -2.0,
                "NULL_VECTOR": 0.0,
                "ORTHOGONAL_SAME_NORM": 0.3,
                "PERMUTED_SAME_NORM": 0.2,
            }
            for control, margin in values.items():
                logits = {"A": 0.0, "B": 0.0, "C": 0.0}
                logits[target] = margin
                logits[others[0]] = 0.0
                logits[others[1]] = 0.0
                observations[f"{case['case_id']}::{control}"] = {"token_logits": logits}
        verdict = runner.control_metrics(cases, observations)
        self.assertTrue(verdict["pass"], verdict["failures"])
        self.assertGreater(verdict["objective_min_specific_direction_margin"], 0.0)

    def test_control_metrics_rejects_compliance_like_nonselective_effect(self):
        case = {
            "case_id": "case-a",
            "family_id": "fam-1",
            "semantic_target": "AFFIRMATIVE",
            "output_code_identity": "A",
        }
        observations = {}
        for control in runner.CONTROL_FAMILY:
            # +VECTOR changes all A/B/C equally, so target margin does not move.
            shift = 5.0 if control == "+VECTOR" else 0.0
            observations[f"case-a::{control}"] = {"token_logits": {"A": shift, "B": shift, "C": shift}}
        verdict = runner.control_metrics([case], observations)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any(x.startswith("PLUS_NOT_POSITIVE") for x in verdict["failures"]))

    def test_scope_bridge_contract_never_claims_full_identity_by_source(self):
        source = (ROOT / "tools" / "trigger1_abstract_native_q8_execute_v1.py").read_text(encoding="utf-8")
        self.assertIn('"strict_micro_mechanistic_identity_claimed": False', source)
        self.assertIn('"broadcast_full_causal_identity_claimed": False', source)
        self.assertIn('"legacy_last_token_witness_used_as_causal_identity_premise": False', source)

    def test_semantic_promotion_stays_false_without_dual_readout(self):
        source = (ROOT / "tools" / "trigger1_abstract_native_q8_execute_v1.py").read_text(encoding="utf-8")
        self.assertIn('"context_valid_dual_readout_agrees": False', source)
        self.assertIn('"semantic_jspace_promotion_ready": False', source)
        self.assertIn("CONTEXT_BOUNDARY_MULTI_CODEBOOK_GENERATED_TEXT_DUAL_READOUT_STILL_REQUIRED", source)


if __name__ == "__main__":
    unittest.main()
