#!/usr/bin/env python3
"""Deterministic post-load model-state digest primitive for Trigger-2.

This is a source/static primitive, not checkpoint runtime evidence by itself.
It complements CHECKPOINT_INPUT_IDENTITY_ABI/v1 by binding the complete serialized
PyTorch ``state_dict()`` presented by a loaded model to one deterministic digest.

Scope law
---------
- ``state_dict()`` parameters and persistent buffers are included.
- Entry name, dtype, shape, raw contiguous tensor bytes and per-entry digest are bound.
- Mapping iteration order is deliberately ignored; entries are sorted by name.
- Device placement is not part of semantic state identity because every tensor is copied
  to contiguous CPU bytes before hashing. Runtime/device/dtype policy must remain a
  separately bound receipt field.
- This primitive does NOT independently prove that state came from particular checkpoint
  bytes. Selection-grade evidence still requires reconciliation with an admitted checkpoint
  manifest plus loader/input/forward identity.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

SCHEMA = "CLAY_TRIGGER2_LOADED_MODEL_STATE_DIGEST/v1"
DOMAIN = b"CLAY_TRIGGER2_LOADED_MODEL_STATE_DIGEST_V1\0"
ENTRY_DOMAIN = b"CLAY_TRIGGER2_LOADED_MODEL_STATE_ENTRY_V1\0"


class ModelStateDigestError(RuntimeError):
    pass


def _json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def _entry_envelope(name: str, dtype: str, shape: list[int], raw: bytes) -> bytes:
    if not isinstance(name, str) or not name:
        raise ModelStateDigestError("STATE_ENTRY_NAME_REQUIRED")
    if not isinstance(dtype, str) or not dtype:
        raise ModelStateDigestError("STATE_ENTRY_DTYPE_REQUIRED")
    if not isinstance(shape, list) or any(not isinstance(x, int) or x < 0 for x in shape):
        raise ModelStateDigestError("STATE_ENTRY_SHAPE_INVALID")
    header = _json_bytes({"name": name, "dtype": dtype, "shape": shape, "raw_nbytes": len(raw)})
    return ENTRY_DOMAIN + header + b"\0" + raw


def digest_raw_entries(entries: Iterable[tuple[str, str, list[int], bytes]]) -> dict[str, Any]:
    """Digest already-materialized tensor entries; useful for deterministic unit tests."""
    normalized: list[tuple[str, str, list[int], bytes]] = []
    seen: set[str] = set()
    for name, dtype, shape, raw in entries:
        if name in seen:
            raise ModelStateDigestError(f"DUPLICATE_STATE_ENTRY:{name}")
        if not isinstance(raw, (bytes, bytearray, memoryview)):
            raise ModelStateDigestError(f"STATE_ENTRY_RAW_BYTES_REQUIRED:{name}")
        seen.add(name)
        normalized.append((name, dtype, list(shape), bytes(raw)))
    if not normalized:
        raise ModelStateDigestError("MODEL_STATE_EMPTY")

    rows: list[dict[str, Any]] = []
    aggregate = sha256(DOMAIN)
    total_raw_nbytes = 0
    for name, dtype, shape, raw in sorted(normalized, key=lambda x: x[0]):
        envelope = _entry_envelope(name, dtype, shape, raw)
        entry_sha = _sha256_bytes(envelope)
        total_raw_nbytes += len(raw)
        row = {
            "name": name,
            "dtype": dtype,
            "shape": shape,
            "numel": None,
            "raw_nbytes": len(raw),
            "raw_bytes_sha256": _sha256_bytes(raw),
            "entry_sha256": entry_sha,
        }
        rows.append(row)
        aggregate.update(len(envelope).to_bytes(8, "big"))
        aggregate.update(envelope)

    return {
        "schema": SCHEMA,
        "state_entry_count": len(rows),
        "total_raw_nbytes": total_raw_nbytes,
        "model_state_sha256": aggregate.hexdigest(),
        "entries": rows,
        "scope": "PYTORCH_STATE_DICT_PARAMETERS_AND_PERSISTENT_BUFFERS",
    }


def _tensor_raw_identity(name: str, tensor: Any) -> tuple[str, str, list[int], bytes, int]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - runtime dependency boundary
        raise ModelStateDigestError(f"TORCH_REQUIRED:{type(exc).__name__}") from exc
    if not torch.is_tensor(tensor):
        raise ModelStateDigestError(f"NON_TENSOR_STATE_ENTRY:{name}:{type(tensor).__name__}")
    t = tensor.detach().cpu().contiguous()
    raw = t.view(torch.uint8).numpy().tobytes(order="C")
    return name, str(t.dtype), [int(x) for x in t.shape], raw, int(t.numel())


def digest_state_dict(state_dict: Mapping[str, Any]) -> dict[str, Any]:
    """Digest a PyTorch-style state_dict with deterministic name-sorted semantics."""
    if not isinstance(state_dict, Mapping) or not state_dict:
        raise ModelStateDigestError("STATE_DICT_REQUIRED")
    materialized: list[tuple[str, str, list[int], bytes]] = []
    numel_by_name: dict[str, int] = {}
    for name, tensor in state_dict.items():
        if not isinstance(name, str) or not name:
            raise ModelStateDigestError("STATE_DICT_NAME_INVALID")
        n, dtype, shape, raw, numel = _tensor_raw_identity(name, tensor)
        materialized.append((n, dtype, shape, raw))
        numel_by_name[n] = numel
    result = digest_raw_entries(materialized)
    for row in result["entries"]:
        row["numel"] = numel_by_name[row["name"]]
    return result


def digest_loaded_model(model: Any) -> dict[str, Any]:
    """Digest the loaded model's serialized parameter/persistent-buffer state."""
    state_fn = getattr(model, "state_dict", None)
    if not callable(state_fn):
        raise ModelStateDigestError("MODEL_STATE_DICT_REQUIRED")
    result = digest_state_dict(state_fn())
    result["model_class"] = type(model).__name__
    result["credit_boundary"] = {
        "checkpoint_consumed_state_credit": 0,
        "checkpoint_selection_credit": 0,
        "jspace_model_credit": 0,
        "training_credit": 0,
        "whole_hcu_runtime_credit": 0,
        "whole_entityos_runtime_credit": 0,
    }
    return result


__all__ = [
    "SCHEMA",
    "ModelStateDigestError",
    "digest_raw_entries",
    "digest_state_dict",
    "digest_loaded_model",
]
