import unittest

from inference_receipt_v1 import (
    InferenceReceiptError,
    build_inference_receipt,
    validate_inference_receipt,
)
from reactive_event_router_v1 import route_event


ENGINE_SHA256 = "a" * 64


def model_event():
    return {
        "schema": "HCU_REACTIVE_EVENT/v1",
        "entity_generation": 7,
        "novelty": 0.8,
        "contradiction": 0.0,
        "uncertainty": 0.10,
        "forecast_need": 0.0,
        "effect_pressure": 0.0,
        "zero_relevance": 0.10,
        "due_recheck": False,
        "requested_internal_provider": "hcu",
        "resolved_internal_engine": "hcu_local_08b",
        "resolved_internal_engine_class": "LOCAL_SHARED_WEIGHT_08B",
        "resolved_internal_engine_artifact_sha256": ENGINE_SHA256,
    }


def script_only_event():
    event = model_event()
    event.update(novelty=0.0)
    for key in (
        "requested_internal_provider",
        "resolved_internal_engine",
        "resolved_internal_engine_class",
        "resolved_internal_engine_artifact_sha256",
    ):
        event.pop(key)
    return event


class InferenceReceiptTests(unittest.TestCase):
    def test_producer_derives_exact_route_echo_and_candidate_digest(self):
        decision = route_event(model_event(), current_generation=7)
        result = {"candidate": "inspect causal predecessor", "confidence": 0.61}
        receipt = build_inference_receipt(decision, result)

        self.assertEqual(receipt.event_sha256, decision.event_sha256)
        self.assertEqual(receipt.router_policy_sha256, decision.router_policy_sha256)
        self.assertEqual(receipt.decision_sha256, decision.decision_sha256)
        self.assertEqual(receipt.engine_identity_sha256, decision.engine_identity_sha256)
        self.assertEqual(receipt.resolved_engine_identity, decision.resolved_engine_identity)
        self.assertEqual(receipt.resolved_engine_class, decision.resolved_engine_class)
        self.assertEqual(
            receipt.resolved_engine_artifact_sha256,
            decision.resolved_engine_artifact_sha256,
        )
        self.assertEqual(len(receipt.candidate_result_sha256), 64)
        self.assertEqual(len(receipt.receipt_sha256), 64)
        validate_inference_receipt(decision, receipt, candidate_result=result)

    def test_exact_replay_is_deterministic(self):
        decision = route_event(model_event(), current_generation=7)
        result = {"candidate": ["h1", "h0"], "selected": None}
        a = build_inference_receipt(decision, result)
        b = build_inference_receipt(decision, dict(reversed(list(result.items()))))
        self.assertEqual(a, b)

    def test_candidate_result_change_changes_receipt_without_changing_route(self):
        decision = route_event(model_event(), current_generation=7)
        a = build_inference_receipt(decision, {"candidate": "A"})
        b = build_inference_receipt(decision, {"candidate": "B"})
        self.assertEqual(a.decision_sha256, b.decision_sha256)
        self.assertEqual(a.engine_identity_sha256, b.engine_identity_sha256)
        self.assertNotEqual(a.candidate_result_sha256, b.candidate_result_sha256)
        self.assertNotEqual(a.receipt_sha256, b.receipt_sha256)

    def test_post_hoc_route_echo_mutation_fails_closed(self):
        decision = route_event(model_event(), current_generation=7)
        receipt = build_inference_receipt(decision, {"candidate": "A"})
        poisoned = dict(receipt.__dict__)
        poisoned["event_sha256"] = "0" * 64
        with self.assertRaisesRegex(InferenceReceiptError, "ROUTE_ECHO_MISMATCH"):
            validate_inference_receipt(decision, poisoned)

    def test_post_hoc_candidate_digest_mutation_breaks_receipt_identity(self):
        decision = route_event(model_event(), current_generation=7)
        receipt = build_inference_receipt(decision, {"candidate": "A"})
        poisoned = dict(receipt.__dict__)
        poisoned["candidate_result_sha256"] = "0" * 64
        with self.assertRaisesRegex(InferenceReceiptError, "RECEIPT_DIGEST_MISMATCH"):
            validate_inference_receipt(decision, poisoned)

    def test_actual_candidate_must_match_bound_candidate_digest(self):
        decision = route_event(model_event(), current_generation=7)
        receipt = build_inference_receipt(decision, {"candidate": "A"})
        with self.assertRaisesRegex(InferenceReceiptError, "CANDIDATE_RESULT_DIGEST_MISMATCH"):
            validate_inference_receipt(decision, receipt, candidate_result={"candidate": "B"})

    def test_script_only_route_cannot_emit_inference_receipt(self):
        decision = route_event(script_only_event(), current_generation=7)
        with self.assertRaisesRegex(InferenceReceiptError, "MODEL_ROUTE_REQUIRED"):
            build_inference_receipt(decision, {"candidate": "should not exist"})

    def test_noncanonical_candidate_result_fails_closed(self):
        decision = route_event(model_event(), current_generation=7)
        with self.assertRaisesRegex(InferenceReceiptError, "CANDIDATE_RESULT:CANONICALIZATION_FAILED"):
            build_inference_receipt(decision, {"bad": float("nan")})


if __name__ == "__main__":
    unittest.main()
