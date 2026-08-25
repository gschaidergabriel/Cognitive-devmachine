#!/usr/bin/env python3
"""Deterministic llama.cpp control-vector buffer layout for J-Space experiments.

llama.cpp's native cvec adapter stores one n_embd vector for each model layer after
layer 0. The input data buffer is consumed with offset n_embd * (layer - 1); the
layer range only controls which already-loaded per-layer vectors are applied.

Therefore a vector intended for native layer 20 must not be passed as a naked
n_embd-sized buffer with il_start=il_end=20: that buffer populates native layer 1
and leaves layer 20 zero. This helper constructs the exact sparse multi-layer F32
buffer while keeping cross-runtime layer mapping an explicit external claim.

This module performs no model/provider/network call and mints no runtime credit.
"""
from __future__ import annotations

import hashlib
import math
import struct
from typing import Any, Iterable

SCHEMA = "JSPACE_LLAMACPP_CVEC_LAYOUT/v1"


class CvecLayoutError(ValueError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise CvecLayoutError(code)


def _finite_float(value: Any) -> float:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), "FINITE_FLOAT_REQUIRED")
    out = float(value)
    _require(math.isfinite(out), "FINITE_FLOAT_REQUIRED")
    return out


def consumed_native_layers(*, data_len_floats: int, n_embd: int, n_layer: int) -> list[int]:
    """Return native layer slots llama.cpp can populate from the supplied float count.

    Mirrors llama_adapter_cvec::apply(): layer 0 has no tensor; native layer ``il``
    consumes [n_embd*(il-1), n_embd*il) when that full slice exists.
    """
    _require(isinstance(data_len_floats, int) and data_len_floats >= 0, "DATA_LEN_INVALID")
    _require(isinstance(n_embd, int) and n_embd > 0, "N_EMBD_INVALID")
    _require(isinstance(n_layer, int) and n_layer > 1, "N_LAYER_INVALID")
    return [
        il
        for il in range(1, n_layer)
        if n_embd * il <= data_len_floats
    ]


def build_single_native_layer_buffer(
    vector: Iterable[float],
    *,
    n_embd: int,
    n_layer: int,
    native_layer_index: int,
    gain: float = 1.0,
    source_layer_index: int | None = None,
    layer_mapping_evidence_sha256: str | None = None,
) -> dict[str, Any]:
    """Build a sparse F32 cvec buffer with exactly one non-zero native layer slot.

    ``native_layer_index`` is deliberately separate from ``source_layer_index``.
    This helper does not assume that a PyTorch hook index equals llama.cpp's native
    graph layer index; that equivalence requires its own evidence.
    """
    _require(isinstance(n_embd, int) and n_embd > 0, "N_EMBD_INVALID")
    _require(isinstance(n_layer, int) and n_layer > 1, "N_LAYER_INVALID")
    _require(
        isinstance(native_layer_index, int)
        and not isinstance(native_layer_index, bool)
        and 1 <= native_layer_index < n_layer,
        "NATIVE_LAYER_INDEX_INVALID",
    )
    if source_layer_index is not None:
        _require(
            isinstance(source_layer_index, int) and not isinstance(source_layer_index, bool) and source_layer_index >= 0,
            "SOURCE_LAYER_INDEX_INVALID",
        )
    if layer_mapping_evidence_sha256 is not None:
        _require(
            isinstance(layer_mapping_evidence_sha256, str)
            and len(layer_mapping_evidence_sha256) == 64
            and all(c in "0123456789abcdef" for c in layer_mapping_evidence_sha256.lower()),
            "LAYER_MAPPING_EVIDENCE_SHA256_INVALID",
        )

    values = [_finite_float(x) for x in vector]
    _require(len(values) == n_embd, "VECTOR_DIMENSION_MISMATCH")
    scale = _finite_float(gain)
    scaled = [x * scale for x in values]
    _require(all(math.isfinite(x) for x in scaled), "SCALED_VECTOR_NONFINITE")

    # llama.cpp allocates cvec tensors for native layers 1..n_layer-1 and reads
    # their data from n_embd * (il - 1). A full buffer is intentionally used so
    # the selected slot remains correct independent of il_start/il_end filtering.
    total_floats = n_embd * (n_layer - 1)
    buffer = [0.0] * total_floats
    offset = n_embd * (native_layer_index - 1)
    buffer[offset : offset + n_embd] = scaled

    packed = struct.pack(f"<{len(buffer)}f", *buffer)
    selected_packed = struct.pack(f"<{len(scaled)}f", *scaled)
    nonzero_layers = []
    for il in range(1, n_layer):
        start = n_embd * (il - 1)
        segment = buffer[start : start + n_embd]
        if any(x != 0.0 for x in segment):
            nonzero_layers.append(il)

    return {
        "schema": SCHEMA,
        "n_embd": n_embd,
        "n_layer": n_layer,
        "native_layer_index": native_layer_index,
        "source_layer_index": source_layer_index,
        "layer_mapping_evidence_sha256": layer_mapping_evidence_sha256,
        "gain": scale,
        "data_len_floats": total_floats,
        "target_offset_floats": offset,
        "il_start": native_layer_index,
        "il_end": native_layer_index,
        "consumed_native_layers": consumed_native_layers(
            data_len_floats=total_floats, n_embd=n_embd, n_layer=n_layer
        ),
        "nonzero_native_layers": nonzero_layers,
        "selected_vector_f32_sha256": hashlib.sha256(selected_packed).hexdigest(),
        "buffer_f32le_sha256": hashlib.sha256(packed).hexdigest(),
        "buffer": buffer,
        "runtime_credit_minted": False,
        "mapping_credit_minted": False,
        "evidence_scope": "DETERMINISTIC_NATIVE_CVEC_LAYOUT_ONLY",
    }


def sparse_buffer_without_payload(layout: dict[str, Any]) -> dict[str, Any]:
    """Return receipt-safe metadata without embedding the potentially large float array."""
    return {key: value for key, value in layout.items() if key != "buffer"}
