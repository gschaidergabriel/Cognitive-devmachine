import copy
import hashlib
import unittest
from dataclasses import asdict

from engine_admission_v1 import (
    ENGINE_ADMISSION_RECEIPT_SCHEMA,
    LOCK_SCHEMA,
    ArtifactDigest,
    EngineArtifactLock,
    VerifiedEngineAdmission,
    derive_engine_artifact_sha256,
)
from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from inference_receipt_v1 import InferenceReceiptError, make_inference_receipt
from physical_engine_lease_v1 import issue_physical_engine_lease
from reactive_event_router_v1 import (
    ENTRY_BINDING_SCHEMA,
    HASH_SERIALIZATION_SCHEMA,
    EngineAdmission,
    route_event,
)
from xeno_entry_fabric_v1 import admit_entry, to_hcu_reactive_event


CAPABILITY_BINDING_SHA256 = "b" * 64
CHECKPOINT_SHA256 = "1" * 64
TOKENIZER_SHA256 = "2" * 64
RUNTIME_SHA256 = "3" * 64
BUILD_SHA256 = "4" * 64
LOADER_RUNTIME_SHA256 = "5" * 64
BOUNDARY_RECEIPT_SHA256 = "6" * 64
OUTPUT_SHA256 = "d" * 64
ADMITTED_BUDGET = {
    "max_model_calls": 1,
    "max_tokens": 1024,
    "max_wall_ms": 2500,
}


def _canonical_sha256(value):
    return hashlib.sha256(canonicalize(value)).hexdigest()


def _engine_artifact_sha256():
    lock = EngineArtifactLock(
        schema=LOCK_SCHEMA,
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


def verified_engine_admission(*, generation=7):
    admission = EngineAdmission(
        provider_alias="hcu",
        engine_identity="hcu_local_08b",
        engine_class="LOCAL_SHARED_WEIGHT_08B",
        engine_artifact_sha256=ENGINE_SHA256,
    )
    checkpoint = ArtifactDigest("FILE_SHA256", CHECKPOINT_SHA256, 1, 10)
    tokenizer = ArtifactDigest("FILE_SHA256", TOKENIZER_SHA256, 1, 11)
    runtime = ArtifactDigest("FILE_SHA256", RUNTIME_SHA256, 1, 12)
    build = ArtifactDigest("FILE_SHA256", BUILD_SHA256, 1, 13)
    material = {
        "schema": ENGINE_ADMISSION_RECEIPT_SCHEMA,
        "hash_serialization_schema": HASH_SERIALIZATION_SCHEMA,
        "entity_generation": generation,
        "provider_alias": admission.provider_alias,
        "engine_identity": admission.engine_identity,
        "engine_class": admission.engine_class,
        "checkpoint": checkpoint.__dict__,
        "tokenizer": tokenizer.__dict__,
        "runtime": runtime.__dict__,
        "build": build.__dict__,
        "engine_artifact_sha256": ENGINE_SHA256,
    }
    return VerifiedEngineAdmission(
        entity_generation=generation,
        admission=admission,
        checkpoint=checkpoint,
        tokenizer=tokenizer,
        runtime=runtime,
        build=build,
        engine_artifact_sha256=ENGINE_SHA256,
        receipt_sha256=_canonical_sha256(material),
    )


def engine_admission_receipt(*, generation=7):
    return verified_engine_admission(generation=generation).receipt()


def engine_load_lease(*, verified=None, generation=7):
    verified = verified or verified_engine_admission(generation=generation)
    lease = issue_physical_engine_lease(
        verified,
        current_generation=generation,
        loader_generation=generation,
        loader_consumed_checkpoint_sha256=CHECKPOINT_SHA256,
        loader_consumed_tokenizer_sha256=TOKENIZER_SHA256,
        loader_consumed_runtime_sha256=RUNTIME_SHA256,
        loader_consumed_build_sha256=BUILD_SHA256,
        loader_instance_id=f"loader-{generation}-a",
        loader_runtime_sha256=LOADER_RUNTIME_SHA256,
        lease_id=f"lease-{generation}-a",
        artifact_boundary_receipt_sha256=BOUNDARY_RECEIPT_SHA256,
    )
    return asdict(lease)


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
        "budget": dict(ADMITTED_BUDGET),
        "payload_ref": "unifieddb:payload:receipt:1",
        "payload_sha256": "e" * 64,
    }


def admitted_packet():
    return admit_entry(
        base_entry(),
        current_generation=7,
        expected_capability_binding_sha256=CAPABILITY_BINDING_SHA256,
        admitted_capabilities=("memory.read", "hcu.route"),
        admitted_budget=ADMITTED_BUDGET,
    )


def entry_binding(packet):
    return {
        "schema": ENTRY_BINDING_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "event_sha256": packet.event_sha256,
    }


def model_route():
    packet = admitted_packet()
    event = to_hcu_reactive_event(packet, novelty=0.8, zero_relevance=0.8)
    event["requested_internal_provider"] = "hcu"
    entry_bindings = {packet.admission_sha256: entry_binding(packet)}
    engine_artifacts = {"hcu_local_08b": ENGINE_SHA256}
    verified = verified_engine_admission()
    decision = route_event(
        event,
        current_generation=7,
        engine_admission=verified.admission,
        admitted_engine_artifacts=engine_artifacts,
        admitted_entry_bindings=entry_bindings,
    )
    return packet, decision, entry_bindings, engine_artifacts, verified


def receipt_kwargs(*, verified=None, load_lease=None):
    packet, decision, entry_bindings, engine_artifacts, default_verified = model_route()
    verified = verified or default_verified
    engine_receipt = verified.receipt()
    engine_receipt_sha256 = engine_receipt["receipt_sha256"]
    load_lease = load_lease or engine_load_lease(verified=verified, generation=verified.entity_generation)
    load_lease_sha256 = load_lease["lease_sha256"]
    kwargs = {
        "current_generation": 7,
        "admitted_route_generations": {decision.decision_sha256: 7},
        "entry_admission_sha256": packet.admission_sha256,
        "admitted_entry_bindings": entry_bindings,
        "admitted_engine_artifacts": engine_artifacts,
        "engine_admission_receipt_sha256": engine_receipt_sha256,
        "admitted_engine_admission_receipts": {engine_receipt_sha256: engine_receipt},
        "engine_load_lease_sha256": load_lease_sha256,
        "admitted_engine_load_leases": {load_lease_sha256: load_lease},
        "model_call_id": "model-call:receipt:1",
        "output_ref": "unifieddb:candidate-output:receipt:1",
        "output_sha256": OUTPUT_SHA256,
        "output_size": 128,
    }
    return packet, decision, kwargs


class InferenceReceiptTests(unittest.TestCase):
    def test_current_identity_schemas_are_selected(self):
        self.assertEqual(CANONICALIZATION_SCHEMA, "RFC8785_JCS_IJSON/v1")
        self.assertEqual(HASH_SERIALIZATION_SCHEMA, CANONICALIZATION_SCHEMA)
        self.assertEqual(ENTRY_BINDING_SCHEMA, "ENTITYOS_HCU_ENTRY_ADMISSION_BINDING/v2")
        self.assertEqual(ENGINE_ADMISSION_RECEIPT_SCHEMA, "HCU_VERIFIED_ENGINE_ADMISSION_RECEIPT/v2")

    def test_bound_candidate_receipt_is_deterministic(self):
        packet, decision, kwargs = receipt_kwargs()
        a = make_inference_receipt(decision, **kwargs)
        b = make_inference_receipt(decision, **copy.deepcopy(kwargs))
        self.assertEqual(a, b)
        self.assertEqual(a.schema, "HCU_INFERENCE_RECEIPT/v2")
        self.assertEqual(a.status, "CANDIDATE_ONLY")
        self.assertEqual(a.hash_serialization_schema, CANONICALIZATION_SCHEMA)
        self.assertEqual(a.entry_binding_schema, ENTRY_BINDING_SCHEMA)
        self.assertEqual(a.entity_generation, 7)
        self.assertEqual(a.entry_admission_sha256, packet.admission_sha256)
        self.assertEqual(a.event_sha256, packet.event_sha256)
        self.assertEqual(a.decision_sha256, decision.decision_sha256)
        self.assertEqual(a.resolved_engine_artifact_sha256, ENGINE_SHA256)
        self.assertEqual(a.engine_admission_receipt_sha256, kwargs["engine_admission_receipt_sha256"])
        self.assertEqual(a.engine_load_lease_sha256, kwargs["engine_load_lease_sha256"])
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

    def test_legacy_bare_entry_binding_fails_closed(self):
        packet, decision, kwargs = receipt_kwargs()
        kwargs["admitted_entry_bindings"] = {packet.admission_sha256: packet.event_sha256}
        with self.assertRaisesRegex(InferenceReceiptError, "ENTRY_ADMISSION_BINDING_V2_REQUIRED"):
            make_inference_receipt(decision, **kwargs)

    def test_route_entry_admission_must_match_receipt_admission(self):
        _packet, decision, kwargs = receipt_kwargs()
        kwargs["entry_admission_sha256"] = "9" * 64
        with self.assertRaisesRegex(InferenceReceiptError, "ROUTE_ENTRY_ADMISSION_IDENTITY_MISMATCH"):
            make_inference_receipt(decision, **kwargs)

    def test_entry_binding_must_match_route_event(self):
        packet, decision, kwargs = receipt_kwargs()
        binding = entry_binding(packet)
        binding["event_sha256"] = "9" * 64
        kwargs["admitted_entry_bindings"] = {packet.admission_sha256: binding}
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
        stale_verified = verified_engine_admission(generation=6)
        stale_lease = engine_load_lease(verified=stale_verified, generation=6)
        _packet, decision, kwargs = receipt_kwargs(verified=stale_verified, load_lease=stale_lease)
        with self.assertRaisesRegex(InferenceReceiptError, "STALE_ENGINE_ADMISSION_RECEIPT_GENERATION"):
            make_inference_receipt(decision, **kwargs)

    def test_engine_admission_receipt_bundle_tamper_fails_closed(self):
        _packet, decision, kwargs = receipt_kwargs()
        receipt = copy.deepcopy(next(iter(kwargs["admitted_engine_admission_receipts"].values())))
        receipt["runtime"]["sha256"] = "9" * 64
        kwargs["admitted_engine_admission_receipts"] = {kwargs["engine_admission_receipt_sha256"]: receipt}
        with self.assertRaisesRegex(
            InferenceReceiptError,
            "ENGINE_ADMISSION_RECEIPT_BUNDLE_DIGEST_MISMATCH|ENGINE_ADMISSION_RECEIPT_DIGEST_MISMATCH",
        ):
            make_inference_receipt(decision, **kwargs)

    def test_engine_admission_receipt_canonicalization_downgrade_fails_closed(self):
        _packet, decision, kwargs = receipt_kwargs()
        receipt = copy.deepcopy(next(iter(kwargs["admitted_engine_admission_receipts"].values())))
        receipt["hash_serialization_schema"] = "legacy/python-json"
        kwargs["admitted_engine_admission_receipts"] = {kwargs["engine_admission_receipt_sha256"]: receipt}
        with self.assertRaisesRegex(InferenceReceiptError, "ENGINE_ADMISSION_RECEIPT_CANONICALIZATION_SCHEMA_UNSUPPORTED"):
            make_inference_receipt(decision, **kwargs)

    def test_missing_physical_engine_load_lease_fails_closed(self):
        _packet, decision, kwargs = receipt_kwargs()
        kwargs["admitted_engine_load_leases"] = {}
        with self.assertRaisesRegex(InferenceReceiptError, "ENGINE_LOAD_LEASE_NOT_ADMITTED"):
            make_inference_receipt(decision, **kwargs)

    def test_stale_physical_engine_load_lease_fails_closed(self):
        stale_verified = verified_engine_admission(generation=6)
        stale_lease = engine_load_lease(verified=stale_verified, generation=6)
        _packet, decision, kwargs = receipt_kwargs()
        kwargs["engine_load_lease_sha256"] = stale_lease["lease_sha256"]
        kwargs["admitted_engine_load_leases"] = {stale_lease["lease_sha256"]: stale_lease}
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
        lease["loader_instance_id"] = "tampered-loader"
        old_sha = kwargs["engine_load_lease_sha256"]
        kwargs["admitted_engine_load_leases"] = {old_sha: lease}
        with self.assertRaisesRegex(InferenceReceiptError, "ENGINE_LOAD_LEASE_DIGEST_MISMATCH"):
            make_inference_receipt(decision, **kwargs)

    def test_physical_engine_load_lease_canonicalization_downgrade_fails_closed(self):
        _packet, decision, kwargs = receipt_kwargs()
        lease = copy.deepcopy(next(iter(kwargs["admitted_engine_load_leases"].values())))
        lease["canonicalization_schema"] = "legacy/python-json"
        old_sha = kwargs["engine_load_lease_sha256"]
        kwargs["admitted_engine_load_leases"] = {old_sha: lease}
        with self.assertRaisesRegex(InferenceReceiptError, "ENGINE_LOAD_LEASE_CANONICALIZATION_SCHEMA_UNSUPPORTED"):
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
        entry_bindings = {packet.admission_sha256: entry_binding(packet)}
        decision = route_event(event, current_generation=7, admitted_entry_bindings=entry_bindings)
        verified = verified_engine_admission()
        engine_receipt = verified.receipt()
        load_lease = engine_load_lease(verified=verified)
        with self.assertRaisesRegex(InferenceReceiptError, "MODEL_ACTIVATION_ROUTE_REQUIRED"):
            make_inference_receipt(
                decision,
                current_generation=7,
                admitted_route_generations={decision.decision_sha256: 7},
                entry_admission_sha256=packet.admission_sha256,
                admitted_entry_bindings=entry_bindings,
                admitted_engine_artifacts={"hcu_local_08b": ENGINE_SHA256},
                engine_admission_receipt_sha256=engine_receipt["receipt_sha256"],
                admitted_engine_admission_receipts={engine_receipt["receipt_sha256"]: engine_receipt},
                engine_load_lease_sha256=load_lease["lease_sha256"],
                admitted_engine_load_leases={load_lease["lease_sha256"]: load_lease},
                model_call_id="model-call:should-not-exist",
                output_ref="unifieddb:candidate-output:should-not-exist",
                output_sha256=OUTPUT_SHA256,
                output_size=1,
            )


if __name__ == "__main__":
    unittest.main()
