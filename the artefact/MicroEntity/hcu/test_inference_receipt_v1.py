import hashlib
import unittest
from dataclasses import replace

from engine_admission_v1 import (
    ENGINE_ADMISSION_RECEIPT_SCHEMA,
    LOCK_SCHEMA,
    ArtifactDigest,
    EngineArtifactLock,
    VerifiedEngineAdmission,
    derive_engine_artifact_sha256,
)
from engine_load_lease_v1 import (
    ACTUAL_LOADER_EVIDENCE_SOURCE,
    CONSUMPTION_SCHEMA,
    VERIFIED_LOAD_SCHEMA,
    LoaderConsumedArtifact,
    LoaderConsumption,
    issue_engine_load_lease,
    loader_consumption_record,
    loader_consumption_record_sha256,
    verify_loader_consumption,
)
from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from inference_receipt_v1 import InferenceReceiptError, make_inference_receipt
from reactive_event_router_v1 import (
    ENTRY_BINDING_SCHEMA,
    HASH_SERIALIZATION_SCHEMA,
    EngineAdmission,
    route_event,
)
from xeno_entry_fabric_v1 import admit_entry, to_hcu_reactive_event


def digest(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


CAPABILITY_BINDING_SHA256 = digest("capability-binding")
CHECKPOINT_SHA256 = digest("checkpoint")
TOKENIZER_SHA256 = digest("tokenizer")
RUNTIME_SHA256 = digest("runtime")
BUILD_SHA256 = digest("build")
LOADER_BINDING_SHA256 = digest("loader-binding")
OUTPUT_SHA256 = digest("output")
ADMITTED_BUDGET = {
    "max_model_calls": 1,
    "max_tokens": 1024,
    "max_wall_ms": 2500,
}


def canonical_sha256(value) -> str:
    return hashlib.sha256(canonicalize(value)).hexdigest()


def engine_artifact_sha256() -> str:
    lock = EngineArtifactLock(
        schema=LOCK_SCHEMA,
        provider_alias="hcu",
        engine_identity="hcu_local_08b",
        engine_class="LOCAL_SHARED_WEIGHT_08B",
        checkpoint_sha256=CHECKPOINT_SHA256,
        tokenizer_sha256=TOKENIZER_SHA256,
        runtime_sha256=RUNTIME_SHA256,
        build_sha256=BUILD_SHA256,
        engine_artifact_sha256=digest("provisional-bundle"),
    )
    return derive_engine_artifact_sha256(lock)


ENGINE_SHA256 = engine_artifact_sha256()


def verified_engine_admission(*, generation: int = 7) -> VerifiedEngineAdmission:
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
        "hash_serialization_schema": CANONICALIZATION_SCHEMA,
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
        receipt_sha256=canonical_sha256(material),
    )


def loader_artifact(artifact: ArtifactDigest, *, evidence_source: str = ACTUAL_LOADER_EVIDENCE_SOURCE):
    return LoaderConsumedArtifact(
        kind=artifact.kind,
        sha256=artifact.sha256,
        file_count=artifact.file_count,
        byte_count=artifact.byte_count,
        evidence_source=evidence_source,
    )


def verified_engine_load(verified: VerifiedEngineAdmission, *, generation: int = 7):
    lease = issue_engine_load_lease(
        verified,
        loader_id="entityos:hcu:loader:1",
        loader_binding_sha256=LOADER_BINDING_SHA256,
        current_generation=generation,
    )
    consumption = LoaderConsumption(
        schema=CONSUMPTION_SCHEMA,
        entity_generation=generation,
        loader_id=lease.loader_id,
        loader_binding_sha256=lease.loader_binding_sha256,
        engine_identity=lease.engine_identity,
        engine_artifact_sha256=lease.engine_artifact_sha256,
        checkpoint=loader_artifact(verified.checkpoint),
        tokenizer=loader_artifact(verified.tokenizer),
        runtime=loader_artifact(verified.runtime),
        build=loader_artifact(verified.build),
    )
    admitted_loader_consumptions = {
        loader_consumption_record_sha256(consumption): loader_consumption_record(consumption)
    }
    return verify_loader_consumption(
        lease,
        verified,
        consumption,
        admitted_loader_consumptions=admitted_loader_consumptions,
        current_generation=generation,
    )


def verified_load_receipt(load) -> dict:
    def artifact(value):
        return {
            "kind": value.kind,
            "sha256": value.sha256,
            "file_count": value.file_count,
            "byte_count": value.byte_count,
            "evidence_source": value.evidence_source,
        }

    return {
        "schema": VERIFIED_LOAD_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "entity_generation": load.entity_generation,
        "loader_id": load.loader_id,
        "loader_binding_sha256": load.loader_binding_sha256,
        "engine_admission_receipt_sha256": load.engine_admission_receipt_sha256,
        "engine_load_lease_sha256": load.engine_load_lease_sha256,
        "engine_identity": load.engine_identity,
        "engine_class": load.engine_class,
        "engine_artifact_sha256": load.engine_artifact_sha256,
        "checkpoint": artifact(load.checkpoint),
        "tokenizer": artifact(load.tokenizer),
        "runtime": artifact(load.runtime),
        "build": artifact(load.build),
        "consumption_receipt_sha256": load.consumption_receipt_sha256,
    }


def base_entry():
    return {
        "schema": "XENO_ENTRY_PACKET/v1",
        "ingress_id": "ingress:receipt:v3:1",
        "causal_id": "causal:receipt:v3:1",
        "entity_generation": 7,
        "source_kind": "HUMAN_PROMPT",
        "source_id": "user:test",
        "modality": "TEXT",
        "observed_time": "2026-08-23T23:24:00+07:00",
        "received_time": "2026-08-23T23:24:01+07:00",
        "provenance_ref": "unifieddb:source:receipt:v3:1",
        "provenance_sha256": digest("provenance"),
        "capabilities": ["memory.read", "hcu.route"],
        "capability_binding_sha256": CAPABILITY_BINDING_SHA256,
        "parent_id": None,
        "stream_id": "stream:receipt:v3",
        "budget": dict(ADMITTED_BUDGET),
        "payload_ref": "unifieddb:payload:receipt:v3:1",
        "payload_sha256": digest("payload"),
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


def fixture():
    packet = admitted_packet()
    event = to_hcu_reactive_event(packet, novelty=0.8, zero_relevance=0.8)
    event["requested_internal_provider"] = "hcu"
    entry_bindings = {packet.admission_sha256: entry_binding(packet)}
    verified = verified_engine_admission()
    engine_artifacts = {"hcu_local_08b": ENGINE_SHA256}
    decision = route_event(
        event,
        current_generation=7,
        engine_admission=verified.admission,
        admitted_engine_artifacts=engine_artifacts,
        admitted_entry_bindings=entry_bindings,
    )
    load = verified_engine_load(verified)
    load_receipt = verified_load_receipt(load)
    kwargs = {
        "current_generation": 7,
        "admitted_route_generations": {decision.decision_sha256: 7},
        "entry_admission_sha256": packet.admission_sha256,
        "admitted_entry_bindings": entry_bindings,
        "admitted_engine_artifacts": engine_artifacts,
        "verified_engine_admission": verified,
        "admitted_engine_admission_receipts": {verified.receipt_sha256: verified.receipt()},
        "verified_engine_load": load,
        "admitted_verified_engine_loads": {load.consumption_receipt_sha256: load_receipt},
        "model_call_id": "model-call:receipt:v3:1",
        "output_ref": "unifieddb:candidate-output:receipt:v3:1",
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
        self.assertEqual(VERIFIED_LOAD_SCHEMA, "HCU_VERIFIED_ENGINE_LOAD/v1")

    def test_bound_candidate_receipt_is_deterministic_and_jcs_v3(self):
        packet, decision, kwargs = fixture()
        a = make_inference_receipt(decision, **kwargs)
        b = make_inference_receipt(decision, **kwargs)
        self.assertEqual(a, b)
        self.assertEqual(a.schema, "HCU_INFERENCE_RECEIPT/v3")
        self.assertEqual(a.status, "CANDIDATE_ONLY")
        self.assertEqual(a.hash_serialization_schema, CANONICALIZATION_SCHEMA)
        self.assertEqual(a.entry_binding_schema, ENTRY_BINDING_SCHEMA)
        self.assertEqual(a.entry_admission_sha256, packet.admission_sha256)
        self.assertEqual(a.engine_load_consumption_receipt_sha256, kwargs["verified_engine_load"].consumption_receipt_sha256)
        self.assertEqual(a.engine_load_loader_binding_sha256, LOADER_BINDING_SHA256)

    def test_legacy_bare_entry_binding_fails_closed(self):
        packet, decision, kwargs = fixture()
        kwargs["admitted_entry_bindings"] = {packet.admission_sha256: packet.event_sha256}
        with self.assertRaisesRegex(InferenceReceiptError, "ENTRY_ADMISSION_BINDING_V2_REQUIRED"):
            make_inference_receipt(decision, **kwargs)

    def test_stale_route_generation_fails_closed(self):
        _packet, decision, kwargs = fixture()
        kwargs["current_generation"] = 8
        with self.assertRaisesRegex(InferenceReceiptError, "STALE_ROUTE_GENERATION"):
            make_inference_receipt(decision, **kwargs)

    def test_engine_artifact_revocation_fails_closed(self):
        _packet, decision, kwargs = fixture()
        kwargs["admitted_engine_artifacts"] = {"hcu_local_08b": digest("revoked-engine")}
        with self.assertRaisesRegex(InferenceReceiptError, "ENGINE_ARTIFACT_ADMISSION_MISMATCH"):
            make_inference_receipt(decision, **kwargs)

    def test_engine_admission_receipt_must_be_admitted(self):
        _packet, decision, kwargs = fixture()
        kwargs["admitted_engine_admission_receipts"] = {}
        with self.assertRaisesRegex(InferenceReceiptError, "ENGINE_ADMISSION_RECEIPT_NOT_ADMITTED"):
            make_inference_receipt(decision, **kwargs)

    def test_verified_load_must_be_admitted(self):
        _packet, decision, kwargs = fixture()
        kwargs["admitted_verified_engine_loads"] = {}
        with self.assertRaisesRegex(InferenceReceiptError, "VERIFIED_ENGINE_LOAD_NOT_ADMITTED"):
            make_inference_receipt(decision, **kwargs)

    def test_stale_verified_load_generation_fails_closed(self):
        _packet, decision, kwargs = fixture()
        kwargs["verified_engine_load"] = replace(kwargs["verified_engine_load"], entity_generation=6)
        with self.assertRaisesRegex(InferenceReceiptError, "STALE_VERIFIED_ENGINE_LOAD_GENERATION"):
            make_inference_receipt(decision, **kwargs)

    def test_post_hoc_loader_evidence_cannot_mint_inference_receipt(self):
        _packet, decision, kwargs = fixture()
        load = kwargs["verified_engine_load"]
        bad_checkpoint = replace(load.checkpoint, evidence_source="POST_HOC_FILESYSTEM_REHASH")
        kwargs["verified_engine_load"] = replace(load, checkpoint=bad_checkpoint)
        with self.assertRaisesRegex(InferenceReceiptError, "ACTUAL_LOADER_READ_EVIDENCE_REQUIRED"):
            make_inference_receipt(decision, **kwargs)

    def test_tampered_verified_load_digest_fails_closed(self):
        _packet, decision, kwargs = fixture()
        load = kwargs["verified_engine_load"]
        kwargs["verified_engine_load"] = replace(load, loader_id="tampered-loader")
        with self.assertRaisesRegex(InferenceReceiptError, "VERIFIED_ENGINE_LOAD_DIGEST_MISMATCH"):
            make_inference_receipt(decision, **kwargs)

    def test_output_digest_is_typed(self):
        _packet, decision, kwargs = fixture()
        kwargs["output_sha256"] = "not-a-digest"
        with self.assertRaisesRegex(InferenceReceiptError, "output_sha256"):
            make_inference_receipt(decision, **kwargs)


if __name__ == "__main__":
    unittest.main()
