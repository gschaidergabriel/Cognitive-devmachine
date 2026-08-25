import copy
import json
import unittest
from pathlib import Path

from tools import trigger2_qwen35_checkpoint_candidates_gate_v3 as g

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research_entity/global/j-space/research/trigger2_qwen35_08b_checkpoint_candidates_v2.json"
with REGISTRY.open(encoding="utf-8") as fh:
    BASE = json.load(fh)


def candidate(x, cid):
    return next(c for c in x["candidates"] if c["candidate_id"] == cid)


class Trigger2CheckpointCandidatesGateV3Test(unittest.TestCase):
    def test_current_registry_is_source_integrity_valid_but_never_selection_ready(self):
        r = g.adjudicate(copy.deepcopy(BASE))
        self.assertTrue(r["pass"], r["failures"])
        self.assertTrue(r["registry_source_integrity_valid"])
        self.assertFalse(r["selection_ready"])
        self.assertIsNone(r["checkpoint_winner"])
        self.assertFalse(r["training_credit_minted"])
        self.assertFalse(r["jspace_credit_minted"])
        for cid in g.BOUND_MEASURED:
            n = r["normalized_candidates"][cid]
            self.assertTrue(n["snapshot_registry_identity_complete"])
            self.assertTrue(n["matched_baseline_participation_eligible"])
            self.assertTrue(n["loader_smoke_observed"])
            self.assertFalse(n["selection_input_identity_complete"])
            self.assertFalse(n["winner_eligible"])
            self.assertIsNone(n["consumed_identity_match"])

    def test_qwen35_text_architecture_is_normalized_from_nested_text_config(self):
        r = g.adjudicate(copy.deepcopy(BASE))
        arch = r["normalized_candidates"]["QWEN35_08B_BASE"]["architecture"]
        self.assertEqual(arch["model_type"], "qwen3_5")
        self.assertEqual(arch["text_model_type"], "qwen3_5_text")
        self.assertEqual(arch["num_hidden_layers"], 24)
        self.assertEqual(arch["hidden_size"], 1024)
        self.assertEqual(arch["num_attention_heads"], 8)
        self.assertEqual(arch["num_key_value_heads"], 2)
        self.assertEqual(arch["vocab_size"], 248320)
        self.assertEqual(arch["max_position_embeddings"], 262144)

    def test_controls_may_join_matched_baseline_without_becoming_winner_eligible(self):
        r = g.adjudicate(copy.deepcopy(BASE))
        for cid in ("QWEN35_08B_BASE", "QWEN35_08B_POSTTRAINED"):
            n = r["normalized_candidates"][cid]
            self.assertTrue(n["matched_baseline_participation_eligible"])
            self.assertFalse(n["winner_eligible"])

    def test_consumed_identity_cannot_be_self_minted_from_loader_smoke(self):
        x = copy.deepcopy(BASE)
        target = candidate(x, "QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED")
        target["consumed_identity_match"] = True
        self.assertIn(
            "CONSUMED_IDENTITY_MATCH_UNSUPPORTED_BY_CURRENT_RECEIPTS:QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED",
            g.adjudicate(x)["failures"],
        )

    def test_target_weight_hash_if_declared_must_belong_to_bound_snapshot_manifest(self):
        x = copy.deepcopy(BASE)
        target = candidate(x, "QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED")
        target["weights_sha256"] = "0" * 64
        self.assertIn(
            "REGISTRY_WEIGHT_NOT_IN_BOUND_MANIFEST:QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED",
            g.adjudicate(x)["failures"],
        )

    def test_target_preserves_multiple_weight_artifacts_instead_of_inventing_one_consumed_hash(self):
        r = g.adjudicate(copy.deepcopy(BASE))
        weights = r["normalized_candidates"]["QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED"]["weight_manifest"]
        paths = {row["path"] for row in weights}
        self.assertIn("model.safetensors", paths)
        self.assertIn("model.safetensors-00001-of-00001.safetensors", paths)
        self.assertEqual(len(weights), 2)

    def test_snapshot_digest_mutation_fails_closed(self):
        x = copy.deepcopy(BASE)
        base = candidate(x, "QWEN35_08B_BASE")
        base["file_manifest_sha256"] = "0" * 64
        self.assertIn(
            "REGISTRY_RECEIPT_DIGEST_MISMATCH:QWEN35_08B_BASE:file_manifest_sha256",
            g.adjudicate(x)["failures"],
        )

    def test_revision_mutation_fails_closed(self):
        x = copy.deepcopy(BASE)
        base = candidate(x, "QWEN35_08B_BASE")
        base["immutable_revision"] = "0" * 40
        self.assertIn(
            "REGISTRY_RECEIPT_REVISION_MISMATCH:QWEN35_08B_BASE",
            g.adjudicate(x)["failures"],
        )

    def test_external_unmeasured_candidate_cannot_join_matched_baseline(self):
        x = copy.deepcopy(BASE)
        ext = candidate(x, "QWEN35_08B_LEW_ABLITERATED_EXTERNAL")
        ext["selection_eligible"] = True
        self.assertIn(
            "UNBOUND_CANDIDATE_CANNOT_JOIN_MATCHED_BASELINE:QWEN35_08B_LEW_ABLITERATED_EXTERNAL",
            g.adjudicate(x)["failures"],
        )

    def test_loader_observation_must_match_bound_receipt(self):
        x = copy.deepcopy(BASE)
        base = candidate(x, "QWEN35_08B_BASE")
        base["loader_consumption_observed"] = False
        self.assertIn(
            "LOADER_OBSERVATION_DECLARATION_MISMATCH:QWEN35_08B_BASE",
            g.adjudicate(x)["failures"],
        )

    def test_source_registry_cannot_select_winner_or_self_attest_matched_pilot(self):
        x = copy.deepcopy(BASE)
        x["selected_candidate"] = "QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED"
        x["matched_pilot_contract"]["matched_pilot_executed"] = True
        failures = g.adjudicate(x)["failures"]
        self.assertIn("SOURCE_REGISTRY_CANNOT_SELECT_WINNER", failures)
        self.assertIn("SOURCE_REGISTRY_CANNOT_SELF_ATTEST_MATCHED_PILOT", failures)

    def test_standalone_chat_template_is_derived_as_snapshot_fact_not_runtime_consumption(self):
        r = g.adjudicate(copy.deepcopy(BASE))
        target = r["normalized_candidates"]["QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED"]
        self.assertEqual(target["chat_template"]["status"], "STANDALONE_FILE_PRESENT")
        self.assertEqual(
            target["chat_template"]["sha256"],
            "273d8e0e683b885071fb17e08d71e5f2a5ddfb5309756181681de4f5a1822d80",
        )
        self.assertFalse(target["selection_input_identity_complete"])


if __name__ == "__main__":
    unittest.main()
