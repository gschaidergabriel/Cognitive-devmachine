from pathlib import Path
import os
import tempfile
import unittest

from engine_admission_v1 import (
    EngineAdmission,
    EngineArtifactLock,
    EngineArtifactPaths,
    LOCK_SCHEMA,
    derive_engine_artifact_sha256,
    digest_artifact_path,
    verify_and_construct_engine_admission,
)
from engine_load_lease_v1 import (
    EngineLoadLeaseError,
    assert_engine_load_lease_unchanged,
    stage_verified_engine_load_lease,
)


class EngineLoadLeaseTests(unittest.TestCase):
    def fixture(self, root: Path):
        checkpoint = root / "checkpoint"
        tokenizer = root / "tokenizer"
        checkpoint.mkdir()
        tokenizer.mkdir()
        (checkpoint / "model.safetensors").write_bytes(b"weights-A")
        (tokenizer / "tokenizer.json").write_bytes(b'{"v":1}')
        runtime = root / "runtime.bin"
        build = root / "build.lock"
        runtime.write_bytes(b"runtime-A")
        build.write_bytes(b"build-A")
        paths = EngineArtifactPaths(checkpoint, tokenizer, runtime, build)

        provisional = EngineArtifactLock(
            schema=LOCK_SCHEMA,
            provider_alias="hcu",
            engine_identity="hcu_local_08b",
            engine_class="LOCAL_SHARED_WEIGHT_08B",
            checkpoint_sha256=digest_artifact_path(checkpoint).sha256,
            tokenizer_sha256=digest_artifact_path(tokenizer).sha256,
            runtime_sha256=digest_artifact_path(runtime).sha256,
            build_sha256=digest_artifact_path(build).sha256,
            engine_artifact_sha256="0" * 64,
        )
        lock = EngineArtifactLock(
            **{
                **provisional.__dict__,
                "engine_artifact_sha256": derive_engine_artifact_sha256(provisional),
            }
        )
        verified = verify_and_construct_engine_admission(
            lock,
            paths,
            entity_generation=7,
            current_generation=7,
        )
        return {
            "checkpoint": checkpoint,
            "tokenizer": tokenizer,
            "runtime": runtime,
            "build": build,
        }, verified

    def test_original_mutation_does_not_change_lease_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths, verified = self.fixture(root)
            lease = stage_verified_engine_load_lease(
                verified,
                paths,
                lease_root=root / "leases",
                current_generation=7,
            )
            original = paths["checkpoint"] / "model.safetensors"
            original.write_bytes(b"weights-B")
            self.assertEqual(
                (lease.checkpoint / "model.safetensors").read_bytes(),
                b"weights-A",
            )
            assert_engine_load_lease_unchanged(lease, current_generation=7)

    def test_staged_mutation_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths, verified = self.fixture(root)
            lease = stage_verified_engine_load_lease(
                verified,
                paths,
                lease_root=root / "leases",
                current_generation=7,
            )
            staged = lease.checkpoint / "model.safetensors"
            staged.chmod(0o644)
            staged.write_bytes(b"poison")
            with self.assertRaisesRegex(
                EngineLoadLeaseError,
                "LEASE_CHECKPOINT_DIGEST_MISMATCH",
            ):
                assert_engine_load_lease_unchanged(lease, current_generation=7)

    def test_stale_generation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths, verified = self.fixture(root)
            with self.assertRaisesRegex(EngineLoadLeaseError, "STALE_ENTITY_GENERATION"):
                stage_verified_engine_load_lease(
                    verified,
                    paths,
                    lease_root=root / "leases",
                    current_generation=8,
                )

    def test_source_mutation_before_stage_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths, verified = self.fixture(root)
            paths["runtime"].write_bytes(b"changed")
            with self.assertRaisesRegex(
                EngineLoadLeaseError,
                "SOURCE_RUNTIME_DIGEST_MISMATCH",
            ):
                stage_verified_engine_load_lease(
                    verified,
                    paths,
                    lease_root=root / "leases",
                    current_generation=7,
                )

    def test_symlink_source_member_rejected(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlink unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths, verified = self.fixture(root)
            target = paths["checkpoint"] / "model.safetensors"
            link = paths["checkpoint"] / "alias"
            try:
                link.symlink_to(target.name)
            except OSError:
                self.skipTest("symlink creation unavailable")
            with self.assertRaisesRegex(
                EngineLoadLeaseError,
                "ARTIFACT_SYMLINK_FORBIDDEN",
            ):
                stage_verified_engine_load_lease(
                    verified,
                    paths,
                    lease_root=root / "leases",
                    current_generation=7,
                )

    def test_same_verified_identity_reuses_same_lease_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths, verified = self.fixture(root)
            lease_root = root / "leases"
            first = stage_verified_engine_load_lease(
                verified,
                paths,
                lease_root=lease_root,
                current_generation=7,
            )
            second = stage_verified_engine_load_lease(
                verified,
                paths,
                lease_root=lease_root,
                current_generation=7,
            )
            self.assertEqual(first.lease_id_sha256, second.lease_id_sha256)
            self.assertEqual(first.lease_root, second.lease_root)
            self.assertEqual(
                first.receipt()["runtime_credit"],
                "ZERO_UNTIL_REAL_LOADER_CONSUMPTION_ECHO",
            )


if __name__ == "__main__":
    unittest.main()
