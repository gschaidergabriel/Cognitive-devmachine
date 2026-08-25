from __future__ import annotations

import copy
import unittest

from tools import trigger1_intervention_scope_equivalence_v1 as gate


def payload(last_fn, all_fn, native_fn, n: int = 18):
    rows = []
    for i in range(n):
        base = (i + 1) / 10.0
        for path, fn in (
            (gate.PATHS[0], last_fn),
            (gate.PATHS[1], all_fn),
            (gate.PATHS[2], native_fn),
        ):
            rows.append({"cell_id": f"cell-{i:02d}", "path": path, "semantic_effect": fn(i, base)})
    return {
        "schema": gate.SCHEMA,
        "metric_identity": "normalized_semantic_causal_effect/v1",
        "normalizer_identity": "frozen_calibration_scale/v1",
        "rows": rows,
    }


class InterventionScopeEquivalenceTests(unittest.TestCase):
    def test_scope_invariant_response_equivalence_closes_declared_scope_blocker_only(self):
        result = gate.adjudicate(payload(
            lambda _i, x: x,
            lambda _i, x: 1.02 * x,
            lambda _i, x: 0.99 * x,
        ))
        self.assertEqual(result["classification"], "SCOPE_INVARIANT_SEMANTIC_RESPONSE_EQUIVALENCE")
        self.assertTrue(result["response_equivalence_claim_allowed"])
        self.assertFalse(result["causal_identity_claim_allowed"])
        self.assertTrue(result["last_token_vs_pytorch_broadcast"]["pass"])
        self.assertTrue(result["pytorch_broadcast_vs_native_cvec"]["pass"])

    def test_last_token_divergence_with_broadcast_native_agreement_is_classified_broadcast_only(self):
        result = gate.adjudicate(payload(
            lambda i, x: x if i % 2 == 0 else -x,
            lambda _i, x: x,
            lambda _i, x: 1.01 * x,
        ))
        self.assertEqual(result["classification"], "BROADCAST_SCOPE_CARRIER_REPLICATION_ONLY")
        self.assertFalse(result["response_equivalence_claim_allowed"])
        self.assertFalse(result["causal_identity_claim_allowed"])
        self.assertFalse(result["last_token_vs_pytorch_broadcast"]["pass"])
        self.assertTrue(result["pytorch_broadcast_vs_native_cvec"]["pass"])

    def test_native_carrier_divergence_fails_closed(self):
        result = gate.adjudicate(payload(
            lambda _i, x: x,
            lambda _i, x: x,
            lambda i, x: -x if i % 2 else x,
        ))
        self.assertEqual(result["classification"], "NATIVE_CARRIER_RESPONSE_DIVERGENCE")
        self.assertFalse(result["response_equivalence_claim_allowed"])
        self.assertFalse(result["causal_identity_claim_allowed"])

    def test_incomplete_three_way_cell_is_rejected(self):
        value = payload(lambda _i, x: x, lambda _i, x: x, lambda _i, x: x)
        value["rows"].pop()
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_THREE_WAY_CELL"):
            gate.adjudicate(value)

    def test_too_few_cells_is_rejected(self):
        value = payload(lambda _i, x: x, lambda _i, x: x, lambda _i, x: x, n=17)
        with self.assertRaisesRegex(ValueError, "INSUFFICIENT_MATCHED_CELLS"):
            gate.adjudicate(value)


if __name__ == "__main__":
    unittest.main()
