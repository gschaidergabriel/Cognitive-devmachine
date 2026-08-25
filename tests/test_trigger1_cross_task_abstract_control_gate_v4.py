import copy
import unittest

from tools import trigger1_cross_task_abstract_control_gate_v3 as v3
from tools import trigger1_cross_task_abstract_control_gate_v4 as g


def valid():
    basis = []
    vecs = [[1.0, 0.1, 0.0], [1.0, 0.08, 0.02], [1.0, 0.12, -0.01]]
    for i, vec in enumerate(vecs):
        basis.append(
            {
                "family_id": f"basis-{i}",
                "task_grammar_id": f"basis-grammar-{i}",
                "direction": vec,
            }
        )

    causal = []
    margin = {
        "TARGET": 0.5,
        "NULL": 0.0,
        "SIGN_FLIP": -0.4,
        "ORTHOGONAL": 0.0,
        "PERMUTED": 0.0,
    }
    for fi in range(3):
        fam = f"hold-{fi}"
        grammar = f"hold-grammar-{fi}"
        for target in g.STATES:
            for code in g.CODES:
                for ri in range(2):
                    for polarity in g.POLARITIES:
                        common = {
                            "family_id": fam,
                            "task_grammar_id": grammar,
                            "vector_state_id": target,
                            "requested_code": code,
                            "probe_polarity": polarity,
                            "proof_topology_id": f"top-r{ri}",
                            "demo_context_id": f"demo-{target}-{code}-r{ri}",
                            "prompt_tokens": 128 + ri,
                            "probe_tokens": 16,
                            "last_token_index": 127 + ri,
                            "replicate_id": f"r{ri}",
                        }
                        for ctrl, score in margin.items():
                            causal.append({**common, "control": ctrl, "target_margin": score})
                        causal.append(
                            {
                                **common,
                                "control": "NUISANCE",
                                "nuisance_axis_id": "n0",
                                "target_margin": -0.05,
                            }
                        )
                        causal.append(
                            {
                                **common,
                                "control": "NUISANCE",
                                "nuisance_axis_id": "n1",
                                "target_margin": 0.0,
                            }
                        )

    off = []
    for fi in range(3):
        for ri in range(3):
            off.append(
                {
                    "family_id": f"hold-{fi}",
                    "replicate_id": f"o{ri}",
                    "control": "TARGET",
                    "unrelated_task_margin": 0.01,
                }
            )
            off.append(
                {
                    "family_id": f"hold-{fi}",
                    "replicate_id": f"o{ri}",
                    "control": "NULL",
                    "unrelated_task_margin": 0.0,
                }
            )

    return {
        "schema": g.ATTESTATION_SCHEMA,
        "primary_settings": {
            "gguf_sha256": g.PINNED_GGUF_SHA256,
            "llama_cpp_commit": g.PINNED_LLAMA_CPP_COMMIT,
            "injection_layer": g.PRIMARY_LAYER,
            "gain": g.PRIMARY_GAIN,
            "gain_selected_on_evaluation": False,
            "token_scope": "ALL_PROMPT_TOKENS",
        },
        "basis_family_directions": basis,
        "rank_consistency": {
            "representation_rank": "TWO_DIMENSIONAL_REQUIRED",
            "intervention_rank": "TWO_DIMENSIONAL_REQUIRED",
            "downstream_rank": "TWO_DIMENSIONAL_REQUIRED",
            "analyzer": "trigger1_semantic_simplex_rank_analyze.py",
            "shared_geometry_scale_preserved": True,
            "zero_sum_simplex_preserved": True,
            "downstream_coordinates_in_admitted_orthonormal_basis": True,
            "independent_unit_normalization_used": False,
        },
        "rank2_target_to_target_displacement_verified": True,
        "simple_sign_flip_used_as_semantic_opposite": False,
        "position_length_design": {
            "tokenizer_identity_bound_to_pinned_runtime": True,
            "length_position_nuisance_fit_calibration_only_and_frozen": True,
            "target_token_count_predictability_above_null": False,
        },
        "geometry_permutation_null": {
            "pairwise_cosine_q95": 0.2,
            "loo_cosine_q95": 0.2,
            "derived_from_preregistered_class_assignment_permutations": True,
        },
        "nuisance_subspace": {
            "schema": g.NUISANCE_SCHEMA,
            "fit_split": "CALIBRATION",
            "frozen_before_holdout": True,
            "receipt_sha256": "a" * 64,
            "rank": 2,
            "axes": [
                {"axis_id": "n0", "vector_sha256": "b" * 64},
                {"axis_id": "n1", "vector_sha256": "c" * 64},
            ],
        },
        "holdout_causal_rows": causal,
        "off_target_rows": off,
    }


def as_v3(candidate):
    out = copy.deepcopy(candidate)
    out["schema"] = v3.ATTESTATION_SCHEMA
    return out


class GateV4Tests(unittest.TestCase):
    def test_valid(self):
        out = g.adjudicate(valid())
        self.assertTrue(out["cross_task_abstract_native_control_pass"], out["failures"])

    def test_control_topology_mismatch_is_newly_rejected(self):
        x = valid()
        for row in x["holdout_causal_rows"]:
            if (
                row["family_id"] == "hold-0"
                and row["vector_state_id"] == "S0"
                and row["requested_code"] == "A"
                and row["probe_polarity"] == "NONNEGATED"
                and row["replicate_id"] == "r0"
                and row["control"] == "NULL"
            ):
                row["proof_topology_id"] = "mismatched-null-topology"
                break
        self.assertTrue(v3.adjudicate(as_v3(x))["cross_task_abstract_native_control_pass"])
        out = g.adjudicate(x)
        self.assertFalse(out["cross_task_abstract_native_control_pass"])
        self.assertTrue(any(f.startswith("CAUSAL_CONTROL_MATCH_FAIL:proof_topology_id") for f in out["failures"]))

    def test_control_token_position_mismatch_is_newly_rejected(self):
        x = valid()
        for row in x["holdout_causal_rows"]:
            if (
                row["family_id"] == "hold-0"
                and row["vector_state_id"] == "S1"
                and row["requested_code"] == "B"
                and row["probe_polarity"] == "NEGATED"
                and row["replicate_id"] == "r1"
                and row["control"] == "ORTHOGONAL"
            ):
                row["prompt_tokens"] += 4
                row["last_token_index"] += 4
                break
        self.assertTrue(v3.adjudicate(as_v3(x))["cross_task_abstract_native_control_pass"])
        out = g.adjudicate(x)
        self.assertFalse(out["cross_task_abstract_native_control_pass"])
        self.assertTrue(any(f.startswith("CAUSAL_CONTROL_MATCH_FAIL:prompt_tokens") for f in out["failures"]))

    def test_topology_must_be_factorial_with_code_and_polarity(self):
        x = valid()
        for row in x["holdout_causal_rows"]:
            if (
                row["requested_code"] == "A"
                and row["probe_polarity"] == "NEGATED"
                and row["replicate_id"] == "r1"
            ):
                row["proof_topology_id"] = "top-r0"
        self.assertTrue(v3.adjudicate(as_v3(x))["cross_task_abstract_native_control_pass"])
        out = g.adjudicate(x)
        self.assertFalse(out["cross_task_abstract_native_control_pass"])
        self.assertTrue(
            any(
                f.startswith("PROOF_TOPOLOGY_FULL_FACTORIAL_CELL_MISSING")
                or f.startswith("PROOF_TOPOLOGY_FULL_FACTORIAL_IMBALANCE")
                for f in out["failures"]
            )
        )

    def test_non_worst_nuisance_axis_cannot_hide_topology_mismatch(self):
        x = valid()
        for row in x["holdout_causal_rows"]:
            if (
                row["family_id"] == "hold-2"
                and row["vector_state_id"] == "S2"
                and row["requested_code"] == "C"
                and row["probe_polarity"] == "NEGATED"
                and row["replicate_id"] == "r1"
                and row.get("nuisance_axis_id") == "n0"
            ):
                row["proof_topology_id"] = "hidden-axis-topology"
                break
        # V3 delegates only the worst nuisance margin (n1 here), so n0's topology
        # mismatch does not survive into its v2 comparison.
        self.assertTrue(v3.adjudicate(as_v3(x))["cross_task_abstract_native_control_pass"])
        out = g.adjudicate(x)
        self.assertFalse(out["cross_task_abstract_native_control_pass"])
        self.assertTrue(any("NUISANCE@n0" in f for f in out["failures"]))


if __name__ == "__main__":
    unittest.main()
