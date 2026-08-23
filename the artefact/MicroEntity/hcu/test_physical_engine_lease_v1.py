#!/usr/bin/env python3
from __future__ import annotations

import unittest

from physical_engine_lease_v1 import (
    PhysicalEngineLeaseError,
    assert_physical_engine_lease_current,
    inference_lease_echo,
    issue_physical_engine_lease,
)
from reactive_event_router_v1 import EngineAdmission


def digest(ch: str) -> str:
    return ch * 64


class PhysicalEngineLeaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.admission = EngineAdmission(
            provider_alias="hcu",
            engine_identity="hcu_local_08b",
            engine_class="LOCAL_SHARED_WEIGHT_08B",
            engine_artifact_sha256=digest("1"),
        )
        self.engine_registry = {"hcu_local_08b": digest("1")}
        self.aux_registry = {
            "hcu_local_08b": {
                "tokenizer_sha256": digest("2"),
                "runtime_build_sha256": digest("3"),
            }
        }
        self.kwargs = dict(
            current_generation=7,
            loader_generation=7,
            admitted_engine_artifacts=self.engine_registry,
            admitted_aux_artifacts=self.aux_registry,
            loader_consumed_checkpoint_sha256=digest("1"),
            loader_consumed_tokenizer_sha256=digest("2"),
            loader_consumed_runtime_build_sha256=digest("3"),
            loader_instance_id="loader-7-a",
            lease_id="lease-7-a",
            artifact_boundary_receipt_sha256=digest("4"),
        )

    def issue(self, **overrides):
        values = dict(self.kwargs)
        values.update(overrides)
        return issue_physical_engine_lease(self.admission, **values)

    def test_exact_loader_consumption_is_bound_deterministically(self) -> None:
        first = self.issue()
        second = self.issue()
        self.assertEqual(first, second)
        self.assertEqual(first.canonicalization_schema, "RFC8785_JCS_IJSON/v1")
        self.assertEqual(first.admitted_checkpoint_sha256, digest("1"))
        self.assertEqual(first.loader_consumed_checkpoint_sha256, digest("1"))
        self.assertEqual(len(first.lease_sha256), 64)

    def test_preload_checkpoint_hash_cannot_cover_different_consumed_bytes(self) -> None:
        with self.assertRaisesRegex(PhysicalEngineLeaseError, "LOADER_CONSUMED_CHECKPOINT_MISMATCH"):
            self.issue(loader_consumed_checkpoint_sha256=digest("5"))

    def test_consumed_tokenizer_must_match_independent_registry(self) -> None:
        with self.assertRaisesRegex(PhysicalEngineLeaseError, "LOADER_CONSUMED_TOKENIZER_MISMATCH"):
            self.issue(loader_consumed_tokenizer_sha256=digest("5"))

    def test_consumed_runtime_build_must_match_independent_registry(self) -> None:
        with self.assertRaisesRegex(PhysicalEngineLeaseError, "LOADER_CONSUMED_RUNTIME_BUILD_MISMATCH"):
            self.issue(loader_consumed_runtime_build_sha256=digest("5"))

    def test_loader_generation_is_fenced_at_issue(self) -> None:
        with self.assertRaisesRegex(PhysicalEngineLeaseError, "STALE_LOADER_GENERATION"):
            self.issue(loader_generation=6)

    def test_lease_generation_is_rechecked_before_inference(self) -> None:
        lease = self.issue()
        with self.assertRaisesRegex(PhysicalEngineLeaseError, "STALE_PHYSICAL_ENGINE_LEASE"):
            assert_physical_engine_lease_current(
                lease,
                current_generation=8,
                admitted_engine_artifacts=self.engine_registry,
                admitted_aux_artifacts=self.aux_registry,
            )

    def test_registry_revocation_invalidates_lease(self) -> None:
        lease = self.issue()
        with self.assertRaisesRegex(PhysicalEngineLeaseError, "PHYSICAL_ENGINE_LEASE_CHECKPOINT_REVOKED"):
            assert_physical_engine_lease_current(
                lease,
                current_generation=7,
                admitted_engine_artifacts={"hcu_local_08b": digest("5")},
                admitted_aux_artifacts=self.aux_registry,
            )

    def test_aux_registry_revocation_invalidates_lease(self) -> None:
        lease = self.issue()
        changed = {
            "hcu_local_08b": {
                "tokenizer_sha256": digest("5"),
                "runtime_build_sha256": digest("3"),
            }
        }
        with self.assertRaisesRegex(PhysicalEngineLeaseError, "PHYSICAL_ENGINE_LEASE_TOKENIZER_REVOKED"):
            assert_physical_engine_lease_current(
                lease,
                current_generation=7,
                admitted_engine_artifacts=self.engine_registry,
                admitted_aux_artifacts=changed,
            )

    def test_boundary_receipt_placeholder_is_rejected(self) -> None:
        with self.assertRaisesRegex(PhysicalEngineLeaseError, "artifact_boundary_receipt_sha256"):
            self.issue(artifact_boundary_receipt_sha256="0" * 64)

    def test_inference_echo_contains_consumed_byte_and_lease_identity(self) -> None:
        lease = self.issue()
        echo = inference_lease_echo(lease)
        self.assertEqual(echo["physical_engine_lease_sha256"], lease.lease_sha256)
        self.assertEqual(echo["physical_engine_lease_generation"], 7)
        self.assertEqual(echo["loader_consumed_checkpoint_sha256"], digest("1"))
        self.assertEqual(echo["loader_consumed_tokenizer_sha256"], digest("2"))
        self.assertEqual(echo["loader_consumed_runtime_build_sha256"], digest("3"))


if __name__ == "__main__":
    unittest.main()
