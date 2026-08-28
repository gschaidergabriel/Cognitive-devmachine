#!/usr/bin/env python3
"""Fail-closed Trigger-1 discriminator for hosted output-logit vector control.

This module does NOT perform provider network I/O. It turns one sparse token-logit
vector into the matched Trigger-1 control family and builds a request only after an
exact, non-dynamic OpenRouter model route is bound to route-specific FREE economic
provenance plus exact model/tokenizer identity.

A successful hosted logit-bias experiment is OUTPUT_LOGIT_VECTOR_CONTROL component
evidence only. It is not hidden-state/cvec evidence and cannot mint J-Space model
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
EXACT_FREE_QWEN_ROUTE = "qwen/qwen3-0.6b-04-28:free"
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
    axis = min(range(len(values)), key=lambda i: (abs(values[i]), i))
    denom = vnorm * vnorm
    projection = values[axis] / denom
    candidate = [(-projection * value) for value in values]
    candidate[axis] += 1.0
    cnorm = _norm(candidate)
    if cnorm <= 1e-15:
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

    route_evidence = openrouter.get("route_evidence")
    if not isinstance(route_evidence, Mapping):
        return {"ok": False, "reason": "ROUTE_SPECIFIC_ZERO_PRICE_EVIDENCE_REQUIRED"}
    record = route_evidence.get(model)
    if not isinstance(record, Mapping):
        return {"ok": False, "reason": "ROUTE_SPECIFIC_ZERO_PRICE_EVIDENCE_REQUIRED"}
    if record.get("price") != "FREE":
        return {"ok": False, "reason": "ROUTE_PRICE_NOT_EXPLICIT_FREE"}
    if record.get("prompt_token_price") != 0 or record.get("completion_token_price") != 0:
        return {"ok": False, "reason": "ROUTE_TOKEN_PRICE_NOT_EXPLICIT_ZERO"}
    if record.get("exact_model_identity") is not True:
        return {"ok": False, "reason": "ROUTE_EXACT_MODEL_IDENTITY_REQUIRED"}
    weights_repository = str(record.get("weights_repository") or "").strip()
    weights_revision = str(record.get("weights_revision") or "").strip()
    if not weights_repository or not weights_revision:
        return {"ok": False, "reason": "ROUTE_WEIGHTS_IDENTITY_REQUIRED"}
    try:
        tokenizer_sha256 = _require_sha256(record.get("tokenizer_json_sha256") or "", "TOKENIZER")
    except Trigger1LogitVectorError:
        return {"ok": False, "reason": "ROUTE_TOKENIZER_SHA256_REQUIRED"}
    return {
        "ok": True,
        "model": model,
        "economic_evidence_kind": "EXACT_ROUTE_ZERO_PRICE",
        "economic_source": record.get("source") or openrouter.get("source"),
        "weights_repository": weights_repository,
        "weights_revision": weights_revision,
        "tokenizer_json_sha256": tokenizer_sha256,
        "route_evidence_sha256": _canonical_digest(record),
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
    route = exact_free_route_gate(model, provenance) if provenance is not None else current_exact_free_route_gate(model)
    if not route.get("ok"):
        raise Trigger1LogitVectorError(str(route.get("reason") or "EXACT_FREE_ROUTE_REQUIRED"))
    tokenizer_id = str(tokenizer_id).strip()
    if not tokenizer_id:
        raise Trigger1LogitVectorError("EXACT_TOKENIZER_ID_REQUIRED")
    if tokenizer_id != route.get("weights_repository"):
        raise Trigger1LogitVectorError("TOKENIZER_ID_ROUTE_IDENTITY_MISMATCH")
    tokenizer_digest = _require_sha256(tokenizer_sha256, "TOKENIZER")
    if tokenizer_digest != route.get("tokenizer_json_sha256"):
        raise Trigger1LogitVectorError("TOKENIZER_SHA256_ROUTE_IDENTITY_MISMATCH")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise Trigger1LogitVectorError("FIXED_INTEGER_SEED_REQUIRED")
    if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or max_tokens <= 0:
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
            "require_parameters": True,
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
        "weights_repository": route["weights_repository"],
        "weights_revision": route["weights_revision"],
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
    gate = current_exact_free_route_gate(EXACT_FREE_QWEN_ROUTE)
    print(json.dumps({
        "schema": "TRIGGER1_OPENROUTER_LOGIT_VECTOR_GATE_STATUS/v1",
        "network_io": False,
        "exact_route": EXACT_FREE_QWEN_ROUTE,
        "gate": gate,
        "credit_scope": CREDIT_SCOPE,
        "next_gate": (
            "BUILD_SIX_MATCHED_REQUESTS_THEN_EXECUTE_VIA_CURRENT_LANE_BINDING_AND_"
            "FREE_LANE_EXECUTION_RECEIPTS_WITHOUT_PROMOTING_HIDDEN_STATE_CREDIT"
        ),
    }, sort_keys=True))
    return 0 if gate.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
