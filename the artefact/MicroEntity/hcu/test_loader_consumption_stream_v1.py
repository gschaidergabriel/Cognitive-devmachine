#!/usr/bin/env python3
from __future__ import annotations

import errno
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import loader_consumption_stream_v1 as stream
from loader_consumption_stream_v1 import (
    LoaderConsumptionStreamError,
    STREAM_FILE_EVIDENCE_CLASS,
    witnessed_load_regular_file_memfd,
)


class LoaderConsumptionStreamTests(unittest.TestCase):
    def invoke(self, source: Path, payload: bytes, loader):
        return witnessed_load_regular_file_memfd(
            source,
            expected_source_sha256=hashlib.sha256(payload).hexdigest(),
            expected_source_byte_count=len(payload),
            artifact_kind="checkpoint",
            loader_id="llama-cpp-path-loader-candidate",
            loader_binding_sha256="a" * 64,
            loader=loader,
        )

    def test_regular_file_streams_to_same_sealed_object_seen_by_loader(self):
        payload = (b"GGUF-streaming-test-block-" * 10000) + b"end"
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "model.gguf"
            source.write_bytes(payload)
            observed_path = None

            def loader(handle):
                nonlocal observed_path
                observed_path = handle.proc_path
                self.assertTrue(os.path.exists(handle.proc_path))
                self.assertEqual(handle.byte_count, len(payload))
                self.assertEqual(handle.sha256, hashlib.sha256(payload).hexdigest())
                with open(handle.proc_path, "rb", buffering=0) as fh:
                    loaded = fh.read()
                self.assertEqual(loaded, payload)
                return hashlib.sha256(loaded).hexdigest()

            result = self.invoke(source, payload, loader)
            self.assertEqual(result.value, hashlib.sha256(payload).hexdigest())
            self.assertEqual(result.witness.evidence_class, STREAM_FILE_EVIDENCE_CLASS)
            self.assertEqual(result.witness.sha256, hashlib.sha256(payload).hexdigest())
            self.assertEqual(result.witness.byte_count, len(payload))
            self.assertIsNotNone(observed_path)
            self.assertFalse(os.path.exists(observed_path))

    def test_loader_cannot_mutate_streamed_memfd(self):
        payload = b"immutable-streamed-model"
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "model.gguf"
            source.write_bytes(payload)

            def loader(handle):
                with self.assertRaises(OSError) as caught:
                    os.pwrite(handle.fd, b"X", 0)
                self.assertIn(caught.exception.errno, (errno.EPERM, errno.EBUSY))
                with open(handle.proc_path, "rb", buffering=0) as fh:
                    return fh.read()

            result = self.invoke(source, payload, loader)
            self.assertEqual(result.value, payload)

    def test_wrong_expected_digest_fails_before_loader(self):
        payload = b"exact-model"
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "model.gguf"
            source.write_bytes(payload)
            called = False

            def loader(handle):
                nonlocal called
                called = True
                return handle.sha256

            with self.assertRaisesRegex(LoaderConsumptionStreamError, "SOURCE_SHA256_MISMATCH"):
                witnessed_load_regular_file_memfd(
                    source,
                    expected_source_sha256="b" * 64,
                    expected_source_byte_count=len(payload),
                    artifact_kind="checkpoint",
                    loader_id="loader",
                    loader_binding_sha256="c" * 64,
                    loader=loader,
                )
            self.assertFalse(called)

    def test_wrong_expected_size_fails_before_loader(self):
        payload = b"exact-model"
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "model.gguf"
            source.write_bytes(payload)
            called = False

            def loader(handle):
                nonlocal called
                called = True
                return handle.sha256

            with self.assertRaisesRegex(LoaderConsumptionStreamError, "SOURCE_SIZE_MISMATCH"):
                witnessed_load_regular_file_memfd(
                    source,
                    expected_source_sha256=hashlib.sha256(payload).hexdigest(),
                    expected_source_byte_count=len(payload) + 1,
                    artifact_kind="checkpoint",
                    loader_id="loader",
                    loader_binding_sha256="d" * 64,
                    loader=loader,
                )
            self.assertFalse(called)

    def test_symlink_source_fails_closed(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlink unavailable")
        payload = b"exact-model"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.gguf"
            link = root / "model.gguf"
            target.write_bytes(payload)
            try:
                link.symlink_to(target.name)
            except OSError:
                self.skipTest("symlink creation unavailable")
            with self.assertRaisesRegex(LoaderConsumptionStreamError, "SOURCE_SYMLINK_FORBIDDEN"):
                self.invoke(link, payload, lambda handle: handle.sha256)

    def test_source_mutation_during_copy_fails_before_loader(self):
        payload = b"A" * (stream._CHUNK + 4096)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "model.gguf"
            source.write_bytes(payload)
            original_read = stream.os.read
            injected = False
            called = False

            def mutate_after_first_read(fd: int, size: int):
                nonlocal injected
                block = original_read(fd, size)
                if not injected and block:
                    injected = True
                    with source.open("r+b") as fh:
                        fh.seek(len(payload) - 1)
                        fh.write(b"B")
                        fh.flush()
                        os.fsync(fh.fileno())
                return block

            def loader(handle):
                nonlocal called
                called = True
                return handle.sha256

            with patch.object(stream.os, "read", side_effect=mutate_after_first_read):
                with self.assertRaisesRegex(LoaderConsumptionStreamError, "SOURCE_CHANGED_DURING_COPY"):
                    self.invoke(source, payload, loader)
            self.assertTrue(injected)
            self.assertFalse(called)


if __name__ == "__main__":
    unittest.main()
