#!/usr/bin/env python3
"""Exact tensor identity primitive for EntityOS/HCU evidence binding.

This module deliberately separates exact tensor identity from value-normalized digests.
Exact identity binds schema, dtype, shape, byte length and the exact contiguous payload
bytes. A digest produced after dtype conversion (for example float32 normalization) is a
value digest only and must never be relabeled as exact tensor/token identity.

This source grants no runtime, J-Space, HCU, training or canonical-semantic credit.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

SCHEMA = "ENTITYOS_HCU_EXACT_TENSOR_IDENTITY/v1"
VALUE_DIGEST_CLASS = "CANONICALIZED_VALUE_DIGEST_NOT_EXACT_TENSOR_IDENTITY"


class TensorIdentityRejected(ValueError):
    """Fail-closed rejection for ambiguous tensor identity inputs."""


def _normalize_dtype(dtype: str) -> str:
    if not isinstance(dtype, str):
        raise TensorIdentityRejected("DTYPE_STRING_REQUIRED")
    normalized = dtype.strip()
    if not normalized:
        raise TensorIdentityRejected("NONEMPTY_DTYPE_REQUIRED")
    try:
        normalized.encode("ascii")
    except UnicodeEncodeError as exc:
        raise TensorIdentityRejected("ASCII_DTYPE_REQUIRED") from exc
    return normalized


def _normalize_shape(shape: Iterable[int]) -> tuple[int, ...]:
    try:
        values = tuple(shape)
    except TypeError as exc:
        raise TensorIdentityRejected("SHAPE_ITERABLE_REQUIRED") from exc
    normalized: list[int] = []
    for dim in values:
        if isinstance(dim, bool) or not isinstance(dim, int):
            raise TensorIdentityRejected("INTEGER_SHAPE_DIMENSIONS_REQUIRED")
        if dim < 0:
            raise TensorIdentityRejected("NONNEGATIVE_SHAPE_DIMENSIONS_REQUIRED")
        normalized.append(dim)
    return tuple(normalized)


def exact_tensor_identity(payload: bytes, *, dtype: str, shape: Iterable[int]) -> dict[str, Any]:
    """Return exact tensor identity over metadata plus payload bytes."""
    if not isinstance(payload, (bytes, bytearray, memoryview)):
        raise TensorIdentityRejected("BYTES_LIKE_PAYLOAD_REQUIRED")
    raw = bytes(payload)
    normalized_dtype = _normalize_dtype(dtype)
    normalized_shape = _normalize_shape(shape)
    header = {
        "byte_length": len(raw),
        "dtype": normalized_dtype,
        "schema": SCHEMA,
        "shape": list(normalized_shape),
    }
    header_bytes = json.dumps(
        header,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    framed = len(header_bytes).to_bytes(8, "big") + header_bytes + raw
    return {
        **header,
        "sha256": hashlib.sha256(framed).hexdigest(),
        "identity_semantics": "EXACT_DTYPE_SHAPE_PAYLOAD_IDENTITY",
    }


def torch_exact_tensor_identity(tensor: Any) -> dict[str, Any]:
    """Bind an exact logical strided PyTorch tensor without dtype normalization."""
    try:
        import torch
    except Exception as exc:
        raise TensorIdentityRejected("PYTORCH_REQUIRED_FOR_TORCH_TENSOR_IDENTITY") from exc

    if not isinstance(tensor, torch.Tensor):
        raise TensorIdentityRejected("TORCH_TENSOR_REQUIRED")
    if tensor.layout != torch.strided:
        raise TensorIdentityRejected("STRIDED_TENSOR_REQUIRED")

    logical = tensor.detach().to(device="cpu").contiguous()
    payload = logical.view(torch.uint8).numpy().tobytes(order="C")
    result = exact_tensor_identity(
        payload,
        dtype=str(logical.dtype),
        shape=tuple(int(dim) for dim in logical.shape),
    )
    result.update(
        {
            "device_observed_before_normalization": str(tensor.device),
            "layout": str(tensor.layout),
            "requires_grad_observed": bool(tensor.requires_grad),
        }
    )
    return result


def canonicalized_value_digest_notice(*, normalization: str) -> dict[str, str]:
    """Machine-readable fence for deliberately normalized value digests."""
    if not isinstance(normalization, str) or not normalization.strip():
        raise TensorIdentityRejected("NORMALIZATION_DESCRIPTION_REQUIRED")
    return {
        "evidence_class": VALUE_DIGEST_CLASS,
        "normalization": normalization.strip(),
        "exact_tensor_identity": "false",
    }
