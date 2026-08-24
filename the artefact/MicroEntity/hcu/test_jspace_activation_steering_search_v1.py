import hashlib
import unittest

from jspace_activation_steering_search_v1 import (
    ActivationSteeringError,
    EVIDENCE_CLASS,
    HOOK_RECEIPT_SCHEMA,
    MISSING_CAUSAL_CONTROLS,
    REQUIRED_CAUSAL_CONTROLS,
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
        pre = _sha(f"pre:{layer_id}:{seed}")
        # A correct zero-vector control is an exact physical no-op at the selected activation.
        post = pre if all(value == 0.0 for value in vector) else _sha(f"post:{layer_id}:{seed}:{alpha}:{vector_sha}")
        receipt = HookReceipt(
            HOOK_RECEIPT_SCHEMA,
            "synthetic:v1",
            f"invocation:{seed}",
            layer_id,
            seed,
            alpha,
            vector_sha,
            pre,
            post,
        )
        return SteeringObservation(f"{base + effect:.9f}", receipt)


def score(observation):
    return float(observation.output_text)


class ActivationSteeringSearchTests(unittest.TestCase):
    def _successful_search(self):
        return search_activation_steering(
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

    def test_finds_directional_layer_and_alpha_with_zero_control(self):
        result = self._successful_search()
        self.assertTrue(result.success)
        self.assertEqual((result.best.layer_id, result.best.alpha), ("L3", 2.0))
        self.assertEqual(result.sign_control.alpha, -2.0)
        self.assertAlmostEqual(result.zero_control_mean_delta, 0.0)

    def test_success_is_explicitly_noncausal_under_current_jspace_gate(self):
        result = self._successful_search()
        self.assertTrue(result.success)
        self.assertEqual(result.evidence_class, EVIDENCE_CLASS)
        self.assertFalse(result.jspace_causal_credit)
        self.assertEqual(result.required_causal_controls, REQUIRED_CAUSAL_CONTROLS)
        self.assertEqual(result.missing_causal_controls, MISSING_CAUSAL_CONTROLS)
        self.assertIn("BASELINE_CORRUPTED", result.missing_causal_controls)
        self.assertIn("SHAM_CONTROL", result.missing_causal_controls)
        self.assertIn("OFF_TARGET_CONTROL", result.missing_causal_controls)

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

    def test_rejects_zero_vector_control_that_changes_activation(self):
        class BadZeroExecutor(SyntheticExecutor):
            def run(self, prompt, *, layer_id, vector, alpha, seed):
                observation = super().run(prompt, layer_id=layer_id, vector=vector, alpha=alpha, seed=seed)
                if observation.hook_receipt is None or not all(value == 0.0 for value in vector):
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
                        receipt.applied_vector_sha256,
                        receipt.pre_activation_sha256,
                        _sha("unexpected-zero-vector-mutation"),
                    ),
                )

        with self.assertRaisesRegex(ActivationSteeringError, "ZERO_VECTOR_CONTROL_CHANGED_ACTIVATION"):
            search_activation_steering(
                BadZeroExecutor(),
                "probe",
                (1.0, 0.0),
                vector_control_packet_sha256="1" * 64,
                layer_ids=("L3",),
                alphas=(-1.0, 1.0),
                seeds=(1,),
                score_fn=score,
                min_delta=0.1,
                min_directional_gap=0.1,
            )


if __name__ == "__main__":
    unittest.main()
