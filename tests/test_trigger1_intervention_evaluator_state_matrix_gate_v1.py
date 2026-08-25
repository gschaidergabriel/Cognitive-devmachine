import hashlib
import unittest
from unittest import mock

from tools import trigger1_intervention_evaluator_state_matrix_gate_v1 as g


def h(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def valid():
    vecs = {state: h("vec-" + state) for state in g.STATES}
    rows = []
    for fi in range(3):
        fam = f"hold-{fi}"
        grammar = f"grammar-{fi}"
        for evaluator in g.STATES:
            for code in g.CODES:
                for polarity in g.POLARITIES:
                    for ri in range(2):
                        rep = f"r{ri}"
                        case_id = f"{fam}-{evaluator}-{code}-{polarity}-{rep}"
                        prompt_sha = h(case_id)
                        for intervention in g.STATES:
                            rows.append({
                                "family_id": fam,
                                "task_grammar_id": grammar,
                                "intervention_state_id": intervention,
                                "evaluator_state_id": evaluator,
                                "requested_code": code,
                                "probe_polarity": polarity,
                                "replicate_id": rep,
                                "case_id": case_id,
                                "prompt_sha256": prompt_sha,
                                "vector_sha256": vecs[intervention],
                                "intervention_margin": 0.5 if intervention == evaluator else 0.0,
                                "null_margin": 0.0,
                            })
    return {
        "schema": g.ATTESTATION_SCHEMA,
        "base_v4_attestation": {"synthetic_fixture": True},
        "intervention_vectors": [
            {"intervention_state_id": state, "vector_sha256": vecs[state]}
            for state in g.STATES
        ],
        "intervention_evaluator_rows": rows,
    }


def base_pass(_candidate):
    return {"cross_task_abstract_native_control_pass": True, "failures": []}


class MatrixGateTests(unittest.TestCase):
    def adjudicate(self, candidate):
        with mock.patch.object(g.v4, "adjudicate", side_effect=base_pass):
            return g.adjudicate(candidate)

    def test_valid_complete_matrix(self):
        out = self.adjudicate(valid())
        self.assertTrue(out["intervention_evaluator_state_matrix_pass"], out["failures"])
        self.assertEqual(out["matrix"]["rows"], 324)
        self.assertEqual(out["matrix"]["prompt_strata"], 108)
        self.assertEqual(out["matrix"]["replicates_per_cell"], 2)
        self.assertGreater(out["matrix"]["minimum_diagonal_effect"], g.MIN_DIAGONAL_EFFECT)
        self.assertGreater(out["matrix"]["minimum_diagonal_offdiagonal_gap"], g.MIN_SPECIFICITY_GAP)
        self.assertFalse(out["authenticated_runtime_evidence"])

    def test_generic_confidence_direction_fails(self):
        candidate = valid()
        for row in candidate["intervention_evaluator_rows"]:
            row["intervention_margin"] = 0.5
        out = self.adjudicate(candidate)
        self.assertFalse(out["intervention_evaluator_state_matrix_pass"])
        self.assertTrue(any("DIAGONAL_NOT_ABOVE_OFF_DIAGONAL" in f for f in out["failures"]))

    def test_missing_cross_state_cell_fails(self):
        candidate = valid()
        candidate["intervention_evaluator_rows"] = [
            row for row in candidate["intervention_evaluator_rows"]
            if not (
                row["family_id"] == "hold-0"
                and row["intervention_state_id"] == "S2"
                and row["evaluator_state_id"] == "S1"
                and row["requested_code"] == "B"
                and row["probe_polarity"] == "NEGATED"
                and row["replicate_id"] == "r1"
            )
        ]
        out = self.adjudicate(candidate)
        self.assertFalse(out["intervention_evaluator_state_matrix_pass"])
        self.assertTrue(any("INTERVENTION_SET_INCOMPLETE" in f for f in out["failures"]))

    def test_prompt_drift_across_intervention_fails(self):
        candidate = valid()
        for row in candidate["intervention_evaluator_rows"]:
            if (
                row["family_id"] == "hold-0"
                and row["evaluator_state_id"] == "S0"
                and row["requested_code"] == "A"
                and row["probe_polarity"] == "NONNEGATED"
                and row["replicate_id"] == "r0"
                and row["intervention_state_id"] == "S2"
            ):
                row["prompt_sha256"] = h("different")
        out = self.adjudicate(candidate)
        self.assertFalse(out["intervention_evaluator_state_matrix_pass"])
        self.assertTrue(any("MODEL_FACING_CASE_DRIFT_ACROSS_INTERVENTIONS" in f for f in out["failures"]))

    def test_duplicate_state_vector_hash_fails(self):
        candidate = valid()
        duplicate = candidate["intervention_vectors"][1]["vector_sha256"]
        candidate["intervention_vectors"][2]["vector_sha256"] = duplicate
        for row in candidate["intervention_evaluator_rows"]:
            if row["intervention_state_id"] == "S2":
                row["vector_sha256"] = duplicate
        out = self.adjudicate(candidate)
        self.assertFalse(out["intervention_evaluator_state_matrix_pass"])
        self.assertIn("DISTINCT_STATE_VECTOR_HASHES_REQUIRED", out["failures"])

    def test_vector_registry_mismatch_fails(self):
        candidate = valid()
        candidate["intervention_evaluator_rows"][0]["vector_sha256"] = h("wrong")
        out = self.adjudicate(candidate)
        self.assertFalse(out["intervention_evaluator_state_matrix_pass"])
        self.assertTrue(any("VECTOR_REGISTRY_MISMATCH" in f for f in out["failures"]))

    def test_diagonal_must_exceed_null(self):
        candidate = valid()
        for row in candidate["intervention_evaluator_rows"]:
            if row["intervention_state_id"] == row["evaluator_state_id"]:
                row["intervention_margin"] = 0.02
        out = self.adjudicate(candidate)
        self.assertFalse(out["intervention_evaluator_state_matrix_pass"])
        self.assertTrue(any("DIAGONAL_EFFECT_NOT_POSITIVE" in f for f in out["failures"]))

    def test_base_v4_failure_propagates(self):
        candidate = valid()
        with mock.patch.object(
            g.v4,
            "adjudicate",
            return_value={"cross_task_abstract_native_control_pass": False, "failures": ["BASE_SENTINEL"]},
        ):
            out = g.adjudicate(candidate)
        self.assertFalse(out["intervention_evaluator_state_matrix_pass"])
        self.assertIn("BASE_V4_GATE_NOT_PASS", out["failures"])
        self.assertIn("BASE_V4:BASE_SENTINEL", out["failures"])


if __name__ == "__main__":
    unittest.main()
