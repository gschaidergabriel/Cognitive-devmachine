#!/usr/bin/env python3
"""Regression tests for V18 FrontendArtifact contract identity binding.

This is intentionally a small local/CI discriminator. It uses the selected committed V18
grammar but does not claim strict-LALR/target-VPS release evidence.
"""
from __future__ import annotations

import copy
import unittest
from pathlib import Path

import claycode_base_frontend as front
import claycode_base_typed_ir_v18_bridge as bridge

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"


class V18BridgeContractHashTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        grammar = GRAMMAR.read_text(encoding="utf-8")
        cls.artifact = front.compile_frontend("record X { a:Int }\n", grammar, strict=False)

    def test_current_frontend_artifact_is_accepted(self) -> None:
        row = bridge.validate_frontend_artifact(copy.deepcopy(self.artifact))
        self.assertEqual(row["contract_hash"], self.artifact["contract_hash"])

    def test_contract_hash_tamper_is_rejected(self) -> None:
        bad = copy.deepcopy(self.artifact)
        bad["contract_hash"] = "f" * 64
        with self.assertRaisesRegex(bridge.V18BridgeError, "contract_hash mismatch"):
            bridge.validate_frontend_artifact(bad)

    def test_missing_contract_hash_is_rejected(self) -> None:
        bad = copy.deepcopy(self.artifact)
        bad.pop("contract_hash")
        with self.assertRaisesRegex(bridge.V18BridgeError, "contract_hash mismatch"):
            bridge.validate_frontend_artifact(bad)

    def test_semantic_hash_tamper_still_fails_before_contract(self) -> None:
        bad = copy.deepcopy(self.artifact)
        bad["semantic_hash"] = "0" * 64
        with self.assertRaisesRegex(bridge.V18BridgeError, "semantic_hash mismatch"):
            bridge.validate_frontend_artifact(bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
