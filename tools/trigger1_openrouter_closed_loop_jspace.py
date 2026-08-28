#!/usr/bin/env python3
"""Closed-loop Global J-Space -> hosted output-logit vector controller.

This is a provider-agnostic control component for Trigger-1. It performs no network
I/O and grants no hidden-state/cvec credit. It converts a bounded Global J-Space
state into a sparse token-logit vector, emits one-token request bodies, then updates
the next J-Space state from the observed token id. The intended hosted executor is
an exact FREE route that proves logit_bias/seed/logprobs parameter consumption.

Credit scope: CLOSED_LOOP_OUTPUT_LOGIT_VECTOR_CONTROL_COMPONENT_ONLY.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

SCHEMA = "TRIGGER1_CLOSED_LOOP_JSPACE_LOGIT_CONTROLLER/v1"
ADAPTER_SCHEMA = "JSPACE_OUTPUT_LOGIT_ADAPTER/v1"
STEP_SCHEMA = "TRIGGER1_CLOSED_LOOP_JSPACE_LOGIT_STEP/v1"
CREDIT_SCOPE = "CLOSED_LOOP_OUTPUT_LOGIT_VECTOR_CONTROL_COMPONENT_ONLY"
CONTROLS = (
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
)


class ClosedLoopJSpaceError(ValueError):
    pass


def _sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _finite(x: Any, name: str) -> float:
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ClosedLoopJSpaceError(f"{name}:FINITE_NUMBER_REQUIRED")
    y = float(x)
    if not math.isfinite(y):
        raise ClosedLoopJSpaceError(f"{name}:FINITE_NUMBER_REQUIRED")
    return 0.0 if y == 0.0 else y


def _norm(v: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _orthogonal_same_norm(v: Sequence[float]) -> tuple[float, ...]:
    if len(v) < 2 or _norm(v) == 0:
        raise ClosedLoopJSpaceError("ORTHOGONAL_CONTROL_REQUIRES_NONZERO_DIMENSION_GE_2")
    n2 = sum(x * x for x in v)
    axis = min(range(len(v)), key=lambda i: (abs(v[i]), i))
    proj = v[axis] / n2
    w = [-proj * x for x in v]
    w[axis] += 1.0
    wn = _norm(w)
    if wn <= 1e-15:
        raise ClosedLoopJSpaceError("ORTHOGONAL_CONTROL_DEGENERATE")
    scale = _norm(v) / wn
    return tuple(x * scale for x in w)


def control_state(primary: Sequence[float], control: str) -> tuple[float, ...]:
    v = tuple(_finite(x, "state") for x in primary)
    if not v or _norm(v) == 0:
        raise ClosedLoopJSpaceError("NONZERO_PRIMARY_STATE_REQUIRED")
    if control not in CONTROLS:
        raise ClosedLoopJSpaceError("UNKNOWN_CONTROL")
    if control == "+VECTOR":
        return v
    if control == "SIGN_FLIP":
        return tuple(-x for x in v)
    if control in {"BASELINE", "NULL_VECTOR"}:
        return tuple(0.0 for _ in v)
    if control == "ORTHOGONAL_SAME_NORM":
        return _orthogonal_same_norm(v)
    p = tuple(v[1:]) + (v[0],)
    if p == v:
        raise ClosedLoopJSpaceError("PERMUTED_CONTROL_NOT_DISTINCT")
    return p


@dataclass(frozen=True)
class OutputLogitAdapter:
    schema: str
    source_basis_id: str
    source_basis_sha256: str
    model: str
    tokenizer_id: str
    tokenizer_sha256: str
    token_ids: tuple[int, ...]
    projection_rows: tuple[tuple[float, ...], ...]
    feedback_rows: tuple[tuple[float, ...], ...]
    decay: float
    feedback_gain: float
    adapter_sha256: str


def build_adapter(
    *,
    source_basis_id: str,
    source_basis_sha256: str,
    model: str,
    tokenizer_id: str,
    tokenizer_sha256: str,
    token_ids: Sequence[int],
    projection_rows: Sequence[Sequence[float]],
    feedback_rows: Sequence[Sequence[float]],
    decay: float = 0.8,
    feedback_gain: float = 0.2,
) -> OutputLogitAdapter:
    if not source_basis_id.strip() or len(source_basis_sha256) != 64:
        raise ClosedLoopJSpaceError("SOURCE_BASIS_IDENTITY_REQUIRED")
    if not model.strip() or not tokenizer_id.strip() or len(tokenizer_sha256) != 64:
        raise ClosedLoopJSpaceError("MODEL_TOKENIZER_IDENTITY_REQUIRED")
    tids = tuple(int(x) for x in token_ids)
    if not tids or any(x < 0 for x in tids) or len(set(tids)) != len(tids):
        raise ClosedLoopJSpaceError("DISTINCT_NONNEGATIVE_TOKEN_IDS_REQUIRED")
    proj = tuple(tuple(_finite(x, "projection") for x in row) for row in projection_rows)
    fb = tuple(tuple(_finite(x, "feedback") for x in row) for row in feedback_rows)
    if len(proj) != len(tids) or len(fb) != len(tids):
        raise ClosedLoopJSpaceError("TOKEN_ROW_COUNT_MISMATCH")
    dims = {len(row) for row in proj + fb}
    if len(dims) != 1 or not dims or next(iter(dims)) < 2:
        raise ClosedLoopJSpaceError("JSPACE_DIMENSION_MISMATCH")
    d = _finite(decay, "decay")
    g = _finite(feedback_gain, "feedback_gain")
    if not (0 <= d <= 1) or g < 0:
        raise ClosedLoopJSpaceError("FEEDBACK_PARAMETER_OUT_OF_RANGE")
    material = {
        "schema": ADAPTER_SCHEMA,
        "source_basis_id": source_basis_id,
        "source_basis_sha256": source_basis_sha256.lower(),
        "model": model,
        "tokenizer_id": tokenizer_id,
        "tokenizer_sha256": tokenizer_sha256.lower(),
        "token_ids": tids,
        "projection_rows": proj,
        "feedback_rows": fb,
        "decay": d,
        "feedback_gain": g,
    }
    return OutputLogitAdapter(**material, adapter_sha256=_sha(material))


def project_bias(adapter: OutputLogitAdapter, state: Sequence[float], gain: float) -> dict[str, float]:
    v = tuple(_finite(x, "state") for x in state)
    dim = len(adapter.projection_rows[0])
    if len(v) != dim:
        raise ClosedLoopJSpaceError("STATE_DIMENSION_MISMATCH")
    k = _finite(gain, "gain")
    out: dict[str, float] = {}
    for token_id, row in zip(adapter.token_ids, adapter.projection_rows):
        raw = k * sum(a * b for a, b in zip(row, v))
        out[str(token_id)] = max(-100.0, min(100.0, raw))
    return out


def build_step_request(
    *,
    adapter: OutputLogitAdapter,
    source_packet_sha256: str,
    primary_state: Sequence[float],
    control: str,
    gain: float,
    step_index: int,
    seed: int,
    messages: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    if len(source_packet_sha256) != 64:
        raise ClosedLoopJSpaceError("SOURCE_PACKET_SHA256_REQUIRED")
    if isinstance(step_index, bool) or step_index < 0 or isinstance(seed, bool):
        raise ClosedLoopJSpaceError("STEP_AND_SEED_INTEGER_REQUIRED")
    state = control_state(primary_state, control)
    bias = project_bias(adapter, state, gain)
    body: dict[str, Any] = {
        "model": adapter.model,
        "messages": [dict(m) for m in messages],
        "max_tokens": 1,
        "temperature": 0,
        "seed": int(seed),
        "logprobs": True,
        "top_logprobs": 20,
        "provider": {"require_parameters": True, "allow_fallbacks": False},
    }
    if control != "BASELINE":
        body["logit_bias"] = bias
    identity = {
        "schema": STEP_SCHEMA,
        "credit_scope": CREDIT_SCOPE,
        "adapter_sha256": adapter.adapter_sha256,
        "source_packet_sha256": source_packet_sha256.lower(),
        "control": control,
        "state_sha256": _sha(state),
        "bias_sha256": _sha(bias),
        "step_index": step_index,
        "seed": seed,
        "request_body_sha256": _sha(body),
    }
    identity["step_identity_sha256"] = _sha(identity)
    return {"identity": identity, "body": body, "state": state, "bias": bias}


def advance_state(
    adapter: OutputLogitAdapter,
    current_state: Sequence[float],
    *,
    observed_token_id: int,
) -> tuple[float, ...]:
    v = tuple(_finite(x, "state") for x in current_state)
    try:
        index = adapter.token_ids.index(int(observed_token_id))
    except ValueError:
        feedback = tuple(0.0 for _ in v)
    else:
        feedback = adapter.feedback_rows[index]
    if len(feedback) != len(v):
        raise ClosedLoopJSpaceError("FEEDBACK_DIMENSION_MISMATCH")
    return tuple(adapter.decay * x + adapter.feedback_gain * y for x, y in zip(v, feedback))


def bind_transition(
    *,
    step_identity_sha256: str,
    observed_token_id: int,
    current_state: Sequence[float],
    next_state: Sequence[float],
) -> dict[str, Any]:
    material = {
        "schema": SCHEMA,
        "credit_scope": CREDIT_SCOPE,
        "step_identity_sha256": step_identity_sha256,
        "observed_token_id": int(observed_token_id),
        "current_state_sha256": _sha(tuple(current_state)),
        "next_state_sha256": _sha(tuple(next_state)),
    }
    return {**material, "transition_sha256": _sha(material)}


__all__ = [
    "ADAPTER_SCHEMA", "CREDIT_SCOPE", "CONTROLS", "ClosedLoopJSpaceError",
    "OutputLogitAdapter", "build_adapter", "control_state", "project_bias",
    "build_step_request", "advance_state", "bind_transition",
]
