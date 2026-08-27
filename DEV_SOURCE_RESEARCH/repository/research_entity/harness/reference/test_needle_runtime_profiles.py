import json
import unittest
from pathlib import Path

from .needle_runtime_contract import NeedleAdapterError, AliasProfile
from .needle_runtime_profiles import (
    NeedleRuntimeIdentity,
    build_cactus_tools_payload,
    build_jax_tools_payload,
    build_runtime_payload,
)

FIXTURE = Path(__file__).parent / "fixtures" / "frank_needle_active_tools_20260804.json"
TOOLS = json.loads(FIXTURE.read_text(encoding="utf-8"))


class ProfileTests(unittest.TestCase):
    def test_jax_51(self):
        payload, needle_tools, contract = build_jax_tools_payload(TOOLS)
        self.assertEqual(len(needle_tools), 51)
        self.assertEqual(len(contract), 51)
        self.assertTrue(payload.startswith("["))

    def test_cactus_51(self):
        payload, needle_tools, contract = build_cactus_tools_payload(TOOLS)
        self.assertEqual(len(needle_tools), 51)
        self.assertEqual(len(contract), 51)
        self.assertIn('"type":"object"', payload)
        self.assertIn('"properties":{', payload)
        self.assertNotIn('"type": "', payload)

    def test_cactus_aliases(self):
        payload, _, _ = build_cactus_tools_payload(TOOLS)
        self.assertIn("list_capabilities", payload)
        self.assertIn("search_knowledge", payload)
        self.assertIn("expression", payload)

    def test_cactus_rejects_quote_description(self):
        with self.assertRaises(NeedleAdapterError):
            build_cactus_tools_payload(
                [{"name": "x", "description": 'say "hi"', "parameters": {}}],
                AliasProfile({}, {}),
            )

    def test_cactus_rejects_param_brace_description(self):
        src = [
            {
                "name": "x",
                "description": "",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "v": {"type": "string", "description": "literal { brace"}
                    },
                    "required": ["v"],
                },
            }
        ]
        with self.assertRaises(NeedleAdapterError):
            build_cactus_tools_payload(src, AliasProfile({}, {}))

    def test_cactus_rejects_unknown_type(self):
        src = [
            {
                "name": "x",
                "parameters": {
                    "type": "object",
                    "properties": {"v": {"type": "mystery"}},
                    "required": ["v"],
                },
            }
        ]
        with self.assertRaises(NeedleAdapterError):
            build_cactus_tools_payload(src, AliasProfile({}, {}))

    def test_identity_accepts_pinned_hashes(self):
        ident = NeedleRuntimeIdentity(
            "JAX_PYTHON",
            "cactus-compute/needle:needle/model/run.py",
            "954022e5b96dcf3aee30a3537c3a2cd2ac1c0e67",
            "40a32e91d1d4197bf15ba559b74f6727c342dc8746918742fc7d8e2c1f18df40",
            "0823f5b9133c68a8140addc5d7a425fa9119c4c8cb4a550363b4bffa4ba1c8c7",
        )
        self.assertEqual(len(ident.identity_sha256), 64)

    def test_identity_rejects_unpinned(self):
        with self.assertRaises(NeedleAdapterError):
            NeedleRuntimeIdentity("JAX_PYTHON", "x", "y", "UNPINNED", "z").validate()

    def test_unknown_profile_rejected(self):
        with self.assertRaises(NeedleAdapterError):
            build_runtime_payload("NOPE", TOOLS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
