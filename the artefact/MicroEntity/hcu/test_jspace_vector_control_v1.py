import random
import unittest
from decimal import Decimal, localcontext

from jspace_vector_control_v1 import (
    JSpaceControlError,
    decode_control,
    encode_control,
    max_abs_reconstruction_error,
)


class VectorControlV1Tests(unittest.TestCase):
    def setUp(self):
        self.vector = [0.25, -0.5, 1.0, -0.125]
        self.kw = dict(basis_id="B42", role="critic", generation=91, gates={"broadcast": 1}, workspace=["ws:7", "hp:2"])

    def decode(self, packet):
        return decode_control(packet, expected_basis_id="B42", expected_role="critic", expected_generation=91)

    def test_deterministic_packet(self):
        self.assertEqual(encode_control(self.vector, **self.kw), encode_control(self.vector, **self.kw))

    def test_round_trip_reconstruction_is_bounded(self):
        packet = encode_control(self.vector, **self.kw)
        decoded = self.decode(packet)
        err = max_abs_reconstruction_error(self.vector, decoded.vector)
        # Compare against the exact canonical scale serialized by the ABI, not caller Decimal context.
        scale_text = packet.splitlines()[0].split(" scale=", 1)[1].split(" ", 1)[0]
        scale = Decimal(scale_text)
        with localcontext() as ctx:
            ctx.prec = 80
            bound = scale / Decimal(2)
        self.assertLessEqual(err, bound)

    def test_sign_is_preserved_for_nonzero_coordinates(self):
        decoded = self.decode(encode_control(self.vector, **self.kw))
        for original, reconstructed in zip(self.vector, decoded.vector):
            self.assertEqual(Decimal(str(original)) > 0, reconstructed > 0)

    def test_wrong_basis_rejected(self):
        packet = encode_control(self.vector, **self.kw)
        with self.assertRaisesRegex(JSpaceControlError, "wrong J-Space basis"):
            decode_control(packet, expected_basis_id="B99", expected_role="critic", expected_generation=91)

    def test_stale_generation_rejected(self):
        packet = encode_control(self.vector, **self.kw)
        with self.assertRaisesRegex(JSpaceControlError, "stale or unexpected generation"):
            decode_control(packet, expected_basis_id="B42", expected_role="critic", expected_generation=92)

    def test_role_swap_rejected(self):
        packet = encode_control(self.vector, **self.kw)
        with self.assertRaisesRegex(JSpaceControlError, "wrong cell role"):
            decode_control(packet, expected_basis_id="B42", expected_role="planner", expected_generation=91)

    def test_null_vector_control(self):
        packet = encode_control([0, 0, 0, 0], **self.kw)
        decoded = self.decode(packet)
        self.assertEqual(decoded.vector, (Decimal(0),) * 4)

    def test_permutation_changes_payload_identity(self):
        p1 = self.decode(encode_control(self.vector, **self.kw))
        p2 = self.decode(encode_control(list(reversed(self.vector)), **self.kw))
        self.assertNotEqual(p1.payload_sha256, p2.payload_sha256)

    def test_gate_metadata_poison_rejected(self):
        packet = encode_control(self.vector, **self.kw)
        poisoned = packet.replace('gate:{"broadcast":1}', 'gate:{"broadcast":0}')
        with self.assertRaisesRegex(JSpaceControlError, "packet digest mismatch"):
            self.decode(poisoned)

    def test_random_vector_with_plausible_metadata_rejected(self):
        packet = encode_control(self.vector, **self.kw)
        rnd = [random.Random(7).uniform(-1, 1) for _ in self.vector]
        foreign = encode_control(rnd, **self.kw)
        q8_foreign = foreign.splitlines()[1]
        poisoned_lines = packet.splitlines()
        poisoned_lines[1] = q8_foreign
        with self.assertRaisesRegex(JSpaceControlError, "payload digest mismatch"):
            self.decode("\n".join(poisoned_lines))

    def test_boolean_and_nonfinite_coordinates_rejected(self):
        with self.assertRaises(JSpaceControlError):
            encode_control([True], **self.kw)
        with self.assertRaises(JSpaceControlError):
            encode_control([float("nan")], **self.kw)

    def test_malformed_duplicate_workspace_rejected(self):
        with self.assertRaises(JSpaceControlError):
            encode_control(self.vector, **{**self.kw, "workspace": ["ws:7", "ws:7"]})

    def test_unusual_experiment_metadata_only_vs_payload_bound_poison(self):
        """Exactly-one GO experiment: weak metadata-only admission is fooled; ABI/v1 is not."""
        packet = encode_control(self.vector, **self.kw)
        foreign = encode_control([-1.0, 0.75, 0.5, -0.25], **self.kw)
        poisoned = packet.splitlines()
        poisoned[1] = foreign.splitlines()[1]
        poisoned = "\n".join(poisoned)

        # Counter-reality/control: a naive metadata-only check would accept this poison.
        header = poisoned.splitlines()[0]
        metadata_only_accepts = "basis=B42" in header and "role=critic" in header and "gen=91" in header
        self.assertTrue(metadata_only_accepts)

        # Production ABI binds the q8 payload cryptographically and rejects the same packet.
        with self.assertRaisesRegex(JSpaceControlError, "payload digest mismatch"):
            self.decode(poisoned)


if __name__ == "__main__":
    unittest.main(verbosity=2)
