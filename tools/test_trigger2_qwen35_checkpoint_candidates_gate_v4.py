#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import unittest

import trigger2_qwen35_checkpoint_candidates_gate_v3 as v3
import trigger2_qwen35_checkpoint_candidates_gate_v4 as v4

REGISTRY_PATH = (
    v3.ROOT
    / "research_entity/global/j-space/research/trigger2_qwen35_08b_checkpoint_candidates_v2.json"
)
TARGET = "QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED"
BASE = "QWEN35_08B_BASE"


def load_fixture():
    with REGISTRY_PATH.open(encoding="utf-8") as fh:
        registry = json.load(fh)
    identities, loaders = v3.load_bound_receipts()
    return registry, identities, loaders


def candidate(registry, cid):
    return next(x for x in registry["candidates"] if x["candidate_id"] == cid)


class GateV4Tests(unittest.TestCase):
    def test_current_registry_passes_source_integrity(self):
        registry, identities, loaders = load_fixture()
        out = v4.adjudicate(registry, identities=identities, loaders=loaders)
        self.assertTrue(out["pass"], out["failures"])
        self.assertFalse(out["selection_ready"])
        self.assertIsNone(out["checkpoint_winner"])
        self.assertFalse(out["training_credit_minted"])

    def test_nested_architecture_null_fails_closed(self):
        registry, identities, loaders = load_fixture()
        identities = copy.deepcopy(identities)
        identities[TARGET]["config"]["text_config"]["num_hidden_layers"] = None
        out = v4.adjudicate(registry, identities=identities, loaders=loaders)
        self.assertIn("BOUND_ARCHITECTURE_INCOMPLETE:" + TARGET, out["failures"])
        self.assertFalse(out["pass"])

    def test_nested_architecture_bool_does_not_count_as_int(self):
        registry, identities, loaders = load_fixture()
        identities = copy.deepcopy(identities)
        identities[BASE]["config"]["text_config"]["hidden_size"] = True
        out = v4.adjudicate(registry, identities=identities, loaders=loaders)
        self.assertIn("BOUND_ARCHITECTURE_INCOMPLETE:" + BASE, out["failures"])

    def test_matched_baseline_participation_mutation_fails(self):
        registry, identities, loaders = load_fixture()
        registry = copy.deepcopy(registry)
        candidate(registry, BASE)["selection_eligible"] = False
        out = v4.adjudicate(registry, identities=identities, loaders=loaders)
        self.assertIn("BOUND_MATCHED_BASELINE_PARTICIPATION_REQUIRED:" + BASE, out["failures"])

    def test_consumed_identity_cannot_be_self_promoted(self):
        registry, identities, loaders = load_fixture()
        registry = copy.deepcopy(registry)
        candidate(registry, TARGET)["consumed_identity_match"] = True
        out = v4.adjudicate(registry, identities=identities, loaders=loaders)
        self.assertIn(
            "CONSUMED_IDENTITY_MATCH_UNSUPPORTED_BY_CURRENT_RECEIPTS:" + TARGET,
            out["failures"],
        )

    def test_schema_mutation_fails(self):
        registry, identities, loaders = load_fixture()
        registry = copy.deepcopy(registry)
        registry["schema"] = "STALE"
        out = v4.adjudicate(registry, identities=identities, loaders=loaders)
        self.assertIn("SCHEMA_MISMATCH", out["failures"])

    def test_bound_revision_mutation_fails(self):
        registry, identities, loaders = load_fixture()
        identities = copy.deepcopy(identities)
        identities[BASE]["requested_revision"] = "0" * 40
        out = v4.adjudicate(registry, identities=identities, loaders=loaders)
        self.assertIn("REGISTRY_RECEIPT_REVISION_MISMATCH:" + BASE, out["failures"])

    def test_registry_digest_mutation_fails(self):
        registry, identities, loaders = load_fixture()
        registry = copy.deepcopy(registry)
        candidate(registry, BASE)["config_sha256"] = "0" * 64
        out = v4.adjudicate(registry, identities=identities, loaders=loaders)
        self.assertIn(
            "REGISTRY_RECEIPT_DIGEST_MISMATCH:" + BASE + ":config_sha256",
            out["failures"],
        )

    def test_loader_receipt_mutation_fails(self):
        registry, identities, loaders = load_fixture()
        loaders = copy.deepcopy(loaders)
        loaders[BASE]["loader_consumption_observed"] = False
        out = v4.adjudicate(registry, identities=identities, loaders=loaders)
        self.assertIn("LOADER_OBSERVATION_DECLARATION_MISMATCH:" + BASE, out["failures"])

    def test_bound_role_mutation_fails(self):
        registry, identities, loaders = load_fixture()
        registry = copy.deepcopy(registry)
        candidate(registry, TARGET)["candidate_role"] = "CONTROL"
        out = v4.adjudicate(registry, identities=identities, loaders=loaders)
        self.assertIn("BOUND_ROLE_MISMATCH:" + TARGET, out["failures"])


if __name__ == "__main__":
    unittest.main()
