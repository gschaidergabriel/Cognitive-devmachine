#!/usr/bin/env python3
"""Route/credential-level FREE_ONLY economic provenance for the autonomous swarm.

The provider admission file grants owner-authorized access to free contingents.
This module is the narrower runtime gate required by supervisor epochs 8.70/8.71:
a concrete credential fingerprint + endpoint + model/route must have zero-cost/free
provider-side evidence before an autonomous network call is allowed.

A positive executable binding is successor-dynamic: admission/economic provenance
cannot form a self-consistent stale island beneath a newer supervisor. The canonical
SUPERVISOR_INBOX and the exact steering bytes selected by it are bound alongside the
lane authority digests and are revalidated before/after provider calls.
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
SUPERVISOR_INBOX_PATH = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
DEFAULT_ARTIFACTS = Path("/artifacts/clay-entityos-swarm")
RECEIPT_SCHEMA = "FREE_LANE_EXECUTION_RECEIPT/v1"
NVIDIA_ENTITLEMENT_SCHEMA = "NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_RECEIPT/v1"
ADMISSION_SCHEMA = "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION/v1"
PROVENANCE_SCHEMA = "ENTITYOS_HCU_FREE_LANE_ECONOMIC_PROVENANCE/v1"
_DENY_EXECUTION_MARKERS = ("QUARANTIN", "BLOCK", "FORBID", "DISABL", "REVOK")


def _json_snapshot(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"object required: {path}")
    return obj, hashlib.sha256(raw).hexdigest()


def _host(endpoint: str) -> str:
    return (urlparse(endpoint).hostname or "").lower()


def _canonical_json_digest(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


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


def _nvidia_entitlement_receipt(
    *,
    record: dict[str, Any],
    credential_fingerprint: str,
    model_or_route: str,
    endpoint: str,
) -> dict[str, Any] | None:
    """Validate one canonical credential-bound NVIDIA free-entitlement record.

    The economic-provenance authority must bind the exact non-secret credential
    fingerprint to provider-side entitlement evidence. The evidence itself is
    digest-bound and the requested model must be explicitly listed. This keeps a
    provider-global NIM statement, key presence, or HTTP success from self-admitting
    a concrete credential/model lane.
    """
    rows = record.get("credential_entitlements")
    if not isinstance(rows, dict):
        return None
    bound = rows.get(credential_fingerprint)
    if not isinstance(bound, dict):
        return None
    if bound.get("provider_side_zero_cost_confirmed") is not True:
        return None

    observed_at = bound.get("entitlement_observed_at")
    evidence = bound.get(
        "provider_side_developer_program_or_free_hosted_nim_entitlement_evidence"
    )
    evidence_digest = bound.get("entitlement_evidence_digest")
    allowed_models = bound.get("allowed_models")

    if not isinstance(observed_at, str) or not observed_at.strip():
        return None
    if not isinstance(evidence, dict) or not evidence:
        return None

    endpoint_host = _host(endpoint)
    if endpoint_host != "integrate.api.nvidia.com":
        return None

    # A digest proves evidence integrity, not who the evidence is about. Require
    # the nested provider evidence to name the same concrete credential/provider/
    # endpoint as the outer entitlement and requested lane before FREE_ONLY use.
    evidence_provider = str(evidence.get("provider") or "").strip().lower()
    evidence_fingerprint = str(evidence.get("credential_fingerprint") or "").strip()
    evidence_endpoint_host = str(evidence.get("endpoint_host") or "").strip().lower()
    if evidence_provider != "nvidia":
        return None
    if evidence_fingerprint != credential_fingerprint:
        return None
    if evidence_endpoint_host != endpoint_host:
        return None

    if not isinstance(evidence_digest, str) or len(evidence_digest) != 64:
        return None
    try:
        int(evidence_digest, 16)
    except ValueError:
        return None
    if _canonical_json_digest(evidence) != evidence_digest.lower():
        return None
    if not isinstance(allowed_models, list) or not allowed_models:
        return None
    normalized_models = [str(model).strip() for model in allowed_models if str(model).strip()]
    if model_or_route not in set(normalized_models):
        return None

    return {
        "schema": NVIDIA_ENTITLEMENT_SCHEMA,
        "credential_fingerprint": credential_fingerprint,
        "provider": "nvidia",
        "endpoint_host": endpoint_host,
        "provider_side_developer_program_or_free_hosted_nim_entitlement_evidence": evidence,
        "entitlement_observed_at": observed_at,
        "entitlement_evidence_digest": evidence_digest.lower(),
        "allowed_models": normalized_models,
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
        receipt = _nvidia_entitlement_receipt(
            record=record,
            credential_fingerprint=credential_fingerprint,
            model_or_route=model_or_route,
            endpoint=endpoint,
        )
        if receipt is None:
            return {
                "ok": False,
                "reason": "NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_RECEIPT_NOT_BOUND",
            }
        return {
            "ok": True,
            "kind": record.get("evidence_kind"),
            "source": record.get("source"),
            "endpoint_host": _host(endpoint),
            "scope": record.get("scope"),
            "credential_entitlement_receipt": receipt,
            "assertion": "EXACT_NVIDIA_CREDENTIAL_MODEL_FREE_ENTITLEMENT_BOUND",
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


def _current_supervisor_snapshot() -> dict[str, Any]:
    """Resolve current supervisor through the canonical inbox and bind exact bytes."""
    inbox, inbox_digest = _json_snapshot(SUPERVISOR_INBOX_PATH)
    epoch = str(inbox.get("schema_version") or "").strip()
    steering_ref = inbox.get("steering")
    if not epoch or not isinstance(steering_ref, str) or not steering_ref.strip():
        raise ValueError("SUPERVISOR_IDENTITY_REQUIRED")
    rel = Path(steering_ref)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("SUPERVISOR_STEERING_REF_INVALID")
    repo_root = ROOT.resolve()
    steering_path = (repo_root / rel).resolve()
    try:
        steering_path.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError("SUPERVISOR_STEERING_REF_OUTSIDE_REPO") from exc
    steering, steering_digest = _json_snapshot(steering_path)
    if str(steering.get("schema_version") or "").strip() != epoch:
        raise ValueError("SUPERVISOR_INBOX_STEERING_EPOCH_MISMATCH")
    if (
        steering.get("active_program") != "ENTITYOS_HCU"
        or steering.get("product") != "EntityOS"
        or steering.get("integrated_cognition_compute_architecture") != "HCU"
    ):
        raise ValueError("SUPERVISOR_PRODUCT_AUTHORITY_MISMATCH")
    free_only = steering.get("free_only")
    if not isinstance(free_only, dict) or free_only.get("enabled") is not True:
        raise ValueError("SUPERVISOR_FREE_ONLY_REQUIRED")
    if free_only.get("no_paid_fallback") is not True:
        raise ValueError("SUPERVISOR_NO_PAID_FALLBACK_REQUIRED")
    owner_contingents = free_only.get("owner_authorized_free_contingents")
    if not isinstance(owner_contingents, list):
        raise ValueError("SUPERVISOR_OWNER_FREE_CONTINGENTS_REQUIRED")
    normalized_contingents = tuple(
        sorted({str(item).strip().lower() for item in owner_contingents if str(item).strip()})
    )
    execution_state = str(
        free_only.get("execution_state")
        or free_only.get("external_llm_provider_execution")
        or "OWNER_AUTHORIZED_FREE_CONTINGENTS"
    ).strip().upper()
    if any(marker in execution_state for marker in _DENY_EXECUTION_MARKERS):
        raise ValueError("SUPERVISOR_EXTERNAL_PROVIDER_EXECUTION_NOT_AUTHORIZED")
    return {
        "epoch": epoch,
        "steering_ref": steering_ref,
        "inbox_digest": inbox_digest,
        "steering_digest": steering_digest,
        "execution_state": execution_state,
        "owner_authorized_free_contingents": normalized_contingents,
    }


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
        supervisor = _current_supervisor_snapshot()
        admission, admission_digest = _json_snapshot(ADMISSION_PATH)
        provenance, provenance_digest = _json_snapshot(PROVENANCE_PATH)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return {
            "ok": False,
            "reason": "FREE_LANE_AUTHORITY_SNAPSHOT_INVALID",
            "detail": str(exc) or type(exc).__name__,
        }

    if admission.get("schema") != ADMISSION_SCHEMA or admission.get("mode") != "FREE_ONLY":
        return {"ok": False, "reason": "FREE_PROVIDER_ADMISSION_AUTHORITY_INVALID"}
    epoch = str(admission.get("authority_epoch") or "")
    if not epoch:
        return {"ok": False, "reason": "FREE_PROVIDER_ADMISSION_EPOCH_MISSING"}
    if epoch != supervisor["epoch"]:
        return {"ok": False, "reason": "FREE_LANE_SUPERVISOR_EPOCH_MISMATCH"}
    if provenance.get("schema") != PROVENANCE_SCHEMA or provenance.get("mode") != "FREE_ONLY":
        return {"ok": False, "reason": "ECONOMIC_PROVENANCE_AUTHORITY_INVALID"}
    if str(provenance.get("authority_epoch") or "") != epoch:
        return {"ok": False, "reason": "FREE_LANE_AUTHORITY_EPOCH_MISMATCH"}

    provider_name = provider.strip().lower()
    if provider_name not in supervisor["owner_authorized_free_contingents"]:
        return {"ok": False, "reason": "PROVIDER_NOT_AUTHORIZED_BY_CURRENT_SUPERVISOR"}
    provider_admission = ((admission.get("providers") or {}).get(provider_name) or {})
    if provider_admission.get("admitted") is not True:
        return {"ok": False, "reason": "PROVIDER_NOT_CURRENTLY_ADMITTED"}
    if provider_admission.get("cost_class") != "FREE":
        return {"ok": False, "reason": "PROVIDER_COST_CLASS_NOT_FREE"}

    evidence = _lane_evidence_from_provenance(
        provenance,
        provider_name,
        credential_fingerprint,
        model_or_route,
        endpoint,
        artifacts=artifacts,
    )
    if not evidence.get("ok"):
        return {
            "ok": False,
            "reason": evidence.get("reason") or "FREE_LANE_ECONOMIC_PROVENANCE_REQUIRED",
            "supervisor_epoch": supervisor["epoch"],
            "supervisor_inbox_digest": supervisor["inbox_digest"],
            "supervisor_steering_digest": supervisor["steering_digest"],
            "admission_epoch": epoch,
            "admission_digest": admission_digest,
            "economic_provenance_digest": provenance_digest,
        }
    return {
        "ok": True,
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "supervisor_epoch": supervisor["epoch"],
        "supervisor_steering_ref": supervisor["steering_ref"],
        "supervisor_execution_state": supervisor["execution_state"],
        "supervisor_inbox_digest": supervisor["inbox_digest"],
        "supervisor_steering_digest": supervisor["steering_digest"],
        "admission_epoch": epoch,
        "admission_digest": admission_digest,
        "economic_provenance_digest": provenance_digest,
        "evidence": evidence,
    }


def binding_still_current(binding: dict[str, Any]) -> bool:
    """Re-resolve all bound authority surfaces and compare exact digests fail-closed."""
    if not binding.get("ok"):
        return False
    try:
        supervisor = _current_supervisor_snapshot()
        _, admission_digest = _json_snapshot(ADMISSION_PATH)
        _, provenance_digest = _json_snapshot(PROVENANCE_PATH)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return False
    return (
        supervisor["epoch"] == binding.get("supervisor_epoch")
        and supervisor["inbox_digest"] == binding.get("supervisor_inbox_digest")
        and supervisor["steering_digest"] == binding.get("supervisor_steering_digest")
        and admission_digest == binding.get("admission_digest")
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
        "supervisor_epoch": binding.get("supervisor_epoch"),
        "supervisor_steering_ref": binding.get("supervisor_steering_ref"),
        "supervisor_execution_state": binding.get("supervisor_execution_state"),
        "supervisor_inbox_digest": binding.get("supervisor_inbox_digest"),
        "supervisor_steering_digest": binding.get("supervisor_steering_digest"),
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