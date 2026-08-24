#!/usr/bin/env python3
import hashlib
import unittest

from loader_consumption_witness_v1 import (
    EVIDENCE_CLASS,
    WITNESS_SCHEMA,
    LoaderConsumptionWitnessError,
    assert_memfd_write_is_sealed,
    witnessed_load_bytes,
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


if __name__ == "__main__":
    unittest.main()
