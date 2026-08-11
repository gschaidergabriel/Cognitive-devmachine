#!/usr/bin/env python3
"""Zero-cost provider discovery and policy for Clay/FRANK.

This module never prints secrets and never performs paid calls. Together is a
hard-denied provider and is intentionally absent from discovery and routing.
"""
from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import secrets
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse


DENIED_PROVIDERS = frozenset({"together"})
ZERO_COST_ONLY = True
PAYMENT_REQUIRED_STATUS = 402
MAX_PROVIDER_RESPONSE_BYTES = 2_000_000
TEXT_CHAT_ROLES = frozenset({"system", "user", "assistant"})
PROCESS_PAYMENT_LATCHES: set[str] = set()


@dataclass(frozen=True)
class ProviderSpec:
    provider_id: str
    key_names: tuple[str, ...]
    priority: int
    openai_compatible_base_url: str
    free_or_prepaid_only: bool = True
    zero_cost_evidence: str | None = None


PROVIDERS = (
    ProviderSpec(
        "nvidia",
        ("NVIDIA_API_KEY", "NVCF_API_KEY"),
        100,
        "https://integrate.api.nvidia.com/v1",
        True,
        "nvidia_developer_program_free_prototype_endpoint",
    ),
    ProviderSpec("groq", ("GROQ_API_KEY",), 80, "https://api.groq.com/openai/v1"),
    ProviderSpec(
        "cerebras",
        ("CEREBRAS_API_KEY",),
        75,
        "https://api.cerebras.ai/v1",
    ),
    ProviderSpec(
        "gemini",
        ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        70,
        "https://generativelanguage.googleapis.com/v1beta/openai",
    ),
    ProviderSpec(
        "openrouter",
        ("OPENROUTER_API_KEY",),
        50,
        "https://openrouter.ai/api/v1",
    ),
)


def _attested_zero_cost_providers(environ: dict[str, str]) -> set[str]:
    """Return explicitly operator-attested zero-cost provider IDs."""
    raw = environ.get("FRANK_ZERO_COST_ATTESTED_PROVIDERS", "")
    return {
        provider_id.strip().lower()
        for provider_id in raw.split(",")
        if provider_id.strip()
        and provider_id.strip().lower() not in DENIED_PROVIDERS
    }


def _configured_key_name(
    spec: ProviderSpec, environ: dict[str, str]
) -> str | None:
    return next(
        (name for name in spec.key_names if environ.get(name, "").strip()),
        None,
    )


def _budget_epoch(environ: dict[str, str]) -> str:
    value = environ.get("FRANK_FREE_ONLY_BUDGET_EPOCH", "").strip()
    return value or "PROCESS_LOCAL"


def _budget_epoch_id(environ: dict[str, str]) -> str:
    return hashlib.sha256(_budget_epoch(environ).encode("utf-8")).hexdigest()[:16]


def _payment_latch_key(provider_id: str, environ: dict[str, str]) -> str:
    return hashlib.sha256(
        f"{_budget_epoch(environ)}:{provider_id}".encode("utf-8")
    ).hexdigest()


def inventory(
    environ: dict[str, str] | None = None,
    *,
    payment_latches: set[str] | None = None,
) -> list[dict]:
    env = os.environ if environ is None else environ
    latches = PROCESS_PAYMENT_LATCHES if payment_latches is None else payment_latches
    attested = _attested_zero_cost_providers(env)
    rows = []
    for spec in PROVIDERS:
        if spec.provider_id in DENIED_PROVIDERS:
            continue
        key_name = _configured_key_name(spec, env)
        zero_cost_evidence = spec.zero_cost_evidence
        if spec.provider_id in attested:
            zero_cost_evidence = "operator_zero_cost_attestation"
        eligible_before_latch = bool(
            key_name and zero_cost_evidence and ZERO_COST_ONLY
        )
        payment_blocked = _payment_latch_key(spec.provider_id, env) in latches
        row = asdict(spec)
        row["key_names"] = list(spec.key_names)
        row.update(
            {
                "configured": key_name is not None,
                "configured_via": key_name,
                "secret_exposed": False,
                "zero_cost_assured": zero_cost_evidence is not None,
                "zero_cost_evidence": zero_cost_evidence,
                "budget_epoch_id": _budget_epoch_id(env),
                "payment_blocked_current_budget_epoch": payment_blocked,
                "eligible_before_payment_latch": eligible_before_latch,
                "eligible": bool(eligible_before_latch and not payment_blocked),
            }
        )
        rows.append(row)
    return sorted(rows, key=lambda x: (-x["priority"], x["provider_id"]))


def route(
    environ: dict[str, str] | None = None,
    *,
    payment_latches: set[str] | None = None,
) -> dict:
    rows = inventory(environ, payment_latches=payment_latches)
    eligible = [row for row in rows if row["eligible"]]
    blocked = [
        row["provider_id"]
        for row in rows
        if row["eligible_before_payment_latch"]
        and row["payment_blocked_current_budget_epoch"]
    ]
    if eligible:
        reason = "highest_priority_configured_zero_cost_provider"
    elif blocked:
        reason = "payment_required_hard_stop_active"
    else:
        reason = "no_configured_zero_cost_provider"
    return {
        "selected": eligible[0]["provider_id"] if eligible else None,
        "candidates": [row["provider_id"] for row in eligible],
        "zero_cost_only": ZERO_COST_ONLY,
        "denied_providers": sorted(DENIED_PROVIDERS),
        "payment_blocked_providers": blocked,
        "reason": reason,
    }


def receipt() -> dict:
    return {
        "schema_version": "1.1",
        "kind": "FREE_API_CAPABILITY_RECEIPT",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "inventory": inventory(),
        "route": route(),
        "invariants": {
            "secrets_never_serialized": True,
            "paid_calls_forbidden": True,
            "together_access_forbidden": True,
            "payment_required_is_hard_stop": True,
            "network_probe_performed": False,
        },
    }


def _safe_request_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _safe_attempt_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]


def _validate_text_chat_request(messages, model) -> None:
    if not isinstance(model, str) or not model.strip():
        raise ValueError("model_must_be_nonempty_string")
    if not isinstance(messages, list):
        raise ValueError("messages_must_be_list")
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("message_must_be_object")
        if not isinstance(message.get("role"), str) or not message["role"].strip():
            raise ValueError("message_role_must_be_nonempty_string")
        if message["role"] not in TEXT_CHAT_ROLES:
            raise ValueError("message_role_not_supported_by_text_adapter")
        if not isinstance(message.get("content"), str):
            raise ValueError("message_content_must_be_string")


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject redirects so bearer credentials cannot cross an origin boundary."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ProviderResponseTooLarge(ValueError):
    """The provider response exceeded the bounded adapter's byte limit."""


def _open_no_redirect(request: urllib.request.Request, timeout: int):
    return urllib.request.build_opener(_NoRedirectHandler()).open(
        request, timeout=timeout
    )


def _validated_endpoint(
    spec: ProviderSpec, raw_base_url: str, environ: dict[str, str]
) -> tuple[str, str]:
    """Return request URL and redacted endpoint-capability ID after binding."""
    parsed = urlparse(raw_base_url)
    provider_url = urlparse(spec.openai_compatible_base_url)

    if parsed.username is not None or parsed.password is not None:
        raise RuntimeError("provider_endpoint_userinfo_forbidden")
    if parsed.query or parsed.fragment or parsed.params:
        raise RuntimeError("provider_endpoint_not_bound_to_selected_provider")

    local_test = parsed.hostname in {"127.0.0.1", "localhost"} and environ.get(
        "FRANK_ALLOW_LOCAL_TEST_ENDPOINT"
    ) == "1"
    if parsed.scheme != "https" and not local_test:
        raise RuntimeError("provider_endpoint_must_use_https")

    try:
        parsed_port = parsed.port or (443 if parsed.scheme == "https" else 80)
        provider_port = provider_url.port or 443
    except ValueError as exc:
        raise RuntimeError(
            "provider_endpoint_not_bound_to_selected_provider"
        ) from exc

    if not local_test:
        if (
            parsed.scheme != provider_url.scheme
            or parsed.hostname != provider_url.hostname
            or parsed_port != provider_port
            or parsed.path != provider_url.path
        ):
            raise RuntimeError("provider_endpoint_not_bound_to_selected_provider")
        base_url = spec.openai_compatible_base_url
        scheme = provider_url.scheme
        host = provider_url.hostname
        port = provider_port
        base_path = provider_url.path
    else:
        if parsed.hostname is None:
            raise RuntimeError("provider_endpoint_not_bound_to_selected_provider")
        base_url = raw_base_url.rstrip("/")
        scheme = parsed.scheme
        host = parsed.hostname
        port = parsed_port
        base_path = parsed.path.rstrip("/")

    request_url = f"{base_url.rstrip('/')}/chat/completions"
    operation_path = f"{base_path.rstrip('/')}/chat/completions"
    endpoint_capability = f"{scheme}://{host}:{port}{operation_path}"
    endpoint_capability_id = _safe_request_id(endpoint_capability)
    return request_url, endpoint_capability_id


def _zero_cost_evidence_for(
    spec: ProviderSpec, environ: dict[str, str]
) -> str | None:
    if spec.provider_id in _attested_zero_cost_providers(environ):
        return "operator_zero_cost_attestation"
    return spec.zero_cost_evidence


def _cost_policy_principal_id(
    spec: ProviderSpec, key_name: str, environ: dict[str, str]
) -> str:
    evidence = _zero_cost_evidence_for(spec, environ) or "NONE"
    value = (
        f"{spec.provider_id}:{key_name}:{evidence}:{_budget_epoch(environ)}"
    )
    return _safe_request_id(value)


def _is_valid_http_status(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and 100 <= value <= 599
    )


def execute_chat(
    messages: list[dict[str, str]],
    *,
    model: str,
    environ: dict[str, str] | None = None,
    opener=None,
    now=time.time,
    nonce_factory=None,
    payment_latches: set[str] | None = None,
) -> dict:
    """Execute one bounded chat request and return output plus a redacted receipt."""
    _validate_text_chat_request(messages, model)
    env = os.environ if environ is None else environ
    latches = PROCESS_PAYMENT_LATCHES if payment_latches is None else payment_latches
    route_state = route(env, payment_latches=latches)
    selected = route_state["selected"]
    if not selected:
        if route_state["reason"] == "payment_required_hard_stop_active":
            raise RuntimeError("payment_required_hard_stop_active")
        raise RuntimeError("no_configured_zero_cost_provider")

    spec = next(item for item in PROVIDERS if item.provider_id == selected)
    key_name = _configured_key_name(spec, env)
    if key_name is None:
        raise RuntimeError("configured_provider_key_missing")

    raw_base_url = env.get(
        "FRANK_PROVIDER_BASE_URL", spec.openai_compatible_base_url
    )
    request_url, endpoint_capability_id = _validated_endpoint(
        spec, raw_base_url, env
    )
    cost_policy_principal_id = _cost_policy_principal_id(spec, key_name, env)

    attempt_nonce = (
        secrets.token_hex(16) if nonce_factory is None else nonce_factory()
    )
    if not isinstance(attempt_nonce, str) or not attempt_nonce:
        raise ValueError("attempt_nonce_must_be_nonempty_string")

    started = now()
    lifecycle = ["REQUESTED", "AUTHORIZED", "CLAIMED"]
    body = json.dumps(
        {"model": model, "messages": messages, "stream": False}
    ).encode()
    request = urllib.request.Request(
        request_url,
        data=body,
        headers={
            "Authorization": f"Bearer {env[key_name]}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    request_opener = _open_no_redirect if opener is None else opener
    status = None
    response_started = False
    retryable = False

    try:
        with request_opener(request, timeout=30) as response:
            candidate_status = getattr(response, "status", None)
            if not _is_valid_http_status(candidate_status):
                raise ValueError("response_status_must_be_http_integer")
            status = candidate_status
            response_started = True
            lifecycle.append("EXECUTED")
            response_body = response.read(MAX_PROVIDER_RESPONSE_BYTES + 1)
            if len(response_body) > MAX_PROVIDER_RESPONSE_BYTES:
                raise ProviderResponseTooLarge
        if not 200 <= status < 300:
            content = None
            if status == PAYMENT_REQUIRED_STATUS:
                latches.add(_payment_latch_key(selected, env))
                outcome = "payment_required_hard_stop"
                cooldown_seconds = 0
                retryable = False
            elif status == 429:
                outcome = "rate_limited"
                cooldown_seconds = 60
                retryable = True
            else:
                outcome = "provider_error"
                cooldown_seconds = 15
                retryable = True
        else:
            payload = json.loads(response_body)
            choices = payload["choices"]
            if not isinstance(choices, list) or not choices:
                raise ValueError("response_choices_must_be_nonempty_list")
            message = choices[0]["message"]
            if not isinstance(message, dict):
                raise ValueError("response_message_must_be_object")
            content = message["content"]
            if not isinstance(content, str):
                raise ValueError("response_content_must_be_string")
            lifecycle.extend(["VERIFIED", "DONE"])
            outcome = "success"
            cooldown_seconds = 0
            retryable = False
    except urllib.error.HTTPError as exc:
        content = None
        if not _is_valid_http_status(exc.code):
            status = None
            outcome = "invalid_provider_response"
            cooldown_seconds = 15
            retryable = False
        elif exc.code == PAYMENT_REQUIRED_STATUS:
            status = exc.code
            lifecycle.append("EXECUTED")
            latches.add(_payment_latch_key(selected, env))
            outcome = "payment_required_hard_stop"
            cooldown_seconds = 0
            retryable = False
        elif exc.code == 429:
            status = exc.code
            lifecycle.append("EXECUTED")
            outcome = "rate_limited"
            cooldown_seconds = 60
            retryable = True
        else:
            status = exc.code
            lifecycle.append("EXECUTED")
            outcome = "provider_error"
            cooldown_seconds = 15
            retryable = True
    except ProviderResponseTooLarge:
        content = None
        outcome = "provider_response_too_large"
        cooldown_seconds = 15
        retryable = False
    except (
        json.JSONDecodeError,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
    ):
        content = None
        outcome = "invalid_provider_response"
        cooldown_seconds = 15
        retryable = False
    except (
        urllib.error.URLError,
        OSError,
        http.client.HTTPException,
    ):
        content = None
        outcome = (
            "incomplete_provider_response"
            if response_started
            else "unreachable_provider"
        )
        cooldown_seconds = 15
        retryable = True

    finished = now()
    body_digest = hashlib.sha256(body).hexdigest()
    request_id = _safe_request_id(
        f"{selected}:{endpoint_capability_id}:"
        f"{cost_policy_principal_id}:{body_digest}"
    )
    receipt_data = {
        "schema_version": "1.1",
        "kind": "FREE_API_EXECUTION_RECEIPT",
        "provider": selected,
        "model": model,
        "endpoint_capability_id": endpoint_capability_id,
        "cost_policy_principal_id": cost_policy_principal_id,
        "budget_epoch_id": _budget_epoch_id(env),
        "request_id": request_id,
        "attempt_id": _safe_attempt_id(
            f"{request_id}:{started}:{attempt_nonce}"
        ),
        "status": status,
        "outcome": outcome,
        "lifecycle": lifecycle,
        "retryable": retryable,
        "cooldown_seconds": cooldown_seconds,
        "payment_latch_active": (
            _payment_latch_key(selected, env) in latches
        ),
        "duration_ms": max(0, round((finished - started) * 1000)),
        "secret_exposed": False,
        "together_accessed": False,
    }
    return {"content": content, "receipt": receipt_data}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("inventory", "route", "receipt"))
    parser.add_argument("--write", type=Path)
    args = parser.parse_args()
    payload = (
        inventory()
        if args.command == "inventory"
        else route()
        if args.command == "route"
        else receipt()
    )
    encoded = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


if __name__ == "__main__":
    main()
