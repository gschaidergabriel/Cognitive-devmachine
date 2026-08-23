#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import pipeline_cognitive_fabric_admission_v1 as admission


class DefaultZeroImportTests(unittest.TestCase):
    def test_loads_canonical_capsule_and_packet_from_jspace_tree(self):
        capsule, packet = admission.load_default_zero_modules()
        self.assertEqual(capsule.SCHEMA, "ZERO_WORKSPACE_CAPSULE/v1")
        self.assertEqual(packet.SCHEMA, "ZERO_INFERENCE_PACKET/v2")
        self.assertIs(packet.capsule_v1, capsule)
        self.assertEqual(
            Path(capsule.__file__).resolve(),
            ROOT / "research_entity" / "global" / "j-space" / "implementations" / "zero_workspace_capsule_v1.py",
        )
        self.assertEqual(
            Path(packet.__file__).resolve(),
            ROOT / "research_entity" / "global" / "j-space" / "implementations" / "zero_inference_packet_v2.py",
        )

    def test_loader_restores_existing_top_level_capsule_alias(self):
        sentinel = object()
        previous = sys.modules.get("zero_workspace_capsule_v1")
        sys.modules["zero_workspace_capsule_v1"] = sentinel
        try:
            capsule, packet = admission.load_default_zero_modules()
            self.assertIs(packet.capsule_v1, capsule)
            self.assertIs(sys.modules["zero_workspace_capsule_v1"], sentinel)
        finally:
            if previous is None:
                sys.modules.pop("zero_workspace_capsule_v1", None)
            else:
                sys.modules["zero_workspace_capsule_v1"] = previous


if __name__ == "__main__":
    unittest.main()
