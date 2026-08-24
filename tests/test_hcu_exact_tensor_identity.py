#!/usr/bin/env python3
"""Regression coverage for exact HCU/J-Space tensor identity semantics.

These tests are source/component regressions only. They grant no model-runtime,
J-Space-causal, HCU-full, training or whole-product credit.
"""
from __future__ import annotations

import struct

import pytest

from tools.hcu_exact_tensor_identity import (
    TensorIdentityRejected,
    canonicalized_value_digest_notice,
    exact_tensor_identity,
)


def test_exact_identity_binds_shape_even_when_payload_bytes_match() -> None:
    payload = struct.pack("<ff", 1.0, 2.0)
    vector = exact_tensor_identity(payload, dtype="torch.float32", shape=(2,))
    matrix = exact_tensor_identity(payload, dtype="torch.float32", shape=(1, 2))

    assert vector["sha256"] != matrix["sha256"]
    assert vector["shape"] == [2]
    assert matrix["shape"] == [1, 2]


def test_exact_identity_binds_dtype_even_when_payload_bytes_match() -> None:
    payload = bytes.fromhex("0000803f")
    float_view = exact_tensor_identity(payload, dtype="torch.float32", shape=(1,))
    int_view = exact_tensor_identity(payload, dtype="torch.int32", shape=(1,))

    assert float_view["sha256"] != int_view["sha256"]


def test_exact_identity_is_stable_for_same_envelope_and_payload() -> None:
    payload = bytes(range(32))
    first = exact_tensor_identity(payload, dtype="torch.uint8", shape=(4, 8))
    second = exact_tensor_identity(memoryview(payload), dtype="torch.uint8", shape=[4, 8])

    assert first == second
    assert first["identity_semantics"] == "EXACT_DTYPE_SHAPE_PAYLOAD_IDENTITY"


def test_float32_normalization_can_collapse_distinct_integer_values() -> None:
    # IEEE-754 binary32 cannot distinguish every integer above 2**24. This demonstrates
    # why a float32-normalized value digest cannot be used as a general exact token-ID
    # identity protocol, even if today's selected vocabulary happens to stay below it.
    left = struct.pack("<f", float(16_777_216))
    right = struct.pack("<f", float(16_777_217))

    assert left == right


def test_legacy_value_payload_does_not_bind_tensor_shape() -> None:
    # The current v1 activation probe hashes float32 contiguous bytes only. A 1-D tensor
    # [1, 2] and a 2-D tensor [[1, 2]] therefore have the same value payload unless shape
    # is separately included in the identity envelope.
    flattened_value_payload = struct.pack("<ff", 1.0, 2.0)

    one_dimensional = flattened_value_payload
    two_dimensional = flattened_value_payload

    assert one_dimensional == two_dimensional
    assert exact_tensor_identity(one_dimensional, dtype="torch.float32", shape=(2,))["sha256"] != exact_tensor_identity(
        two_dimensional, dtype="torch.float32", shape=(1, 2)
    )["sha256"]


def test_normalized_value_digest_must_be_machine_readably_downgraded() -> None:
    notice = canonicalized_value_digest_notice(normalization="float32 CPU contiguous bytes")

    assert notice["evidence_class"] == "CANONICALIZED_VALUE_DIGEST_NOT_EXACT_TENSOR_IDENTITY"
    assert notice["exact_tensor_identity"] == "false"


@pytest.mark.parametrize(
    ("payload", "dtype", "shape", "error"),
    [
        ("not-bytes", "torch.float32", (1,), "BYTES_LIKE_PAYLOAD_REQUIRED"),
        (b"", "", (0,), "NONEMPTY_DTYPE_REQUIRED"),
        (b"", "torch.float32", (-1,), "NONNEGATIVE_SHAPE_DIMENSIONS_REQUIRED"),
        (b"", "torch.float32", (True,), "INTEGER_SHAPE_DIMENSIONS_REQUIRED"),
    ],
)
def test_ambiguous_identity_inputs_fail_closed(payload, dtype, shape, error) -> None:
    with pytest.raises(TensorIdentityRejected, match=error):
        exact_tensor_identity(payload, dtype=dtype, shape=shape)
