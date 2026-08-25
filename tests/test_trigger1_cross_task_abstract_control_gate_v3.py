from __future__ import annotations

import copy
import unittest

from tools import trigger1_cross_task_abstract_control_gate_v3 as gate


SHA_A = "a" * 64
SHA_B = "b" * 64


def binding(rank: int = 2) -> dict:
    axes = [
        {"axis_id": f"q{i}", "vector_sha256": SHA_A if i % 2 == 0 else SHA_B}
        for i in range(rank)
    ]
    return {
        "schema": gate.NUISANCE_SCHEMA,
        "fit_split": "CALIBRATION",
        "frozen_before_holdout": True,
        "receipt_sha256": SHA_A,
        "rank": rank,
        "axes": axes,
    }


def row(control: str, margin: float, axis_id: str | None = None) -> dict:
    out = {
        "family_id": "HOLD1",
        "task_grammar_id": "GRAM1",
        "vector_state_id": "S0",
        "requested_code": "A",
        "probe_polarity": "NONNEGATED",
        "replicate_id": "r0",
        "proof_topology_id": "top0",
        "demo_context_id": "demo0",
        "prompt_tokens": 20,
        "probe_tokens": 5,
        "last_token_index": 19,
        "control": control,
        "target_margin": margin,
    }
    if axis_id is not None:
        out["nuisance_axis_id"] = axis_id
    return out


class RankCompleteNuisanceGateV3Test(unittest.TestCase):
    def test_rank2_requires_every_axis_per_cell(self):
        candidate = {
            "nuisance_subspace": binding(2),
            "holdout_causal_rows": [row("NUISANCE", 0.1, "q0")],
        }
        failures: list[str] = []
        _, audit = gate._prepare_rank_complete_nuisance(candidate, failures)
        self.assertFalse(audit["rank_complete"])
        self.assertTrue(any(f.startswith("NUISANCE_AXIS_COVERAGE_INCOMPLETE:") for f in failures))
        self.assertTrue(any("missing=q1" in f for f in failures))

    def test_rank2_collapses_to_worst_axis_for_v2(self):
        candidate = {
            "nuisance_subspace": binding(2),
            "holdout_causal_rows": [
                row("TARGET", 1.0),
                row("NUISANCE", 0.10, "q0"),
                row("NUISANCE", 0.35, "q1"),
            ],
        }
        failures: list[str] = []
        delegated, audit = gate._prepare_rank_complete_nuisance(candidate, failures)
        self.assertEqual(failures, [])
        self.assertTrue(audit["rank_complete"])
        self.assertEqual(audit["nuisance_rank"], 2)
        nuisance = [r for r in delegated["holdout_causal_rows"] if r.get("control") == "NUISANCE"]
        self.assertEqual(len(nuisance), 1)
        self.assertEqual(nuisance[0]["target_margin"], 0.35)
        self.assertEqual(nuisance[0]["rank_complete_worst_nuisance_axis_id"], "q1")
        self.assertEqual(nuisance[0]["rank_complete_nuisance_axis_count"], 2)
        self.assertNotIn("nuisance_axis_id", nuisance[0])
        self.assertEqual(delegated["schema"], gate.v2.ATTESTATION_SCHEMA)

    def test_duplicate_axis_fails_closed(self):
        candidate = {
            "nuisance_subspace": binding(2),
            "holdout_causal_rows": [
                row("NUISANCE", 0.10, "q0"),
                row("NUISANCE", 0.20, "q0"),
                row("NUISANCE", 0.30, "q1"),
            ],
        }
        failures: list[str] = []
        gate._prepare_rank_complete_nuisance(candidate, failures)
        self.assertTrue(any("DUPLICATE_NUISANCE_AXIS:q0" in f for f in failures))

    def test_unbound_axis_fails_closed(self):
        candidate = {
            "nuisance_subspace": binding(1),
            "holdout_causal_rows": [row("NUISANCE", 0.10, "q9")],
        }
        failures: list[str] = []
        gate._prepare_rank_complete_nuisance(candidate, failures)
        self.assertTrue(any("NUISANCE_AXIS_UNBOUND:q9" in f for f in failures))

    def test_axis_id_on_non_nuisance_control_is_forbidden(self):
        candidate = {
            "nuisance_subspace": binding(1),
            "holdout_causal_rows": [
                row("TARGET", 1.0, "q0"),
                row("NUISANCE", 0.10, "q0"),
            ],
        }
        failures: list[str] = []
        gate._prepare_rank_complete_nuisance(candidate, failures)
        self.assertTrue(any("NON_NUISANCE_AXIS_ID_FORBIDDEN" in f for f in failures))

    def test_axis_count_must_equal_bound_rank(self):
        b = binding(2)
        b["axes"] = b["axes"][:1]
        candidate = {"nuisance_subspace": b, "holdout_causal_rows": [row("NUISANCE", 0.1, "q0")]}
        failures: list[str] = []
        gate._prepare_rank_complete_nuisance(candidate, failures)
        self.assertIn("NUISANCE_SUBSPACE_AXIS_COUNT_RANK_MISMATCH", failures)

    def test_adjudicate_never_mints_credit_on_malformed_candidate(self):
        out = gate.adjudicate({"schema": gate.ATTESTATION_SCHEMA})
        self.assertFalse(out["cross_task_abstract_native_control_pass"])
        self.assertFalse(out["canonical_credit_minted"])
        self.assertFalse(out["canonical_semantics_promotion"])
        self.assertFalse(out["jspace_model_runtime_credit"])
        self.assertFalse(out["whole_hcu_credit"])
        self.assertFalse(out["whole_entityos_hcu_credit"])
        self.assertFalse(out["training_credit"])


if __name__ == "__main__":
    unittest.main()
