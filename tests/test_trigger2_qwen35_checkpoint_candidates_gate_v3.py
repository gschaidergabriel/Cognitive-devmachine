from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools import trigger2_qwen35_checkpoint_candidates_gate_v3 as gate

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research_entity/global/j-space/research/trigger2_qwen35_08b_checkpoint_candidates_v2.json"


class Trigger2Qwen35CheckpointGateV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.identities, cls.loaders = gate.load_bound_receipts()

    def adjudicate(self, registry=None, identities=None, loaders=None):
        return gate.adjudicate(
            copy.deepcopy(self.registry if registry is None else registry),
            copy.deepcopy(self.identities if identities is None else identities),
            copy.deepcopy(self.loaders if loaders is None else loaders),
        )

    def test_current_registry_source_integrity_passes_but_selection_stays_closed(self):
        result = self.adjudicate()
        self.assertTrue(result["pass"], result["failures"])
        self.assertFalse(result["selection_ready"])
        self.assertIsNone(result["checkpoint_winner"])
        for cid in gate.BOUND_MEASURED:
            normalized = result["normalized_candidates"][cid]
            self.assertTrue(normalized["legacy_participation_intent"])
            self.assertTrue(normalized["snapshot_registry_identity_complete"])
            self.assertTrue(normalized["loader_smoke_observed"])
            self.assertIsNone(normalized["consumed_identity_match"])
            self.assertFalse(normalized["selection_input_identity_complete"])
            self.assertFalse(normalized["matched_baseline_participation_eligible"])
            self.assertFalse(normalized["winner_eligible"])

    def test_target_preserves_ambiguous_weight_representations_and_index(self):
        result = self.adjudicate()
        target = result["normalized_candidates"]["QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED"]
        paths = [x["path"] for x in target["weight_manifest"]]
        self.assertEqual(
            [
                "model.safetensors",
                "model.safetensors-00001-of-00001.safetensors",
                "model.safetensors.index.json",
            ],
            paths,
        )
        self.assertIsNone(target["consumed_identity_match"])

    def test_nested_qwen35_text_architecture_is_recovered_from_identity_receipt(self):
        result = self.adjudicate()
        for cid in gate.BOUND_MEASURED:
            arch = result["normalized_candidates"][cid]["architecture"]
            self.assertEqual(24, arch["num_hidden_layers"])
            self.assertEqual(1024, arch["hidden_size"])
            self.assertEqual(8, arch["num_attention_heads"])
            self.assertEqual(2, arch["num_key_value_heads"])
            self.assertEqual(248320, arch["vocab_size"])
            self.assertEqual(262144, arch["max_position_embeddings"])

    def test_base_explicitly_distinguishes_no_standalone_template_from_unknown_runtime_template(self):
        result = self.adjudicate()
        template = result["normalized_candidates"]["QWEN35_08B_BASE"]["chat_template"]
        self.assertEqual("NO_STANDALONE_CHAT_TEMPLATE_FILE_IN_BOUND_SNAPSHOT", template["status"])
        self.assertIsNone(template["sha256"])
        self.assertEqual("UNRESOLVED_SELECTION_INPUT_ABI", template["runtime_resolved_template_identity"])

    def test_consumed_identity_cannot_be_self_promoted_from_registry(self):
        registry = copy.deepcopy(self.registry)
        target = next(
            c for c in registry["candidates"]
            if c["candidate_id"] == "QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED"
        )
        target["consumed_identity_match"] = True
        result = self.adjudicate(registry=registry)
        self.assertFalse(result["pass"])
        self.assertIn(
            "CONSUMED_IDENTITY_MATCH_UNSUPPORTED_BY_CURRENT_RECEIPTS:"
            "QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED",
            result["failures"],
        )

    def test_revision_digest_loader_and_role_mutations_fail_closed(self):
        registry = copy.deepcopy(self.registry)
        registry["candidates"][0]["immutable_revision"] = "0" * 40
        self.assertFalse(self.adjudicate(registry=registry)["pass"])

        registry = copy.deepcopy(self.registry)
        registry["candidates"][1]["file_manifest_sha256"] = "0" * 64
        self.assertFalse(self.adjudicate(registry=registry)["pass"])

        loaders = copy.deepcopy(self.loaders)
        loaders["QWEN35_08B_BASE"]["loader_consumption_observed"] = False
        self.assertFalse(self.adjudicate(loaders=loaders)["pass"])

        registry = copy.deepcopy(self.registry)
        registry["candidates"][0]["candidate_role"] = "TARGET_MEASURED"
        self.assertFalse(self.adjudicate(registry=registry)["pass"])

    def test_nested_architecture_null_fails_snapshot_completeness(self):
        identities = copy.deepcopy(self.identities)
        identities["QWEN35_08B_BASE"]["config"]["text_config"]["hidden_size"] = None
        result = self.adjudicate(identities=identities)
        self.assertFalse(result["pass"])
        self.assertIn(
            "SNAPSHOT_IDENTITY_COMPLETENESS_DECLARATION_MISMATCH:QWEN35_08B_BASE",
            result["failures"],
        )


if __name__ == "__main__":
    unittest.main()
