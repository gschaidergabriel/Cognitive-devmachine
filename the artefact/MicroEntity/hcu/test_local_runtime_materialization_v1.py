#!/usr/bin/env python3
"""Deterministic source regressions for local llama.cpp/Qwen materialization.

These tests use tiny synthetic local files. Passing them grants no runtime/model/J-Space
or training credit; it only proves the materialization gate fails closed around byte and
path identity before any physical model invocation.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from local_runtime_materialization_v1 import (
    LocalRuntimeMaterializationError,
    verify_local_runtime_materialization,
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def candidates(archive: bytes, model_bytes: bytes) -> tuple[dict, dict]:
    model_sha = sha(model_bytes)
    source = "1" * 40
    model = {
        "schema": "HCU_LOCAL_APPROX_08B_MODEL_CANDIDATE/v1",
        "status": "CANDIDATE_ONLY_NO_RUNTIME_CREDIT",
        "upstream_model_artifact": {
            "repository": "Qwen/test",
            "artifact": "test.gguf",
            "sha256": model_sha,
            "byte_count": len(model_bytes),
        },
        "single_file_role_mapping": {
            "checkpoint_expected_sha256": model_sha,
            "tokenizer_container_expected_sha256": model_sha,
        },
        "documented_local_runtime_family": {"exact_runtime_source_commit": source},
    }
    runtime = {
        "schema": "HCU_LOCAL_RUNTIME_CANDIDATE/v1",
        "status": "ATTESTED_DISTRIBUTION_CANDIDATE_ONLY_NO_RUNTIME_CREDIT",
        "runtime_family": "llama.cpp",
        "upstream": {"build_tag": "b-test", "source_repository_digest": source},
        "distribution_candidate": {
            "platform": "ubuntu-x64",
            "acceleration": "CPU",
            "asset": "llama-test.tar.gz",
            "archive_sha256": sha(archive),
        },
        "model_pairing": {
            "model_repository": "Qwen/test",
            "model_artifact": "test.gguf",
            "model_sha256": model_sha,
            "model_byte_count": len(model_bytes),
        },
    }
    return model, runtime


class LocalRuntimeMaterializationTests(unittest.TestCase):
    def fixture(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        archive_bytes = b"attested-runtime-archive"
        model_bytes = b"tiny-gguf-fixture"
        archive = root / "runtime.tar.gz"
        archive.write_bytes(archive_bytes)
        model_path = root / "model.gguf"
        model_path.write_bytes(model_bytes)
        extracted = root / "extracted"
        (extracted / "bin").mkdir(parents=True)
        (extracted / "lib").mkdir()
        binary = extracted / "bin/llama-cli"
        binary.write_bytes(b"ELF-test-binary")
        binary.chmod(0o755)
        (extracted / "lib/libggml.so").write_bytes(b"dep-a")
        (extracted / "lib/libllama.so").write_bytes(b"dep-b")
        model, runtime = candidates(archive_bytes, model_bytes)
        return temp, root, archive, model_path, extracted, model, runtime

    def run_fixture(self, **changes):
        temp, root, archive, model_path, extracted, model, runtime = self.fixture()
        kwargs = dict(
            model_candidate=model,
            runtime_candidate=runtime,
            runtime_archive_path=archive,
            extraction_root=extracted,
            runtime_binary_relative_path="bin/llama-cli",
            dependency_relative_paths=["lib/libllama.so", "lib/libggml.so"],
            model_path=model_path,
        )
        kwargs.update(changes)
        return temp, root, kwargs

    def test_exact_local_bytes_produce_stable_sorted_identity(self):
        temp, _root, kwargs = self.run_fixture()
        with temp:
            first = verify_local_runtime_materialization(**kwargs)
            kwargs["dependency_relative_paths"] = list(reversed(kwargs["dependency_relative_paths"]))
            second = verify_local_runtime_materialization(**kwargs)
            self.assertEqual(first.receipt.materialization_sha256, second.receipt.materialization_sha256)
            self.assertEqual([item.relative_path for item in first.receipt.dependencies],
                             ["lib/libggml.so", "lib/libllama.so"])
            self.assertEqual(first.receipt.model_byte_count, len(b"tiny-gguf-fixture"))
            self.assertTrue(first.runtime_binary_path.is_file())

    def test_archive_digest_drift_fails_closed(self):
        temp, _root, kwargs = self.run_fixture()
        with temp:
            kwargs["runtime_archive_path"].write_bytes(b"mutated")
            with self.assertRaisesRegex(LocalRuntimeMaterializationError, "RUNTIME_ARCHIVE_SHA256_MISMATCH"):
                verify_local_runtime_materialization(**kwargs)

    def test_model_digest_drift_fails_closed(self):
        temp, _root, kwargs = self.run_fixture()
        with temp:
            kwargs["model_path"].write_bytes(b"mutated-model")
            with self.assertRaisesRegex(LocalRuntimeMaterializationError, "MODEL_SHA256_MISMATCH"):
                verify_local_runtime_materialization(**kwargs)

    def test_non_executable_runtime_binary_fails_closed(self):
        temp, _root, kwargs = self.run_fixture()
        with temp:
            binary = kwargs["extraction_root"] / "bin/llama-cli"
            binary.chmod(0o644)
            with self.assertRaisesRegex(LocalRuntimeMaterializationError, "EXECUTABLE_BIT_REQUIRED"):
                verify_local_runtime_materialization(**kwargs)

    def test_runtime_binary_symlink_fails_closed(self):
        temp, root, kwargs = self.run_fixture()
        with temp:
            binary = kwargs["extraction_root"] / "bin/llama-cli"
            target = root / "other"
            target.write_bytes(b"ELF-test-binary")
            target.chmod(0o755)
            binary.unlink()
            binary.symlink_to(target)
            with self.assertRaisesRegex(LocalRuntimeMaterializationError, "SYMLINK_FORBIDDEN"):
                verify_local_runtime_materialization(**kwargs)

    def test_dependency_path_escape_fails_closed(self):
        temp, _root, kwargs = self.run_fixture()
        with temp:
            kwargs["dependency_relative_paths"] = ["../outside.so"]
            with self.assertRaisesRegex(LocalRuntimeMaterializationError, "PATH_TRAVERSAL_FORBIDDEN"):
                verify_local_runtime_materialization(**kwargs)

    def test_duplicate_dependency_identity_fails_closed(self):
        temp, _root, kwargs = self.run_fixture()
        with temp:
            kwargs["dependency_relative_paths"] = ["lib/libllama.so", "lib/libllama.so"]
            with self.assertRaisesRegex(LocalRuntimeMaterializationError, "DEPENDENCY_RELATIVE_PATH_DUPLICATE"):
                verify_local_runtime_materialization(**kwargs)

    def test_candidate_source_mismatch_fails_closed(self):
        temp, _root, kwargs = self.run_fixture()
        with temp:
            kwargs["runtime_candidate"]["upstream"]["source_repository_digest"] = "2" * 40
            with self.assertRaisesRegex(LocalRuntimeMaterializationError, "RUNTIME_SOURCE_CANDIDATE_MISMATCH"):
                verify_local_runtime_materialization(**kwargs)

    def test_promoted_candidate_status_is_rejected(self):
        temp, _root, kwargs = self.run_fixture()
        with temp:
            kwargs["runtime_candidate"]["status"] = "PASS"
            with self.assertRaisesRegex(LocalRuntimeMaterializationError, "RUNTIME_CANDIDATE_MUST_REMAIN_NONPROMOTED"):
                verify_local_runtime_materialization(**kwargs)


if __name__ == "__main__":
    unittest.main()
