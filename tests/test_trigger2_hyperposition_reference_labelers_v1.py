#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "trigger2_hyperposition_reference_labelers_v1.py"
spec = importlib.util.spec_from_file_location("tr2label", MODULE_PATH)
m = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m)


def state():
    return {
        "query_id": "q1",
        "branches": [
            {
                "branch_id": "b_alpha",
                "v_semantic_value": "ALLOW",
                "K_context_predicate": "ctx_a",
                "E_plus": [],
                "E_minus": [],
                "F_falsifier": "disc_alpha_false",
                "T_validity_scope": "synthetic_episode",
                "A_origin_provenance": "family_a",
                "sigma_epistemic_status": "HYPOTHESIS",
                "projection_visibility": "VISIBLE",
            },
            {
                "branch_id": "b_beta",
                "v_semantic_value": "DENY",
                "K_context_predicate": "ctx_a",
                "E_plus": [],
                "E_minus": [],
                "F_falsifier": "disc_beta_false",
                "T_validity_scope": "synthetic_episode",
                "A_origin_provenance": "family_b",
                "sigma_epistemic_status": "HYPOTHESIS",
                "projection_visibility": "VISIBLE",
            },
        ],
    }


class TestTrigger2HyperpositionReferenceLabelersV1(unittest.TestCase):
    def test_support_preserves_both_branches(self):
        out = m.U_update(
            state(),
            {
                "evidence_id": "e1",
                "provenance": "p1",
                "independence_group": "ig1",
                "evidence_kind": "MEASUREMENT",
                "polarity": "SUPPORT",
                "target_branch_ids": ["b_alpha"],
            },
        )
        self.assertEqual([b["branch_id"] for b in out["branches"]], ["b_alpha", "b_beta"])
        self.assertEqual(out["branches"][0]["sigma_epistemic_status"], "SUPPORTED")
        self.assertEqual(out["branches"][1]["sigma_epistemic_status"], "HYPOTHESIS")

    def test_duplicate_evidence_idempotent(self):
        obs = {
            "evidence_id": "e1",
            "provenance": "p1",
            "independence_group": "ig1",
            "evidence_kind": "MEASUREMENT",
            "polarity": "SUPPORT",
            "target_branch_ids": ["b_alpha"],
        }
        once = m.U_update(state(), obs)
        twice = m.U_update(once, obs)
        self.assertEqual(len(twice["branches"][0]["E_plus"]), 1)

    def test_majority_cannot_falsify(self):
        with self.assertRaises(m.LabelerError):
            m.U_update(
                state(),
                {
                    "evidence_id": "e1",
                    "provenance": "p1",
                    "independence_group": "ig1",
                    "evidence_kind": "MAJORITY",
                    "polarity": "FALSIFY",
                    "target_branch_ids": ["b_beta"],
                },
            )

    def test_unqualified_discriminator_stays_unresolved(self):
        result = m.D_resolve(
            state(),
            {"qualified": False, "evidence_kind": "MEASUREMENT", "selected_branch_id": "b_alpha"},
        )
        self.assertEqual(result["resolution_state"], "UNRESOLVED")

    def test_majority_discriminator_stays_unresolved(self):
        result = m.D_resolve(
            state(),
            {"qualified": True, "evidence_kind": "MAJORITY", "selected_branch_id": "b_alpha"},
        )
        self.assertEqual(result["resolution_state"], "UNRESOLVED")

    def test_resolution_requires_all_competitors_falsified(self):
        updated = m.U_update(
            state(),
            {
                "evidence_id": "e_beta_f",
                "provenance": "p2",
                "independence_group": "ig2",
                "evidence_kind": "DIRECT_TEST",
                "polarity": "FALSIFY",
                "target_branch_ids": ["b_beta"],
            },
        )
        result = m.D_resolve(
            updated,
            {"qualified": True, "evidence_kind": "DIRECT_TEST", "selected_branch_id": "b_alpha"},
        )
        self.assertEqual(result["resolution_state"], "RESOLVED_SYNTHETIC_TASK")
        self.assertEqual(result["resolved_branch_id"], "b_alpha")
        self.assertFalse(result["canonical_truth_minted"])

    def test_projection_filter_is_not_deletion(self):
        candidate = state()
        candidate["branches"][1]["projection_visibility"] = "FILTERED_BUT_RETAINED"
        m.validate_state(candidate)
        self.assertEqual(len(candidate["branches"]), 2)

    def test_discriminator_ranking_is_deterministic_and_not_probability(self):
        candidates = [
            {
                "discriminator_id": "d2",
                "separation_count": 2,
                "independence_score": 1.0,
                "cost": 2,
                "risk": 0,
                "coordination_cost": 0,
            },
            {
                "discriminator_id": "d1",
                "separation_count": 2,
                "independence_score": 1.0,
                "cost": 1,
                "risk": 0,
                "coordination_cost": 0,
            },
        ]
        out = m.U_d_test_order(candidates)
        self.assertEqual(out[0]["discriminator_id"], "d1")
        self.assertFalse(out[0]["score_is_probability"])

    def test_salience_never_truth_or_probability(self):
        out = m.f_salience_rank(
            [
                {"item_id": "i1", "decision_relevance": 5, "retrieval_cost": 1, "staleness_penalty": 0},
                {"item_id": "i2", "decision_relevance": 3, "retrieval_cost": 0, "staleness_penalty": 0},
            ]
        )
        self.assertEqual(out[0]["item_id"], "i1")
        self.assertFalse(out[0]["salience_is_probability"])
        self.assertFalse(out[0]["salience_is_truth"])

    def test_label_episode_emits_full_training_reference(self):
        episode = {
            "hyperposition_state_before": state(),
            "event_or_observation": {
                "evidence_id": "e1",
                "provenance": "p1",
                "independence_group": "ig1",
                "evidence_kind": "MEASUREMENT",
                "polarity": "SUPPORT",
                "target_branch_ids": ["b_alpha"],
            },
            "discriminator_result": None,
            "discriminator_candidates": [],
            "salience_items": [],
            "semantic_class_or_action": "ABSTAIN",
        }
        out = m.label_episode(episode)
        self.assertEqual(out["schema"], m.SCHEMA)
        self.assertEqual(out["resolution"]["resolution_state"], "UNRESOLVED")
        self.assertTrue(out["training_only_reference"])
        self.assertFalse(out["canonical_truth_minted"])


if __name__ == "__main__":
    unittest.main()
