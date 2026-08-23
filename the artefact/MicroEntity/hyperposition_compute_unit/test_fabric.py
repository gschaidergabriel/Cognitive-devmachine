import unittest

from fabric import HCUPacket, PacketClass, generation_matches


class FabricTests(unittest.TestCase):
    def packet(self, **kwargs):
        base = dict(
            packet_class=PacketClass.CANDIDATE_HYPOTHESIS,
            cycle_id="cycle-1",
            causal_id="causal-1",
            entity_generation=7,
            producer_cell_id="critic-01",
            payload={"claim": "candidate only"},
        )
        base.update(kwargs)
        return HCUPacket(**base)

    def test_packet_id_is_deterministic(self):
        p = self.packet()
        self.assertEqual(p.packet_id(), p.packet_id())

    def test_direct_effect_authority_is_forbidden(self):
        with self.assertRaises(ValueError):
            self.packet(payload={"direct_effect": True}).validate()

    def test_canonical_fact_authority_is_forbidden(self):
        with self.assertRaises(ValueError):
            self.packet(payload={"canonical_fact": "x"}).validate()

    def test_simulated_state_must_be_typed(self):
        with self.assertRaises(ValueError):
            self.packet(
                packet_class=PacketClass.SIMULATED_STATE,
                simulated=False,
            ).validate()

    def test_generation_fence(self):
        p = self.packet()
        self.assertTrue(generation_matches(p, 7))
        self.assertFalse(generation_matches(p, 8))


if __name__ == "__main__":
    unittest.main()
