import math
import unittest

from jspace_model_activation_basis_v1 import (
    JSpaceModelActivationBasisError,
    build_capture,
    calibrate_basis,
    project_control_packet,
)
from jspace_vector_control_v1 import encode_vector


MODEL_SHA = "1" * 64
TOKENIZER_SHA = "2" * 64
RUNTIME_SHA = "3" * 64


def capture(values, *, family, polarity, seed=7, layer="model.layers.12", model_sha=MODEL_SHA):
    return build_capture(
        values,
        model_artifact_sha256=model_sha,
        tokenizer_artifact_sha256=TOKENIZER_SHA,
        runtime_build_sha256=RUNTIME_SHA,
        layer_id=layer,
        prompt_family_id=family,
        prompt_polarity=polarity,
        seed=seed,
    )


class JSpaceModelActivationBasisTests(unittest.TestCase):
    def basis(self):
        # Axis A mean delta points +x; Axis B mean delta points +y.
        return calibrate_basis(
            {
                "axis:a": (
                    (capture((2.0, 0.0, 0.0), family="a:1", polarity="POSITIVE"), capture((0.0, 0.0, 0.0), family="a:1", polarity="NEGATIVE")),
                    (capture((3.0, 0.0, 0.0), family="a:2", polarity="POSITIVE"), capture((1.0, 0.0, 0.0), family="a:2", polarity="NEGATIVE")),
                ),
                "axis:b": (
                    (capture((0.0, 4.0, 0.0), family="b:1", polarity="POSITIVE"), capture((0.0, 1.0, 0.0), family="b:1", polarity="NEGATIVE")),
                ),
            },
            basis_id="qwen3-0.6b:model.layers.12:jspace:v1",
        )

    def test_contrastive_axes_are_unit_and_model_bound(self):
        basis = self.basis()
        self.assertEqual(basis.hidden_size, 3)
        self.assertEqual(basis.model_artifact_sha256, MODEL_SHA)
        self.assertEqual(basis.layer_id, "model.layers.12")
        self.assertEqual(tuple(axis.axis_id for axis in basis.axes), ("axis:a", "axis:b"))
        self.assertEqual(basis.axes[0].direction, (1.0, 0.0, 0.0))
        self.assertEqual(basis.axes[1].direction, (0.0, 1.0, 0.0))
        for axis in basis.axes:
            self.assertAlmostEqual(math.sqrt(sum(v * v for v in axis.direction)), 1.0)

    def test_control_packet_projects_only_through_exact_basis_identity(self):
        basis = self.basis()
        packet = encode_vector(
            (0.5, -1.0),
            basis_id=basis.basis_id,
            basis_sha256=basis.basis_sha256,
            generation=7,
            role="critic",
            control_condition="BASELINE",
        )
        projection = project_control_packet(packet, basis, current_generation=7, expected_role="critic")
        self.assertEqual(projection.layer_id, basis.layer_id)
        self.assertEqual(projection.hidden_size, 3)
        self.assertAlmostEqual(projection.hidden_vector[0], 0.5, places=2)
        self.assertAlmostEqual(projection.hidden_vector[1], -1.0, places=7)
        self.assertAlmostEqual(projection.hidden_vector[2], 0.0, places=7)

    def test_wrong_model_identity_inside_contrastive_pair_fails_closed(self):
        positive = capture((1.0, 0.0), family="x", polarity="POSITIVE")
        negative = capture((0.0, 0.0), family="x", polarity="NEGATIVE", model_sha="4" * 64)
        with self.assertRaisesRegex(JSpaceModelActivationBasisError, "CONTRASTIVE_PAIR_MODEL_LAYER_IDENTITY_MISMATCH"):
            calibrate_basis({"axis:x": ((positive, negative),)}, basis_id="basis:x")

    def test_unpaired_prompt_family_fails_closed(self):
        positive = capture((1.0, 0.0), family="x:positive", polarity="POSITIVE")
        negative = capture((0.0, 0.0), family="x:negative", polarity="NEGATIVE")
        with self.assertRaisesRegex(JSpaceModelActivationBasisError, "CONTRASTIVE_PAIR_FAMILY_MISMATCH"):
            calibrate_basis({"axis:x": ((positive, negative),)}, basis_id="basis:x")

    def test_zero_contrastive_direction_fails_closed(self):
        positive = capture((1.0, 2.0), family="x", polarity="POSITIVE")
        negative = capture((1.0, 2.0), family="x", polarity="NEGATIVE")
        with self.assertRaisesRegex(JSpaceModelActivationBasisError, "CONTRASTIVE_DIRECTION_ZERO_OR_NONFINITE"):
            calibrate_basis({"axis:x": ((positive, negative),)}, basis_id="basis:x")

    def test_packet_from_other_basis_is_rejected(self):
        basis = self.basis()
        packet = encode_vector(
            (0.5, -1.0),
            basis_id="other:basis",
            basis_sha256="5" * 64,
            generation=7,
            role="critic",
        )
        with self.assertRaisesRegex(JSpaceModelActivationBasisError, "CONTROL_PACKET_MODEL_BASIS_ID_MISMATCH"):
            project_control_packet(packet, basis, current_generation=7, expected_role="critic")


if __name__ == "__main__":
    unittest.main()
