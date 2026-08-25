#!/usr/bin/env python3
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


d = load(ROOT / "tools" / "trigger2_synthetic_taskworld_relation_deriver_v1.py", "tr2derive")
lab = load(ROOT / "tools" / "trigger2_hyperposition_reference_labelers_v2.py", "tr2labelv2")


def decisive_world(signal: str = "signal_allow(a)"):
    return {
        "schema": d.WORLD_SCHEMA,
        "world_id": "world-decisive",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "base_facts": ["kind(a)"],
        "rules": [
            {"rule_id": "r_allow", "if_all": ["kind(a)", "signal_allow(a)"], "then": "allow(a)"},
            {"rule_id": "r_not_deny", "if_all": ["kind(a)", "signal_allow(a)"], "then": "!deny(a)"},
            {"rule_id": "r_deny", "if_all": ["kind(a)", "signal_deny(a)"], "then": "deny(a)"},
            {"rule_id": "r_not_allow", "if_all": ["kind(a)", "signal_deny(a)"], "then": "!allow(a)"},
        ],
        "branches": [
            {"branch_id": "b_allow", "claim_literal": "allow(a)"},
            {"branch_id": "b_deny", "claim_literal": "deny(a)"},
        ],
        "observation": {
            "evidence_event_id": "event-001",
            "correlation_ancestry_id": "sensor-family-001",
            "independence_group": "sensor-group-001",
            "provenance": "synthetic-fixture",
            "independence_qualified": True,
            "add_facts": [signal],
        },
    }


def hp_state():
    def branch(bid, value):
        return {
            "branch_id": bid,
            "v": value,
            "K": "APPLIES",
            "E_plus": [],
            "E_minus": [],
            "F": [],
            "pending_falsifiers": [],
            "correlated_observations": [],
            "T": "synthetic_episode",
            "A": {"origin": "fixture"},
            "sigma": "LIVE_UNRESOLVED",
            "projection_visibility": "VISIBLE",
        }
    return {"query_id": "q", "branches": [branch("b_allow", "ALLOW"), branch("b_deny", "DENY")]}


class TestSyntheticTaskworldRelationDeriverV1(unittest.TestCase):
    def test_decisive_support_and_competitor_falsification_are_derived(self):
        receipt = d.derive(decisive_world())
        self.assertEqual(
            receipt["relation_by_branch"],
            {"b_allow": "SUPPORTS", "b_deny": "FALSIFIES"},
        )
        self.assertEqual(receipt["decision_role"], "DECISIVE_SUPPORT")
        self.assertEqual(receipt["selected_branch_id"], "b_allow")
        self.assertTrue(d.verify_receipt(receipt))

    def test_caller_cannot_inject_relation_or_target(self):
        for key, value in (
            ("relation", "SUPPORTS"),
            ("branch_relations", {"b_allow": "SUPPORTS"}),
            ("target_branch_ids", ["b_allow"]),
            ("decision_role", "DECISIVE_SUPPORT"),
            ("winner_branch_id", "b_allow"),
        ):
            world = decisive_world()
            world["observation"][key] = value
            with self.assertRaises(d.DerivationError):
                d.derive(world)

    def test_mutating_formal_observation_flips_semantic_result(self):
        allow = d.derive(decisive_world("signal_allow(a)"))
        deny = d.derive(decisive_world("signal_deny(a)"))
        self.assertEqual(allow["selected_branch_id"], "b_allow")
        self.assertEqual(deny["selected_branch_id"], "b_deny")
        self.assertEqual(deny["relation_by_branch"]["b_allow"], "FALSIFIES")
        self.assertEqual(deny["relation_by_branch"]["b_deny"], "SUPPORTS")
        self.assertNotEqual(allow["receipt_sha256"], deny["receipt_sha256"])

    def test_unrelated_observation_is_nondecisive_and_irrelevant(self):
        world = decisive_world("noise(a)")
        receipt = d.derive(world)
        self.assertEqual(
            receipt["relation_by_branch"],
            {"b_allow": "IRRELEVANT", "b_deny": "IRRELEVANT"},
        )
        self.assertEqual(receipt["decision_role"], "NONDECISIVE")
        self.assertIsNone(receipt["selected_branch_id"])

    def test_explicit_contradiction_is_counter_not_falsification(self):
        world = decisive_world()
        world["observation"]["add_facts"] = ["allow(a)", "!allow(a)"]
        receipt = d.derive(world)
        self.assertEqual(receipt["relation_by_branch"]["b_allow"], "COUNTERS")
        self.assertEqual(receipt["truth_after_by_branch"]["b_allow"], "BOTH")
        self.assertEqual(receipt["decision_role"], "NONDECISIVE")

    def test_branch_permutation_is_equivariant(self):
        world_a = decisive_world()
        world_b = decisive_world()
        world_b["branches"] = list(reversed(world_b["branches"]))
        a = d.derive(world_a)
        b = d.derive(world_b)
        self.assertEqual(a["relation_by_branch"], b["relation_by_branch"])
        self.assertEqual(a["truth_after_by_branch"], b["truth_after_by_branch"])
        self.assertEqual(a["selected_branch_id"], b["selected_branch_id"])

    def test_receipt_tamper_is_detected(self):
        receipt = d.derive(decisive_world())
        bad = copy.deepcopy(receipt)
        bad["relation_by_branch"]["b_allow"] = "FALSIFIES"
        self.assertFalse(d.verify_receipt(bad))

    def test_derived_packets_share_event_and_receipt_identity(self):
        receipt = d.derive(decisive_world())
        self.assertEqual(len(receipt["derived_observations"]), 2)
        for packet in receipt["derived_observations"]:
            self.assertEqual(packet["evidence_event_id"], "event-001")
            self.assertEqual(packet["correlation_ancestry_id"], "sensor-family-001")
            self.assertEqual(packet["derivation_receipt_sha256"], receipt["receipt_sha256"])
            self.assertFalse(packet["canonical_truth_allowed"])
            self.assertFalse(packet["direct_effect_authority"])

    def test_current_labeler_v2_can_consume_only_verified_derived_packets(self):
        receipt = d.derive(decisive_world())
        after = d.apply_to_labeler_v2(hp_state(), receipt, lab)
        by_id = {b["branch_id"]: b for b in after["branches"]}
        self.assertEqual(by_id["b_allow"]["sigma"], "SUPPORTED_UNRESOLVED")
        self.assertEqual(by_id["b_deny"]["sigma"], "FALSIFIED")
        resolution = lab.d_resolve(after)
        self.assertEqual(resolution, {"resolution": "PASS", "selected_branch_id": "b_allow"})

    def test_credit_and_authority_remain_zero_false(self):
        receipt = d.derive(decisive_world())
        self.assertFalse(receipt["canonical_truth_minted"])
        self.assertFalse(receipt["direct_effect_authority_minted"])
        self.assertFalse(receipt["runtime_credit_minted"])
        self.assertFalse(receipt["jspace_model_runtime_credit_minted"])
        self.assertFalse(receipt["training_credit_minted"])
        self.assertTrue(receipt["synthetic_task_only"])


if __name__ == "__main__":
    unittest.main()
