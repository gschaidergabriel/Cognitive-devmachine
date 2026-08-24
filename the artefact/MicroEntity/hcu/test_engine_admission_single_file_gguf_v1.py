#!/usr/bin/env python3
"""Deterministic source regression for a single-file GGUF EngineAdmission layout.

This test does not download Qwen, execute llama.cpp, or grant model/runtime credit. It
checks only that the existing EngineArtifactPaths/EngineArtifactLock contract can bind one
immutable GGUF container to both the checkpoint role and the tokenizer-container role without
inventing a second tokenizer artifact identity.
"""
from __future__ import annotations

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


class SingleFileGGUFEngineAdmissionTests(unittest.TestCase):
    def fixture(self, root: Path):
        model = root / "model.gguf"
        runtime = root / "runtime.bin"
        build = root / "build.lock"
        model.write_bytes(b"GGUF-single-container-model-and-tokenizer-metadata-v1")
        runtime.write_bytes(b"local-runtime-candidate-v1")
        build.write_bytes(b"local-build-candidate-v1")

        model_digest = digest_artifact_path(model).sha256
        runtime_digest = digest_artifact_path(runtime).sha256
        build_digest = digest_artifact_path(build).sha256
        provisional = EngineArtifactLock(
            schema=LOCK_SCHEMA,
            provider_alias="hcu",
            engine_identity="hcu_local_08b",
            engine_class="LOCAL_SHARED_WEIGHT_08B",
            checkpoint_sha256=model_digest,
            tokenizer_sha256=model_digest,
            runtime_sha256=runtime_digest,
            build_sha256=build_digest,
            engine_artifact_sha256="0" * 64,
        )
        lock = EngineArtifactLock(
            **{
                **provisional.__dict__,
                "engine_artifact_sha256": derive_engine_artifact_sha256(provisional),
            }
        )
        return model, EngineArtifactPaths(model, model, runtime, build), lock

    def test_same_gguf_file_can_bind_checkpoint_and_tokenizer_container_roles(self):
        with tempfile.TemporaryDirectory() as tmp:
            model, paths, lock = self.fixture(Path(tmp))
            verified = verify_and_construct_engine_admission(
                lock,
                paths,
                entity_generation=11,
                current_generation=11,
            )
            expected = digest_artifact_path(model).sha256
            self.assertEqual(verified.checkpoint.kind, "FILE_SHA256")
            self.assertEqual(verified.tokenizer.kind, "FILE_SHA256")
            self.assertEqual(verified.checkpoint.sha256, expected)
            self.assertEqual(verified.tokenizer.sha256, expected)
            self.assertEqual(verified.checkpoint.byte_count, verified.tokenizer.byte_count)
            self.assertEqual(verified.admission.engine_identity, "hcu_local_08b")
            self.assertEqual(
                verified.admitted_engine_artifacts(),
                {"hcu_local_08b": lock.engine_artifact_sha256},
            )

    def test_single_gguf_mutation_after_lock_fails_before_admission(self):
        with tempfile.TemporaryDirectory() as tmp:
            model, paths, lock = self.fixture(Path(tmp))
            model.write_bytes(b"GGUF-mutated-after-lock")
            with self.assertRaisesRegex(
                EngineAdmissionError,
                "checkpoint_sha256:LOADED_BYTES_MISMATCH",
            ):
                verify_and_construct_engine_admission(
                    lock,
                    paths,
                    entity_generation=11,
                    current_generation=11,
                )


if __name__ == "__main__":
    unittest.main()
