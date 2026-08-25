#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trigger1_semantic_abstraction_gate_v1 as gate
from tools import trigger1_abstract_casebook_v1 as casebook


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def valid_fixture() -> dict:
    cal = casebook.producer_case_specs("CALIBRATION")
    hold = casebook.producer_case_specs("HOLDOUT")
    candidate = {
        "preregistration_evidence": {
            "case_plans": {
                "CALIBRATION": {"cases": copy.deepcopy(cal)},
                "HOLDOUT": {"cases": copy.deepcopy(hold)},
            }
        },
        "vector_derivation": {},
        "semantic_abstraction_attestation": {
            "schema": gate.ATTESTATION_SCHEMA,
            "basis_rows": casebook.basis_rows(),
        },
    }
    case_rows = [("CALIBRATION", row) for row in cal] + [("HOLDOUT", row) for row in hold]
    receipts = [
        {
            "split": split,
            "case_id": row["case_id"],
            "runtime_receipt_sha256": h(f"nuisance:{split}:{row['case_id']}"),
        }
        for split, row in case_rows
    ]
    analysis = {
        "candidate_semantic_interaction": 2.0,
        "nuisance_semantic_interaction": 0.10,
        "sign_flip_semantic_interaction": -1.25,
        "max_abs_nuisance_fraction": 0.25,
        "analysis_implementation_sha256": h("analysis-implementation"),
        "analysis_result_receipt_sha256": h("analysis-result"),
    }
    analysis["analysis_binding_sha256"] = gate.canonical_sha({
        key: analysis[key]
        for key in (
            "candidate_semantic_interaction",
            "nuisance_semantic_interaction",
            "sign_flip_semantic_interaction",
            "max_abs_nuisance_fraction",
            "analysis_implementation_sha256",
            "analysis_result_receipt_sha256",
        )
    })
    att = candidate["semantic_abstraction_attestation"]
    att["lexical_nuisance_control"] = {
        "control_identity": gate.NUISANCE_CONTROL,
        "construction": "DIRECT_POLE_LEXEMES_ONLY",
        "excluded_from_semantic_basis": True,
        "runtime_receipts": receipts,
        "interaction_analysis": analysis,
    }
    att["native_intervention_semantics"] = {
        "basis_carrier": "QWEN3_0_6B_Q8_NATIVE_LAYER_INPUT_21",
        "actuation": "LLAMA_CPP_LLAMA_SET_ADAPTER_CVEC_LAYER20",
        "downstream_transport_endpoint": "QWEN3_0_6B_Q8_NATIVE_LAYER_INPUT_24",
        "promotion_evidence_path": "NATIVE_Q8_TO_NATIVE_CVEC_ONLY",
        "prior_last_token_witness_role": "DISCOVERY_ONLY",
        "cross_method_causal_equivalence_claimed": False,
        "native_end_to_end_promotion_only": True,
        "gguf_sha256": h("gguf"),
        "llama_cpp_commit": h("llama"),
        "basis_packet_sha256": h("basis-packet"),
        "downstream_transport_receipt_sha256": h("downstream"),
    }
    first = gate.adjudicate(candidate)
    candidate["vector_derivation"]["label_free_basis_prompt_universe_sha256"] = first["basis_prompt_universe_sha256"]
    second = gate.adjudicate(candidate)
    att["abstraction_audit_sha256"] = second["abstraction_audit_sha256"]
    final = gate.adjudicate(candidate)
    if not final["semantic_abstraction_candidate"]:
        raise AssertionError(final["failures"])
    return candidate


class SemanticAbstractionGateTests(unittest.TestCase):
    def test_casebook_is_full_factorial_and_content_disjoint(self):
        b = casebook.basis_rows()
        c = casebook.producer_case_specs("CALIBRATION")
        hrows = casebook.producer_case_specs("HOLDOUT")
        self.assertEqual((len(b), len(c), len(hrows)), (18, 9, 9))
        expected = {(target, code) for target in gate.TARGETS for code in ("A", "B", "C")}
        self.assertEqual({(r["semantic_target"], r["output_code_identity"]) for r in c}, expected)
        self.assertEqual({(r["semantic_target"], r["output_code_identity"]) for r in hrows}, expected)
        sets = {
            "basis": set().union(*(gate.lexical_tokens(r["prompt"]) for r in b)),
            "cal": set().union(*(gate.lexical_tokens(r["prompt"]) for r in c)),
            "hold": set().union(*(gate.lexical_tokens(r["prompt"]) for r in hrows)),
        }
        self.assertFalse(sets["basis"] & sets["cal"])
        self.assertFalse(sets["basis"] & sets["hold"])
        self.assertFalse(sets["cal"] & sets["hold"])

    def test_valid_hard_abstraction_fixture_passes(self):
        candidate = valid_fixture()
        result = gate.adjudicate(candidate)
        self.assertTrue(result["semantic_abstraction_candidate"], result["failures"])
        self.assertTrue(result["content_derived_lexical_family_required"])
        self.assertFalse(result["cross_method_causal_equivalence_required"])

    def test_direct_pole_synonym_fails(self):
        candidate = valid_fixture()
        row = candidate["semantic_abstraction_attestation"]["basis_rows"][0]
        row["prompt"] = "The committee approved the route."
        row["prompt_sha256"] = gate.prompt_sha(row["prompt"])
        row["lexical_content_sha256"] = gate.lexical_family_sha(gate.lexical_tokens(row["prompt"]))
        result = gate.adjudicate(candidate)
        self.assertTrue(any("DIRECT_POLE_LEXEME_LEAK" in f for f in result["failures"]))

    def test_cross_split_actual_prompt_overlap_fails(self):
        candidate = valid_fixture()
        basis_prompt = candidate["semantic_abstraction_attestation"]["basis_rows"][0]["prompt"]
        row = candidate["preregistration_evidence"]["case_plans"]["HOLDOUT"]["cases"][0]
        row["prompt"] = basis_prompt
        row["prompt_sha256"] = gate.prompt_sha(basis_prompt)
        result = gate.adjudicate(candidate)
        self.assertTrue(any("LEXICAL_SPLIT_OVERLAP" in f for f in result["failures"]))

    def test_fake_lexical_family_hash_fails_even_with_valid_shape(self):
        candidate = valid_fixture()
        rows = candidate["preregistration_evidence"]["case_plans"]["CALIBRATION"]["cases"]
        family = rows[0]["scenario_family_sha256"]
        for row in rows:
            if row["scenario_family_sha256"] == family:
                row["lexical_family_sha256"] = h("arbitrary-metadata")
        result = gate.adjudicate(candidate)
        self.assertTrue(any("LEXICAL_FAMILY_NOT_CONTENT_DERIVED" in f for f in result["failures"]))

    def test_nuisance_must_cover_exact_case_universe(self):
        candidate = valid_fixture()
        candidate["semantic_abstraction_attestation"]["lexical_nuisance_control"]["runtime_receipts"].pop()
        result = gate.adjudicate(candidate)
        self.assertIn("LEXICAL_NUISANCE_RECEIPT_CASE_UNIVERSE_MISMATCH", result["failures"])

    def test_nuisance_cannot_reproduce_candidate_interaction(self):
        candidate = valid_fixture()
        analysis = candidate["semantic_abstraction_attestation"]["lexical_nuisance_control"]["interaction_analysis"]
        analysis["nuisance_semantic_interaction"] = 1.0
        analysis["analysis_binding_sha256"] = gate.canonical_sha({
            key: analysis[key]
            for key in (
                "candidate_semantic_interaction", "nuisance_semantic_interaction",
                "sign_flip_semantic_interaction", "max_abs_nuisance_fraction",
                "analysis_implementation_sha256", "analysis_result_receipt_sha256",
            )
        })
        result = gate.adjudicate(candidate)
        self.assertIn("LEXICAL_NUISANCE_REPRODUCES_TOO_MUCH_SEMANTIC_INTERACTION", result["failures"])

    def test_cross_method_equivalence_claim_is_rejected(self):
        candidate = valid_fixture()
        native = candidate["semantic_abstraction_attestation"]["native_intervention_semantics"]
        native["cross_method_causal_equivalence_claimed"] = True
        result = gate.adjudicate(candidate)
        self.assertIn("CROSS_METHOD_CAUSAL_EQUIVALENCE_MUST_NOT_BE_CLAIMED", result["failures"])


if __name__ == "__main__":
    unittest.main()
