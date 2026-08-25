from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_scope_equivalence_adjudicator as gate

RECEIPT = "a" * 64


def rows_for(last, all_tokens, native):
    effects = {
        gate.SCOPES[0]: last,
        gate.SCOPES[1]: all_tokens,
        gate.SCOPES[2]: native,
    }
    rows = []
    targets = ["AFFIRMATIVE", "NEGATIVE", "NEUTRAL", "AFFIRMATIVE", "NEGATIVE", "NEUTRAL"]
    for scope, values in effects.items():
        for i, effect in enumerate(values):
            scores = {
                "BASELINE": 0.0,
                "+VECTOR": float(effect),
                "SIGN_FLIP": -float(effect),
                "NULL_VECTOR": 0.0,
                "ORTHOGONAL_SAME_NORM": 0.10 * float(effect),
                "PERMUTED_SAME_NORM": 0.05 * float(effect),
                "LABEL_ONLY_NUISANCE_VECTOR": 0.08 * float(effect),
            }
            for control, score in scores.items():
                rows.append({
                    "case_id": f"case-{i}",
                    "family_id": f"family-{i // 2}",
                    "semantic_target": targets[i],
                    "scope": scope,
                    "control": control,
                    "score": score,
                    "runtime_receipt_sha256": RECEIPT,
                })
    return rows


def payload(last, all_tokens, native):
    return {"schema": gate.SCHEMA, "rows": rows_for(last, all_tokens, native)}


class ScopeEquivalenceTests(unittest.TestCase):
    def test_three_way_functional_equivalence_can_pass(self):
        last = [1, 2, 3, 4, 5, 6]
        all_tokens = [1.02, 2.04, 3.06, 4.08, 5.10, 6.12]
        native = [1.01, 2.02, 3.03, 4.04, 5.05, 6.06]
        result = gate.adjudicate(payload(last, all_tokens, native))
        self.assertTrue(result["pass"], result["failures"])
        self.assertTrue(result["native_all_token_causal_carrier_candidate"])
        self.assertTrue(result["strict_last_token_native_replication_candidate"])
        self.assertEqual("LAST_TOKEN_TO_NATIVE_FUNCTIONAL_EQUIVALENCE_SUPPORTED", result["classification"])

    def test_broadcast_native_carrier_survives_without_last_token_equivalence(self):
        last = [6, 1, 5, 2, 4, 3]
        all_tokens = [1, 2, 3, 4, 5, 6]
        native = [1.01, 2.02, 3.03, 4.04, 5.05, 6.06]
        result = gate.adjudicate(payload(last, all_tokens, native))
        self.assertTrue(result["pass"], result["failures"])
        self.assertTrue(result["native_all_token_causal_carrier_candidate"])
        self.assertFalse(result["strict_last_token_native_replication_candidate"])
        self.assertEqual("BROADCAST_SCOPE_NATIVE_CARRIER_ONLY", result["classification"])

    def test_invalid_runtime_receipt_cannot_mint_native_candidate(self):
        p = payload([1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6])
        p["rows"][0]["runtime_receipt_sha256"] = "bad"
        result = gate.adjudicate(p)
        self.assertFalse(result["pass"])
        self.assertFalse(result["native_all_token_causal_carrier_candidate"])
        self.assertFalse(result["strict_last_token_native_replication_candidate"])

    def test_case_universe_mismatch_fails_closed(self):
        p = payload([1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6])
        p["rows"] = [
            row for row in p["rows"]
            if not (row["scope"] == gate.SCOPES[2] and row["case_id"] == "case-5")
        ]
        result = gate.adjudicate(p)
        self.assertIn("SCOPE_CASE_UNIVERSE_MISMATCH", result["failures"])
        self.assertFalse(result["native_all_token_causal_carrier_candidate"])


if __name__ == "__main__":
    unittest.main()
