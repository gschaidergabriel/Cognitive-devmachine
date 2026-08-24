#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import replace
import hashlib
import struct
import unittest

from jspace_llamacpp_cvec_bridge_v1 import (
    LlamaCppCVecBridgeError,
    QWEN3_06B_CHECKPOINT_SHA256,
    QWEN3_06B_LLAMA_CPP_SOURCE_COMMIT,
    build_llamacpp_cvec_buffer,
    build_qwen3_06b_candidate_cvec,
    validate_llamacpp_cvec_binding,
)
from jspace_vector_control_v1 import encode_vector


class LlamaCppCVecBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.basis_sha = hashlib.sha256(b"jspace-basis-v1").hexdigest()
        self.packet = encode_vector(
            [1.0, -0.5, 0.25, 0.0],
            basis_id="basis-v1",
            basis_sha256=self.basis_sha,
            generation=7,
            role="planner",
            control_condition="SIGN_FLIP",
        )

    def _build(self, **overrides):
        kwargs = dict(
            current_generation=7,
            expected_basis_id="basis-v1",
            expected_basis_sha256=self.basis_sha,
            expected_role="planner",
            checkpoint_sha256=hashlib.sha256(b"checkpoint").hexdigest(),
            llama_cpp_source_commit="1" * 40,
            n_embd=4,
            n_layer=5,
            il_start=2,
            il_end=3,
            strength=2.0,
        )
        kwargs.update(overrides)
        return build_llamacpp_cvec_buffer(self.packet, **kwargs)

    def test_layer_major_no_layer0_and_selected_range(self):
        raw, binding = self._build()
        self.assertEqual(binding.float_count, 16)
        self.assertEqual(binding.byte_count, 64)
        self.assertEqual(len(raw), 64)
        chunks = [raw[i * 16:(i + 1) * 16] for i in range(4)]  # physical layers 1..4
        self.assertEqual(chunks[0], b"\x00" * 16)
        self.assertNotEqual(chunks[1], b"\x00" * 16)
        self.assertEqual(chunks[1], chunks[2])
        self.assertEqual(chunks[3], b"\x00" * 16)
        values = struct.unpack("<4f", chunks[1])
        self.assertGreater(values[0], 0.0)
        self.assertLess(values[1], 0.0)
        validate_llamacpp_cvec_binding(binding, raw, self.packet)

    def test_deterministic_identity(self):
        raw_a, binding_a = self._build()
        raw_b, binding_b = self._build()
        self.assertEqual(raw_a, raw_b)
        self.assertEqual(binding_a, binding_b)

    def test_sign_strength_changes_raw_identity(self):
        raw_pos, binding_pos = self._build(strength=1.0)
        raw_neg, binding_neg = self._build(strength=-1.0)
        self.assertNotEqual(raw_pos, raw_neg)
        self.assertNotEqual(binding_pos.cvec_f32le_sha256, binding_neg.cvec_f32le_sha256)
        self.assertNotEqual(binding_pos.binding_sha256, binding_neg.binding_sha256)

    def test_zero_strength_yields_zero_buffer(self):
        raw, binding = self._build(strength=0.0)
        self.assertEqual(raw, b"\x00" * len(raw))
        validate_llamacpp_cvec_binding(binding, raw, self.packet)

    def test_dimension_mismatch_fails_closed(self):
        with self.assertRaisesRegex(LlamaCppCVecBridgeError, "VECTOR_DIMENSION_MUST_EQUAL_MODEL_N_EMBD"):
            self._build(n_embd=5)

    def test_layer_zero_and_last_overrun_fail_closed(self):
        with self.assertRaisesRegex(LlamaCppCVecBridgeError, "layer_range"):
            self._build(il_start=0)
        with self.assertRaisesRegex(LlamaCppCVecBridgeError, "layer_range"):
            self._build(il_end=5)

    def test_stale_generation_fails_closed(self):
        with self.assertRaises(Exception):
            self._build(current_generation=8)

    def test_raw_mutation_fails_closed(self):
        raw, binding = self._build()
        tampered = bytearray(raw)
        tampered[20] ^= 1
        with self.assertRaisesRegex(LlamaCppCVecBridgeError, "CVEC_BUFFER_DIGEST_MISMATCH"):
            validate_llamacpp_cvec_binding(binding, bytes(tampered), self.packet)

    def test_binding_mutation_fails_closed(self):
        raw, binding = self._build()
        tampered = replace(binding, strength=3.0)
        with self.assertRaisesRegex(LlamaCppCVecBridgeError, "LLAMA_CPP_CVEC_BINDING_DIGEST_MISMATCH"):
            validate_llamacpp_cvec_binding(tampered, raw, self.packet)

    def test_packet_identity_mutation_fails_closed(self):
        raw, binding = self._build()
        other = encode_vector(
            [1.0, -0.25, 0.25, 0.0],
            basis_id="basis-v1",
            basis_sha256=self.basis_sha,
            generation=7,
            role="planner",
            control_condition="SIGN_FLIP",
        )
        with self.assertRaisesRegex(LlamaCppCVecBridgeError, "VECTOR_CONTROL_PACKET_IDENTITY_MISMATCH"):
            validate_llamacpp_cvec_binding(binding, raw, other)

    def test_pinned_qwen3_06b_wrapper_binds_exact_candidate(self):
        packet = encode_vector(
            [0.0] * 1023 + [1.0],
            basis_id="qwen3-06b-jspace-basis-v1",
            basis_sha256=self.basis_sha,
            generation=9,
            role="planner",
            control_condition="LESION",
        )
        raw, binding = build_qwen3_06b_candidate_cvec(
            packet,
            current_generation=9,
            expected_basis_id="qwen3-06b-jspace-basis-v1",
            expected_basis_sha256=self.basis_sha,
            expected_role="planner",
            il_start=10,
            il_end=20,
            strength=0.5,
        )
        self.assertEqual(binding.checkpoint_sha256, QWEN3_06B_CHECKPOINT_SHA256)
        self.assertEqual(binding.llama_cpp_source_commit, QWEN3_06B_LLAMA_CPP_SOURCE_COMMIT)
        self.assertEqual(binding.n_embd, 1024)
        self.assertEqual(binding.n_layer, 28)
        self.assertEqual(binding.float_count, 27 * 1024)
        self.assertEqual(len(raw), 27 * 1024 * 4)
        validate_llamacpp_cvec_binding(binding, raw, packet)


if __name__ == "__main__":
    unittest.main()
