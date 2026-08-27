from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate_v11 as gate
from tests.test_trigger1_jspace_abstract_deconfound_scope_gate import valid_candidate


class PromotionV11Test(unittest.TestCase):
    def test_requires_v10_and_hard_native_deconfound(self):
        c = valid_candidate()
        with mock.patch.object(gate.v10, "adjudicate", return_value={
            "scientifically_independent_vector_candidate": True,
            "v10_failures": [],
        }):
            r = gate.adjudicate(c)
        self.assertTrue(r["abstract_native_semantic_jspace_candidate"])
        self.assertTrue(r["cross_scope_causal_effect_equivalence_candidate"])
        self.assertFalse(r["strict_micro_mechanistic_identity_candidate"])
        self.assertFalse(r["canonical_credit_minted"])

    def test_positive_hard_gate_cannot_rescue_failed_v10(self):
        c = valid_candidate()
        with mock.patch.object(gate.v10, "adjudicate", return_value={
            "scientifically_independent_vector_candidate": False,
            "v10_failures": ["UPSTREAM_FAIL"],
        }):
            r = gate.adjudicate(c)
        self.assertFalse(r["abstract_native_semantic_jspace_candidate"])
        self.assertIn("UPSTREAM_FAIL", r["v11_failures"])

    def test_failed_lexical_deconfound_blocks_promotion(self):
        c = valid_candidate()
        c["abstract_state_deconfound"]["basis_holdout_lexically_disjoint"] = False
        with mock.patch.object(gate.v10, "adjudicate", return_value={
            "scientifically_independent_vector_candidate": True,
            "v10_failures": [],
        }):
            r = gate.adjudicate(c)
        self.assertFalse(r["abstract_native_semantic_jspace_candidate"])
        self.assertIn("BASIS_HOLDOUT_LEXICAL_DISJOINTNESS_REQUIRED", r["v11_failures"])

    def test_scope_bridge_is_optional_for_native_abstract_candidate(self):
        c = valid_candidate()
        c.pop("cross_scope_effect_bridge")
        with mock.patch.object(gate.v10, "adjudicate", return_value={
            "scientifically_independent_vector_candidate": True,
            "v10_failures": [],
        }):
            r = gate.adjudicate(c)
        self.assertTrue(r["abstract_native_semantic_jspace_candidate"])
        self.assertFalse(r["cross_scope_causal_effect_equivalence_candidate"])
        self.assertIn("CROSS_SCOPE_EFFECT_BRIDGE_NOT_PROVIDED", r["v11_scope_bridge_failures"])


if __name__ == "__main__":
    unittest.main()
