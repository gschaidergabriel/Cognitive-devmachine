import os
from pathlib import Path
import tempfile
import unittest

from engine_admission_v1 import (
    EngineAdmissionError,
    EngineArtifactLock,
    EngineArtifactPaths,
    LOCK_SCHEMA,
    derive_engine_artifact_sha256,
    digest_artifact_path,
    verify_and_construct_engine_admission,
)
from reactive_event_router_v1 import route_event


class EngineAdmissionProducerTests(unittest.TestCase):
    def fixture(self, root: Path):
        checkpoint = root / "checkpoint"
        tokenizer = root / "tokenizer"
        checkpoint.mkdir()
        tokenizer.mkdir()
        (checkpoint / "model-00001-of-00002.safetensors").write_bytes(b"weights-A")
        (checkpoint / "model-00002-of-00002.safetensors").write_bytes(b"weights-B")
        (tokenizer / "tokenizer.json").write_bytes(b'{"version":1}')
        (tokenizer / "config.json").write_bytes(b'{"eos":2}')
        runtime = root / "runtime.bin"
        build = root / "build.lock"
        runtime.write_bytes(b"runtime-bytes-v1")
        build.write_bytes(b"entityos-hcu-build-v1")
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
        return paths, lock

    def test_exact_bytes_construct_engine_admission_and_router_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths, lock = self.fixture(Path(tmp))
            verified = verify_and_construct_engine_admission(
                lock, paths, entity_generation=7, current_generation=7
            )
            self.assertEqual(verified.admission.engine_identity, "hcu_local_08b")
            self.assertEqual(verified.admission.engine_artifact_sha256, lock.engine_artifact_sha256)
            self.assertEqual(
                verified.admitted_engine_artifacts(),
                {"hcu_local_08b": lock.engine_artifact_sha256},
            )
            event = {
                "schema": "HCU_REACTIVE_EVENT/v1",
                "entity_generation": 7,
                "requested_internal_provider": "hcu",
                "novelty": 0.8,
                "contradiction": 0.0,
                "uncertainty": 0.0,
                "forecast_need": 0.0,
                "effect_pressure": 0.0,
                "zero_relevance": 0.0,
                "due_recheck": False,
            }
            decision = route_event(
                event,
                current_generation=7,
                engine_admission=verified.admission,
                admitted_engine_artifacts=verified.admitted_engine_artifacts(),
            )
            self.assertEqual(decision.status, "SELECTIVE_MODEL_ACTIVATION")
            self.assertEqual(decision.resolved_engine_artifact_sha256, lock.engine_artifact_sha256)

    def test_same_bytes_produce_deterministic_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths, lock = self.fixture(Path(tmp))
            a = verify_and_construct_engine_admission(lock, paths, entity_generation=7, current_generation=7)
            b = verify_and_construct_engine_admission(lock, paths, entity_generation=7, current_generation=7)
            self.assertEqual(a, b)
            self.assertEqual(a.receipt(), b.receipt())

    def test_checkpoint_mutation_after_lock_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths, lock = self.fixture(Path(tmp))
            (paths.checkpoint / "model-00001-of-00002.safetensors").write_bytes(b"poisoned")
            with self.assertRaisesRegex(EngineAdmissionError, "checkpoint_sha256:LOADED_BYTES_MISMATCH"):
                verify_and_construct_engine_admission(lock, paths, entity_generation=7, current_generation=7)

    def test_tokenizer_mutation_after_lock_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths, lock = self.fixture(Path(tmp))
            (paths.tokenizer / "tokenizer.json").write_bytes(b"poisoned-tokenizer")
            with self.assertRaisesRegex(EngineAdmissionError, "tokenizer_sha256:LOADED_BYTES_MISMATCH"):
                verify_and_construct_engine_admission(lock, paths, entity_generation=7, current_generation=7)

    def test_tree_identity_commits_to_relative_file_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths, lock = self.fixture(Path(tmp))
            old = paths.checkpoint / "model-00001-of-00002.safetensors"
            old.rename(paths.checkpoint / "renamed.safetensors")
            with self.assertRaisesRegex(EngineAdmissionError, "checkpoint_sha256:LOADED_BYTES_MISMATCH"):
                verify_and_construct_engine_admission(lock, paths, entity_generation=7, current_generation=7)

    def test_runtime_mutation_after_lock_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths, lock = self.fixture(Path(tmp))
            paths.runtime.write_bytes(b"different-runtime")
            with self.assertRaisesRegex(EngineAdmissionError, "runtime_sha256:LOADED_BYTES_MISMATCH"):
                verify_and_construct_engine_admission(lock, paths, entity_generation=7, current_generation=7)

    def test_build_mutation_after_lock_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths, lock = self.fixture(Path(tmp))
            paths.build.write_bytes(b"different-build")
            with self.assertRaisesRegex(EngineAdmissionError, "build_sha256:LOADED_BYTES_MISMATCH"):
                verify_and_construct_engine_admission(lock, paths, entity_generation=7, current_generation=7)

    def test_stale_generation_fails_before_admission(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths, lock = self.fixture(Path(tmp))
            with self.assertRaisesRegex(EngineAdmissionError, "STALE_ENTITY_GENERATION"):
                verify_and_construct_engine_admission(lock, paths, entity_generation=7, current_generation=8)

    def test_boolean_generation_is_not_integer(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths, lock = self.fixture(Path(tmp))
            with self.assertRaisesRegex(EngineAdmissionError, "current_generation:NONNEGATIVE_INTEGER_REQUIRED"):
                verify_and_construct_engine_admission(lock, paths, entity_generation=1, current_generation=True)

    def test_bundle_digest_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths, lock = self.fixture(Path(tmp))
            bad = EngineArtifactLock(**{**lock.__dict__, "engine_artifact_sha256": "f" * 64})
            with self.assertRaisesRegex(EngineAdmissionError, "ENGINE_ARTIFACT_BUNDLE_DIGEST_MISMATCH"):
                verify_and_construct_engine_admission(bad, paths, entity_generation=7, current_generation=7)

    def test_unadmitted_provider_or_engine_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths, lock = self.fixture(Path(tmp))
            bad_provider = EngineArtifactLock(**{**lock.__dict__, "provider_alias": "cloud"})
            with self.assertRaisesRegex(EngineAdmissionError, "ENGINE_PROVIDER_NOT_ADMITTED"):
                verify_and_construct_engine_admission(bad_provider, paths, entity_generation=7, current_generation=7)
            bad_engine = EngineArtifactLock(**{**lock.__dict__, "engine_identity": "hcu_future"})
            with self.assertRaisesRegex(EngineAdmissionError, "ENGINE_IDENTITY_NOT_ADMITTED"):
                verify_and_construct_engine_admission(bad_engine, paths, entity_generation=7, current_generation=7)

    def test_symlink_artifact_member_fails_closed(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlink unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            paths, lock = self.fixture(Path(tmp))
            target = paths.checkpoint / "model-00001-of-00002.safetensors"
            link = paths.checkpoint / "alias.safetensors"
            try:
                link.symlink_to(target.name)
            except OSError:
                self.skipTest("symlink creation unavailable")
            with self.assertRaisesRegex(EngineAdmissionError, "ARTIFACT_SYMLINK_FORBIDDEN"):
                verify_and_construct_engine_admission(lock, paths, entity_generation=7, current_generation=7)


if __name__ == "__main__":
    unittest.main()
