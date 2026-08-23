import hashlib
from dataclasses import replace
import unittest

from engine_load_lease_v1 import (
    VERIFIED_LOAD_SCHEMA,
    LoaderConsumedArtifact,
    VerifiedEngineLoad,
)
from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from inference_receipt_v2 import (
    SCHEMA,
    InferenceReceiptV2Error,
    make_inference_receipt_v2,
)
from reactive_event_router_v1 import (
    ENTRY_BINDING_SCHEMA,
    HASH_SERIALIZATION_SCHEMA,
    EngineAdmission,
    route_event,
)


GENERATION = 7
ENTRY_EVENT_SHA256 = "e" * 64
ENTRY_ADMISSION_SHA256 = "1" * 64
ENGINE_ARTIFACT_SHA256 = "a" * 64
ENGINE_ADMISSION_RECEIPT_SHA256 = "b" * 64
ENGINE_LOAD_LEASE_SHA256 = "2" * 64
LOADER_BINDING_SHA256 = "3" * 64
OUTPUT_SHA256 = "9" * 64


def _entry_binding(*, schema=ENTRY_BINDING_SCHEMA, canonicalization_schema=HASH_SERIALIZATION_SCHEMA, event_sha256=ENTRY_EVENT_SHA256):
    return {
        "schema": schema,
        "canonicalization_schema": canonicalization_schema,
        "event_sha256": event_sha256,
    }


def _entry_bindings():
    return {ENTRY_ADMISSION_SHA256: _entry_binding()}


def _route():
    event = {
        "schema": "HCU_REACTIVE_EVENT/v1",
        "entity_generation": GENERATION,
        "ingress_id": "ingress:test:v2",
        "causal_id": "causal:test:v2",
        "entry_canonicalization_schema": HASH_SERIALIZATION_SCHEMA,
        "entry_event_sha256": ENTRY_EVENT_SHA256,
        "entry_admission_sha256": ENTRY_ADMISSION_SHA256,
        "novelty": 0.8,
        "contradiction": 0.0,
        "uncertainty": 0.0,
        "forecast_need": 0.0,
        "effect_pressure": 0.0,
        "zero_relevance": 0.0,
        "due_recheck": False,
    }
    return route_event(
        event,
        current_generation=GENERATION,
        engine_admission=EngineAdmission(
            provider_alias="hcu",
            engine_identity="hcu_local_08b",
            engine_class="LOCAL_SHARED_WEIGHT_08B",
            engine_artifact_sha256=ENGINE_ARTIFACT_SHA256,
        ),
        admitted_engine_artifacts={"hcu_local_08b": ENGINE_ARTIFACT_SHA256},
        admitted_entry_bindings=_entry_bindings(),
    )


def _artifact(kind, digest, count, size):
    return LoaderConsumedArtifact(kind=kind, sha256=digest, file_count=count, byte_count=size)


def _load():
    checkpoint = _artifact("FILE_SHA256", "c" * 64, 1, 11)
    tokenizer = _artifact("TREE_SHA256_V1", "d" * 64, 2, 22)
    runtime = _artifact("FILE_SHA256", "4" * 64, 1, 33)
    build = _artifact("FILE_SHA256", "5" * 64, 1, 44)
    material = {
        "schema": VERIFIED_LOAD_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "entity_generation": GENERATION,
        "loader_id": "loader:test:v2",
        "loader_binding_sha256": LOADER_BINDING_SHA256,
        "engine_admission_receipt_sha256": ENGINE_ADMISSION_RECEIPT_SHA256,
        "engine_load_lease_sha256": ENGINE_LOAD_LEASE_SHA256,
        "engine_identity": "hcu_local_08b",
        "engine_class": "LOCAL_SHARED_WEIGHT_08B",
        "engine_artifact_sha256": ENGINE_ARTIFACT_SHA256,
        "checkpoint": {**checkpoint.__dict__},
        "tokenizer": {**tokenizer.__dict__},
        "runtime": {**runtime.__dict__},
        "build": {**build.__dict__},
    }
    receipt_sha256 = hashlib.sha256(canonicalize(material)).hexdigest()
    return VerifiedEngineLoad(
        schema=VERIFIED_LOAD_SCHEMA,
        canonicalization_schema=CANONICALIZATION_SCHEMA,
        entity_generation=GENERATION,
        loader_id="loader:test:v2",
        loader_binding_sha256=LOADER_BINDING_SHA256,
        engine_admission_receipt_sha256=ENGINE_ADMISSION_RECEIPT_SHA256,
        engine_load_lease_sha256=ENGINE_LOAD_LEASE_SHA256,
        engine_identity="hcu_local_08b",
        engine_class="LOCAL_SHARED_WEIGHT_08B",
        engine_artifact_sha256=ENGINE_ARTIFACT_SHA256,
        checkpoint=checkpoint,
        tokenizer=tokenizer,
        runtime=runtime,
        build=build,
        consumption_receipt_sha256=receipt_sha256,
    )


def _make(decision=None, load=None, *, admitted_load=True, entry_bindings=None):
    decision = decision or _route()
    load = load or _load()
    load_registry = {load.consumption_receipt_sha256: load} if admitted_load else {}
    return make_inference_receipt_v2(
        decision,
        current_generation=GENERATION,
        admitted_route_generations={decision.decision_sha256: GENERATION},
        entry_admission_sha256=ENTRY_ADMISSION_SHA256,
        admitted_entry_bindings=_entry_bindings() if entry_bindings is None else entry_bindings,
        admitted_engine_artifacts={"hcu_local_08b": ENGINE_ARTIFACT_SHA256},
        verified_engine_load_receipt_sha256=load.consumption_receipt_sha256,
        admitted_verified_engine_loads=load_registry,
        admitted_engine_admission_receipts={ENGINE_ADMISSION_RECEIPT_SHA256: {"status": "admitted"}},
        model_call_id="model-call:v2:1",
        output_ref="memory://output/v2/1",
        output_sha256=OUTPUT_SHA256,
        output_size=123,
    )


class InferenceReceiptV2Tests(unittest.TestCase):
    def test_verified_load_chain_emits_jcs_v2_receipt(self):
        receipt = _make()
        self.assertEqual(receipt.schema, SCHEMA)
        self.assertEqual(receipt.canonicalization_schema, CANONICALIZATION_SCHEMA)
        self.assertEqual(receipt.hash_serialization_schema, CANONICALIZATION_SCHEMA)
        self.assertEqual(receipt.engine_load_consumption_receipt_sha256, _load().consumption_receipt_sha256)
        self.assertEqual(len(receipt.receipt_sha256), 64)

    def test_same_inputs_are_deterministic(self):
        self.assertEqual(_make(), _make())

    def test_downgraded_route_canonicalizer_fails_closed(self):
        decision = replace(_route(), hash_serialization_schema="HCU_PYTHON_JSON_DUMPS_SORT_KEYS_UTF8/v1")
        with self.assertRaisesRegex(InferenceReceiptV2Error, "ROUTE_CANONICALIZATION_SCHEMA_UNSUPPORTED"):
            _make(decision=decision)

    def test_legacy_bare_entry_binding_fails_closed(self):
        with self.assertRaisesRegex(InferenceReceiptV2Error, "ENTRY_BINDING_REJECTED:ENTRY_ADMISSION_BINDING_V2_REQUIRED"):
            _make(entry_bindings={ENTRY_ADMISSION_SHA256: ENTRY_EVENT_SHA256})

    def test_wrong_entry_binding_canonicalizer_fails_closed(self):
        bindings = {
            ENTRY_ADMISSION_SHA256: _entry_binding(
                canonicalization_schema="ENTITYOS_HCU_ENTRY_CBOR_RFC8949_SUBSET/v1"
            )
        }
        with self.assertRaisesRegex(InferenceReceiptV2Error, "ENTRY_BINDING_REJECTED:ENTRY_BINDING_CANONICALIZATION_SCHEMA_UNSUPPORTED"):
            _make(entry_bindings=bindings)

    def test_unadmitted_verified_load_fails_closed(self):
        with self.assertRaisesRegex(InferenceReceiptV2Error, "VERIFIED_ENGINE_LOAD_NOT_ADMITTED"):
            _make(admitted_load=False)

    def test_tampered_consumed_bytes_fail_receipt_rebind(self):
        load = _load()
        poisoned_checkpoint = replace(load.checkpoint, sha256="6" * 64)
        poisoned = replace(load, checkpoint=poisoned_checkpoint)
        with self.assertRaisesRegex(InferenceReceiptV2Error, "VERIFIED_ENGINE_LOAD_RECEIPT_DIGEST_MISMATCH"):
            _make(load=poisoned)


if __name__ == "__main__":
    unittest.main()