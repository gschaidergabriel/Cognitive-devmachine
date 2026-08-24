#!/usr/bin/env python3
"""Route-bound successor for the Trigger-1 Qwen3-0.6B FREE logit-vector experiment.

The base executor remains the single experiment implementation. This wrapper adds the
missing OpenRouter runtime-route observation boundary before allowing its bounded
output-logit verdict to remain positive:

- opt in to X-OpenRouter-Metadata on every provider request;
- reuse the canonical Trigger-1 OpenRouter route-identity validator;
- require requested model == the exact admitted Qwen FREE route;
- reject BYOK routing and any material router pipeline;
- require a non-empty response system_fingerprint;
- require one invariant execution-runtime identity across calibration and holdout;
- require the six-control holdout to share one selected OpenRouter route.

Router metadata still does not attest exact model weight bytes or quantization. This
wrapper therefore cannot mint hidden-state/cvec/J-Space/HCU/training credit.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

import trigger1_openrouter_qwen06_logit_vector_execute as base
from trigger1_openrouter_runtime_identity import (
    RuntimeRouteIdentityError,
    extract_runtime_route_identity,
    validate_control_family_runtime_identity,
)

EMPTY_PIPELINE_SHA256 = hashlib.sha256(b"[]").hexdigest()
_ORIGINAL_EXTRACT_OBSERVATION = base.extract_observation
_ORIGINAL_ADJUDICATE = base.adjudicate


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def provider_call_with_router_metadata(
    key: str, body: dict[str, Any], *, owner: str
) -> tuple[int, dict[str, str], Any]:
    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode()
    req = base.urllib.request.Request(
        base.ENDPOINT,
        data=raw,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "clay-trigger1-jspace/1.0",
            "HTTP-Referer": "https://github.com/gschaidergabriel/clay-global-research-entity",
            "X-Title": "Clay Trigger-1 Qwen3-0.6B route-bound vector discriminator",
            "X-OpenRouter-Metadata": "enabled",
        },
    )
    try:
        with base.quota_slot(base.PROVIDER, owner, timeout_s=60.0, lease_s=120.0):
            try:
                with base.urllib.request.urlopen(req, timeout=90) as resp:
                    status = int(resp.status)
                    headers = {str(k).lower(): str(v) for k, v in resp.headers.items()}
                    payload = json.loads(resp.read().decode("utf-8", errors="replace"))
            except base.urllib.error.HTTPError as exc:
                status = int(exc.code)
                headers = ({str(k).lower(): str(v) for k, v in exc.headers.items()} if exc.headers else {})
                text = exc.read().decode("utf-8", errors="replace")
                try:
                    payload = json.loads(text)
                except Exception:
                    payload = {"error": {"message": text[:1600]}}
        base.quota_observe(base.PROVIDER, owner, status, headers)
        return status, headers, payload
    except TimeoutError:
        base.quota_observe(base.PROVIDER, owner, "GATE_TIMEOUT", {})
        return 503, {}, {"error": {"message": "shared provider gate timeout"}}


def _execution_runtime_identity(payload: Mapping[str, Any], route: Mapping[str, Any]) -> dict[str, Any]:
    if route.get("requested") != base.MODEL:
        raise RuntimeRouteIdentityError("REQUESTED_MODEL_ROUTE_MISMATCH")
    if route.get("is_byok") is not False:
        raise RuntimeRouteIdentityError("BYOK_ROUTE_FORBIDDEN_FREE_ONLY")
    if route.get("pipeline_sha256") != EMPTY_PIPELINE_SHA256:
        raise RuntimeRouteIdentityError("MATERIAL_ROUTER_PIPELINE_FORBIDDEN_FOR_CAUSAL_ATTRIBUTION")
    system_fingerprint = payload.get("system_fingerprint")
    if not isinstance(system_fingerprint, str) or not system_fingerprint.strip():
        raise RuntimeRouteIdentityError("SYSTEM_FINGERPRINT_REQUIRED")
    core = {
        "route_identity_sha256": route.get("route_identity_sha256"),
        "selected_provider": route.get("selected_provider"),
        "selected_model": route.get("selected_model"),
        "system_fingerprint": system_fingerprint.strip(),
    }
    return {
        "schema": "CLAY_TRIGGER1_OPENROUTER_EXECUTION_RUNTIME_IDENTITY/v1",
        **core,
        "execution_runtime_identity_sha256": canonical_sha(core),
        "quantization": "UNKNOWN_NOT_ATTESTED_BY_ROUTER_METADATA",
        "exact_model_weight_bytes_attested": False,
        "credit_scope": "OPENROUTER_EXECUTION_RUNTIME_IDENTITY_COMPONENT_ONLY",
    }


def extract_observation_route_bound(payload: Any) -> dict[str, Any]:
    observation = _ORIGINAL_EXTRACT_OBSERVATION(payload)
    if not isinstance(payload, Mapping):
        observation["runtime_identity_error"] = "PAYLOAD_MAPPING_REQUIRED"
        return observation
    try:
        route = extract_runtime_route_identity(payload)
        execution = _execution_runtime_identity(payload, route)
    except RuntimeRouteIdentityError as exc:
        observation["runtime_identity_error"] = str(exc)
        return observation
    observation["runtime_route_identity"] = route
    observation["execution_runtime_identity"] = execution
    return observation


def validate_execution_runtime_family(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    identities: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    if not rows:
        failures.append("NONEMPTY_EXECUTION_ROWS_REQUIRED")
    for index, row in enumerate(rows):
        if row.get("status") != "SUCCESS":
            failures.append(f"ROW_NOT_SUCCESS:{index}")
            continue
        observation = row.get("observation")
        execution = observation.get("execution_runtime_identity") if isinstance(observation, Mapping) else None
        if not isinstance(execution, Mapping):
            detail = (str(observation.get("runtime_identity_error")) if isinstance(observation, Mapping) and observation.get("runtime_identity_error") else "MISSING")
            failures.append(f"EXECUTION_RUNTIME_IDENTITY_{detail}:{index}")
            continue
        digest = execution.get("execution_runtime_identity_sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            failures.append(f"EXECUTION_RUNTIME_IDENTITY_DIGEST_INVALID:{index}")
            continue
        identities.setdefault(digest, dict(execution))
    if not failures and len(identities) != 1:
        failures.append("EXECUTION_RUNTIME_IDENTITY_CHANGED_ACROSS_BATCH")
    return {
        "schema": "CLAY_TRIGGER1_OPENROUTER_EXECUTION_RUNTIME_FAMILY/v1",
        "stable_execution_runtime": not failures and len(identities) == 1,
        "unique_execution_runtime_identities": len(identities),
        "selected_execution_runtime_identity": next(iter(identities.values())) if len(identities) == 1 else None,
        "quantization": "UNKNOWN_NOT_ATTESTED_BY_ROUTER_METADATA",
        "exact_model_weight_bytes_attested": False,
        "failures": failures,
        "credit_scope": "OPENROUTER_EXECUTION_RUNTIME_IDENTITY_COMPONENT_ONLY",
    }


def adjudicate_route_bound(calibration: list[dict[str, Any]], holdout: list[dict[str, Any]], selected_gain: float | None) -> dict[str, Any]:
    verdict = dict(_ORIGINAL_ADJUDICATE(calibration, holdout, selected_gain))
    execution_family = validate_execution_runtime_family(calibration + holdout)
    try:
        route_family = validate_control_family_runtime_identity(holdout)
    except RuntimeRouteIdentityError as exc:
        route_family = {
            "schema": "CLAY_TRIGGER1_OPENROUTER_RUNTIME_ROUTE_FAMILY/v1",
            "stable_selected_route": False,
            "failures": [str(exc)],
            "credit_scope": "OPENROUTER_SELECTED_ROUTE_IDENTITY_COMPONENT_ONLY",
        }
    runtime_identity_pass = bool(execution_family.get("stable_execution_runtime") and route_family.get("stable_selected_route"))
    original_pass = bool(verdict.get("pass"))
    verdict["pre_runtime_identity_pass"] = original_pass
    verdict["runtime_route_family"] = route_family
    verdict["execution_runtime_family"] = execution_family
    verdict["runtime_identity_pass"] = runtime_identity_pass
    verdict["pass"] = original_pass and runtime_identity_pass
    if original_pass and not runtime_identity_pass:
        verdict["classification"] = "RUNTIME_IDENTITY_UNRESOLVED"
    verdict["hidden_state_jspace_credit"] = False
    verdict["exact_model_weight_bytes_attested"] = False
    verdict["quantization"] = "UNKNOWN_NOT_ATTESTED_BY_ROUTER_METADATA"
    return verdict


def main() -> int:
    base.provider_call = provider_call_with_router_metadata
    base.extract_observation = extract_observation_route_bound
    base.adjudicate = adjudicate_route_bound
    return int(base.main())


if __name__ == "__main__":
    raise SystemExit(main())
