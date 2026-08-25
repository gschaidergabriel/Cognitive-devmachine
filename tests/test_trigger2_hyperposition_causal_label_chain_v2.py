import copy
import unittest

from tools.trigger2_hyperposition_causal_label_chain_v2 import (
    DerivationError,
    EVENT_REGISTRY_SCHEMA,
    WORLD_SCHEMA,
    derive_label_chain,
)


def branch(bid, *, k="APPLIES"):
    return {
        "branch_id": bid,
        "v": bid,
        "K": k,
        "E_plus": [],
        "E_minus": [],
        "F": [],
        "T": "episode",
        "A": {"origin": "synthetic"},
        "sigma": "LIVE_UNRESOLVED",
        "projection_visibility": "VISIBLE",
    }


def state():
    return {"branches": [branch("b0"), branch("b1"), branch("b2")]}


def world():
    return {
        "schema": WORLD_SCHEMA,
        "world_id": "w",
        "branches": [
            {
                "branch_id": "b0",
                "semantic_value": "b0",
                "K": "APPLIES",
                "T": "episode",
                "predicted_outcomes": {"exact": "YES", "signal": "HOT"},
            },
            {
                "branch_id": "b1",
                "semantic_value": "b1",
                "K": "APPLIES",
                "T": "episode",
                "predicted_outcomes": {"exact": "NO", "signal": "COLD"},
            },
            {
                "branch_id": "b2",
                "semantic_value": "b2",
                "K": "APPLIES",
                "T": "episode",
                "predicted_outcomes": {"exact": "NO", "signal": "HOT"},
            },
        ],
        "tests": [
            {
                "test_id": "exact",
                "mode": "EXACT_FOR_SCOPE",
                "outcome_domain": ["YES", "NO"],
            },
            {
                "test_id": "signal",
                "mode": "NONDECISIVE_SIGNAL",
                "outcome_domain": ["HOT", "COLD"],
            },
        ],
    }


def registry():
    return {
        "schema": EVENT_REGISTRY_SCHEMA,
        "world_id": "w",
        "events": {
            "root": {
                "test_id": "exact",
                "observed_outcome": "YES",
                "source_id": "sensor-a",
                "depends_on_event_ids": [],
            },
            "relay": {
                "test_id": "exact",
                "observed_outcome": "YES",
                "source_id": "relay-b",
                "depends_on_event_ids": ["root"],
            },
            "soft": {
                "test_id": "signal",
                "observed_outcome": "HOT",
                "source_id": "sensor-c",
                "depends_on_event_ids": [],
            },
        },
    }


class HyperpositionCausalLabelChainV2(unittest.TestCase):
    def test_exact_event_resolves_unique_matching_branch(self):
        out = derive_label_chain(state(), world(), registry(), "root")
        self.assertEqual(
            out["resolution"],
            {"resolution": "PASS", "selected_branch_id": "b0"},
        )
        by_id = {b["branch_id"]: b for b in out["state_resolved"]["branches"]}
        self.assertEqual(by_id["b0"]["sigma"], "RESOLVED_PASS")
        self.assertEqual(by_id["b1"]["sigma"], "FALSIFIED")
        self.assertEqual(by_id["b2"]["sigma"], "FALSIFIED")
        self.assertFalse(out["canonical_truth_minted"])
        self.assertEqual(out["training_credit_minted"], 0)

    def test_nondecisive_signal_weakens_without_resolution(self):
        out = derive_label_chain(state(), world(), registry(), "soft")
        self.assertEqual(out["resolution"]["resolution"], "UNRESOLVED")
        by_id = {b["branch_id"]: b for b in out["state_after"]["branches"]}
        self.assertEqual(by_id["b0"]["sigma"], "SUPPORTED_UNRESOLVED")
        self.assertEqual(by_id["b2"]["sigma"], "SUPPORTED_UNRESOLVED")
        self.assertEqual(by_id["b1"]["sigma"], "WEAKENED_UNRESOLVED")
        self.assertNotEqual(by_id["b1"]["sigma"], "FALSIFIED")

    def test_caller_cannot_assert_relation_or_independence_identity(self):
        forbidden = (
            "relation",
            "target_branch_ids",
            "winner_branch_id",
            "independence_group",
            "independence_qualified",
            "payload_key",
            "correlation_ancestry_id",
        )
        for field in forbidden:
            with self.subTest(field=field):
                r = registry()
                r["events"]["root"][field] = "attacker-value"
                with self.assertRaises(DerivationError):
                    derive_label_chain(state(), world(), r, "root")

    def test_dependency_graph_derives_shared_ancestry_and_no_independent_credit(self):
        root = derive_label_chain(state(), world(), registry(), "root")
        relay = derive_label_chain(root["state_after"], world(), registry(), "relay")
        root_identity = root["derivation_receipt"]["event_identity"]
        relay_identity = relay["derivation_receipt"]["event_identity"]
        self.assertEqual(
            root_identity["correlation_ancestry_id"],
            relay_identity["correlation_ancestry_id"],
        )
        self.assertTrue(root_identity["independence_qualified"])
        self.assertFalse(relay_identity["independence_qualified"])
        by_id = {b["branch_id"]: b for b in relay["state_after"]["branches"]}
        self.assertTrue(by_id["b0"].get("correlated_observations"))
        self.assertTrue(
            all(
                event["independent_credit"] is False
                for event in by_id["b0"]["correlated_observations"]
            )
        )

    def test_dependency_cycle_is_rejected(self):
        r = registry()
        r["events"]["root"]["depends_on_event_ids"] = ["relay"]
        with self.assertRaises(DerivationError):
            derive_label_chain(state(), world(), r, "root")

    def test_unknown_prediction_stays_live_and_prevents_false_resolution(self):
        w = world()
        del w["branches"][2]["predicted_outcomes"]["exact"]
        out = derive_label_chain(state(), w, registry(), "root")
        relations = {
            x["branch_id"]: x["relation"]
            for x in out["derivation_receipt"]["branch_relations"]
        }
        self.assertEqual(relations["b2"], "UNKNOWN_RELATION")
        self.assertEqual(out["resolution"]["resolution"], "UNRESOLVED")
        by_id = {b["branch_id"]: b for b in out["state_after"]["branches"]}
        self.assertEqual(by_id["b2"]["sigma"], "LIVE_UNRESOLVED")

    def test_state_world_semantic_k_and_t_alignment_is_fail_closed(self):
        mutations = (
            ("v", "DIFFERENT"),
            ("K", "UNKNOWN"),
            ("T", "other-scope"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                s = state()
                s["branches"][0][field] = value
                with self.assertRaises(DerivationError):
                    derive_label_chain(s, world(), registry(), "root")

    def test_exact_event_replay_is_idempotent(self):
        first = derive_label_chain(state(), world(), registry(), "root")
        second = derive_label_chain(first["state_after"], world(), registry(), "root")
        self.assertEqual(first["state_after"], second["state_after"])
        self.assertEqual(first["resolution"], second["resolution"])

    def test_event_dependency_repackaging_cannot_change_root_payload_identity(self):
        r1 = registry()
        a = derive_label_chain(state(), world(), r1, "relay")
        r2 = registry()
        r2["events"]["relay"]["source_id"] = "different-wrapper"
        b = derive_label_chain(state(), world(), r2, "relay")
        ia = a["derivation_receipt"]["event_identity"]
        ib = b["derivation_receipt"]["event_identity"]
        self.assertEqual(ia["correlation_ancestry_id"], ib["correlation_ancestry_id"])
        self.assertEqual(ia["payload_key"], ib["payload_key"])
        self.assertFalse(ia["independence_qualified"])
        self.assertFalse(ib["independence_qualified"])


if __name__ == "__main__":
    unittest.main()
