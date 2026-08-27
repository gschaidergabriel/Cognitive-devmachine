#!/usr/bin/env python3
"""Regression tests for registry-v3 Frank-v0.1 research peer discovery."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import research_interconnect_preflight_v2 as preflight

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research_entity/global/RESEARCH_TRIGGER_REGISTRY.json"
EXPECTED = {
    "clayresearch", "frank", "q23", "gwt", "emergenz", "claycode",
    "hyperposition", "claygraph", "unifieddb", "harness",
}
META = {"666", "go", "q12", "atomic", "dump", "fusion", "hypofusion", "spawn"}


class FrankV01RegistryPeerTest(unittest.TestCase):
    def test_current_registry_exact_peer_set(self) -> None:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        observed = set(preflight._registered_scientific_branches_from_data(data))
        self.assertEqual(observed, EXPECTED)
        self.assertTrue(observed.isdisjoint(META))

    def test_every_priority_is_exact_peer_permutation(self) -> None:
        for trigger, order in preflight.PRIORITY.items():
            with self.subTest(trigger=trigger):
                self.assertEqual(set(order), EXPECTED)
                self.assertEqual(len(order), len(EXPECTED))
                self.assertEqual(len(order), len(set(order)))

    def test_current_build_kinds_are_classified(self) -> None:
        synthetic = {
            "triggers": {
                "claycode": {"kind": "domain_build_research"},
                "frank": {"kind": "whole_target_architecture_build"},
                "harness": {"kind": "direct_frank_v0_1_validation_repair"},
                "q23": {"kind": "multimodal_perception_research"},
                "clayresearch": {"kind": "integrated_frank_v0_1_research_foundry"},
                "gwt": {"kind": "domain_research"},
                "go": {"kind": "maximum_depth_recursive_frank_v0_1_cycle"},
            }
        }
        observed = set(preflight._registered_scientific_branches_from_data(synthetic))
        self.assertEqual(observed, {"claycode", "frank", "harness", "q23", "clayresearch", "gwt"})

    def test_legacy_integrated_kind_remains_compatible(self) -> None:
        observed = preflight._registered_scientific_branches_from_data(
            {"triggers": {"clay": {"kind": "integrated_research_foundry"}}}
        )
        self.assertEqual(observed, ["clay"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
