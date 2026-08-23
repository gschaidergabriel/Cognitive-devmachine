import copy
import hashlib
import json
import unittest

from engine_admission_v1 import EngineArtifactLock, derive_engine_artifact_sha256
from inference_receipt_v1 import (
    InferenceReceiptError,
    make_inference_receipt,
)
from reactive_event_router_v1 import EngineAdmission, route_event
from xeno_entry_fabric_v1 import admit_entry, to_hcu_reactive_event


CAPABILITY_BINDING_SHA256 = "b" * 64
CHECKPOINT_SHA256 = "1" * 64
TOKENIZER_SHA256 = "2" * 64
RUNTIME_SHA256 = "3" * 64
BUILD_SHA256 = "4" * 64
LOADER_RUNTIME_SHA256 = "5" * 64
OUTPUT_SHA256 = "d" * 64


def _canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _engine_artifact_sha256():
    lock = EngineArtifactLock(
        schema="HCU_ENGINE_ARTIFACT_LOCK/v1",
        provider_alias="hcu",
        engine_identity="hcu_local_08b",
        engine_class="LOCAL_SHARED_WEIGHT_08B",
        checkpoint_sha256=CHECKPOINT_SHA256,
        tokenizer_sha256=TOKENIZER_SHA256,
        runtime_sha256=RUNTIME_SHA256,
        build_sha256=BUILD_SHA256,
        engine_artifact_sha256="a" * 64,
    )
    return derive_engine_artifact_sha256(lock)


ENGINE_SHA256 = _engine_artifact_sha256()


def engine_admission_receipt(*, generation=7):
    material = {
        "schema": "HCU_VERIFIED_ENGINE_ADMISSION_RECEIPT/v1",
        "entity_generation": generation,
        "provider_alias": "hcu",
        "engine_identity": "hcu_local_08b",
        "engine_class": "LOCAL_SHARED_WEIGHT_08B",
        "checkpoint": {
            "kind": "FILE_SHA256",
            "sha256": CHECKPOINT_SHA256,
            "file_count": 1,
            "byte_count": 10,
        },
        "tokenizer": {
            "kind": "FILE_SHA256",
            "sha256": TOKENIZER_SHA256,
            "file_count": 1,
            "byte_count": 11,
        },
        "runtime": {
            "kind": "FILE_SHA256",
            "sha256": RUNTIME_SHA256,
            "file_count": 1,
            "byte_count": 12,
        },
        "build": {
            "kind": "FILE_SHA256",
            "sha256": BUILD_SHA256,
            "file_count": 1,
            "byte_count": 13,
        },
        "engine_artifact_sha256": ENGINE_SHA256,
    }
    receipt_sha256 = hashlib.sha256(_canonical(material)).hexdigest()
    return {**material, "receipt_sha256": receipt_sha256}


def engine_load_lease(*, engine_receipt=None, generation=7):
    engine_receipt = engine_receipt or engine_admission_receipt(generation=generation)
    material = {
        "schema": "HCU_PHYSICAL_ENGINE_LOAD_LEASE/v1",
        "entity_generation": generation,
        "engine_identity": "hcu_local_08b",
        "engine_class": "LOCAL_SHARED_WEIGHT_08B",
        "engine_artifact_sha256": ENGINE_SHA256,
        "engine_admission_receipt_sha256": engine_receipt["receipt_sha256"],
        "consumed_checkpoint_sha256": CHECKPOINT_SHA256,
        "consumed_tokenizer_sha256": TOKENIZER_SHA256,
        "consumed_runtime_sha256": RUNTIME_SHA256,
        "consumed_build_sha256": BUILD_SHA256,
        "loader_identity": "entityos:hcu:local-loader:v1",
        "loader_runtime_sha256": LOADER_RUNTIME_SHA256,
        "lease_id": "engine-lease:g7:001",
    }
    lease_sha256 = hashlib.sha256(_canonical(material)).hexdigest()
    return {**material, "lease_sha256": lease_sha256}


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


def receipt_kwargs(*, engine_receipt=None, load_lease=None):
    packet, decision, entry_bindings, engine_artifacts = model_route()
    engine_receipt = engine_receipt or engine_admission_receipt()
    engine_receipt_sha256 = engine_receipt["receipt_sha256"]
    load_lease = load_lease or engine_load_lease(engine_receipt=engine_receipt)
    load_lease_sha256 = load_lease["lease_sha256"]
    kwargs = {
        "current_generation": 7,
        "admitted_route_generations": {decision.decision_sha256: 7},
        "entry_admission_sha256": packet.admission_sha256,
        "admitted_entry_bindings": entry_bindings,
        "admitted_engine_artifacts": engine_artifacts,
        "engine_admission_receipt_sha256": engine_receipt_sha256,
        "admitted_engine_admission_receipts": {
            engine_receipt_sha256: engine_receipt,
        },
        "engine_load_lease_sha256": load_lease_sha256,
        "admitted_engine_load_leases": {
            load_lease_sha256: load_lease,
        },
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
        self.assertEqual(
            a.engine_admission_receipt_sha256,
            kwargs["engine_admission_receipt_sha256"],
        )
        self.assertEqual(
            a.engine_load_lease_sha256,
            kwargs["engine_load_lease_sha256"],
        )
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

    def test_receiptless_structural_engine_admission_cannot_mint_inference_receipt(self):
        _packet, decision, kwargs = receipt_kwargs()
        kwargs["admitted_engine_admission_receipts"] = {}
        with self.assertRaisesRegex(InferenceReceiptError, "ENGINE_ADMISSION_RECEIPT_NOT_ADMITTED"):
            make_inference_receipt(decision, **kwargs)

    def test_engine_admission_receipt_generation_is_bound(self):
        stale_receipt = engine_admission_receipt(generation=6)
        stale_lease = engine_load_lease(engine_receipt=stale_receipt, generation=6)
        _packet, decision, kwargs = receipt_kwargs(engine_receipt=stale_receipt, load_lease=stale_lease)
        with self.assertRaisesRegex(InferenceReceiptError, "STALE_ENGINE_ADMISSION_RECEIPT_GENERATION"):
            make_inference_receipt(decision, **kwargs)

    def test_engine_admission_receipt_bundle_tamper_fails_closed(self):
        receipt = engine_admission_receipt()
        receipt["runtime"]["sha256"] = "9" * 64
        _packet, decision, kwargs = receipt_kwargs()
        kwargs["admitted_engine_admission_receipts"] = {
            kwargs["engine_admission_receipt_sha256"]: receipt,
        }
        with self.assertRaisesRegex(
            InferenceReceiptError,
            "ENGINE_ADMISSION_RECEIPT_BUNDLE_DIGEST_MISMATCH|ENGINE_ADMISSION_RECEIPT_DIGEST_MISMATCH",
        ):
            make_inference_receipt(decision, **kwargs)

    def test_missing_physical_engine_load_lease_fails_closed(self):
        _packet, decision, kwargs = receipt_kwargs()
        kwargs["admitted_engine_load_leases"] = {}
        with self.assertRaisesRegex(InferenceReceiptError, "ENGINE_LOAD_LEASE_NOT_ADMITTED"):
            make_inference_receipt(decision, **kwargs)

    def test_stale_physical_engine_load_lease_fails_closed(self):
        receipt = engine_admission_receipt()
        stale_lease = engine_load_lease(engine_receipt=receipt, generation=6)
        _packet, decision, kwargs = receipt_kwargs(engine_receipt=receipt, load_lease=stale_lease)
        with self.assertRaisesRegex(InferenceReceiptError, "STALE_ENGINE_LOAD_LEASE_GENERATION"):
            make_inference_receipt(decision, **kwargs)

    def test_physical_engine_load_lease_must_bind_engine_admission_receipt(self):
        _packet, decision, kwargs = receipt_kwargs()
        lease = copy.deepcopy(next(iter(kwargs["admitted_engine_load_leases"].values())))
        lease["engine_admission_receipt_sha256"] = "9" * 64
        old_sha = kwargs["engine_load_lease_sha256"]
        kwargs["admitted_engine_load_leases"] = {old_sha: lease}
        with self.assertRaisesRegex(InferenceReceiptError, "ENGINE_LOAD_LEASE_ADMISSION_RECEIPT_MISMATCH"):
            make_inference_receipt(decision, **kwargs)

    def test_physical_engine_load_lease_consumed_bytes_must_match_admission(self):
        _packet, decision, kwargs = receipt_kwargs()
        lease = copy.deepcopy(next(iter(kwargs["admitted_engine_load_leases"].values())))
        lease["consumed_checkpoint_sha256"] = "9" * 64
        old_sha = kwargs["engine_load_lease_sha256"]
        kwargs["admitted_engine_load_leases"] = {old_sha: lease}
        with self.assertRaisesRegex(
            InferenceReceiptError,
            "ENGINE_LOAD_LEASE_CONSUMED_BYTES_MISMATCH:checkpoint_sha256",
        ):
            make_inference_receipt(decision, **kwargs)

    def test_physical_engine_load_lease_digest_tamper_fails_closed(self):
        _packet, decision, kwargs = receipt_kwargs()
        lease = copy.deepcopy(next(iter(kwargs["admitted_engine_load_leases"].values())))
        lease["loader_identity"] = "entityos:hcu:tampered-loader"
        old_sha = kwargs["engine_load_lease_sha256"]
        kwargs["admitted_engine_load_leases"] = {old_sha: lease}
        with self.assertRaisesRegex(InferenceReceiptError, "ENGINE_LOAD_LEASE_DIGEST_MISMATCH"):
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
        engine_receipt = engine_admission_receipt()
        load_lease = engine_load_lease(engine_receipt=engine_receipt)
        with self.assertRaisesRegex(InferenceReceiptError, "MODEL_ACTIVATION_ROUTE_REQUIRED"):
            make_inference_receipt(
                decision,
                current_generation=7,
                admitted_route_generations={decision.decision_sha256: 7},
                entry_admission_sha256=packet.admission_sha256,
                admitted_entry_bindings=entry_bindings,
                admitted_engine_artifacts={"hcu_local_08b": ENGINE_SHA256},
                engine_admission_receipt_sha256=engine_receipt["receipt_sha256"],
                admitted_engine_admission_receipts={
                    engine_receipt["receipt_sha256"]: engine_receipt,
                },
                engine_load_lease_sha256=load_lease["lease_sha256"],
                admitted_engine_load_leases={
                    load_lease["lease_sha256"]: load_lease,
                },
                model_call_id="model-call:should-not-exist",
                output_ref="unifieddb:candidate-output:should-not-exist",
                output_sha256=OUTPUT_SHA256,
                output_size=1,
            )


if __name__ == "__main__":
    unittest.main()
