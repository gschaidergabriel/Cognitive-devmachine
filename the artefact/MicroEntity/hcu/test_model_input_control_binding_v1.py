import hashlib
import unittest
from dataclasses import replace

import model_input_control_binding_v1 as binding_module
from model_input_control_binding_v1 import (
    ModelInputControlBindingError,
    bind_direct_unique_packet_input,
    validate_model_input_control_binding,
)
from jspace_vector_control_v1 import encode_vector, packet_bytes


BASIS_SHA256 = "1" * 64


class ModelInputControlBindingTests(unittest.TestCase):
    def packet(self, **overrides):
        kwargs = dict(
            basis_id="basis:7",
            basis_sha256=BASIS_SHA256,
            generation=7,
            role="critic",
            control_condition="BASELINE",
        )
        kwargs.update(overrides)
        return encode_vector((0.25, -0.5, 1.0), **kwargs)

    def input_bytes(self, packet=None, *, duplicate=False):
        packet = packet or self.packet()
        wire = packet_bytes(packet)
        value = b'{"system":"hcu"}\n' + wire + b'\n{"prompt":"solve"}'
        return value + (b"\n" + wire if duplicate else b"")

    def bind(self, *, packet=None, consumed=None, **overrides):
        packet = packet or self.packet()
        consumed = consumed if consumed is not None else self.input_bytes(packet)
        kwargs = dict(
            generation=7,
            entry_event_sha256="2" * 64,
            entry_admission_sha256="3" * 64,
            route_decision_sha256="4" * 64,
            grid_plan_sha256="5" * 64,
            cell_id="critic.0",
            role="critic",
            executor_id="local-qwen-executor:v1",
            invocation_id="invocation:episode-1:step-1",
            executor_observed_input_sha256=hashlib.sha256(consumed).hexdigest(),
            executor_observed_input_size=len(consumed),
        )
        kwargs.update(overrides)
        return bind_direct_unique_packet_input(packet, consumed, **kwargs)

    def resign(self, binding):
        return replace(
            binding,
            binding_sha256=binding_module._canonical_sha256(
                binding_module._material(binding),
                "TEST_SELF_CONSISTENT_FORGERY",
            ),
        )

    def test_unique_packet_in_exact_executor_input_binds_deterministically(self):
        packet = self.packet()
        consumed = self.input_bytes(packet)
        a = self.bind(packet=packet, consumed=consumed)
        b = self.bind(packet=packet, consumed=consumed)
        self.assertEqual(a, b)
        self.assertEqual(a.input_sha256, hashlib.sha256(consumed).hexdigest())
        self.assertEqual(a.input_size, len(consumed))
        self.assertEqual(consumed[a.packet_offset:a.packet_offset + len(packet_bytes(packet))], packet_bytes(packet))
        validate_model_input_control_binding(a, consumed)

    def test_packet_absent_from_executor_input_fails_closed(self):
        packet = self.packet()
        consumed = b'{"prompt":"no control packet here"}'
        with self.assertRaisesRegex(ModelInputControlBindingError, "VECTOR_CONTROL_PACKET_NOT_IN_EXECUTOR_INPUT"):
            self.bind(packet=packet, consumed=consumed)

    def test_duplicate_packet_occurrence_is_ambiguous_and_rejected(self):
        packet = self.packet()
        consumed = self.input_bytes(packet, duplicate=True)
        with self.assertRaisesRegex(ModelInputControlBindingError, "VECTOR_CONTROL_PACKET_INPUT_OCCURRENCE_AMBIGUOUS"):
            self.bind(packet=packet, consumed=consumed)

    def test_executor_observed_digest_and_size_must_match_exact_bytes(self):
        consumed = self.input_bytes()
        with self.assertRaisesRegex(ModelInputControlBindingError, "EXECUTOR_OBSERVED_INPUT_SHA256_MISMATCH"):
            self.bind(consumed=consumed, executor_observed_input_sha256="6" * 64)
        with self.assertRaisesRegex(ModelInputControlBindingError, "EXECUTOR_OBSERVED_INPUT_SIZE_MISMATCH"):
            self.bind(consumed=consumed, executor_observed_input_size=len(consumed) + 1)
        with self.assertRaisesRegex(ModelInputControlBindingError, "executor_observed_input_size:INTEGER_REQUIRED"):
            self.bind(consumed=consumed, executor_observed_input_size=float(len(consumed)))

    def test_generation_and_role_are_bound_to_packet(self):
        with self.assertRaisesRegex(ModelInputControlBindingError, "VECTOR_CONTROL_GENERATION_MISMATCH"):
            self.bind(generation=8)
        with self.assertRaisesRegex(ModelInputControlBindingError, "VECTOR_CONTROL_ROLE_MISMATCH"):
            self.bind(role="world")

    def test_post_binding_input_mutation_fails_revalidation(self):
        consumed = self.input_bytes()
        binding = self.bind(consumed=consumed)
        mutated = consumed + b"!"
        with self.assertRaisesRegex(ModelInputControlBindingError, "EXECUTOR_INPUT_SHA256_MISMATCH"):
            validate_model_input_control_binding(binding, mutated)

    def test_self_consistent_outer_hash_cannot_launder_packet_identity(self):
        consumed = self.input_bytes()
        binding = self.bind(consumed=consumed)
        forged = self.resign(replace(binding, vector_control_packet_sha256="7" * 64))
        with self.assertRaisesRegex(ModelInputControlBindingError, "VECTOR_CONTROL_PACKET_IDENTITY_MISMATCH"):
            validate_model_input_control_binding(forged, consumed)

    def test_self_consistent_outer_hash_cannot_launder_float_input_size(self):
        consumed = self.input_bytes()
        binding = self.bind(consumed=consumed)
        forged = self.resign(replace(binding, input_size=float(len(consumed))))
        with self.assertRaisesRegex(ModelInputControlBindingError, "input_size:INTEGER_REQUIRED"):
            validate_model_input_control_binding(forged, consumed)

    def test_self_consistent_outer_hash_cannot_launder_normalization_aliases(self):
        consumed = self.input_bytes()
        binding = self.bind(consumed=consumed)
        cases = (
            (
                self.resign(replace(binding, entry_event_sha256=" " + binding.entry_event_sha256)),
                "entry_event_sha256:NONCANONICAL_SHA256",
            ),
            (
                self.resign(replace(binding, executor_id=" " + binding.executor_id)),
                "executor_id:NONCANONICAL_TEXT",
            ),
            (
                self.resign(
                    replace(
                        binding,
                        vector_control_packet_jcs_utf8=binding.vector_control_packet_jcs_utf8 + "\n",
                    )
                ),
                "vector_control_packet_jcs_utf8:NONCANONICAL_TEXT",
            ),
        )
        for forged, code in cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(ModelInputControlBindingError, code):
                    validate_model_input_control_binding(forged, consumed)

    def test_binding_digest_spelling_itself_must_be_canonical(self):
        consumed = self.input_bytes()
        binding = self.bind(consumed=consumed)
        forged = replace(binding, binding_sha256=" " + binding.binding_sha256)
        with self.assertRaisesRegex(ModelInputControlBindingError, "binding_sha256:NONCANONICAL_SHA256"):
            validate_model_input_control_binding(forged, consumed)

    def test_binding_digest_tamper_fails_closed(self):
        consumed = self.input_bytes()
        binding = self.bind(consumed=consumed)
        tampered = replace(binding, invocation_id="invocation:other")
        with self.assertRaisesRegex(ModelInputControlBindingError, "MODEL_INPUT_CONTROL_BINDING_DIGEST_MISMATCH"):
            validate_model_input_control_binding(tampered, consumed)


if __name__ == "__main__":
    unittest.main()
