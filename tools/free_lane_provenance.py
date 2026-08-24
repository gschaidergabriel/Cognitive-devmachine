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
ADMISSION_SCHEMA = "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION/v1"
PROVENANCE_SCHEMA = "ENTITYOS_HCU_FREE_LANE_ECONOMIC_PROVENANCE/v1"


def _json_snapshot(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"object required: {path}")
    return obj, hashlib.sha256(raw).hexdigest()


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
                "kind": "SAME_CREDENTIAL_PROVIDER_RATE_HEADER_MATCH",
                "requests_per_day": got_rpd,
                "tokens_per_minute": got_tpm,
                "observed_worker_ts": row.get("ts"),
                "observed_http_status": row.get("http_status"),
            }
    return newest


def _bound_credential_entitlement(
    *, record: dict[str, Any], credential_fingerprint: str, model_or_route: str
) -> dict[str, Any] | None:
    """Return one exact provider-side zero-cost credential/model binding.

    Provider-wide free-access statements are deliberately insufficient for a
    credential that could otherwise reach paid capacity. Positive admission
    requires the exact credential fingerprint, auditable provider-side evidence,
    and an explicit model/route allowlist containing the requested model.
    """
    rows = record.get("credential_entitlements")
    if not isinstance(rows, dict):
        return None
    bound = rows.get(credential_fingerprint)
    if not isinstance(bound, dict):
        return None
    if bound.get("provider_side_zero_cost_confirmed") is not True:
        return None
    evidence_ref = bound.get("evidence_ref")
    observed_at = bound.get("observed_at")
    allowed_models = bound.get("allowed_models")
    if not isinstance(evidence_ref, str) or not evidence_ref.strip():
        return None
    if not isinstance(observed_at, str) or not observed_at.strip():
        return None
    if not isinstance(allowed_models, list) or not allowed_models:
        return None
    if model_or_route not in {str(model) for model in allowed_models}:
        return None
    return {
        "kind": "EXACT_CREDENTIAL_PROVIDER_SIDE_ZERO_COST_BINDING",
        "evidence_ref": evidence_ref,
        "observed_at": observed_at,
        "account_scope": bound.get("account_scope"),
        "model_or_route": model_or_route,
    }


def _lane_evidence_from_provenance(
    prov: dict[str, Any],
    provider: str,
    credential_fingerprint: str,
    model_or_route: str,
    endpoint: str,
    *,
    artifacts: Path,
) -> dict[str, Any]:
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
        bound = _bound_credential_entitlement(
            record=record,
            credential_fingerprint=credential_fingerprint,
            model_or_route=model_or_route,
        )
        if not bound:
            return {"ok": False, "reason": "NVIDIA_CREDENTIAL_OR_MODEL_FREE_ENTITLEMENT_NOT_BOUND"}
        return {
            "ok": True,
            "kind": record.get("evidence_kind"),
            "source": record.get("source"),
            "endpoint_host": _host(endpoint),
            "scope": record.get("scope"),
            "credential_binding": bound,
            "assertion": "EXACT_NVIDIA_CREDENTIAL_AND_MODEL_BOUND_TO_PROVIDER_SIDE_FREE_NIM_ENTITLEMENT",
        }

    if provider == "groq":
        required = ((record.get("free_plan_models") or {}).get(model_or_route) or {})
        if not required:
            return {"ok": False, "reason": "GROQ_MODEL_NOT_BOUND_TO_DOCUMENTED_FREE_LIMITS"}
        match = _groq_historical_free_match(
            artifacts=artifacts,
            credential_fingerprint=credential_fingerprint,
            model=model_or_route,
            required=required,
        )
        if not match:
            return {"ok": False, "reason": "GROQ_CREDENTIAL_FREE_PLAN_HEADERS_NOT_OBSERVED"}
        return {
            "ok": True,
            "kind": record.get("evidence_kind"),
            "source": record.get("source"),
            "model": model_or_route,
            "provider_observation": match,
            "assertion": "SAME_CREDENTIAL_MATCHES_DOCUMENTED_GROQ_FREE_PLAN_LIMITS",
        }

    if provider == "mistral":
        return {"ok": False, "reason": "MISTRAL_PROVIDER_SIDE_FREE_MODE_NOT_BOUND"}

    return {"ok": False, "reason": "UNKNOWN_PROVIDER"}


def lane_evidence(
    provider: str,
    credential_fingerprint: str,
    model_or_route: str,
    endpoint: str,
    *,
    artifacts: Path = DEFAULT_ARTIFACTS,
) -> dict[str, Any]:
    prov, _ = _json_snapshot(PROVENANCE_PATH)
    if prov.get("schema") != PROVENANCE_SCHEMA or prov.get("mode") != "FREE_ONLY":
        return {"ok": False, "reason": "ECONOMIC_PROVENANCE_AUTHORITY_INVALID"}
    return _lane_evidence_from_provenance(
        prov,
        provider,
        credential_fingerprint,
        model_or_route,
        endpoint,
        artifacts=artifacts,
    )


def current_lane_binding(
    provider: str,
    credential_fingerprint: str,
    model_or_route: str,
    endpoint: str,
    *,
    artifacts: Path = DEFAULT_ARTIFACTS,
) -> dict[str, Any]:
    """Return one exact pre-call authorization snapshot for a concrete lane."""
    try:
        admission, admission_digest = _json_snapshot(ADMISSION_PATH)
        provenance, provenance_digest = _json_snapshot(PROVENANCE_PATH)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return {"ok": False, "reason": "FREE_LANE_AUTHORITY_SNAPSHOT_INVALID", "detail": type(exc).__name__}

    if admission.get("schema") != ADMISSION_SCHEMA or admission.get("mode") != "FREE_ONLY":
        return {"ok": False, "reason": "FREE_PROVIDER_ADMISSION_AUTHORITY_INVALID"}
    epoch = str(admission.get("authority_epoch") or "")
    if not epoch:
        return {"ok": False, "reason": "FREE_PROVIDER_ADMISSION_EPOCH_MISSING"}
    if provenance.get("schema") != PROVENANCE_SCHEMA or provenance.get("mode") != "FREE_ONLY":
        return {"ok": False, "reason": "ECONOMIC_PROVENANCE_AUTHORITY_INVALID"}
    if str(provenance.get("authority_epoch") or "") != epoch:
        return {"ok": False, "reason": "FREE_LANE_AUTHORITY_EPOCH_MISMATCH"}

    provider_admission = ((admission.get("providers") or {}).get(provider) or {})
    if provider_admission.get("admitted") is not True:
        return {"ok": False, "reason": "PROVIDER_NOT_CURRENTLY_ADMITTED"}
    if provider_admission.get("cost_class") != "FREE":
        return {"ok": False, "reason": "PROVIDER_COST_CLASS_NOT_FREE"}

    evidence = _lane_evidence_from_provenance(
        provenance,
        provider,
        credential_fingerprint,
        model_or_route,
        endpoint,
        artifacts=artifacts,
    )
    if not evidence.get("ok"):
        return {
            "ok": False,
            "reason": evidence.get("reason") or "FREE_LANE_ECONOMIC_PROVENANCE_REQUIRED",
            "admission_epoch": epoch,
            "admission_digest": admission_digest,
            "economic_provenance_digest": provenance_digest,
        }
    return {
        "ok": True,
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "admission_epoch": epoch,
        "admission_digest": admission_digest,
        "economic_provenance_digest": provenance_digest,
        "evidence": evidence,
    }


def binding_still_current(binding: dict[str, Any]) -> bool:
    """Re-read authority files and compare exact digests without granting authority."""
    if not binding.get("ok"):
        return False
    try:
        _, admission_digest = _json_snapshot(ADMISSION_PATH)
        _, provenance_digest = _json_snapshot(PROVENANCE_PATH)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return False
    return (
        admission_digest == binding.get("admission_digest")
        and provenance_digest == binding.get("economic_provenance_digest")
    )


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
    binding: dict[str, Any],
    request_id: str | None,
    usage: dict[str, Any],
    http_status: int | str,
    result_digest: str,
    source_commit_and_tree: dict[str, str],
    binding_stable_after_call: bool,
    artifacts: Path = DEFAULT_ARTIFACTS,
) -> dict[str, Any]:
    if not binding.get("ok"):
        raise ValueError("successful pre-call lane binding required")
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_commit_and_tree": source_commit_and_tree,
        "provider": provider,
        "credential_fingerprint": credential_fingerprint,
        "model_or_route": model_or_route,
        "endpoint_host": _host(endpoint),
        "typed_admission_epoch": binding.get("admission_epoch"),
        "typed_admission_digest": binding.get("admission_digest"),
        "economic_provenance_digest": binding.get("economic_provenance_digest"),
        "pre_call_binding_observed_at": binding.get("observed_at"),
        "provider_side_free_entitlement_or_zero_price_evidence": binding.get("evidence"),
        "binding_stable_after_call": bool(binding_stable_after_call),
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
