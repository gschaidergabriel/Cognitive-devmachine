#!/usr/bin/env python3
"""Route/credential-level FREE_ONLY economic provenance for the autonomous swarm.

The provider admission file grants owner-authorized access to free contingents.
This module is the narrower runtime gate required by supervisor epoch 8.70: a
concrete credential fingerprint + endpoint + model/route must have zero-cost/free
provider-side evidence before an autonomous network call is allowed.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PROVENANCE_PATH = ROOT / "governance/FREE_LANE_ECONOMIC_PROVENANCE_2026-08-24.json"
ADMISSION_PATH = ROOT / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
DEFAULT_ARTIFACTS = Path("/artifacts/clay-entityos-swarm")
RECEIPT_SCHEMA = "FREE_LANE_EXECUTION_RECEIPT/v1"


def _json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"object required: {path}")
    return obj


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _host(endpoint: str) -> str:
    return (urlparse(endpoint).hostname or "").lower()


def _int_header(headers: dict[str, Any], key: str) -> int | None:
    raw = headers.get(key)
    if raw is None:
        raw = headers.get(key.lower())
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return None


def _iter_worker_rows(artifacts: Path):
    if not artifacts.exists():
        return
    for path in artifacts.glob("**/workers.jsonl"):
        try:
            with path.open("r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(row, dict):
                        yield row
        except OSError:
            continue


def _groq_historical_free_match(
    *, artifacts: Path, credential_fingerprint: str, model: str, required: dict[str, Any]
) -> dict[str, Any] | None:
    """Return matching Groq rate telemetry only; never use it as billing authority."""
    want_rpd = int(required.get("requests_per_day") or 0)
    want_tpm = int(required.get("tokens_per_minute") or 0)
    newest: dict[str, Any] | None = None
    for row in _iter_worker_rows(artifacts):
        if row.get("provider") != "groq":
            continue
        if row.get("key_fp") != credential_fingerprint or row.get("model") != model:
            continue
        headers = row.get("rate") or {}
        if not isinstance(headers, dict):
            continue
        got_rpd = _int_header(headers, "x-ratelimit-limit-requests")
        got_tpm = _int_header(headers, "x-ratelimit-limit-tokens")
        if got_rpd == want_rpd and got_tpm == want_tpm:
            newest = {
                "kind": "SAME_CREDENTIAL_RATE_HEADER_MATCH_CORROBORATING_ONLY",
                "requests_per_day": got_rpd,
                "tokens_per_minute": got_tpm,
                "observed_worker_ts": row.get("ts"),
                "observed_http_status": row.get("http_status"),
            }
    return newest


def _parse_utc(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(dt.timezone.utc)


def _groq_bound_free_tier(
    *, record: dict[str, Any], credential_fingerprint: str, model_or_route: str
) -> dict[str, Any] | None:
    """Require fresh provider-side Free-tier evidence bound to the exact Groq key.

    Rate-limit headers are deliberately insufficient: Groq documents organization-
    specific exceptions and permits projects to set limits below the organization
    ceiling, so a paid project can present Free-like RPD/TPM values.
    """
    rows = record.get("credential_entitlements")
    if not isinstance(rows, dict):
        return None
    bound = rows.get(credential_fingerprint)
    if not isinstance(bound, dict):
        return None
    if bound.get("provider_side_free_tier_confirmed") is not True:
        return None
    if str(bound.get("tier") or "").upper() != "FREE":
        return None
    evidence_ref = bound.get("evidence_ref")
    if not isinstance(evidence_ref, str) or not evidence_ref.strip():
        return None
    observed_at = _parse_utc(bound.get("observed_at"))
    valid_until = _parse_utc(bound.get("valid_until"))
    if observed_at is None or valid_until is None or valid_until <= observed_at:
        return None
    max_age_s = int(record.get("max_entitlement_age_seconds") or 0)
    if max_age_s <= 0 or (valid_until - observed_at).total_seconds() > max_age_s:
        return None
    now = dt.datetime.now(dt.timezone.utc)
    if now < observed_at or now >= valid_until:
        return None
    allowed_models = bound.get("allowed_models")
    if not isinstance(allowed_models, list) or model_or_route not in set(allowed_models):
        return None
    return {
        "kind": "EXACT_GROQ_CREDENTIAL_PROVIDER_SIDE_FREE_TIER_BINDING",
        "evidence_ref": evidence_ref,
        "observed_at": observed_at.isoformat(),
        "valid_until": valid_until.isoformat(),
        "tier": "FREE",
        "account_scope": bound.get("account_scope"),
        "model_or_route": model_or_route,
    }


def lane_evidence(
    provider: str,
    credential_fingerprint: str,
    model_or_route: str,
    endpoint: str,
    *,
    artifacts: Path = DEFAULT_ARTIFACTS,
) -> dict[str, Any]:
    prov = _json(PROVENANCE_PATH)
    record = ((prov.get("providers") or {}).get(provider) or {})
    if not record:
        return {"ok": False, "reason": "PROVIDER_NOT_IN_ECONOMIC_PROVENANCE"}
    if _host(endpoint) != str(record.get("allowed_endpoint_host") or ""):
        return {"ok": False, "reason": "ENDPOINT_NOT_ZERO_COST_BOUND"}

    if provider == "openrouter":
        if model_or_route not in set(record.get("allowed_routes") or []):
            return {"ok": False, "reason": "OPENROUTER_ROUTE_NOT_EXPLICIT_ZERO_PRICE"}
        return {
            "ok": True,
            "kind": record.get("evidence_kind"),
            "source": record.get("source"),
            "route": model_or_route,
            "assertion": "EXACT_ROUTE_ZERO_PROMPT_AND_COMPLETION_PRICE",
        }

    if provider == "nvidia":
        return {
            "ok": True,
            "kind": record.get("evidence_kind"),
            "source": record.get("source"),
            "endpoint_host": _host(endpoint),
            "scope": record.get("scope"),
            "assertion": "NVIDIA_HOSTED_NIM_PROTOTYPING_ROUTE_ONLY",
        }

    if provider == "groq":
        required = ((record.get("free_plan_models") or {}).get(model_or_route) or {})
        if not required:
            return {"ok": False, "reason": "GROQ_MODEL_NOT_BOUND_TO_DOCUMENTED_FREE_LIMITS"}
        bound = _groq_bound_free_tier(
            record=record,
            credential_fingerprint=credential_fingerprint,
            model_or_route=model_or_route,
        )
        if not bound:
            return {"ok": False, "reason": "GROQ_CREDENTIAL_FREE_TIER_NOT_BOUND"}
        corroborating = _groq_historical_free_match(
            artifacts=artifacts,
            credential_fingerprint=credential_fingerprint,
            model=model_or_route,
            required=required,
        )
        return {
            "ok": True,
            "kind": record.get("evidence_kind"),
            "source": record.get("source"),
            "model": model_or_route,
            "credential_binding": bound,
            "rate_limit_telemetry": corroborating,
            "assertion": "EXACT_GROQ_CREDENTIAL_BOUND_TO_FRESH_PROVIDER_SIDE_FREE_TIER",
        }

    if provider == "mistral":
        # Ordinary Mistral API keys are explicitly not plan-scoped. Until the
        # organization/workspace's Free mode and disabled PAYG are bound from a
        # provider-side admin surface, autonomous execution fails closed.
        return {"ok": False, "reason": "MISTRAL_PROVIDER_SIDE_FREE_MODE_NOT_BOUND"}

    return {"ok": False, "reason": "UNKNOWN_PROVIDER"}


def lane_is_zero_cost(
    provider: str,
    credential_fingerprint: str,
    model_or_route: str,
    endpoint: str,
    *,
    artifacts: Path = DEFAULT_ARTIFACTS,
) -> bool:
    return bool(lane_evidence(
        provider, credential_fingerprint, model_or_route, endpoint, artifacts=artifacts
    ).get("ok"))


def emit_execution_receipt(
    *,
    provider: str,
    credential_fingerprint: str,
    model_or_route: str,
    endpoint: str,
    evidence: dict[str, Any],
    request_id: str | None,
    usage: dict[str, Any],
    http_status: int | str,
    result_digest: str,
    source_commit_and_tree: dict[str, str],
    artifacts: Path = DEFAULT_ARTIFACTS,
) -> dict[str, Any]:
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_commit_and_tree": source_commit_and_tree,
        "provider": provider,
        "credential_fingerprint": credential_fingerprint,
        "model_or_route": model_or_route,
        "endpoint_host": _host(endpoint),
        "typed_admission_epoch": str(_json(ADMISSION_PATH).get("authority_epoch")),
        "typed_admission_digest": _sha(ADMISSION_PATH),
        "provider_side_free_entitlement_or_zero_price_evidence": evidence,
        "request_id": request_id,
        "input_output_usage": usage,
        "http_status": http_status,
        "paid_fallback_attempt_count": 0,
        "result_digest": result_digest,
    }
    out = artifacts / "free_lane_execution_receipts.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(receipt, sort_keys=True, ensure_ascii=False) + "\n")
    return receipt
