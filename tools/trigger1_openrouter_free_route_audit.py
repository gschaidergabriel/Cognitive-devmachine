#!/usr/bin/env python3
"""Network-free Trigger-1 audit for exact FREE OpenRouter output-logit routes.

Consumes a previously captured OpenRouter model catalog plus canonical economic
provenance and optional exact tokenizer bindings. It never performs network I/O.
A route is READY only when all of these are simultaneously true:
- exact non-dynamic model id;
- prompt and completion price are exactly zero;
- logit_bias, logprobs and seed are model-supported;
- an exact tokenizer id + SHA-256 is supplied explicitly or bound in canonical route evidence;
- the exact model id is explicitly admitted in economic provenance.

READY is only permission to construct/run the existing hosted output-logit control
family. It does not grant hidden-state/J-Space/HCU/EntityOS/training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

DYNAMIC_FREE_ROUTER = "openrouter/free"
SCHEMA = "TRIGGER1_OPENROUTER_FREE_ROUTE_AUDIT/v1"
READY_SCOPE = "OUTPUT_LOGIT_VECTOR_ROUTE_PREFLIGHT_ONLY"
REQUIRED_PARAMETERS = frozenset({"logit_bias", "logprobs", "seed"})


def _is_zero(value: Any) -> bool:
    try:
        return float(value) == 0.0
    except (TypeError, ValueError):
        return False


def _valid_sha256(value: Any) -> bool:
    text = str(value or "").strip().lower()
    if len(text) != 64:
        return False
    try:
        int(text, 16)
    except ValueError:
        return False
    return True


def _catalog_rows(catalog: Any) -> list[dict[str, Any]]:
    rows = catalog.get("data") if isinstance(catalog, Mapping) else catalog
    if not isinstance(rows, list):
        raise ValueError("OPENROUTER_CATALOG_DATA_LIST_REQUIRED")
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _openrouter_provenance(provenance: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(provenance, Mapping):
        return {}
    providers = provenance.get("providers")
    openrouter = providers.get("openrouter") if isinstance(providers, Mapping) else None
    return openrouter if isinstance(openrouter, Mapping) else {}


def _allowed_routes(provenance: Mapping[str, Any] | None) -> set[str]:
    routes = _openrouter_provenance(provenance).get("allowed_routes")
    return {str(x).strip() for x in routes} if isinstance(routes, list) else set()


def _canonical_tokenizer_binding(
    provenance: Mapping[str, Any] | None, model: str
) -> dict[str, str]:
    route_evidence = _openrouter_provenance(provenance).get("route_evidence")
    evidence = route_evidence.get(model) if isinstance(route_evidence, Mapping) else None
    if not isinstance(evidence, Mapping):
        return {}
    digest = str(evidence.get("tokenizer_json_sha256") or "").strip().lower()
    repo = str(evidence.get("weights_repository") or "").strip()
    revision = str(evidence.get("weights_revision") or "").strip()
    if not _valid_sha256(digest) or not repo or not revision:
        return {}
    return {
        "tokenizer_id": f"{repo}@{revision}:tokenizer.json",
        "tokenizer_sha256": digest,
    }


def audit_model(
    card: Mapping[str, Any],
    *,
    economic_provenance: Mapping[str, Any] | None = None,
    tokenizer_bindings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    model = str(card.get("id") or "").strip()
    pricing = card.get("pricing") if isinstance(card.get("pricing"), Mapping) else {}
    supported = {str(x) for x in card.get("supported_parameters", []) if isinstance(x, str)}
    hf_id = str(card.get("hugging_face_id") or "").strip()
    architecture = card.get("architecture") if isinstance(card.get("architecture"), Mapping) else {}
    tokenizer_family = str(architecture.get("tokenizer") or "").strip()
    allowed = _allowed_routes(economic_provenance)

    raw_binding = tokenizer_bindings.get(model) if isinstance(tokenizer_bindings, Mapping) else None
    binding = raw_binding if isinstance(raw_binding, Mapping) else _canonical_tokenizer_binding(economic_provenance, model)
    tokenizer_id = str(binding.get("tokenizer_id") or "").strip()
    tokenizer_sha256 = str(binding.get("tokenizer_sha256") or "").strip().lower()

    blockers: list[str] = []
    if not model:
        blockers.append("EXACT_MODEL_ID_MISSING")
    elif model == DYNAMIC_FREE_ROUTER:
        blockers.append("DYNAMIC_FREE_ROUTER_CANNOT_BIND_MODEL_TOKENIZER_IDENTITY")

    zero_price = _is_zero(pricing.get("prompt")) and _is_zero(pricing.get("completion"))
    if not zero_price:
        blockers.append("EXACT_ROUTE_NOT_ZERO_PRICE")

    missing_parameters = sorted(REQUIRED_PARAMETERS - supported)
    blockers.extend(f"PARAMETER_UNSUPPORTED:{name}" for name in missing_parameters)

    if not hf_id:
        blockers.append("PUBLIC_MODEL_ARTIFACT_ID_MISSING")
    if not tokenizer_id or not _valid_sha256(tokenizer_sha256):
        blockers.append("EXACT_TOKENIZER_BINDING_MISSING")

    if model and model not in allowed:
        blockers.append("EXACT_ROUTE_NOT_ECONOMICALLY_ADMITTED")

    status = "READY" if not blockers else "BLOCKED"
    return {
        "model": model,
        "status": status,
        "credit_scope": READY_SCOPE if status == "READY" else "NONE",
        "zero_price": zero_price,
        "hugging_face_id": hf_id or None,
        "tokenizer_family": tokenizer_family or None,
        "supported_parameters": sorted(supported),
        "missing_required_parameters": missing_parameters,
        "tokenizer_binding": {
            "tokenizer_id": tokenizer_id or None,
            "tokenizer_sha256": tokenizer_sha256 if _valid_sha256(tokenizer_sha256) else None,
        },
        "economic_route_admitted": bool(model and model in allowed),
        "blockers": blockers,
    }


def audit_catalog(
    catalog: Any,
    *,
    economic_provenance: Mapping[str, Any] | None = None,
    tokenizer_bindings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    rows = _catalog_rows(catalog)
    audited = [
        audit_model(
            row,
            economic_provenance=economic_provenance,
            tokenizer_bindings=tokenizer_bindings,
        )
        for row in rows
    ]
    exact_zero = [row for row in audited if row["zero_price"] and row["model"] != DYNAMIC_FREE_ROUTER]
    parameter_candidates = [
        row for row in exact_zero
        if not row["missing_required_parameters"] and row["hugging_face_id"]
    ]
    ready = [row for row in parameter_candidates if row["status"] == "READY"]
    snapshot = {
        "schema": SCHEMA,
        "network_io": False,
        "catalog_rows": len(rows),
        "exact_zero_price_routes": len(exact_zero),
        "parameter_capable_open_weight_candidates": len(parameter_candidates),
        "ready_routes": [row["model"] for row in ready],
        "candidates": parameter_candidates,
        "credit_scope": READY_SCOPE if ready else "NONE",
        "evidence_boundary": (
            "READY means only exact FREE output-logit route preflight. Actual vector consumption, matched controls, "
            "disjoint holdout and reproducibility are still required before any steering component credit."
        ),
    }
    raw = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    snapshot["audit_sha256"] = hashlib.sha256(raw).hexdigest()
    return snapshot


def _load(path: str | None, default: Any) -> Any:
    if not path:
        return default
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--economic-provenance")
    ap.add_argument("--tokenizer-bindings")
    args = ap.parse_args()
    result = audit_catalog(
        _load(args.catalog, {}),
        economic_provenance=_load(args.economic_provenance, {}),
        tokenizer_bindings=_load(args.tokenizer_bindings, {}),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ready_routes"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
