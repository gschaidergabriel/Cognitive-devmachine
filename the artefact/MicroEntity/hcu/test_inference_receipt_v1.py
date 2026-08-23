import copy
import unittest

from inference_receipt_v1 import (
    InferenceReceiptError,
    make_inference_receipt,
)
from reactive_event_router_v1 import EngineAdmission, route_event
from xeno_entry_fabric_v1 import admit_entry, to_hcu_reactive_event


CAPABILITY_BINDING_SHA256 = "b" * 64
ENGINE_SHA256 = "a" * 64
OUTPUT_SHA256 = "d" * 64


def base_entry():
    return {
        "schema": "XENO_ENTRY_PACKET/v1",
        "ingress_id": "ingress:receipt:1",
        "causal_id": "causal:receipt:1",
        "entity_generation": 7,
        "source_kind": "HUMAN_PROMPT",
        "source_id": "user:test",
        "modality": "TEXT",
        "observed_time": "2026-08-23T23:24:00+07:00",
        "received_time": "2026-08-23T23:24:01+07:00",
        "provenance_ref": "unifieddb:source:receipt:1",
        "provenance_sha256": "c" * 64,
        "capabilities": ["memory.read", "hcu.route"],
        "capability_binding_sha256": CAPABILITY_BINDING_SHA256,
        "parent_id": None,
        "stream_id": "stream:receipt",
        "budget": {
            "max_model_calls": 1,
            "max_tokens": 1024,
            "max_wall_ms": 2500,
        },
        "payload_ref": "unifieddb:payload:receipt:1",
        "payload_sha256": "e" * 64,
    }


def admitted_packet():
    return admit_entry(
        base_entry(),
        current_generation=7,
        expected_capability_binding_sha256=CAPABILITY_BINDING_SHA256,
        admitted_capabilities=("memory.read", "hcu.route"),
    )


def model_route():
    packet = admitted_packet()
    event = to_hcu_reactive_event(packet, novelty=0.8, zero_relevance=0.8)
    event["requested_internal_provider"] = "hcu"
    entry_bindings = {packet.admission_sha256: packet.event_sha256}
    engine_artifacts = {"hcu_local_08b": ENGINE_SHA256}
    engine_admission = EngineAdmission(
        provider_alias="hcu",
        engine_identity="hcu_local_08b",
        engine_class="LOCAL_SHARED_WEIGHT_08B",
        engine_artifact_sha256=ENGINE_SHA256,
    )
    decision = route_event(
        event,
        current_generation=7,
        engine_admission=engine_admission,
        admitted_engine_artifacts=engine_artifacts,
        admitted_entry_bindings=entry_bindings,
    )
    return packet, decision, entry_bindings, engine_artifacts


def receipt_kwargs():
    packet, decision, entry_bindings, engine_artifacts = model_route()
    kwargs = {
        "current_generation": 7,
        "admitted_route_generations": {decision.decision_sha256: 7},
        "entry_admission_sha256": packet.admission_sha256,
        "admitted_entry_bindings": entry_bindings,
        "admitted_engine_artifacts": engine_artifacts,
        "model_call_id": "model-call:receipt:1",
        "output_ref": "unifieddb:candidate-output:receipt:1",
        "output_sha256": OUTPUT_SHA256,
        "output_size": 128,
    }
    return packet, decision, kwargs


class InferenceReceiptTests(unittest.TestCase):
    def test_bound_candidate_receipt_is_deterministic(self):
        packet, decision, kwargs = receipt_kwargs()
        a = make_inference_receipt(decision, **kwargs)
        b = make_inference_receipt(decision, **copy.deepcopy(kwargs))
        self.assertEqual(a, b)
        self.assertEqual(a.status, "CANDIDATE_ONLY")
        self.assertEqual(a.entity_generation, 7)
        self.assertEqual(a.entry_admission_sha256, packet.admission_sha256)
        self.assertEqual(a.event_sha256, packet.event_sha256)
        self.assertEqual(a.decision_sha256, decision.decision_sha256)
        self.assertEqual(a.resolved_engine_artifact_sha256, ENGINE_SHA256)
        self.assertEqual(len(a.receipt_sha256), 64)

    def test_stale_bound_route_generation_fails_closed(self):
        _packet, decision, kwargs = receipt_kwargs()
        kwargs["current_generation"] = 8
        with self.assertRaisesRegex(InferenceReceiptError, "STALE_ROUTE_GENERATION"):
            make_inference_receipt(decision, **kwargs)

    def test_missing_route_generation_binding_fails_closed(self):
        _packet, decision, kwargs = receipt_kwargs()
        kwargs["admitted_route_generations"] = {}
        with self.assertRaisesRegex(InferenceReceiptError, "ROUTE_GENERATION_NOT_ADMITTED"):
            make_inference_receipt(decision, **kwargs)

    def test_unadmitted_entry_receipt_fails_closed(self):
        _packet, decision, kwargs = receipt_kwargs()
        kwargs["admitted_entry_bindings"] = {}
        with self.assertRaisesRegex(InferenceReceiptError, "ENTRY_ADMISSION_NOT_ADMITTED"):
            make_inference_receipt(decision, **kwargs)

    def test_route_entry_admission_must_match_receipt_admission(self):
        _packet, decision, kwargs = receipt_kwargs()
        kwargs["entry_admission_sha256"] = "9" * 64
        with self.assertRaisesRegex(InferenceReceiptError, "ROUTE_ENTRY_ADMISSION_IDENTITY_MISMATCH"):
            make_inference_receipt(decision, **kwargs)

    def test_entry_binding_must_match_route_event(self):
        packet, decision, kwargs = receipt_kwargs()
        kwargs["admitted_entry_bindings"] = {packet.admission_sha256: "9" * 64}
        with self.assertRaisesRegex(InferenceReceiptError, "ENTRY_EVENT_ROUTE_IDENTITY_MISMATCH"):
            make_inference_receipt(decision, **kwargs)

    def test_engine_lock_rotation_fails_closed(self):
        _packet, decision, kwargs = receipt_kwargs()
        kwargs["admitted_engine_artifacts"] = {"hcu_local_08b": "9" * 64}
        with self.assertRaisesRegex(InferenceReceiptError, "ENGINE_ARTIFACT_ADMISSION_MISMATCH"):
            make_inference_receipt(decision, **kwargs)

    def test_output_digest_and_size_are_typed(self):
        _packet, decision, kwargs = receipt_kwargs()
        kwargs["output_sha256"] = "not-a-digest"
        with self.assertRaisesRegex(InferenceReceiptError, "output_sha256"):
            make_inference_receipt(decision, **kwargs)

        _packet, decision, kwargs = receipt_kwargs()
        kwargs["output_size"] = -1
        with self.assertRaisesRegex(InferenceReceiptError, "output_size"):
            make_inference_receipt(decision, **kwargs)

    def test_script_only_route_cannot_mint_inference_receipt(self):
        packet = admitted_packet()
        event = to_hcu_reactive_event(packet)
        entry_bindings = {packet.admission_sha256: packet.event_sha256}
        decision = route_event(
            event,
            current_generation=7,
            admitted_entry_bindings=entry_bindings,
        )
        with self.assertRaisesRegex(InferenceReceiptError, "MODEL_ACTIVATION_ROUTE_REQUIRED"):
            make_inference_receipt(
                decision,
                current_generation=7,
                admitted_route_generations={decision.decision_sha256: 7},
                entry_admission_sha256=packet.admission_sha256,
                admitted_entry_bindings=entry_bindings,
                admitted_engine_artifacts={"hcu_local_08b": ENGINE_SHA256},
                model_call_id="model-call:should-not-exist",
                output_ref="unifieddb:candidate-output:should-not-exist",
                output_sha256=OUTPUT_SHA256,
                output_size=1,
            )


if __name__ == "__main__":
    unittest.main()
