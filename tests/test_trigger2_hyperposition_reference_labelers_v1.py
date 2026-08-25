import unittest

from tools.trigger2_hyperposition_reference_labelers_v1 import (
    BRANCH_SCHEMA,
    OBS_SCHEMA,
    TEST_SCHEMA,
    D_resolve,
    LabelerError,
    U_d_test_order,
    U_update,
    f_salience_rank,
    label_transition,
)


def ev(eid, ancestry, group, role="NONDECISIVE"):
    return {
        "evidence_id": eid,
        "provenance_ancestry_id": ancestry,
        "independence_group": group,
        "decision_role": role,
    }


def branches():
    def b(i, value):
        return {
            "schema": BRANCH_SCHEMA,
            "branch_id": i,
            "v_semantic_value": value,
            "K_context_predicate": "ALL",
            "E_plus": [],
            "E_minus": [],
            "F_falsifier": f"falsify:{i}",
            "T_validity_scope": "episode",
            "A_origin_provenance": "synthetic:test",
            "sigma_epistemic_status": "HYPOTHESIS",
            "projection_visibility": "VISIBLE",
            "validity": "LIVE",
        }
    return [b("b0", "A"), b("b1", "B"), b("b2", "C")]


class LabelersV1(unittest.TestCase):
    def test_support_updates_only_matching_branch(self):
        bs = branches()
        obs = {
            "schema": OBS_SCHEMA,
            "evidence": ev("e1", "src:a", "g1"),
            "branch_relations": {"b0": "SUPPORT", "b1": "NO_EFFECT", "b2": "NO_EFFECT"},
        }
        out = U_update(bs, obs)
        self.assertEqual(len(out[0]["E_plus"]), 1)
        self.assertEqual(out[1]["E_plus"], [])
        self.assertEqual(bs[0]["E_plus"], [])

    def test_duplicate_evidence_not_double_counted(self):
        bs = branches()
        item = ev("e1", "src:a", "g1")
        obs = {"schema": OBS_SCHEMA, "evidence": item, "branch_relations": {"b0": "SUPPORT", "b1": "NO_EFFECT", "b2": "NO_EFFECT"}}
        once = U_update(bs, obs)
        twice = U_update(once, obs)
        self.assertEqual(len(twice[0]["E_plus"]), 1)

    def test_falsifier_does_not_resolve_without_executed_discriminator(self):
        bs = branches()
        obs = {
            "schema": OBS_SCHEMA,
            "evidence": ev("e1", "src:a", "g1", "DECISIVE_CONTRADICTION"),
            "branch_relations": {"b0": "NO_EFFECT", "b1": "FALSIFY", "b2": "NO_EFFECT"},
        }
        after = U_update(bs, obs)
        r = D_resolve(after, {"context_id": "c", "discriminator_executed": False, "discriminator_admissible": True, "resolution_scope": "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE"})
        self.assertEqual(r["status"], "UNRESOLVED")

    def test_unique_branch_resolves_after_admissible_discriminator(self):
        bs = branches()
        bs[0]["E_plus"].append(ev("p", "src:p", "gp", "DECISIVE_SUPPORT"))
        bs[1]["validity"] = "FALSIFIED"
        bs[2]["validity"] = "FALSIFIED"
        r = D_resolve(bs, {"context_id": "c", "discriminator_executed": True, "discriminator_admissible": True, "resolution_scope": "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE"})
        self.assertEqual(r["status"], "RESOLVED_WITHIN_TASK")
        self.assertEqual(r["resolved_branch"], "b0")
        self.assertFalse(r["canonical_truth_minted"])

    def test_multiple_live_branches_never_majority_collapse(self):
        bs = branches()
        for i in range(5):
            bs[0]["E_plus"].append(ev(f"e{i}", f"src:{i}", f"g{i}"))
        r = D_resolve(bs, {"context_id": "c", "discriminator_executed": True, "discriminator_admissible": True, "resolution_scope": "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE"})
        self.assertEqual(r["status"], "UNRESOLVED")

    def test_discriminator_ranking_prefers_pair_coverage(self):
        bs = branches()
        tests = [
            {"schema": TEST_SCHEMA, "test_id": "t1", "admissible": True, "observable": True, "separates_branch_pairs": [["b0", "b1"]], "novel_independence_groups": 1, "cost_units": 1},
            {"schema": TEST_SCHEMA, "test_id": "t2", "admissible": True, "observable": True, "separates_branch_pairs": [["b0", "b1"], ["b0", "b2"], ["b1", "b2"]], "novel_independence_groups": 1, "cost_units": 3},
        ]
        ranked = U_d_test_order(bs, tests)
        self.assertEqual(ranked[0]["test_id"], "t2")
        self.assertIsNone(ranked[0]["truth_probability"])

    def test_inadmissible_discriminator_ranks_below_admissible(self):
        bs = branches()
        tests = [
            {"schema": TEST_SCHEMA, "test_id": "unsafe", "admissible": False, "observable": True, "separates_branch_pairs": [["b0", "b1"], ["b0", "b2"], ["b1", "b2"]], "novel_independence_groups": 3, "cost_units": 0},
            {"schema": TEST_SCHEMA, "test_id": "safe", "admissible": True, "observable": True, "separates_branch_pairs": [["b0", "b1"]], "novel_independence_groups": 0, "cost_units": 3},
        ]
        ranked = U_d_test_order(bs, tests)
        self.assertEqual(ranked[0]["test_id"], "safe")

    def test_salience_never_changes_truth(self):
        items = [
            {"item_id": "a", "decision_relevance": 3, "deadline_urgency": 2, "reentry_cost": 1},
            {"item_id": "b", "decision_relevance": 2, "deadline_urgency": 3, "reentry_cost": 0},
        ]
        ranked = f_salience_rank(items)
        self.assertEqual(ranked[0]["item_id"], "a")
        self.assertTrue(all(x["truth_status_changed"] is False for x in ranked))
        self.assertTrue(all(x["truth_probability"] is None for x in ranked))

    def test_salience_rejects_confidence_proxy(self):
        with self.assertRaises(LabelerError):
            f_salience_rank([{"item_id": "a", "decision_relevance": 3, "deadline_urgency": 2, "reentry_cost": 1, "confidence": 0.9}])

    def test_transition_never_mints_canonical_truth(self):
        bs = branches()
        obs = {"schema": OBS_SCHEMA, "evidence": ev("e1", "src:a", "g1"), "branch_relations": {"b0": "SUPPORT", "b1": "NO_EFFECT", "b2": "NO_EFFECT"}}
        ctx = {"context_id": "c", "discriminator_executed": False, "discriminator_admissible": True, "resolution_scope": "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE"}
        out = label_transition(bs, obs, ctx)
        self.assertFalse(out["canonical_truth_minted"])
        self.assertFalse(out["direct_effect_authority"])

    def test_merge_requires_exact_equivalence_certificate(self):
        bs = branches()
        bs[1]["v_semantic_value"] = bs[0]["v_semantic_value"]
        bs[1]["K_context_predicate"] = bs[0]["K_context_predicate"]
        bs[1]["T_validity_scope"] = bs[0]["T_validity_scope"]
        obs = {
            "schema": OBS_SCHEMA,
            "evidence": ev("noop", "src:m", "gm"),
            "branch_relations": {"b0": "NO_EFFECT", "b1": "NO_EFFECT", "b2": "NO_EFFECT"},
            "merge_directives": [{
                "source_branch_ids": ["b0", "b1"],
                "merged_branch_id": "b01",
                "equivalence_rule": "EXACT_SYNTHETIC_EQUIVALENCE",
                "equivalence_certificate_id": "cert-1",
            }],
        }
        out = U_update(bs, obs)
        by_id = {b["branch_id"]: b for b in out}
        self.assertEqual(by_id["b0"]["validity"], "OUT_OF_SCOPE")
        self.assertEqual(by_id["b1"]["validity"], "OUT_OF_SCOPE")
        self.assertEqual(by_id["b01"]["validity"], "LIVE")
        self.assertEqual(by_id["b01"]["merged_from"], ["b0", "b1"])

    def test_merge_rejects_embedding_similarity_proxy(self):
        bs = branches()
        obs = {
            "schema": OBS_SCHEMA,
            "evidence": ev("noop", "src:m", "gm"),
            "branch_relations": {"b0": "NO_EFFECT", "b1": "NO_EFFECT", "b2": "NO_EFFECT"},
            "merge_directives": [{
                "source_branch_ids": ["b0", "b1"],
                "merged_branch_id": "b01",
                "equivalence_rule": "EMBEDDING_SIMILARITY",
                "equivalence_certificate_id": "bad",
            }],
        }
        with self.assertRaises(LabelerError):
            U_update(bs, obs)

    def test_branch_relation_must_cover_exact_set(self):
        bs = branches()
        obs = {"schema": OBS_SCHEMA, "evidence": ev("e1", "src:a", "g1"), "branch_relations": {"b0": "SUPPORT"}}
        with self.assertRaises(LabelerError):
            U_update(bs, obs)


if __name__ == "__main__":
    unittest.main()
