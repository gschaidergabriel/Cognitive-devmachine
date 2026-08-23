import hashlib
import unittest

from engine_admission_v1 import ArtifactDigest, VerifiedEngineAdmission
from engine_load_lease_v1 import (
    ACTUAL_LOADER_EVIDENCE_SOURCE,
    CONSUMPTION_SCHEMA,
    EngineLoadLeaseError,
    LoaderConsumedArtifact,
    LoaderConsumption,
    issue_engine_load_lease,
    loader_consumption_record,
    loader_consumption_record_sha256,
    verify_loader_consumption,
)
from reactive_event_router_v1 import EngineAdmission

LOADER_BINDING = "9" * 64


def digest(ch, size=10):
    return ArtifactDigest("FILE_SHA256", ch * 64, 1, size)


def verified(generation=7, suffix=""):
    engine_artifact = hashlib.sha256(("engine" + suffix).encode()).hexdigest()
    receipt = hashlib.sha256(("receipt" + suffix).encode()).hexdigest()
    return VerifiedEngineAdmission(
        generation,
        EngineAdmission("local", "hcu_local_08b", "LOCAL_SHARED_WEIGHT_08B", engine_artifact),
        digest("a", 100),
        digest("b", 20),
        digest("c", 30),
        digest("d", 40),
        engine_artifact,
        receipt,
    )


def consumed(v, *, loader="loader:test", binding=LOADER_BINDING, source=ACTUAL_LOADER_EVIDENCE_SOURCE):
    def c(a):
        return LoaderConsumedArtifact(a.kind, a.sha256, a.file_count, a.byte_count, source)

    return LoaderConsumption(
        CONSUMPTION_SCHEMA,
        v.entity_generation,
        loader,
        binding,
        v.admission.engine_identity,
        v.engine_artifact_sha256,
        c(v.checkpoint),
        c(v.tokenizer),
        c(v.runtime),
        c(v.build),
    )


def admitted(c):
    return {loader_consumption_record_sha256(c): loader_consumption_record(c)}


class EngineLoadLeaseTests(unittest.TestCase):
    def issue(self, v):
        return issue_engine_load_lease(
            v,
            loader_id="loader:test",
            loader_binding_sha256=LOADER_BINDING,
            current_generation=7,
        )

    def verify(self, lease, v, c, *, registry=None, generation=7):
        return verify_loader_consumption(
            lease,
            v,
            c,
            admitted_loader_consumptions=admitted(c) if registry is None else registry,
            current_generation=generation,
        )

    def test_issue_is_deterministic_and_selected_jcs_bound(self):
        v = verified()
        a = self.issue(v)
        b = self.issue(v)
        self.assertEqual(a, b)
        self.assertEqual(a.canonicalization_schema, "RFC8785_JCS_IJSON/v1")
        self.assertEqual(len(a.lease_sha256), 64)

    def test_issue_rejects_stale_generation(self):
        with self.assertRaisesRegex(EngineLoadLeaseError, "STALE_ENTITY_GENERATION"):
            issue_engine_load_lease(
                verified(),
                loader_id="loader:test",
                loader_binding_sha256=LOADER_BINDING,
                current_generation=8,
            )

    def test_exact_actual_loader_consumption_verifies_only_after_external_admission(self):
        v = verified()
        lease = self.issue(v)
        c = consumed(v)
        out = self.verify(lease, v, c)
        self.assertEqual(out.engine_load_lease_sha256, lease.lease_sha256)
        self.assertEqual(out.loader_binding_sha256, LOADER_BINDING)
        self.assertEqual(
            out.inference_echo()["engine_load_consumption_receipt_sha256"],
            out.consumption_receipt_sha256,
        )

    def test_counterfeit_actual_loader_label_without_external_admission_fails_closed(self):
        """Unusual falsifier: exact bytes + ACTUAL_LOADER_READ_PATH cannot self-admit."""
        v = verified()
        lease = self.issue(v)
        forged = consumed(v)
        with self.assertRaisesRegex(EngineLoadLeaseError, "LOADER_CONSUMPTION_NOT_ADMITTED"):
            self.verify(lease, v, forged, registry={})

    def test_external_registry_substitution_fails_closed(self):
        v = verified()
        lease = self.issue(v)
        c = consumed(v)
        registry = admitted(c)
        identity = loader_consumption_record_sha256(c)
        poisoned = dict(registry[identity])
        poisoned["loader_id"] = "loader:other"
        registry[identity] = poisoned
        with self.assertRaisesRegex(EngineLoadLeaseError, "LOADER_CONSUMPTION_REGISTRY_MISMATCH"):
            self.verify(lease, v, c, registry=registry)

    def test_post_admission_checkpoint_mutation_fails_closed(self):
        v = verified()
        lease = self.issue(v)
        c = consumed(v)
        poisoned = LoaderConsumption(
            c.schema,
            c.entity_generation,
            c.loader_id,
            c.loader_binding_sha256,
            c.engine_identity,
            c.engine_artifact_sha256,
            LoaderConsumedArtifact(
                c.checkpoint.kind,
                "e" * 64,
                c.checkpoint.file_count,
                c.checkpoint.byte_count,
            ),
            c.tokenizer,
            c.runtime,
            c.build,
        )
        with self.assertRaisesRegex(EngineLoadLeaseError, "checkpoint:CONSUMED_BYTES_MISMATCH"):
            self.verify(lease, v, poisoned)

    def test_posthoc_or_synthetic_digest_is_not_loader_attestation(self):
        v = verified()
        lease = self.issue(v)
        c = consumed(v, source="POSTHOC_FILESYSTEM_REHASH")
        with self.assertRaisesRegex(EngineLoadLeaseError, "ACTUAL_LOADER_READ_EVIDENCE_REQUIRED"):
            self.verify(lease, v, c)

    def test_wrong_loader_binding_and_stale_consumption_fail_closed(self):
        v = verified()
        lease = self.issue(v)
        other_loader = consumed(v, loader="loader:other")
        with self.assertRaisesRegex(EngineLoadLeaseError, "LOADER_ID_MISMATCH"):
            self.verify(lease, v, other_loader)
        other_binding = consumed(v, binding="8" * 64)
        with self.assertRaisesRegex(EngineLoadLeaseError, "LOADER_BINDING_MISMATCH"):
            self.verify(lease, v, other_binding)
        c = consumed(v)
        stale = LoaderConsumption(
            c.schema,
            6,
            c.loader_id,
            c.loader_binding_sha256,
            c.engine_identity,
            c.engine_artifact_sha256,
            c.checkpoint,
            c.tokenizer,
            c.runtime,
            c.build,
        )
        with self.assertRaisesRegex(EngineLoadLeaseError, "STALE_LOADER_CONSUMPTION"):
            self.verify(lease, v, stale)

    def test_lease_cannot_be_reused_for_different_admission(self):
        a = verified(suffix="a")
        b = verified(suffix="b")
        lease = self.issue(a)
        c = consumed(b)
        with self.assertRaisesRegex(EngineLoadLeaseError, "ENGINE_ADMISSION_RECEIPT_MISMATCH"):
            self.verify(lease, b, c)

    def test_consumed_size_or_membership_mismatch_fails_closed(self):
        v = verified()
        lease = self.issue(v)
        c = consumed(v)
        poisoned = LoaderConsumption(
            c.schema,
            c.entity_generation,
            c.loader_id,
            c.loader_binding_sha256,
            c.engine_identity,
            c.engine_artifact_sha256,
            c.checkpoint,
            LoaderConsumedArtifact(
                c.tokenizer.kind,
                c.tokenizer.sha256,
                c.tokenizer.file_count,
                c.tokenizer.byte_count + 1,
            ),
            c.runtime,
            c.build,
        )
        with self.assertRaisesRegex(EngineLoadLeaseError, "tokenizer:CONSUMED_BYTES_MISMATCH"):
            self.verify(lease, v, poisoned)


if __name__ == "__main__":
    unittest.main()
