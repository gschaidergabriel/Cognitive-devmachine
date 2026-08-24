import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("xeno_harness_config", ROOT / "tools/xeno_harness_config.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MOD)


def valid_config():
    return {
        "schema": "XENO_HARNESS_CONFIG/v1",
        "internal_08b": {"enabled": True, "engine_id": "xeno-local-08b"},
        "external_slots": [
            {
                "slot_id": "slot1",
                "role": "PRESTAGE",
                "adapter": "ANTHROPIC_CLAUDE_CODE",
                "secret_ref": "secret://xeno/slot1",
                "model": "claude-code",
                "enabled": True,
            },
            {
                "slot_id": "slot2",
                "role": "UNASSIGNED",
                "adapter": "OPENAI_COMPATIBLE",
                "secret_ref": "secret://xeno/slot2",
                "model": "any-model",
                "enabled": True,
            },
        ],
        "selection": {
            "core": "internal_08b",
            "prestage_enabled": True,
            "prestage": "slot1",
        },
        "grid10": {"enabled": True, "logical_cells": 10},
        "peer_link": {"enabled": True, "protocol": "XENO_PEER_LINK/v1"},
        "global_jspace": {"enabled": True, "profile_id": "jspace-xeno-v1"},
    }


class HarnessConfigTests(unittest.TestCase):
    def test_internal_core_plus_external_prestage(self):
        result = MOD.validate(valid_config())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["selected_core"], "internal_08b")
        self.assertEqual(result["selected_prestage"], "slot1")

    def test_disable_internal_and_promote_external_slot_to_core(self):
        cfg = valid_config()
        cfg["internal_08b"]["enabled"] = False
        cfg["external_slots"][0]["role"] = "UNASSIGNED"
        cfg["external_slots"][1]["role"] = "CORE"
        cfg["selection"] = {"core": "slot2", "prestage_enabled": False, "prestage": None}
        result = MOD.validate(cfg)
        self.assertEqual(result["selected_core"], "slot2")
        self.assertFalse(result["internal_08b_enabled"])

    def test_two_external_slots_can_be_core_and_prestage(self):
        cfg = valid_config()
        cfg["external_slots"][0]["role"] = "PRESTAGE"
        cfg["external_slots"][1]["role"] = "CORE"
        cfg["selection"] = {"core": "slot2", "prestage_enabled": True, "prestage": "slot1"}
        result = MOD.validate(cfg)
        self.assertEqual(result["selected_core"], "slot2")
        self.assertEqual(result["selected_prestage"], "slot1")

    def test_rejects_more_than_two_external_slots(self):
        cfg = valid_config()
        cfg["external_slots"].append({
            "slot_id": "slot3", "role": "UNASSIGNED", "adapter": "OPENAI_COMPATIBLE",
            "secret_ref": "secret://xeno/slot3", "model": "x", "enabled": True,
        })
        with self.assertRaisesRegex(ValueError, "MAX_TWO_EXTERNAL_SLOTS"):
            MOD.validate(cfg)

    def test_rejects_plaintext_token_field(self):
        cfg = valid_config()
        cfg["external_slots"][0]["token"] = "do-not-store-this"
        with self.assertRaisesRegex(ValueError, "PLAINTEXT_SECRET_FIELD_FORBIDDEN"):
            MOD.validate(cfg)

    def test_rejects_same_external_slot_as_core_and_prestage(self):
        cfg = valid_config()
        cfg["external_slots"][0]["role"] = "CORE"
        cfg["selection"] = {"core": "slot1", "prestage_enabled": True, "prestage": "slot1"}
        with self.assertRaisesRegex(ValueError, "CORE_AND_PRESTAGE_MUST_BE_DISTINCT"):
            MOD.validate(cfg)


if __name__ == "__main__":
    unittest.main()
