from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import unittest
from unittest.mock import patch

from tools import trigger1_jspace_promotion_gate_v12 as gate


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_plan() -> dict:
    return gate.case_plan.build_plan()


def candidate() -> dict:
    plan = load_plan()
    geo = h("geometry")
    rank_receipt = h("rank")
    centroid_receipt = h("centroids")
    cvec = {target: h("cvec:" + target) for target in gate.TARGETS}
    emission = {
        "emission_receipt_sha256": h("emission"),
        "target_cvecs": {target: {"cvec_sha256": digest} for target, digest in cvec.items()},
    }
    centroids = {"AFFIRMATIVE": [1.0], "NEGATIVE": [0.0], "NEUTRAL": [-1.0]}

    abstract_runtime = []
    for frozen in plan["holdout_case_rows"]:
        target = frozen["semantic_target"]
        center = centroids[target][0]
        arms = {
            "BASELINE": {
                "runtime_receipt_sha256": h(f"abs:{frozen['case_id']}:base"),
                "cvec_sha256": None,
                "downstream_projection": [center + 2.0],
                "behavior_target_margin": 0.0,
            }
        }
        for semantic in gate.TARGETS:
            matched = semantic == target
            arms[f"CVEC_{semantic}"] = {
                "runtime_receipt_sha256": h(f"abs:{frozen['case_id']}:{semantic}"),
                "cvec_sha256": cvec[semantic],
                "downstream_projection": [center if matched else center + 2.5],
                "behavior_target_margin": 3.0 if matched else 0.5,
            }
        abstract_runtime.append({
            **{key: frozen[key] for key in (
                "case_id", "prompt_sha256", "scenario_family_sha256", "lexical_family_sha256",
                "semantic_target", "output_code_identity",
            )},
            "arms": arms,
        })

    abstract = {
        "schema": gate.ABSTRACT_SCHEMA,
        "case_plan_sha256": gate.EXPECTED_PLAN_SHA,
        "case_plan_source_sha256": gate.EXPECTED_PLAN_SOURCE_SHA,
        "fixed_scaffold_tokens": plan["fixed_scaffold_tokens"],
        "calibration_case_rows": plan["calibration_case_rows"],
        "holdout_case_rows": plan["holdout_case_rows"],
        "native_geometry_receipt_sha256": geo,
        "rank_analysis_receipt_sha256": rank_receipt,
        "calibration_centroid_receipt_sha256": centroid_receipt,
        "representation_rank": 1,
        "target_centroids": centroids,
        "holdout_runtime_rows": abstract_runtime,
    }
    abstract["evidence_receipt_sha256"] = gate.canonical_sha(abstract)

    temporal_rows = []
    for frozen in plan["holdout_case_rows"]:
        target = frozen["semantic_target"]
        center = centroids[target][0]
        projections = {
            "BASELINE_SINGLE": center + 2.0,
            "BASELINE_SPLIT": center + 2.0,
            "BROADCAST_SINGLE": center,
            "BROADCAST_SPLIT": center,
            "LAST_TOKEN_ONLY": center + 0.5,
            "PREFIX_ONLY": center + 1.9,
        }
        behavior = {
            "BASELINE_SINGLE": 0.0,
            "BASELINE_SPLIT": 0.0,
            "BROADCAST_SINGLE": 4.0,
            "BROADCAST_SPLIT": 4.0,
            "LAST_TOKEN_ONLY": 3.5,
            "PREFIX_ONLY": 0.4,
        }
        arms = {}
        for arm in gate.TEMPORAL_ARMS:
            arms[arm] = {
                "runtime_receipt_sha256": h(f"tmp:{frozen['case_id']}:{arm}"),
                "cvec_sha256": None if arm.startswith("BASELINE") else cvec[target],
                "downstream_projection": [projections[arm]],
                "behavior_target_margin": behavior[arm],
            }
        temporal_rows.append({
            **{key: frozen[key] for key in (
                "case_id", "prompt_sha256", "scenario_family_sha256", "semantic_target", "output_code_identity",
            )},
            "arms": arms,
        })
    temporal = {
        "schema": gate.TEMPORAL_SCHEMA,
        "native_api": gate.NATIVE_API,
        "same_vector_layer_gain_across_scope_arms": True,
        "prefix_kv_computed_before_last_token_arm": True,
        "cvec_clear_uses_null_data_api": True,
        "harness_source_sha256": h("temporal-harness"),
        "target_cvec_sha256": cvec,
        "preregistered_thresholds": {
            "min_last_token_recovery_fraction": 0.75,
            "max_last_token_recovery_deviation": 0.25,
            "max_prefix_only_fraction": 0.25,
            "max_batch_partition_fraction": 0.10,
        },
        "rows": temporal_rows,
    }
    temporal["evidence_receipt_sha256"] = gate.canonical_sha(temporal)

    return {
        "native_carrier_geometry": {"geometry_receipt_sha256": geo},
        "semantic_simplex_rank": {"analysis_receipt_sha256": rank_receipt},
        "native_q8_target_cvec_emission": emission,
        "abstract_state_evidence": abstract,
        "temporal_scope_evidence": temporal,
    }


class V12HardBlockerTests(unittest.TestCase):
    def test_frozen_plan_is_six_by_three_balanced_and_lexically_disjoint(self):
        plan = load_plan()
        self.assertEqual(plan["schema"], gate.case_plan.SCHEMA)
        self.assertEqual(plan["plan_sha256"], gate.EXPECTED_PLAN_SHA)
        for key in ("calibration_case_rows", "holdout_case_rows"):
            rows = plan[key]
            self.assertEqual(len(rows), 18)
            counts = Counter((row["semantic_target"], row["output_code_identity"]) for row in rows)
            self.assertEqual(set(counts.values()), {2})
            marker = Counter((row["semantic_target"], row["marker_slot"]) for row in rows)
            self.assertEqual(set(marker.values()), {2})
            by_family = defaultdict(list)
            for row in rows:
                by_family[row["scenario_family_sha256"]].append(row)
            self.assertEqual(len(by_family), 6)
            for family_rows in by_family.values():
                bags = [Counter(gate._tokens(row["prompt"], set(plan["fixed_scaffold_tokens"]))) for row in family_rows]
                self.assertEqual(bags[0], bags[1])
                self.assertEqual(bags[1], bags[2])
        cal_vocab = set().union(*(set(gate._tokens(row["prompt"], set(plan["fixed_scaffold_tokens"]))) for row in plan["calibration_case_rows"]))
        hold_vocab = set().union(*(set(gate._tokens(row["prompt"], set(plan["fixed_scaffold_tokens"]))) for row in plan["holdout_case_rows"]))
        self.assertFalse(cal_vocab & hold_vocab)

    def test_positive_synthetic_hard_evidence_passes_extra_gate(self):
        c = candidate()
        abstract = gate.abstract_gate(c, load_plan())
        temporal = gate.temporal_gate(c, load_plan())
        self.assertTrue(abstract["pass"], abstract["failures"])
        self.assertTrue(temporal["pass"], temporal["failures"])

    def test_direct_semantic_label_in_frozen_case_copy_fails(self):
        import copy
        plan = copy.deepcopy(load_plan())
        row = plan["holdout_case_rows"][0]
        row["prompt"] += " AFFIRMATIVE"
        row["prompt_sha256"] = h(row["prompt"])
        failures = gate.plan_invariants(plan)
        self.assertTrue(any("DIRECT_CUE" in x for x in failures))

    def test_target_cvec_identity_cannot_be_swapped(self):
        c = candidate()
        row = c["temporal_scope_evidence"]["rows"][0]
        target = row["semantic_target"]
        other = next(x for x in gate.TARGETS if x != target)
        row["arms"]["LAST_TOKEN_ONLY"]["cvec_sha256"] = c["temporal_scope_evidence"]["target_cvec_sha256"][other]
        c["temporal_scope_evidence"]["evidence_receipt_sha256"] = gate.canonical_sha({k:v for k,v in c["temporal_scope_evidence"].items() if k != "evidence_receipt_sha256"})
        result = gate.temporal_gate(c, load_plan())
        self.assertFalse(result["pass"])
        self.assertTrue(any("TEMPORAL_CVEC_IDENTITY_MISMATCH" in x for x in result["failures"]))

    def test_prefix_sufficiency_rejects_last_token_equivalence(self):
        c = candidate()
        for row in c["temporal_scope_evidence"]["rows"]:
            target = row["semantic_target"]
            center = c["abstract_state_evidence"]["target_centroids"][target][0]
            row["arms"]["PREFIX_ONLY"]["downstream_projection"] = [center + 0.2]
            row["arms"]["PREFIX_ONLY"]["behavior_target_margin"] = 3.0
        c["temporal_scope_evidence"]["evidence_receipt_sha256"] = gate.canonical_sha({k:v for k,v in c["temporal_scope_evidence"].items() if k != "evidence_receipt_sha256"})
        result = gate.temporal_gate(c, load_plan())
        self.assertFalse(result["pass"])
        self.assertTrue(any("TEMPORAL_PREFIX_EFFECT_TOO_LARGE" in x for x in result["failures"]))

    def test_v12_requires_v11_and_both_new_blockers(self):
        c = candidate()
        with patch.object(gate.v11, "adjudicate", return_value={
            "abstract_native_semantic_jspace_candidate": True,
            "owner_trigger1_goal_credit_candidate": True,
            "full_native_jspace_vector_control_candidate": True,
            "v11_failures": [],
        }):
            result = gate.adjudicate(c)
        self.assertTrue(result["source_frozen_abstract_native_semantic_jspace_candidate"], result["v12_failures"])
        self.assertFalse(result["canonical_credit_minted"])
        self.assertFalse(result["jspace_model_runtime_credit"])


if __name__ == "__main__":
    unittest.main()
