#!/usr/bin/env python3
import errno
import hashlib
import os
import unittest

from loader_consumption_witness_v1 import (
    EVIDENCE_CLASS,
    FD_PATH_EVIDENCE_CLASS,
    WITNESS_SCHEMA,
    LoaderConsumptionWitnessError,
    assert_memfd_write_is_sealed,
    witnessed_load_bytes,
    witnessed_load_memfd,
)


class LoaderConsumptionWitnessTests(unittest.TestCase):
    def test_sealed_memfd_supplies_exact_bytes_to_bound_loader(self):
        payload = b"model-bytes\x00\x01"
        seen = []

        def loader(data: bytes):
            seen.append(data)
            return {"length": len(data), "digest": hashlib.sha256(data).hexdigest()}

        result = witnessed_load_bytes(
            payload,
            artifact_kind="checkpoint",
            loader_id="unit-loader",
            loader_binding_sha256="a" * 64,
            loader=loader,
        )
        self.assertEqual(seen, [payload])
        self.assertEqual(result.value["length"], len(payload))
        self.assertEqual(result.witness.schema, WITNESS_SCHEMA)
        self.assertEqual(result.witness.evidence_class, EVIDENCE_CLASS)
        self.assertEqual(result.witness.sha256, hashlib.sha256(payload).hexdigest())
        self.assertEqual(result.witness.byte_count, len(payload))

    def test_sealed_memfd_path_supplies_same_kernel_object_to_loader(self):
        payload = b"gguf-or-safetensors-model-bytes\x00\x02"
        observed_path = None

        def loader(handle):
            nonlocal observed_path
            observed_path = handle.proc_path
            self.assertTrue(os.path.exists(handle.proc_path))
            self.assertEqual(os.fstat(handle.fd).st_size, len(payload))
            with open(handle.proc_path, "rb", buffering=0) as model_file:
                loaded = model_file.read()
            self.assertEqual(loaded, payload)
            self.assertEqual(handle.sha256, hashlib.sha256(payload).hexdigest())
            return hashlib.sha256(loaded).hexdigest()

        result = witnessed_load_memfd(
            payload,
            artifact_kind="checkpoint",
            loader_id="path-loader",
            loader_binding_sha256="d" * 64,
            loader=loader,
        )
        self.assertEqual(result.value, hashlib.sha256(payload).hexdigest())
        self.assertEqual(result.witness.evidence_class, FD_PATH_EVIDENCE_CLASS)
        self.assertEqual(result.witness.sha256, hashlib.sha256(payload).hexdigest())
        self.assertIsNotNone(observed_path)
        self.assertFalse(os.path.exists(observed_path))

    def test_sealed_memfd_path_is_not_mutable_by_loader(self):
        payload = b"immutable-model"

        def loader(handle):
            with self.assertRaises(OSError) as caught:
                os.pwrite(handle.fd, b"X", 0)
            self.assertIn(caught.exception.errno, (errno.EPERM, errno.EBUSY))
            with open(handle.proc_path, "rb", buffering=0) as model_file:
                return model_file.read()

        result = witnessed_load_memfd(
            payload,
            artifact_kind="checkpoint",
            loader_id="sealed-path-loader",
            loader_binding_sha256="e" * 64,
            loader=loader,
        )
        self.assertEqual(result.value, payload)
        self.assertEqual(result.witness.sha256, hashlib.sha256(payload).hexdigest())

    def test_mutable_input_is_snapshotted_before_loader(self):
        payload = bytearray(b"abc")

        def loader(data: bytes):
            payload[:] = b"xyz"
            return data

        result = witnessed_load_bytes(
            payload,
            artifact_kind="tokenizer",
            loader_id="unit-loader",
            loader_binding_sha256="b" * 64,
            loader=loader,
        )
        self.assertEqual(result.value, b"abc")
        self.assertEqual(result.witness.sha256, hashlib.sha256(b"abc").hexdigest())
        self.assertEqual(payload, bytearray(b"xyz"))

    def test_kernel_rejects_post_seal_write(self):
        self.assertTrue(assert_memfd_write_is_sealed())

    def test_invalid_loader_binding_fails_closed_before_load(self):
        called = False

        def loader(data: bytes):
            nonlocal called
            called = True
            return data

        with self.assertRaisesRegex(
            LoaderConsumptionWitnessError,
            "loader_binding_sha256:LOWERCASE_SHA256_REQUIRED",
        ):
            witnessed_load_bytes(
                b"abc",
                artifact_kind="checkpoint",
                loader_id="unit-loader",
                loader_binding_sha256="not-a-digest",
                loader=loader,
            )
        self.assertFalse(called)

    def test_invalid_memfd_loader_binding_fails_closed_before_load(self):
        called = False

        def loader(handle):
            nonlocal called
            called = True
            return handle

        with self.assertRaisesRegex(
            LoaderConsumptionWitnessError,
            "loader_binding_sha256:LOWERCASE_SHA256_REQUIRED",
        ):
            witnessed_load_memfd(
                b"abc",
                artifact_kind="checkpoint",
                loader_id="path-loader",
                loader_binding_sha256="not-a-digest",
                loader=loader,
            )
        self.assertFalse(called)

    def test_loader_exception_produces_no_false_witness(self):
        class LoaderBoom(RuntimeError):
            pass

        def loader(data: bytes):
            raise LoaderBoom("boom")

        with self.assertRaisesRegex(LoaderBoom, "boom"):
            witnessed_load_bytes(
                b"abc",
                artifact_kind="checkpoint",
                loader_id="unit-loader",
                loader_binding_sha256="c" * 64,
                loader=loader,
            )

    def test_memfd_loader_exception_produces_no_false_witness(self):
        class LoaderBoom(RuntimeError):
            pass

        def loader(handle):
            self.assertTrue(os.path.exists(handle.proc_path))
            raise LoaderBoom("boom")

        with self.assertRaisesRegex(LoaderBoom, "boom"):
            witnessed_load_memfd(
                b"abc",
                artifact_kind="checkpoint",
                loader_id="path-loader",
                loader_binding_sha256="f" * 64,
                loader=loader,
            )


if __name__ == "__main__":
    unittest.main()
