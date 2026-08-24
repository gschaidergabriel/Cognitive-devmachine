import hashlib
import unittest

from jspace_activation_steering_search_v1 import (
    ActivationSteeringError,
    HOOK_RECEIPT_SCHEMA,
    HookReceipt,
    SteeringObservation,
    applied_vector_sha256,
    search_activation_steering,
)


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SyntheticExecutor:
    def __init__(self, target_layer="L3", target=(1.0, 0.0)):
        self.target_layer = target_layer
        self.target = target

    def run(self, prompt, *, layer_id, vector, alpha, seed):
        if layer_id is None:
            return SteeringObservation(f"{0.10 + seed * 0.001:.9f}", None)
        dot = sum(a * b for a, b in zip(vector, self.target))
        effect = dot * alpha if layer_id == self.target_layer else 0.0
        base = 0.10 + seed * 0.001
        vector_sha = applied_vector_sha256(vector)
        receipt = HookReceipt(
            HOOK_RECEIPT_SCHEMA,
            "synthetic:v1",
            f"invocation:{seed}",
            layer_id,
            seed,
            alpha,
            vector_sha,
            _sha(f"pre:{layer_id}:{seed}"),
            _sha(f"post:{layer_id}:{seed}:{alpha}:{vector_sha}"),
        )
        return SteeringObservation(f"{base + effect:.9f}", receipt)


def score(observation):
    return float(observation.output_text)


class ActivationSteeringSearchTests(unittest.TestCase):
    def test_finds_directional_layer_and_alpha_with_zero_control(self):
        result = search_activation_steering(
            SyntheticExecutor(),
            "probe",
            (1.0, 0.0),
            vector_control_packet_sha256="1" * 64,
            layer_ids=("L1", "L3"),
            alphas=(-2.0, -1.0, 1.0, 2.0),
            seeds=(1, 2, 3),
            score_fn=score,
            min_delta=0.5,
            min_directional_gap=1.0,
        )
        self.assertTrue(result.success)
        self.assertEqual((result.best.layer_id, result.best.alpha), ("L3", 2.0))
        self.assertEqual(result.sign_control.alpha, -2.0)
        self.assertAlmostEqual(result.zero_control_mean_delta, 0.0)

    def test_rejects_missing_sign_pair(self):
        with self.assertRaisesRegex(ActivationSteeringError, "SIGN_PAIRED"):
            search_activation_steering(
                SyntheticExecutor(),
                "probe",
                (1.0, 0.0),
                vector_control_packet_sha256="1" * 64,
                layer_ids=("L3",),
                alphas=(1.0,),
                seeds=(1,),
                score_fn=score,
            )

    def test_rejects_forged_applied_vector_receipt(self):
        class BadExecutor(SyntheticExecutor):
            def run(self, *args, **kwargs):
                observation = super().run(*args, **kwargs)
                if observation.hook_receipt is None:
                    return observation
                receipt = observation.hook_receipt
                return SteeringObservation(
                    observation.output_text,
                    HookReceipt(
                        receipt.schema,
                        receipt.executor_id,
                        receipt.invocation_id,
                        receipt.layer_id,
                        receipt.seed,
                        receipt.alpha,
                        "2" * 64,
                        receipt.pre_activation_sha256,
                        receipt.post_activation_sha256,
                    ),
                )

        with self.assertRaisesRegex(ActivationSteeringError, "APPLIED_VECTOR_MISMATCH"):
            search_activation_steering(
                BadExecutor(),
                "probe",
                (1.0, 0.0),
                vector_control_packet_sha256="1" * 64,
                layer_ids=("L3",),
                alphas=(-1.0, 1.0),
                seeds=(1,),
                score_fn=score,
            )


if __name__ == "__main__":
    unittest.main()
