#!/usr/bin/env python3
"""Fail-closed Trigger-1 discriminator for hosted output-logit vector control.

This module does NOT perform provider network I/O.  It turns one sparse token-logit
vector into the matched Trigger-1 control family and builds a request only after an
exact, non-dynamic OpenRouter model route is present in canonical FREE economic
provenance.

Why this exists:
- OpenRouter documents ``logit_bias`` as a token-id -> logit-bias map consumed before
  sampling, so it is a useful hosted *output-logit* intervention discriminator.
- The current ``openrouter/free`` route is a dynamic router and therefore cannot bind
  the exact model/tokenizer identity required by Trigger-1.
- A successful hosted logit-bias experiment is OUTPUT_LOGIT_VECTOR_CONTROL component
  evidence only.  It is not hidden-state/cvec evidence and cannot mint J-Space model
  runtime, HCU, EntityOS, or training credit by itself.

The network-owning caller must still use ``current_lane_binding`` immediately before
I/O and preserve the normal FREE_LANE_EXECUTION_RECEIPT/v1 authority chain.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
ECONOMIC_PROVENANCE_PATH = ROOT / "governance/FREE_LANE_ECONOMIC_PROVENANCE_2026-08-24.json"
DYNAMIC_FREE_ROUTER = "openrouter/free"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
SCHEMA = "TRIGGER1_OPENROUTER_LOGIT_VECTOR_REQUEST/v1"
CREDIT_SCOPE = "OUTPUT_LOGIT_VECTOR_CONTROL_COMPONENT_ONLY"


class Trigger1LogitVectorError(ValueError):
    pass


def _canonical_digest(value: Any) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _require_sha256(value: str, field: str) -> str:
    text = str(value).strip().lower()
    if len(text) != 64:
        raise Trigger1LogitVectorError(f"{field}_SHA256_REQUIRED")
    try:
        int(text, 16)
    except ValueError as exc:
        raise Trigger1LogitVectorError(f"{field}_SHA256_REQUIRED") from exc
    return text


def normalize_sparse_vector(vector: Mapping[str | int, float | int]) -> dict[str, float]:
    if not isinstance(vector, Mapping) or not vector:
        raise Trigger1LogitVectorError("NONEMPTY_SPARSE_LOGIT_VECTOR_REQUIRED")
    out: dict[str, float] = {}
    for raw_token, raw_bias in vector.items():
        token_text = str(raw_token).strip()
        if not token_text.isdigit() or int(token_text) < 0:
            raise Trigger1LogitVectorError("TOKEN_IDS_MUST_BE_NONNEGATIVE_DECIMAL_INTEGERS")
        bias = float(raw_bias)
        if not math.isfinite(bias) or bias < -100.0 or bias > 100.0:
            raise Trigger1LogitVectorError("LOGIT_BIAS_OUT_OF_RANGE")
        canonical_token = str(int(token_text))
        if canonical_token in out:
            raise Trigger1LogitVectorError("DUPLICATE_TOKEN_ID_AFTER_CANONICALIZATION")
        out[canonical_token] = bias
    return dict(sorted(out.items(), key=lambda item: int(item[0])))


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _norm(values: list[float]) -> float:
    return math.sqrt(_dot(values, values))


def _orthogonal_same_norm(values: list[float]) -> list[float]:
    if len(values) < 2:
        raise Trigger1LogitVectorError("ORTHOGONAL_CONTROL_REQUIRES_AT_LEAST_TWO_TOKEN_AXES")
    vnorm = _norm(values)
    if vnorm == 0.0:
        raise Trigger1LogitVectorError("NONZERO_PRIMARY_VECTOR_REQUIRED")

    # Choose the coordinate least aligned with v, project it off v, then rescale.
    axis = min(range(len(values)), key=lambda i: abs(values[i]))
    denom = vnorm * vnorm
    projection = values[axis] / denom
    candidate = [(-projection * value) for value in values]
    candidate[axis] += 1.0
    cnorm = _norm(candidate)
    if cnorm <= 1e-15:
        # This can only happen for a one-axis direction; pick a different axis.
        axis = (axis + 1) % len(values)
        projection = values[axis] / denom
        candidate = [(-projection * value) for value in values]
        candidate[axis] += 1.0
        cnorm = _norm(candidate)
    if cnorm <= 1e-15:
        raise Trigger1LogitVectorError("ORTHOGONAL_CONTROL_DEGENERATE")
    scale = vnorm / cnorm
    return [value * scale for value in candidate]


def control_family(vector: Mapping[str | int, float | int]) -> dict[str, dict[str, float]]:
    primary = normalize_sparse_vector(vector)
    keys = list(primary)
    values = [primary[key] for key in keys]
    if _norm(values) == 0.0:
        raise Trigger1LogitVectorError("NONZERO_PRIMARY_VECTOR_REQUIRED")

    sign_flip = {key: -primary[key] for key in keys}
    null = {key: 0.0 for key in keys}
    orth_values = _orthogonal_same_norm(values)
    orthogonal = {key: orth_values[i] for i, key in enumerate(keys)}

    if len(values) < 2:
        raise Trigger1LogitVectorError("PERMUTED_CONTROL_REQUIRES_AT_LEAST_TWO_TOKEN_AXES")
    perm_values = values[1:] + values[:1]
    permuted = {key: perm_values[i] for i, key in enumerate(keys)}
    if permuted == primary:
        raise Trigger1LogitVectorError("PERMUTED_CONTROL_NOT_DISTINCT_FROM_PRIMARY")

    return {
        "BASELINE": {},
        "+VECTOR": primary,
        "SIGN_FLIP": sign_flip,
        "NULL_VECTOR": null,
        "ORTHOGONAL_SAME_NORM": orthogonal,
        "PERMUTED_SAME_NORM": permuted,
    }


def exact_free_route_gate(model: str, provenance: Mapping[str, Any]) -> dict[str, Any]:
    model = str(model).strip()
    if not model:
        return {"ok": False, "reason": "EXACT_MODEL_ROUTE_REQUIRED"}
    if model == DYNAMIC_FREE_ROUTER:
        return {"ok": False, "reason": "DYNAMIC_FREE_ROUTER_CANNOT_BIND_MODEL_TOKENIZER_IDENTITY"}

    providers = provenance.get("providers") if isinstance(provenance, Mapping) else None
    openrouter = providers.get("openrouter") if isinstance(providers, Mapping) else None
    if not isinstance(openrouter, Mapping):
        return {"ok": False, "reason": "OPENROUTER_ECONOMIC_PROVENANCE_REQUIRED"}
    routes = openrouter.get("allowed_routes")
    if not isinstance(routes, list) or model not in {str(item).strip() for item in routes}:
        return {"ok": False, "reason": "EXACT_MODEL_ROUTE_NOT_ZERO_PRICE_BOUND"}
    if openrouter.get("evidence_kind") != "EXACT_ROUTE_ZERO_PRICE":
        return {"ok": False, "reason": "EXACT_ROUTE_ZERO_PRICE_EVIDENCE_REQUIRED"}
    return {
        "ok": True,
        "model": model,
        "economic_evidence_kind": "EXACT_ROUTE_ZERO_PRICE",
        "economic_source": openrouter.get("source"),
    }


def current_exact_free_route_gate(model: str) -> dict[str, Any]:
    try:
        provenance = json.loads(ECONOMIC_PROVENANCE_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"ok": False, "reason": "ECONOMIC_PROVENANCE_UNREADABLE", "detail": type(exc).__name__}
    return exact_free_route_gate(model, provenance)


def build_request(
    *,
    model: str,
    tokenizer_id: str,
    tokenizer_sha256: str,
    prompt: str,
    vector: Mapping[str | int, float | int],
    control: str,
    seed: int,
    max_tokens: int = 128,
    provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    route = (
        exact_free_route_gate(model, provenance)
        if provenance is not None
        else current_exact_free_route_gate(model)
    )
    if not route.get("ok"):
        raise Trigger1LogitVectorError(str(route.get("reason") or "EXACT_FREE_ROUTE_REQUIRED"))

    tokenizer_id = str(tokenizer_id).strip()
    if not tokenizer_id:
        raise Trigger1LogitVectorError("EXACT_TOKENIZER_ID_REQUIRED")
    tokenizer_digest = _require_sha256(tokenizer_sha256, "TOKENIZER")
    if not isinstance(seed, int):
        raise Trigger1LogitVectorError("FIXED_INTEGER_SEED_REQUIRED")
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        raise Trigger1LogitVectorError("POSITIVE_MAX_TOKENS_REQUIRED")

    family = control_family(vector)
    if control not in family:
        raise Trigger1LogitVectorError("UNKNOWN_CONTROL_LABEL")

    body: dict[str, Any] = {
        "model": str(model).strip(),
        "messages": [{"role": "user", "content": str(prompt)}],
        "max_tokens": max_tokens,
        "temperature": 0,
        "seed": seed,
        "logprobs": True,
        "top_logprobs": 20,
        "provider": {
            # OpenRouter documents this as excluding providers that do not support
            # every request parameter; without it logit_bias may be ignored.
            "require_parameters": True,
            # Keep one request on its first eligible provider rather than silently
            # changing runtime after a failure.
            "allow_fallbacks": False,
        },
    }
    selected = family[control]
    if control != "BASELINE":
        body["logit_bias"] = selected

    identity = {
        "schema": SCHEMA,
        "credit_scope": CREDIT_SCOPE,
        "model": body["model"],
        "tokenizer_id": tokenizer_id,
        "tokenizer_sha256": tokenizer_digest,
        "control": control,
        "control_vector_sha256": _canonical_digest(selected),
        "seed": seed,
        "request_body_sha256": _canonical_digest(body),
        "route_gate": route,
    }
    identity["request_identity_sha256"] = _canonical_digest(identity)
    return {"identity": identity, "body": body}


def main() -> int:
    # The canonical repository currently admits only the dynamic openrouter/free
    # route, so a direct invocation without a future exact route intentionally
    # reports the blocker instead of performing network I/O.
    gate = current_exact_free_route_gate(DYNAMIC_FREE_ROUTER)
    print(json.dumps({
        "schema": "TRIGGER1_OPENROUTER_LOGIT_VECTOR_GATE_STATUS/v1",
        "network_io": False,
        "current_dynamic_route": DYNAMIC_FREE_ROUTER,
        "gate": gate,
        "credit_scope": CREDIT_SCOPE,
        "next_gate": "BIND_ONE_EXACT_ZERO_PRICE_MODEL_ROUTE_WITH_LOGIT_BIAS_AND_TOKENIZER_IDENTITY",
    }, sort_keys=True))
    return 0 if gate.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
