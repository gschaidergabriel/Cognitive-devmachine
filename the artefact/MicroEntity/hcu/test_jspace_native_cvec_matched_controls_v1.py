import unittest

from jspace_llamacpp_cvec_bridge_v1 import (
    build_llamacpp_cvec_buffer,
    validate_llamacpp_cvec_binding,
)
from jspace_vector_control_v1 import (
    CONTROL_CONDITIONS,
    JSpaceVectorControlError,
    decode_vector,
    encode_vector,
)

BASIS_ID = "basis:qwen06:matched-controls"
BASIS_SHA256 = "a" * 64
GENERATION = 878
ROLE = "jspace_control"
CHECKPOINT_SHA256 = "b" * 64
LLAMA_CPP_SOURCE_COMMIT = "1" * 40
VECTOR = (0.2, -0.7, 1.0, 0.4)
NEW_MATCHED_CONDITIONS = (
    "POSITIVE_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
)
LEGACY_CONDITIONS = (
    "BASELINE",
    "NULL_VECTOR",
    "SIGN_FLIP",
    "PERMUTED",
    "ROLE_SWAP",
    "LESION",
)


class NativeCvecMatchedControlIdentityTests(unittest.TestCase):
    def _packet(self, condition: str):
        return encode_vector(
            VECTOR,
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role=ROLE,
            control_condition=condition,
        )

    def test_new_matched_conditions_are_first_class_and_identity_distinct(self):
        packets = [self._packet(condition) for condition in NEW_MATCHED_CONDITIONS]
        self.assertEqual(len({packet.packet_sha256 for packet in packets}), len(packets))
        for condition, packet in zip(NEW_MATCHED_CONDITIONS, packets):
            self.assertEqual(packet.control_condition, condition)
            decoded = decode_vector(
                packet,
                current_generation=GENERATION,
                expected_basis_id=BASIS_ID,
                expected_basis_sha256=BASIS_SHA256,
                expected_role=ROLE,
                expected_control_condition=condition,
            )
            self.assertEqual(len(decoded), len(VECTOR))

    def test_existing_condition_vocabulary_remains_admitted(self):
        self.assertTrue(set(LEGACY_CONDITIONS).issubset(CONTROL_CONDITIONS))
        for condition in LEGACY_CONDITIONS:
            self.assertEqual(self._packet(condition).control_condition, condition)

    def test_literal_experiment_alias_plus_vector_remains_fail_closed(self):
        with self.assertRaisesRegex(JSpaceVectorControlError, "control_condition:UNSUPPORTED"):
            self._packet("+VECTOR")

    def test_llamacpp_binding_preserves_each_new_condition_exactly(self):
        binding_ids = set()
        for condition in NEW_MATCHED_CONDITIONS:
            packet = self._packet(condition)
            raw, binding = build_llamacpp_cvec_buffer(
                packet,
                current_generation=GENERATION,
                expected_basis_id=BASIS_ID,
                expected_basis_sha256=BASIS_SHA256,
                expected_role=ROLE,
                checkpoint_sha256=CHECKPOINT_SHA256,
                llama_cpp_source_commit=LLAMA_CPP_SOURCE_COMMIT,
                n_embd=len(VECTOR),
                n_layer=3,
                il_start=1,
                il_end=1,
                strength=1.0,
            )
            self.assertEqual(binding.vector_control_condition, condition)
            validate_llamacpp_cvec_binding(binding, raw, packet)
            binding_ids.add(binding.binding_sha256)
        self.assertEqual(len(binding_ids), len(NEW_MATCHED_CONDITIONS))

    def test_condition_identity_cannot_mint_state_or_effect_authority(self):
        packet = self._packet("POSITIVE_VECTOR")
        self.assertFalse(hasattr(packet, "capability"))
        self.assertFalse(hasattr(packet, "canonical_state"))
        self.assertFalse(hasattr(packet, "effect_authority"))


if __name__ == "__main__":
    unittest.main()
