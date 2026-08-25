import copy
import unittest

from tools.trigger2_synthetic_hyperposition_oracle_v1 import (
    OracleError,
    WORLD_SCHEMA,
    apply_event,
    derive_observations,
    sha256_json,
)


def world():
    return {
        "schema": WORLD_SCHEMA,
        "world_id": "w",
        "tests": {
            "probe": {"kind": "FINITE_OUTCOME_EQUALITY"},
            "signal": {"kind": "FINITE_OUTCOME_NOISY_SIGNAL"},
        },
        "branch_predictions": {
            "b0": {"probe": "YES", "signal": "HOT"},
            "b1": {"probe": "NO", "signal": "COLD"},
            "b2": {"probe": "NO", "signal": "HOT"},
        },
        "events": {
            "root": {
                "test_id": "probe",
                "observed_outcome": "YES",
                "source_id": "sensor-a",
                "depends_on_event_ids": [],
                "provenance": "synthetic:w:root",
            },
            "relay": {
                "test_id": "probe",
                "observed_outcome": "YES",
                "source_id": "relay-b",
                "depends_on_event_ids": ["root"],
                "provenance": "synthetic:w:relay",
            },
        },
    }


def state():
    def b(bid):
        return {
            "branch_id": bid,
            "v": bid,
            "K": "APPLIES",
            "E_plus": [],
            "E_minus": [],
            "F": [],
            "T": "episode",
            "A": {"origin": "synthetic"},
            "sigma": "LIVE_UNRESOLVED",
            "projection_visibility": "VISIBLE",
        }

    return {"branches": [b("b0"), b("b1"), b("b2")]}


class SyntheticHyperpositionOracleV1(unittest.TestCase):
    def test_exact_world_derives_relations_without_supplied_labels(self):
        out = derive_observations(world(), "root")
        by_relation = {
            x["relation"]: tuple(x["target_branch_ids"])
            for x in out["derived_observations"]
        }
        self.assertEqual(by_relation["SUPPORTS"], ("b0",))
        self.assertEqual(by_relation["FALSIFIES"], ("b1", "b2"))
        self.assertEqual(out["model_visible_fields"], [])
        self.assertTrue(out["evaluator_only"])

    def test_direct_prelabels_are_rejected(self):
        w = world()
        w["events"]["root"]["relation"] = "SUPPORTS"
        with self.assertRaises(OracleError):
            derive_observations(w, "root")

    def test_counterfactual_outcome_changes_entailed_relations_and_hash(self):
        a = derive_observations(world(), "root")
        w = world()
        w["events"]["root"]["observed_outcome"] = "NO"
        b = derive_observations(w, "root")
        self.assertNotEqual(
            a["derived_observations_sha256"],
            b["derived_observations_sha256"],
        )
        amap = {
            bid: rel
            for rel, bids in (
                (x["relation"], x["target_branch_ids"])
                for x in a["derived_observations"]
            )
            for bid in bids
        }
        bmap = {
            bid: rel
            for rel, bids in (
                (x["relation"], x["target_branch_ids"])
                for x in b["derived_observations"]
            )
            for bid in bids
        }
        self.assertEqual(amap["b0"], "SUPPORTS")
        self.assertEqual(bmap["b0"], "FALSIFIES")
        self.assertEqual(bmap["b1"], "SUPPORTS")
        self.assertEqual(bmap["b2"], "SUPPORTS")

    def test_branch_map_order_is_nuisance(self):
        a = derive_observations(world(), "root")
        w = world()
        w["branch_predictions"] = dict(
            reversed(list(w["branch_predictions"].items()))
        )
        b = derive_observations(w, "root")
        self.assertEqual(
            a["derived_observations_sha256"],
            b["derived_observations_sha256"],
        )

    def test_dependency_graph_derives_shared_ancestry_and_no_independent_credit(self):
        root = derive_observations(world(), "root")
        relay = derive_observations(world(), "relay")
        r0 = root["derived_observations"][0]
        r1 = relay["derived_observations"][0]
        self.assertEqual(
            r0["correlation_ancestry_id"],
            r1["correlation_ancestry_id"],
        )
        self.assertTrue(r0["independence_qualified"])
        self.assertFalse(r1["independence_qualified"])

    def test_world_hash_changes_on_semantic_mutation(self):
        a = world()
        b = copy.deepcopy(a)
        b["branch_predictions"]["b1"]["probe"] = "YES"
        self.assertNotEqual(sha256_json(a), sha256_json(b))

    def test_unknown_prediction_never_gets_falsified(self):
        w = world()
        w["branch_predictions"]["b2"]["probe"] = "UNKNOWN"
        out = derive_observations(w, "root")
        by_relation = {
            x["relation"]: set(x["target_branch_ids"])
            for x in out["derived_observations"]
        }
        self.assertIn("b2", by_relation["UNKNOWN_RELATION"])
        self.assertNotIn("b2", by_relation.get("FALSIFIES", set()))

    def test_exact_equality_event_resolves_through_current_labeler(self):
        out = apply_event(state(), world(), "root")
        self.assertEqual(
            out["resolution"],
            {"resolution": "PASS", "selected_branch_id": "b0"},
        )
        self.assertFalse(out["canonical_truth_minted"])
        self.assertFalse(out["training_credit_minted"])

    def test_noisy_signal_weakens_without_resolution(self):
        w = world()
        w["events"]["root"] = {
            "test_id": "signal",
            "observed_outcome": "HOT",
            "source_id": "sensor-a",
            "depends_on_event_ids": [],
            "provenance": "synthetic:w:root",
        }
        out = apply_event(state(), w, "root")
        self.assertEqual(out["resolution"]["resolution"], "UNRESOLVED")
        by_id = {b["branch_id"]: b for b in out["state_after"]["branches"]}
        self.assertEqual(by_id["b1"]["sigma"], "WEAKENED_UNRESOLVED")
        self.assertNotEqual(by_id["b1"]["sigma"], "FALSIFIED")


if __name__ == "__main__":
    unittest.main()
