#!/usr/bin/env python3
"""Zero-cost provider discovery and policy for Clay/FRANK.

This module never prints secrets and never performs paid calls. Together is a
hard-denied provider and is intentionally absent from discovery and routing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path


DENIED_PROVIDERS = frozenset({"together"})
ZERO_COST_ONLY = True
@dataclass(frozen=True)
class ProviderSpec:
    provider_id: str
    key_names: tuple[str, ...]
    priority: int
    openai_compatible_base_url: str
    free_or_prepaid_only: bool = True
    zero_cost_evidence: str | None = None


PROVIDERS = (
    ProviderSpec("nvidia", ("NVIDIA_API_KEY", "NVCF_API_KEY"), 100,
                 "https://integrate.api.nvidia.com/v1", True,
                 "nvidia_developer_program_free_prototype_endpoint"),
    ProviderSpec("groq", ("GROQ_API_KEY",), 80, "https://api.groq.com/openai/v1"),
    ProviderSpec("cerebras", ("CEREBRAS_API_KEY",), 75,
                 "https://api.cerebras.ai/v1"),
    ProviderSpec("gemini", ("GEMINI_API_KEY", "GOOGLE_API_KEY"), 70,
                 "https://generativelanguage.googleapis.com/v1beta/openai"),
    ProviderSpec("openrouter", ("OPENROUTER_API_KEY",), 50,
                 "https://openrouter.ai/api/v1"),
)


def _attested_zero_cost_providers(environ: dict[str, str]) -> set[str]:
    """Return explicitly operator-attested zero-cost provider IDs.

    A key proves configuration, not billing state.  Non-NVIDIA providers therefore
    fail closed unless the execution host explicitly attests that its account/project
    is on a zero-cost plan.  The attestation contains provider IDs only, never secrets.
    """
    raw = environ.get("FRANK_ZERO_COST_ATTESTED_PROVIDERS", "")
    return {
        provider_id.strip().lower()
        for provider_id in raw.split(",")
        if provider_id.strip() and provider_id.strip().lower() not in DENIED_PROVIDERS
    }


def _configured_key_name(spec: ProviderSpec, environ: dict[str, str]) -> str | None:
    return next((name for name in spec.key_names if environ.get(name, "").strip()), None)


def inventory(environ: dict[str, str] | None = None) -> list[dict]:
    env = os.environ if environ is None else environ
    attested = _attested_zero_cost_providers(env)
    rows = []
    for spec in PROVIDERS:
        if spec.provider_id in DENIED_PROVIDERS:
            continue
        key_name = _configured_key_name(spec, env)
        zero_cost_evidence = spec.zero_cost_evidence
        if spec.provider_id in attested:
            zero_cost_evidence = "operator_zero_cost_attestation"
        row = asdict(spec)
        row["key_names"] = list(spec.key_names)
        row.update({
            "configured": key_name is not None,
            "configured_via": key_name,
            "secret_exposed": False,
            "zero_cost_assured": zero_cost_evidence is not None,
            "zero_cost_evidence": zero_cost_evidence,
            "eligible": bool(key_name and zero_cost_evidence and ZERO_COST_ONLY),
        })
        rows.append(row)
    return sorted(rows, key=lambda x: (-x["priority"], x["provider_id"]))


def route(environ: dict[str, str] | None = None) -> dict:
    eligible = [row for row in inventory(environ) if row["eligible"]]
    return {
        "selected": eligible[0]["provider_id"] if eligible else None,
        "candidates": [row["provider_id"] for row in eligible],
        "zero_cost_only": ZERO_COST_ONLY,
        "denied_providers": sorted(DENIED_PROVIDERS),
        "reason": "highest_priority_configured_zero_cost_provider" if eligible
                  else "no_configured_zero_cost_provider",
    }


def receipt() -> dict:
    return {
        "schema_version": "1.0",
        "kind": "FREE_API_CAPABILITY_RECEIPT",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "inventory": inventory(),
        "route": route(),
        "invariants": {
            "secrets_never_serialized": True,
            "paid_calls_forbidden": True,
            "together_access_forbidden": True,
            "network_probe_performed": False,
        },
    }


def _safe_request_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject redirects so bearer credentials cannot cross an origin boundary."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _open_no_redirect(request: urllib.request.Request, timeout: int):
    return urllib.request.build_opener(_NoRedirectHandler()).open(request, timeout=timeout)


def execute_chat(
    messages: list[dict[str, str]],
    *,
    model: str,
    environ: dict[str, str] | None = None,
    opener=None,
    now=time.time,
) -> dict:
    """Execute one bounded chat request and return output plus a redacted receipt.

    The injectable opener makes the full lifecycle testable without an external API.
    Remote execution is limited to policy-listed provider hosts. A localhost override is
    accepted only when FRANK_ALLOW_LOCAL_TEST_ENDPOINT=1.
    """
    env = os.environ if environ is None else environ
    selected = route(env)["selected"]
    if not selected:
        raise RuntimeError("no_configured_zero_cost_provider")
    spec = next(item for item in PROVIDERS if item.provider_id == selected)
    key_name = _configured_key_name(spec, env)
    base_url = env.get("FRANK_PROVIDER_BASE_URL", spec.openai_compatible_base_url).rstrip("/")
    from urllib.parse import urlparse
    parsed = urlparse(base_url)
    provider_host = urlparse(spec.openai_compatible_base_url).hostname
    local_test = parsed.hostname in {"127.0.0.1", "localhost"} and env.get(
        "FRANK_ALLOW_LOCAL_TEST_ENDPOINT"
    ) == "1"
    if parsed.scheme != "https" and not local_test:
        raise RuntimeError("provider_endpoint_must_use_https")
    if parsed.hostname != provider_host and not local_test:
        raise RuntimeError("provider_endpoint_not_bound_to_selected_provider")

    started = now()
    lifecycle = ["REQUESTED", "AUTHORIZED", "CLAIMED"]
    body = json.dumps({"model": model, "messages": messages, "stream": False}).encode()
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {env[key_name]}", "Content-Type": "application/json"},
        method="POST",
    )
    request_opener = _open_no_redirect if opener is None else opener
    try:
        with request_opener(request, timeout=30) as response:
            response_body = response.read(2_000_000)
            status = getattr(response, "status", 200)
        lifecycle.append("EXECUTED")
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
    except urllib.error.HTTPError as exc:
        lifecycle.append("EXECUTED")
        status = exc.code
        content = None
        outcome = "rate_limited" if status == 429 else "provider_error"
        cooldown_seconds = 60 if status == 429 else 15
    except (
        json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError,
    ):
        content = None
        outcome = "invalid_provider_response"
        cooldown_seconds = 15
    except (urllib.error.URLError, TimeoutError):
        status = None
        content = None
        outcome = "unreachable_provider"
        cooldown_seconds = 15

    finished = now()
    body_digest = hashlib.sha256(body).hexdigest()
    request_id = _safe_request_id(f"{selected}:{parsed.hostname}:{body_digest}")
    receipt_data = {
        "schema_version": "1.0",
        "kind": "FREE_API_EXECUTION_RECEIPT",
        "provider": selected,
        "model": model,
        "endpoint_host": parsed.hostname,
        "request_id": request_id,
        "attempt_id": _safe_request_id(f"{request_id}:{started}"),
        "status": status,
        "outcome": outcome,
        "lifecycle": lifecycle,
        "cooldown_seconds": cooldown_seconds,
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
    payload = inventory() if args.command == "inventory" else route() if args.command == "route" else receipt()
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


if __name__ == "__main__":
    main()
