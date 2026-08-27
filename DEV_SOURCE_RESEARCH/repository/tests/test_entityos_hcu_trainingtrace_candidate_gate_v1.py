import copy
import unittest
from tools import entityos_hcu_trainingtrace_candidate_gate_v1 as gate

SHA = "a" * 64


def base_method():
    return {
        "schema": gate.ROW_SCHEMA,
        "evidence_class": "METHOD_ONLY",
        "reality_level": "R2",
        "family_id": "method-hyperposition-01",
        "provenance_ancestry_id": "method-source-01",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "fact_status": "UNKNOWN",
        "target_type": "PROTOCOL_METHOD",
        "split": "TRAIN",
        "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
        "selected_using_holdout": False,
        "hyperposition": {
            "alternatives": ["H1", "H0"],
            "resolution_status": "UNRESOLVED",
            "resolved_alternative": None,
        },
    }


def causal_jspace():
    x = base_method()
    x.update({
        "evidence_class": "COMPONENT_CAUSAL_MEASURED",
        "reality_level": "R4",
        "fact_status": "MEASURED",
        "target_type": "JSPACE_VECTOR_EFFECT",
        "source_model_family": "QWEN35_08B",
        "target_model_family": "QWEN35_08B",
        "causal_receipt_sha256": SHA,
        "model_runtime_binding": {
            "model_id": "Qwen/Qwen3.5-0.8B-Base",
            "model_revision": "rev",
            "weights_sha256": SHA,
            "runtime_id": "runtime",
            "runtime_revision": "build",
        },
        "hyperposition": None,
    })
    return x


class TrainingTraceCandidateGateTest(unittest.TestCase):
    def test_method_row_passes_without_minting_credit(self):
        out = gate.adjudicate(base_method())
        self.assertTrue(out["candidate_admission_pass"])
        self.assertFalse(out["canonical_truth_minted"])
        self.assertFalse(out["training_credit_minted"])

    def test_method_row_cannot_assert_verified_fact(self):
        x = base_method(); x["fact_status"] = "VERIFIED"
        out = gate.adjudicate(x)
        self.assertFalse(out["candidate_admission_pass"])
        self.assertIn("METHOD_OR_SYNTHETIC_ROW_CANNOT_ASSERT_FACT", out["failures"])

    def test_unresolved_hyperposition_cannot_collapse(self):
        x = base_method(); x["hyperposition"]["resolved_alternative"] = "H1"
        self.assertFalse(gate.adjudicate(x)["candidate_admission_pass"])

    def test_causal_jspace_row_passes_at_candidate_scope(self):
        self.assertTrue(gate.adjudicate(causal_jspace())["candidate_admission_pass"])

    def test_jspace_method_only_is_rejected(self):
        x = base_method(); x["target_type"] = "JSPACE_VECTOR_EFFECT"
        self.assertFalse(gate.adjudicate(x)["candidate_admission_pass"])

    def test_cross_model_jspace_label_transfer_is_forbidden(self):
        x = causal_jspace(); x["source_model_family"] = "QWEN3_06B"
        out = gate.adjudicate(x)
        self.assertFalse(out["candidate_admission_pass"])
        self.assertIn("CROSS_MODEL_JSPACE_LABEL_TRANSFER_FORBIDDEN", out["failures"])

    def test_holdout_selection_is_forbidden(self):
        x = causal_jspace(); x["selected_using_holdout"] = True
        self.assertFalse(gate.adjudicate(x)["candidate_admission_pass"])

    def test_generated_row_cannot_claim_measured(self):
        x = base_method(); x["fact_status"] = "MEASURED"
        out = gate.adjudicate(x)
        self.assertFalse(out["candidate_admission_pass"])
        self.assertIn("GENERATED_OR_COUNTERREALITY_CANNOT_ASSERT_MEASURED_FACT", out["failures"])

    def test_direct_effect_authority_forbidden(self):
        x = causal_jspace(); x["direct_effect_authority"] = True
        self.assertFalse(gate.adjudicate(x)["candidate_admission_pass"])

if __name__ == "__main__":
    unittest.main()
