import importlib.util
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "fabric.py"
SPEC = importlib.util.spec_from_file_location("hcu_fabric", MODULE_PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class FabricTests(unittest.TestCase):
    def packet(self, **kwargs):
        base = dict(
            packet_class=MOD.PacketClass.CANDIDATE_HYPOTHESIS,
            cycle_id="cycle-1",
            causal_id="causal-1",
            entity_generation=7,
            producer_cell_id="critic-01",
            payload={"claim": "candidate only"},
        )
        base.update(kwargs)
        return MOD.HCUPacket(**base)

    def test_packet_id_is_deterministic(self):
        packet = self.packet()
        self.assertEqual(packet.packet_id(), packet.packet_id())

    def test_direct_effect_authority_is_forbidden(self):
        with self.assertRaises(ValueError):
            self.packet(payload={"direct_effect": True}).validate()

    def test_canonical_fact_authority_is_forbidden(self):
        with self.assertRaises(ValueError):
            self.packet(payload={"canonical_fact": "x"}).validate()

    def test_nested_authority_field_is_forbidden(self):
        with self.assertRaises(ValueError):
            self.packet(payload={"wrapper": {"direct_effect": True}}).validate()

    def test_authority_field_inside_sequence_is_forbidden(self):
        with self.assertRaises(ValueError):
            self.packet(payload={"branches": [{"claim": "ok"}, {"canonical_write": {"x": 1}}]}).validate()

    def test_cyclic_payload_is_rejected_fail_closed(self):
        payload = {"claim": "candidate only"}
        payload["self"] = payload
        with self.assertRaises(ValueError):
            self.packet(payload=payload).validate()

    def test_non_string_mapping_key_is_rejected(self):
        with self.assertRaises(ValueError):
            self.packet(payload={1: "ambiguous"}).validate()

    def test_simulated_state_must_be_explicitly_typed(self):
        with self.assertRaises(ValueError):
            self.packet(packet_class=MOD.PacketClass.SIMULATED_STATE).validate()

    def test_generation_fence(self):
        packet = self.packet()
        self.assertTrue(MOD.generation_matches(packet, 7))
        self.assertFalse(MOD.generation_matches(packet, 8))


if __name__ == "__main__":
    unittest.main()
