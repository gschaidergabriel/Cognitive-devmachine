#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import replace
import unittest

from engine_admission_v1 import ArtifactDigest, VerifiedEngineAdmission
from physical_engine_lease_v1 import (
    PhysicalEngineLeaseError,
    assert_physical_engine_lease_current,
    inference_lease_echo,
    issue_physical_engine_lease,
)
from reactive_event_router_v1 import EngineAdmission


def digest(ch: str) -> str:
    return ch * 64


def artifact(ch: str, size: int) -> ArtifactDigest:
    return ArtifactDigest(kind="FILE_SHA256", sha256=digest(ch), file_count=1, byte_count=size)


class PhysicalEngineLeaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.verified = VerifiedEngineAdmission(
            entity_generation=7,
            admission=EngineAdmission(
                provider_alias="hcu",
                engine_identity="hcu_local_08b",
                engine_class="LOCAL_SHARED_WEIGHT_08B",
                engine_artifact_sha256=digest("9"),
            ),
            checkpoint=artifact("1", 100),
            tokenizer=artifact("2", 20),
            runtime=artifact("3", 30),
            build=artifact("4", 40),
            engine_artifact_sha256=digest("9"),
            receipt_sha256=digest("8"),
        )
        self.kwargs = dict(
            current_generation=7,
            loader_generation=7,
            loader_consumed_checkpoint_sha256=digest("1"),
            loader_consumed_tokenizer_sha256=digest("2"),
            loader_consumed_runtime_sha256=digest("3"),
            loader_consumed_build_sha256=digest("4"),
            loader_instance_id="loader-7-a",
            loader_runtime_sha256=digest("5"),
            lease_id="lease-7-a",
            artifact_boundary_receipt_sha256=digest("6"),
        )

    def issue(self, **overrides):
        values = dict(self.kwargs)
        values.update(overrides)
        return issue_physical_engine_lease(self.verified, **values)

    def test_bundle_identity_is_distinct_from_checkpoint_identity(self) -> None:
        lease = self.issue()
        self.assertEqual(lease.engine_artifact_sha256, digest("9"))
        self.assertEqual(lease.consumed_checkpoint_sha256, digest("1"))
        self.assertNotEqual(lease.engine_artifact_sha256, lease.consumed_checkpoint_sha256)

    def test_exact_component_consumption_is_bound_deterministically(self) -> None:
        first = self.issue()
        second = self.issue()
        self.assertEqual(first, second)
        self.assertEqual(first.canonicalization_schema, "RFC8785_JCS_IJSON/v1")
        self.assertEqual(len(first.lease_sha256), 64)

    def test_each_consumed_component_must_match_verified_admission(self) -> None:
        for field, error in (
            ("loader_consumed_checkpoint_sha256", "LOADER_CONSUMED_CHECKPOINT_MISMATCH"),
            ("loader_consumed_tokenizer_sha256", "LOADER_CONSUMED_TOKENIZER_MISMATCH"),
            ("loader_consumed_runtime_sha256", "LOADER_CONSUMED_RUNTIME_MISMATCH"),
            ("loader_consumed_build_sha256", "LOADER_CONSUMED_BUILD_MISMATCH"),
        ):
            with self.subTest(field=field):
                with self.assertRaisesRegex(PhysicalEngineLeaseError, error):
                    self.issue(**{field: digest("7")})

    def test_loader_generation_is_fenced_at_issue(self) -> None:
        with self.assertRaisesRegex(PhysicalEngineLeaseError, "STALE_LOADER_GENERATION"):
            self.issue(loader_generation=6)

    def test_verified_admission_generation_is_fenced(self) -> None:
        stale = replace(self.verified, entity_generation=6)
        with self.assertRaisesRegex(PhysicalEngineLeaseError, "STALE_VERIFIED_ENGINE_ADMISSION"):
            issue_physical_engine_lease(stale, **self.kwargs)

    def test_lease_is_rechecked_against_current_verified_admission(self) -> None:
        lease = self.issue()
        changed = replace(self.verified, receipt_sha256=digest("7"))
        with self.assertRaisesRegex(
            PhysicalEngineLeaseError,
            "PHYSICAL_ENGINE_LEASE_ENGINE_ADMISSION_RECEIPT_SHA256_REVOKED",
        ):
            assert_physical_engine_lease_current(
                lease,
                current_generation=7,
                verified_engine_admission=changed,
            )

    def test_lease_digest_tampering_fails_closed(self) -> None:
        lease = replace(self.issue(), loader_instance_id="tampered-loader")
        with self.assertRaisesRegex(PhysicalEngineLeaseError, "PHYSICAL_ENGINE_LEASE_DIGEST_MISMATCH"):
            assert_physical_engine_lease_current(
                lease,
                current_generation=7,
                verified_engine_admission=self.verified,
            )

    def test_boundary_receipt_placeholder_is_rejected(self) -> None:
        with self.assertRaisesRegex(PhysicalEngineLeaseError, "artifact_boundary_receipt_sha256"):
            self.issue(artifact_boundary_receipt_sha256="0" * 64)

    def test_inference_echo_carries_bundle_admission_and_consumed_component_identities(self) -> None:
        lease = self.issue()
        assert_physical_engine_lease_current(
            lease,
            current_generation=7,
            verified_engine_admission=self.verified,
        )
        echo = inference_lease_echo(lease)
        self.assertEqual(echo["engine_load_lease_sha256"], lease.lease_sha256)
        self.assertEqual(echo["engine_admission_receipt_sha256"], digest("8"))
        self.assertEqual(echo["consumed_checkpoint_sha256"], digest("1"))
        self.assertEqual(echo["consumed_tokenizer_sha256"], digest("2"))
        self.assertEqual(echo["consumed_runtime_sha256"], digest("3"))
        self.assertEqual(echo["consumed_build_sha256"], digest("4"))


if __name__ == "__main__":
    unittest.main()
