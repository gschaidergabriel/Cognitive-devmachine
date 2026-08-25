from __future__ import annotations

from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

# The standalone test fixture doesn't include the repository's v10 module. Inject only a
# placeholder for import; every test patches adjudicate before use.
fake_v10 = types.ModuleType("trigger1_jspace_promotion_gate_v10")
fake_v10.adjudicate = lambda candidate: {}
sys.modules.setdefault("trigger1_jspace_promotion_gate_v10", fake_v10)

import trigger1_jspace_promotion_gate_v11 as gate


def base_positive():
    return {
        "scientifically_independent_vector_candidate": True,
        "owner_trigger1_goal_credit_candidate": True,
        "modular_hcu_jspace_control_candidate": True,
        "full_native_jspace_vector_control_candidate": True,
        "v10_failures": [],
    }


def text_result(ok=True):
    return {
        "pass": ok,
        "failures": [] if ok else ["LEXICAL_SHORTCUT"],
        "audit_receipt_sha256": "a" * 64,
    }


def scope_result(native=True, strict=False):
    return {
        "pass": native,
        "failures": [] if native else ["NATIVE_FAIL"],
        "classification": "BROADCAST_SCOPE_NATIVE_CARRIER_ONLY" if native and not strict else "LAST_TOKEN_TO_NATIVE_FUNCTIONAL_EQUIVALENCE_SUPPORTED",
        "native_all_token_causal_carrier_candidate": native,
        "strict_last_token_native_replication_candidate": strict,
        "pytorch_last_vs_all_scope_equivalence_pass": strict,
        "native_vs_pytorch_all_token_carrier_match_pass": native,
    }


class PromotionV11Tests(unittest.TestCase):
    def test_abstract_native_candidate_does_not_require_last_token_equivalence(self):
        with patch.object(gate.v10, "adjudicate", return_value=base_positive()), \
             patch.object(gate.text_audit, "audit", return_value=text_result(True)), \
             patch.object(gate.scope_gate, "adjudicate", return_value=scope_result(True, False)):
            result = gate.adjudicate({})
        self.assertTrue(result["scientifically_independent_vector_candidate"])
        self.assertTrue(result["full_native_jspace_vector_control_candidate"])
        self.assertFalse(result["strict_last_token_native_replication_candidate"])
        self.assertFalse(result["canonical_semantics_promotion"])

    def test_text_leakage_blocks_abstract_semantic_promotion(self):
        with patch.object(gate.v10, "adjudicate", return_value=base_positive()), \
             patch.object(gate.text_audit, "audit", return_value=text_result(False)), \
             patch.object(gate.scope_gate, "adjudicate", return_value=scope_result(True, True)):
            result = gate.adjudicate({})
        self.assertFalse(result["scientifically_independent_vector_candidate"])
        self.assertFalse(result["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(result["full_native_jspace_vector_control_candidate"])

    def test_missing_native_causal_carrier_blocks_even_when_v10_and_text_pass(self):
        with patch.object(gate.v10, "adjudicate", return_value=base_positive()), \
             patch.object(gate.text_audit, "audit", return_value=text_result(True)), \
             patch.object(gate.scope_gate, "adjudicate", return_value=scope_result(False, False)):
            result = gate.adjudicate({})
        self.assertFalse(result["scientifically_independent_vector_candidate"])
        self.assertIn("SCOPE:NATIVE_ALL_TOKEN_CAUSAL_CARRIER_REQUIRED", result["v11_failures"])

    def test_full_native_cannot_bypass_failed_v10_scientific_binding(self):
        failed_base = base_positive()
        failed_base["scientifically_independent_vector_candidate"] = False
        failed_base["v10_failures"] = ["BINDING_FAIL"]
        with patch.object(gate.v10, "adjudicate", return_value=failed_base), \
             patch.object(gate.text_audit, "audit", return_value=text_result(True)), \
             patch.object(gate.scope_gate, "adjudicate", return_value=scope_result(True, True)):
            result = gate.adjudicate({})
        self.assertFalse(result["scientifically_independent_vector_candidate"])
        self.assertFalse(result["full_native_jspace_vector_control_candidate"])

    def test_strict_replication_is_separate_positive_claim(self):
        with patch.object(gate.v10, "adjudicate", return_value=base_positive()), \
             patch.object(gate.text_audit, "audit", return_value=text_result(True)), \
             patch.object(gate.scope_gate, "adjudicate", return_value=scope_result(True, True)):
            result = gate.adjudicate({})
        self.assertTrue(result["scientifically_independent_vector_candidate"])
        self.assertTrue(result["strict_last_token_native_replication_candidate"])


if __name__ == "__main__":
    unittest.main()
