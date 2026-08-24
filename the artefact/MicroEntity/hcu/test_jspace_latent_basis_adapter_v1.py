import math
import unittest
from dataclasses import replace

from jspace_latent_basis_adapter_v1 import (
    JSpaceLatentBasisAdapterError,
    adapt_control_packet,
    build_latent_basis_adapter,
    validate_latent_basis_adapter,
)
from jspace_llamacpp_cvec_bridge_v1 import build_llamacpp_cvec_buffer
from jspace_vector_control_v1 import encode_vector


class JSpaceLatentBasisAdapterTests(unittest.TestCase):
    def adapter(self):
        return build_latent_basis_adapter(
            (
                ("intent:a", "a" * 64, (1.0, 0.0, 0.0)),
                ("intent:b", "b" * 64, (0.0, 1.0, 0.0)),
            ),
            source_jspace_basis_id="global:jspace:semantic:v1",
            source_jspace_basis_sha256="1" * 64,
            local_basis_id="local:model:latent:v1",
            checkpoint_sha256="2" * 64,
            tokenizer_container_sha256="3" * 64,
            runtime_source_commit="4" * 40,
            runtime_build_sha256="5" * 64,
            role="critic",
            n_embd=3,
            n_layer=4,
            il_start=1,
            il_end=2,
            calibration_dataset_sha256="6" * 64,
            calibration_split_sha256="7" * 64,
            holdout_split_sha256="8" * 64,
        )

    def source_packet(self):
        return encode_vector(
            (0.5, -1.0),
            basis_id="global:jspace:semantic:v1",
            basis_sha256="1" * 64,
            generation=7,
            role="critic",
            control_condition="BASELINE",
        )

    def test_shared_semantic_packet_becomes_distinct_local_packet_and_cvec(self):
        adapter = self.adapter()
        local_packet, receipt = adapt_control_packet(self.source_packet(), adapter, current_generation=7)
        self.assertNotEqual(local_packet.packet_sha256, receipt.source_packet_sha256)
        self.assertEqual(local_packet.basis_id, adapter.local_basis_id)
        self.assertEqual(local_packet.basis_sha256, adapter.adapter_sha256)
        self.assertEqual(local_packet.dimension, 3)
        self.assertEqual(receipt.n_embd, 3)

        raw, binding = build_llamacpp_cvec_buffer(
            local_packet,
            current_generation=7,
            expected_basis_id=adapter.local_basis_id,
            expected_basis_sha256=adapter.adapter_sha256,
            expected_role="critic",
            checkpoint_sha256=adapter.checkpoint_sha256,
            llama_cpp_source_commit=adapter.runtime_source_commit,
            n_embd=adapter.n_embd,
            n_layer=adapter.n_layer,
            il_start=adapter.il_start,
            il_end=adapter.il_end,
            strength=1.0,
        )
        self.assertEqual(binding.vector_control_packet_sha256, local_packet.packet_sha256)
        self.assertEqual(binding.cvec_f32le_sha256, __import__("hashlib").sha256(raw).hexdigest())

    def test_adapter_digest_is_revalidated(self):
        adapter = self.adapter()
        forged = replace(adapter, checkpoint_sha256="9" * 64)
        with self.assertRaisesRegex(JSpaceLatentBasisAdapterError, "LATENT_BASIS_ADAPTER_DIGEST_MISMATCH"):
            validate_latent_basis_adapter(forged)

    def test_source_packet_from_wrong_global_basis_fails_closed(self):
        adapter = self.adapter()
        packet = encode_vector(
            (0.5, -1.0),
            basis_id="other:global:basis",
            basis_sha256="9" * 64,
            generation=7,
            role="critic",
        )
        with self.assertRaises(Exception):
            adapt_control_packet(packet, adapter, current_generation=7)

    def test_axis_must_be_unit_calibrated_direction(self):
        with self.assertRaisesRegex(JSpaceLatentBasisAdapterError, "UNIT_DIRECTION_REQUIRED"):
            build_latent_basis_adapter(
                (("intent:a", "a" * 64, (2.0, 0.0, 0.0)),),
                source_jspace_basis_id="global:jspace:semantic:v1",
                source_jspace_basis_sha256="1" * 64,
                local_basis_id="local:model:latent:v1",
                checkpoint_sha256="2" * 64,
                tokenizer_container_sha256="3" * 64,
                runtime_source_commit="4" * 40,
                runtime_build_sha256="5" * 64,
                role="critic",
                n_embd=3,
                n_layer=4,
                il_start=1,
                il_end=2,
                calibration_dataset_sha256="6" * 64,
                calibration_split_sha256="7" * 64,
                holdout_split_sha256="8" * 64,
            )


if __name__ == "__main__":
    unittest.main()
