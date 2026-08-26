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
import math
import os
import secrets
import threading
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse


DENIED_PROVIDERS = frozenset({"together"})
ZERO_COST_ONLY = True
PAYMENT_REQUIRED_STATUS = 402
MAX_PROVIDER_REQUEST_BYTES = 2_000_000
MAX_PROVIDER_RESPONSE_BYTES = 2_000_000
MAX_PROVIDER_OUTPUT_TOKENS = 4_096
MAX_BEARER_TOKEN_CHARACTERS = 8_192
MAX_ATTEMPT_NONCE_CHARACTERS = 128
MAX_PROVIDER_RESPONSE_ID_CHARACTERS = 256
MAX_PROVIDER_SYSTEM_FINGERPRINT_CHARACTERS = 256
MAX_PROVIDER_CREATED_UNIX_SECONDS = 9_999_999_999
MAX_PROVIDER_USAGE_TOKENS = 9_999_999_999
MAX_ZERO_COST_ATTESTATION_CHARACTERS = 1_024
MAX_BUDGET_EPOCH_CHARACTERS = 256
MAX_PROVIDER_BASE_URL_CHARACTERS = 2_048
MAX_LOCAL_TEST_FLAG_CHARACTERS = 1
MAX_PAYMENT_LATCH_ENTRIES = 1_024
# Under the closed alternating schema, 54,792 minimal messages with a leading
# system message occupy 1,999,978 bytes including separators and the smallest
# valid model. The next valid cardinality already exceeds the transport cap.
MAX_TEXT_CHAT_MESSAGES = 54_792
TEXT_CHAT_REQUEST_ENVELOPE_BYTES = 74
TEXT_CHAT_MESSAGE_ENVELOPE_BYTES = 27
JSON_LIST_SEPARATOR_BYTES = 2
MAX_PROVIDER_COOLDOWN_SECONDS = 86_400
MAX_RETRY_AFTER_CHARACTERS = 128
MAX_RECEIPT_DURATION_MS = MAX_PROVIDER_COOLDOWN_SECONDS * 1000
EXECUTION_LOCK_TIMEOUT_SECONDS = 35
TEXT_CHAT_ROLES = frozenset({"system", "user", "assistant"})
TEXT_CHAT_MESSAGE_FIELDS = frozenset({"role", "content"})
TEXT_RESPONSE_CHOICE_REQUIRED_FIELDS = frozenset({"finish_reason", "message"})
TEXT_RESPONSE_USAGE_REQUIRED_FIELDS = frozenset(
    {"prompt_tokens", "completion_tokens", "total_tokens"}
)
TEXT_RESPONSE_USAGE_FIELDS = TEXT_RESPONSE_USAGE_REQUIRED_FIELDS | frozenset(
    {"prompt_tokens_details", "completion_tokens_details"}
)
TEXT_RESPONSE_USAGE_DETAIL_FIELDS = {
    "prompt_tokens_details": ("cached_tokens", "prompt_tokens"),
    "completion_tokens_details": (
        "reasoning_tokens",
        "completion_tokens",
    ),
}
TEXT_RESPONSE_REQUIRED_FIELDS = frozenset(
    {"object", "id", "created", "model", "choices", "usage"}
)
TEXT_RESPONSE_NULL_FIELDS = frozenset(
    {
        "kv_transfer_params",
        "prompt_logprobs",
        "prompt_routed_experts",
        "prompt_text",
        "prompt_token_ids",
    }
)
TEXT_RESPONSE_SERVICE_TIERS = frozenset(
    {"auto", "default", "flex", "scale", "priority"}
)
TEXT_RESPONSE_FIELDS = (
    TEXT_RESPONSE_REQUIRED_FIELDS
    | TEXT_RESPONSE_NULL_FIELDS
    | frozenset({"service_tier", "system_fingerprint"})
)
TEXT_RESPONSE_CHOICE_FIELDS = frozenset(
    {
        "finish_reason",
        "index",
        "logprobs",
        "message",
        "routed_experts",
        "stop_reason",
        "token_ids",
    }
)
TEXT_RESPONSE_MESSAGE_NULL_FIELDS = frozenset(
    {
        "annotations",
        "audio",
        "function_call",
        "refusal",
    }
)
TEXT_RESPONSE_MESSAGE_FIELDS = (
    frozenset({"role", "content", "reasoning", "tool_calls"})
    | TEXT_RESPONSE_MESSAGE_NULL_FIELDS
)
BEARER_TOKEN_CHARACTERS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~+/"
)
PROCESS_PAYMENT_LATCHES: set[str] = set()
PROCESS_EXECUTION_LOCK = threading.Lock()


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

RUNTIME_ENVIRONMENT_KEYS = frozenset(
    {
        "FRANK_ALLOW_LOCAL_TEST_ENDPOINT",
        "FRANK_FREE_ONLY_BUDGET_EPOCH",
        "FRANK_PROVIDER_BASE_URL",
        "FRANK_ZERO_COST_ATTESTED_PROVIDERS",
    }
    | {key_name for spec in PROVIDERS for key_name in spec.key_names}
)
RUNTIME_POLICY_VALUE_MAX_CHARACTERS = {
    "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": MAX_LOCAL_TEST_FLAG_CHARACTERS,
    "FRANK_FREE_ONLY_BUDGET_EPOCH": MAX_BUDGET_EPOCH_CHARACTERS,
    "FRANK_PROVIDER_BASE_URL": MAX_PROVIDER_BASE_URL_CHARACTERS,
    "FRANK_ZERO_COST_ATTESTED_PROVIDERS":
        MAX_ZERO_COST_ATTESTATION_CHARACTERS,
}


def _snapshot_runtime_environment(
    environ: dict[str, str] | None,
) -> dict[str, str]:
    """Capture only recognized runtime inputs before authorization begins."""
    source = os.environ if environ is None else environ
    snapshot: dict[str, str] = {}
    snapshot_failed = False
    try:
        for name in sorted(RUNTIME_ENVIRONMENT_KEYS):
            value = source.get(name)
            if value is None:
                continue
            if type(value) is not str:
                raise ValueError("runtime_environment_values_must_be_strings")
            max_characters = RUNTIME_POLICY_VALUE_MAX_CHARACTERS.get(name)
            if max_characters is not None and len(value) > max_characters:
                raise ValueError("runtime_policy_value_too_large")
            snapshot[name] = value
    except Exception:
        # Environment adapters may include secret material in exception text.
        # Raise only after leaving the handler so no sensitive exception is
        # retained as __context__ or __cause__.
        snapshot_failed = True
    if snapshot_failed:
        raise ValueError("runtime_environment_could_not_be_snapshotted")
    return snapshot


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
        (
            name
            for name in spec.key_names
            if _is_valid_bearer_token(environ.get(name, ""))
        ),
        None,
    )


def _is_valid_bearer_token(value) -> bool:
    """Validate RFC 6750 b64token syntax before header construction."""
    if type(value) is not str or len(value) > MAX_BEARER_TOKEN_CHARACTERS:
        return False
    token = value.rstrip("=")
    return bool(token) and all(
        character in BEARER_TOKEN_CHARACTERS for character in token
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


def _passive_payment_latches(
    payment_latches: set[str] | None,
) -> set[str]:
    """Return latch storage only when membership and mutation are passive."""
    if payment_latches is None:
        payment_latches = PROCESS_PAYMENT_LATCHES
    # Validate a bounded copy rather than iterating caller-owned mutable
    # storage.  The original remains the publication target, while route()
    # independently snapshots the state instant it claims.
    _payment_latch_snapshot(payment_latches)
    return payment_latches


def _payment_latch_snapshot(
    payment_latches: set[str] | None,
) -> set[str]:
    """Return one bounded passive copy for an inventory state claim."""
    if payment_latches is None:
        payment_latches = PROCESS_PAYMENT_LATCHES
    if type(payment_latches) is not set:
        raise ValueError("payment_latches_must_be_set")
    if len(payment_latches) > MAX_PAYMENT_LATCH_ENTRIES:
        raise ValueError("payment_latches_too_large")
    snapshot = payment_latches.copy()
    # Recheck the copied boundary in case the mutable source changed after
    # its passive cardinality preflight but before the bounded copy.
    if len(snapshot) > MAX_PAYMENT_LATCH_ENTRIES:
        raise ValueError("payment_latches_too_large")
    if any(type(latch) is not str for latch in snapshot):
        raise ValueError("payment_latches_must_contain_strings")
    return snapshot


def _try_publish_payment_latch(
    payment_latches: set[str], latch_key: str
) -> bool:
    """Attempt one bounded publication against already selected storage."""
    try:
        before = _payment_latch_snapshot(payment_latches)
        if latch_key in before:
            return True
        if len(before) >= MAX_PAYMENT_LATCH_ENTRIES:
            return False
        payment_latches.add(latch_key)
        after = _payment_latch_snapshot(payment_latches)
        return latch_key in after
    except Exception:
        # The provider response is already execution evidence.  Caller-owned
        # state may have changed while the request was in flight, so latch
        # publication failure must fail closed without suppressing the 402
        # receipt.  Process-control BaseExceptions still propagate.
        return False


def _publish_payment_latch(
    payment_latches: set[str], latch_key: str
) -> tuple[bool, bool]:
    """Publish externally and retain every 402 in process-local hard-stop state."""
    primary_active = _try_publish_payment_latch(payment_latches, latch_key)
    if payment_latches is PROCESS_PAYMENT_LATCHES:
        return primary_active, not primary_active
    fallback_active = _try_publish_payment_latch(
        PROCESS_PAYMENT_LATCHES, latch_key
    )
    return (
        primary_active or fallback_active,
        not (primary_active and fallback_active),
    )


def inventory(
    environ: dict[str, str] | None = None,
    *,
    payment_latches: set[str] | None = None,
) -> list[dict]:
    env = _snapshot_runtime_environment(environ)
    latches = _payment_latch_snapshot(payment_latches)
    if (
        payment_latches is not None
        and payment_latches is not PROCESS_PAYMENT_LATCHES
    ):
        # Failed writes to caller-owned storage are retained in the process
        # fallback.  Merge only bounded, validated copies so later caller
        # repair cannot erase an already observed current-epoch HTTP 402.
        latches.update(_payment_latch_snapshot(PROCESS_PAYMENT_LATCHES))
    # Inventory and route are one state claim. Use one bounded exact-set
    # snapshot so a later latch publication cannot mix two state instants
    # across capacity and per-provider membership fields.
    latch_capacity_exhausted = (
        len(latches) >= MAX_PAYMENT_LATCH_ENTRIES
    )
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
        payment_blocked = bool(
            _payment_latch_key(spec.provider_id, env) in latches
        )
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
                "payment_latch_capacity_exhausted": (
                    latch_capacity_exhausted
                ),
                "eligible_before_payment_latch": eligible_before_latch,
                "eligible": bool(
                    eligible_before_latch
                    and not payment_blocked
                    and not latch_capacity_exhausted
                ),
            }
        )
        rows.append(row)
    return sorted(rows, key=lambda x: (-x["priority"], x["provider_id"]))


def _route_from_inventory(rows: list[dict]) -> dict:
    """Derive routing only from the inventory represented in one receipt."""
    eligible = [row for row in rows if row["eligible"]]
    blocked = [
        row["provider_id"]
        for row in rows
        if row["eligible_before_payment_latch"]
        and row["payment_blocked_current_budget_epoch"]
    ]
    capacity_exhausted = any(
        row["payment_latch_capacity_exhausted"] for row in rows
    )
    capacity_blocks_configured_provider = any(
        row["eligible_before_payment_latch"]
        and row["payment_latch_capacity_exhausted"]
        for row in rows
    )
    if eligible:
        reason = "highest_priority_configured_zero_cost_provider"
    elif blocked:
        reason = "payment_required_hard_stop_active"
    elif capacity_blocks_configured_provider:
        reason = "payment_latch_capacity_exhausted"
    else:
        reason = "no_configured_zero_cost_provider"
    return {
        "selected": eligible[0]["provider_id"] if eligible else None,
        "candidates": [row["provider_id"] for row in eligible],
        "zero_cost_only": ZERO_COST_ONLY,
        "denied_providers": sorted(DENIED_PROVIDERS),
        "payment_blocked_providers": blocked,
        "payment_latch_capacity_exhausted": capacity_exhausted,
        "reason": reason,
    }


def route(
    environ: dict[str, str] | None = None,
    *,
    payment_latches: set[str] | None = None,
) -> dict:
    rows = inventory(environ, payment_latches=payment_latches)
    return _route_from_inventory(rows)


def receipt() -> dict:
    # Inventory and route are one capability claim. Snapshot mutable process
    # inputs once and derive the route from those exact inventory rows so a
    # concurrent environment change cannot produce a contradictory receipt.
    env = _snapshot_runtime_environment(None)
    rows = inventory(env)
    return {
        "schema_version": "1.1",
        "kind": "FREE_API_CAPABILITY_RECEIPT",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "inventory": rows,
        "route": _route_from_inventory(rows),
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


def _is_unicode_scalar_text(value) -> bool:
    """Reject lone UTF-16 surrogates that are not Unicode characters."""
    return type(value) is str and not any(
        0xD800 <= ord(character) <= 0xDFFF for character in value
    )


def _ascii_json_string_payload_size(value: str, stop_after: int) -> int:
    """Count default json.dumps string payload bytes without materializing."""
    total = 0
    for character in value:
        codepoint = ord(character)
        if character in '"\\\b\f\n\r\t':
            total += 2
        elif codepoint <= 0x1F:
            total += 6
        elif codepoint < 0x7F:
            total += 1
        elif codepoint <= 0xFFFF:
            total += 6
        else:
            total += 12
        if total > stop_after:
            return total
    return total


def _enforce_pre_serialization_request_bound(
    messages: tuple[dict[str, str], ...], model: str
) -> None:
    """Reject requests whose exact default JSON size exceeds the byte cap."""
    serialized_size = TEXT_CHAT_REQUEST_ENVELOPE_BYTES
    serialized_size += _ascii_json_string_payload_size(
        model, MAX_PROVIDER_REQUEST_BYTES
    )
    for index, message in enumerate(messages):
        # json.dumps defaults to ensure_ascii=True and separators containing
        # one space. Count both its exact scalar escapes and fixed structure.
        serialized_size += TEXT_CHAT_MESSAGE_ENVELOPE_BYTES
        if index:
            serialized_size += JSON_LIST_SEPARATOR_BYTES
        if serialized_size > MAX_PROVIDER_REQUEST_BYTES:
            raise ValueError("provider_request_too_large")
        serialized_size += _ascii_json_string_payload_size(
            message["role"], MAX_PROVIDER_REQUEST_BYTES - serialized_size
        )
        if serialized_size > MAX_PROVIDER_REQUEST_BYTES:
            raise ValueError("provider_request_too_large")
        serialized_size += _ascii_json_string_payload_size(
            message["content"], MAX_PROVIDER_REQUEST_BYTES - serialized_size
        )
        if serialized_size > MAX_PROVIDER_REQUEST_BYTES:
            raise ValueError("provider_request_too_large")


def _enforce_pre_lock_text_size_lower_bound(messages, model) -> None:
    """Reject proven oversize from passive scalar lengths before locking."""
    total_characters = len(model) if type(model) is str else 0
    if total_characters > MAX_PROVIDER_REQUEST_BYTES:
        raise ValueError("provider_request_too_large")
    if type(messages) is not list:
        return
    for message in messages:
        if type(message) is not dict:
            continue
        for value in message.values():
            if type(value) is str:
                total_characters += len(value)
                if total_characters > MAX_PROVIDER_REQUEST_BYTES:
                    raise ValueError("provider_request_too_large")


def _enforce_pre_snapshot_message_bound(messages) -> None:
    """Reject structurally impossible requests before copying caller data."""
    # Only exact lists have passive built-in len behavior at this boundary.
    # Other types retain the existing fail-closed schema validation path.
    if type(messages) is not list:
        return
    if len(messages) > MAX_TEXT_CHAT_MESSAGES:
        raise ValueError("provider_request_too_large")
    # Exact dict len is passive and the closed text schema permits exactly two
    # members. Reject impossible wide objects before dict(message) duplicates
    # caller-owned storage under the execution lock.
    if any(
        type(message) is dict and len(message) != len(TEXT_CHAT_MESSAGE_FIELDS)
        for message in messages
    ):
        raise ValueError("message_fields_not_supported_by_text_adapter")


def _transport_metadata_or_none(response, attribute):
    """Treat transport-provided properties as untrusted metadata."""
    try:
        return getattr(response, attribute, None)
    except Exception:
        return None


def _retry_after_seconds(headers, received_at: float, default: int = 60) -> int:
    """Parse RFC Retry-After delay-seconds or HTTP-date, else use default."""
    if type(received_at) not in (int, float):
        return default
    if type(received_at) is float and not math.isfinite(received_at):
        return default
    try:
        value = headers.get("Retry-After") if headers is not None else None
    # Header containers cross the transport-adapter boundary.  Their lookup
    # must not suppress a status receipt that was already received.
    except Exception:
        return default
    # Header values are foreign adapter data.  A str subclass can override
    # strip() and must not run code after an HTTP status was already received.
    if type(value) is not str:
        return default
    # RFC 9110 permits only delay-seconds or an HTTP-date. Reject an impossible
    # envelope before normalization or date parsing so already-received 429
    # evidence does not trigger unbounded work on foreign adapter metadata.
    if len(value) > MAX_RETRY_AFTER_CHARACTERS:
        return default
    value = value.strip()
    if value and all("0" <= character <= "9" for character in value):
        try:
            return min(int(value), MAX_PROVIDER_COOLDOWN_SECONDS)
        except ValueError:
            return default
    try:
        retry_at = parsedate_to_datetime(value)
        if retry_at.tzinfo is None:
            return default
        return min(
            max(0, math.ceil(retry_at.timestamp() - received_at)),
            MAX_PROVIDER_COOLDOWN_SECONDS,
        )
    except (OverflowError, TypeError, ValueError):
        return default


def _validate_text_chat_request(messages, model) -> None:
    if type(model) is not str or not model.strip():
        raise ValueError("model_must_be_nonempty_string")
    if not _is_unicode_scalar_text(model):
        raise ValueError("model_must_be_unicode_scalar_string")
    if model != model.strip():
        raise ValueError("model_must_match_served_identifier_exactly")
    if type(messages) is not list:
        raise ValueError("messages_must_be_list")
    if not messages:
        raise ValueError("messages_must_be_nonempty")
    for message in messages:
        if type(message) is not dict:
            raise ValueError("message_must_be_object")
        if any(type(field) is not str for field in message):
            raise ValueError("message_fields_must_be_strings")
        if set(message) != TEXT_CHAT_MESSAGE_FIELDS:
            raise ValueError("message_fields_not_supported_by_text_adapter")
        if type(message.get("role")) is not str or not message["role"].strip():
            raise ValueError("message_role_must_be_nonempty_string")
        if not _is_unicode_scalar_text(message["role"]):
            raise ValueError("message_role_must_be_unicode_scalar_string")
        if message["role"] not in TEXT_CHAT_ROLES:
            raise ValueError("message_role_not_supported_by_text_adapter")
        if type(message.get("content")) is not str:
            raise ValueError("message_content_must_be_string")
        if not _is_unicode_scalar_text(message["content"]):
            raise ValueError("message_content_must_be_unicode_scalar_string")
        if not message["content"].strip():
            raise ValueError("message_content_must_be_nonempty_string")

    if messages[-1]["role"] != "user":
        raise ValueError("conversation_must_end_with_user")

    conversation = messages
    if messages[0]["role"] == "system":
        conversation = messages[1:]
    if any(message["role"] == "system" for message in conversation):
        raise ValueError("system_message_must_be_first")

    expected_role = "user"
    for message in conversation:
        if message["role"] != expected_role:
            raise ValueError("conversation_roles_must_alternate")
        expected_role = "assistant" if expected_role == "user" else "user"


def _snapshot_text_chat_request(messages, model) -> list[dict[str, str]]:
    """Copy mutable caller input once, then validate and use only that copy."""
    # The caller can mutate an exact list after execute_chat's early admission
    # check but before this use. Recheck at the snapshot boundary so that a
    # TOCTOU growth cannot allocate an impossible full copy under the lock.
    _enforce_pre_snapshot_message_bound(messages)
    if type(messages) is not list:
        _validate_text_chat_request(messages, model)
    snapshot_failed = False
    try:
        snapshot = [
            dict(message) if type(message) is dict else message
            for message in tuple(messages)
        ]
    except Exception:
        snapshot_failed = True
    if snapshot_failed:
        raise ValueError("messages_could_not_be_snapshotted")
    _validate_text_chat_request(snapshot, model)
    return snapshot


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject redirects so bearer credentials cannot cross an origin boundary."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ProviderResponseTooLarge(ValueError):
    """The provider response exceeded the bounded adapter's byte limit."""


class ProviderOutputTruncated(ValueError):
    """The provider explicitly stopped because its output limit was reached."""


class ProviderReportedError(ValueError):
    """A syntactically valid HTTP 200 body explicitly reports an error."""


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
    # Status metadata is supplied by a foreign transport adapter.  Reject int
    # subclasses before comparison operators can execute adapter code.
    return type(value) is int and 100 <= value <= 599


def _passive_clock_value_or_none(clock):
    """Read an injected clock without retaining active numeric objects."""
    try:
        value = clock()
    except Exception:
        return None
    if type(value) is int:
        return value
    if type(value) is float and math.isfinite(value):
        return value
    return None


def _bounded_duration_ms(started, finished) -> int:
    """Keep duration telemetry total and bounded for passive clock values."""
    if finished <= started:
        return 0
    try:
        elapsed = finished - started
    except OverflowError:
        return MAX_RECEIPT_DURATION_MS
    if type(elapsed) is float and not math.isfinite(elapsed):
        return MAX_RECEIPT_DURATION_MS
    if elapsed >= MAX_RECEIPT_DURATION_MS / 1000:
        return MAX_RECEIPT_DURATION_MS
    return round(elapsed * 1000)


def _reject_nonfinite_json_constant(value: str) -> None:
    raise ValueError(f"nonstandard_json_constant:{value}")


def _parse_finite_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("json_float_out_of_range")
    return parsed


def _reject_duplicate_json_names(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate_json_name")
        result[name] = value
    return result


def execute_chat(
    messages: list[dict[str, str]],
    *,
    model: str,
    environ: dict[str, str] | None = None,
    opener=None,
    now=time.monotonic,
    wall_time=time.time,
    nonce_factory=None,
    payment_latches: set[str] | None = None,
) -> dict:
    """Serialize authorization through receipt so payment latches are atomic."""
    _enforce_pre_snapshot_message_bound(messages)
    _enforce_pre_lock_text_size_lower_bound(messages, model)
    acquired = PROCESS_EXECUTION_LOCK.acquire(
        timeout=EXECUTION_LOCK_TIMEOUT_SECONDS
    )
    if not acquired:
        raise RuntimeError("execution_busy")
    try:
        return _execute_chat_locked(
            messages,
            model=model,
            environ=environ,
            opener=opener,
            now=now,
            wall_time=wall_time,
            nonce_factory=nonce_factory,
            payment_latches=payment_latches,
        )
    finally:
        PROCESS_EXECUTION_LOCK.release()


def _execute_chat_locked(
    messages: list[dict[str, str]],
    *,
    model: str,
    environ: dict[str, str] | None = None,
    opener=None,
    now=time.monotonic,
    wall_time=time.time,
    nonce_factory=None,
    payment_latches: set[str] | None = None,
) -> dict:
    """Execute one bounded chat request and return output plus a redacted receipt."""
    request_messages = _snapshot_text_chat_request(messages, model)
    _enforce_pre_serialization_request_bound(request_messages, model)
    body = json.dumps(
        {
            "model": model,
            "messages": request_messages,
            "stream": False,
            "n": 1,
            "max_tokens": MAX_PROVIDER_OUTPUT_TOKENS,
        },
        ensure_ascii=True,
    ).encode()
    if len(body) > MAX_PROVIDER_REQUEST_BYTES:
        raise ValueError("provider_request_too_large")
    env = _snapshot_runtime_environment(environ)
    latches = _passive_payment_latches(payment_latches)
    route_state = route(env, payment_latches=latches)
    selected = route_state["selected"]
    if not selected:
        if route_state["reason"] == "payment_required_hard_stop_active":
            raise RuntimeError("payment_required_hard_stop_active")
        if route_state["reason"] == "payment_latch_capacity_exhausted":
            raise RuntimeError("payment_latch_capacity_exhausted")
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
    if type(attempt_nonce) is not str or not attempt_nonce:
        raise ValueError("attempt_nonce_must_be_nonempty_string")
    if not _is_unicode_scalar_text(attempt_nonce):
        raise ValueError("attempt_nonce_must_be_unicode_scalar_string")
    if len(attempt_nonce) > MAX_ATTEMPT_NONCE_CHARACTERS:
        raise ValueError("attempt_nonce_too_large")

    started = _passive_clock_value_or_none(now)
    if started is None:
        raise RuntimeError("monotonic_clock_unavailable")

    # Injected nonce and clock functions are executable caller code. They run
    # after the first authorization decision and can mutate caller-owned latch
    # storage. Re-evaluate after the last such pre-network callback so a newly
    # published hard stop or exhausted latch budget cannot be outrun.
    pre_network_route = route(env, payment_latches=latches)
    if selected in pre_network_route["payment_blocked_providers"]:
        raise RuntimeError("payment_required_hard_stop_active")
    if pre_network_route["payment_latch_capacity_exhausted"]:
        raise RuntimeError("payment_latch_capacity_exhausted")
    if pre_network_route["selected"] != selected:
        raise RuntimeError("capability_state_changed_before_network")

    lifecycle = ["REQUESTED", "AUTHORIZED", "CLAIMED"]
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
    response_headers = None
    response_classified = False
    response_too_large = False
    response_context_error = None
    retryable = False
    finished = None
    payment_latch_active = False
    payment_latch_publication_failed = False
    provider_response_id_sha256 = None
    provider_reasoning_characters = None
    provider_reasoning_sha256 = None
    provider_service_tier = None
    provider_system_fingerprint_sha256 = None
    provider_created_unix_seconds = None
    provider_usage = None

    try:
        try:
            with request_opener(request, timeout=30) as response:
                try:
                    candidate_status = _transport_metadata_or_none(
                        response, "status"
                    )
                    if not _is_valid_http_status(candidate_status):
                        raise ValueError("response_status_must_be_http_integer")
                    status = candidate_status
                    response_started = True
                    response_headers = _transport_metadata_or_none(
                        response, "headers"
                    )
                    lifecycle.append("EXECUTED")
                    if status == 200:
                        response_body = response.read(
                            MAX_PROVIDER_RESPONSE_BYTES + 1
                        )
                        # HTTP body values are foreign adapter data.  Reject
                        # bytes subclasses before len/decode can dispatch to
                        # overridden methods.
                        if type(response_body) is not bytes:
                            raise TypeError("response_body_must_be_bytes")
                        if len(response_body) > MAX_PROVIDER_RESPONSE_BYTES:
                            response_too_large = True
                    else:
                        finished = _passive_clock_value_or_none(now)
                        content = None
                        if status == 202:
                            outcome = "provider_result_pending"
                            cooldown_seconds = 0
                            retryable = False
                        elif 200 <= status <= 299:
                            outcome = "unexpected_success_status"
                            cooldown_seconds = 0
                            retryable = False
                        elif status == PAYMENT_REQUIRED_STATUS:
                            outcome = "payment_required_hard_stop"
                            cooldown_seconds = 0
                            retryable = False
                        elif status == 429:
                            outcome = "rate_limited"
                            cooldown_seconds = _retry_after_seconds(
                                response_headers,
                                _passive_clock_value_or_none(wall_time),
                            )
                            retryable = False
                        else:
                            outcome = "provider_error"
                            cooldown_seconds = 15
                            retryable = False
                        response_classified = True
                except BaseException as exc:
                    # Do not expose suite failures to a foreign __exit__: a
                    # true return would suppress both receipt evidence and
                    # process-control signals. BaseException is transported
                    # across cleanup, then immediately re-raised unchanged.
                    response_context_error = exc
        except Exception:
            if (
                not response_classified
                and not response_too_large
                and response_context_error is None
            ):
                raise
        if response_context_error is not None:
            raise response_context_error
        if response_classified and status == PAYMENT_REQUIRED_STATUS:
            # Foreign response cleanup runs after the suite and can mutate
            # caller-owned or process-local latch state. Publish only after
            # leaving that context so cleanup cannot erase an acknowledged
            # payment hard stop while its receipt still claims it is active.
            (
                payment_latch_active,
                payment_latch_publication_failed,
            ) = _publish_payment_latch(
                latches, _payment_latch_key(selected, env)
            )
        if response_too_large:
            raise ProviderResponseTooLarge
        if status == 200:
            payload = json.loads(
                response_body.decode("utf-8"),
                parse_constant=_reject_nonfinite_json_constant,
                parse_float=_parse_finite_json_float,
                object_pairs_hook=_reject_duplicate_json_names,
            )
            if type(payload) is dict and (
                payload.get("object") == "error" or "error" in payload
            ):
                raise ProviderReportedError
            if type(payload) is not dict:
                raise ValueError("response_must_be_object")
            payload_fields = set(payload)
            if (
                not TEXT_RESPONSE_REQUIRED_FIELDS.issubset(payload_fields)
                or not payload_fields.issubset(TEXT_RESPONSE_FIELDS)
            ):
                raise ValueError("response_top_level_fields_not_supported")
            if any(payload[field] is not None for field in (
                TEXT_RESPONSE_NULL_FIELDS & payload_fields
            )):
                raise ValueError("response_top_level_metadata_not_passive")
            system_fingerprint = payload.get("system_fingerprint")
            if system_fingerprint is not None:
                if (
                    not _is_unicode_scalar_text(system_fingerprint)
                    or not system_fingerprint
                    or len(system_fingerprint)
                    > MAX_PROVIDER_SYSTEM_FINGERPRINT_CHARACTERS
                ):
                    raise ValueError(
                        "response_system_fingerprint_must_be_bounded_unicode_string"
                    )
                provider_system_fingerprint_sha256 = hashlib.sha256(
                    system_fingerprint.encode("utf-8")
                ).hexdigest()
            service_tier = payload.get("service_tier")
            if service_tier is not None:
                if (
                    type(service_tier) is not str
                    or service_tier not in TEXT_RESPONSE_SERVICE_TIERS
                ):
                    raise ValueError("response_service_tier_not_supported")
                provider_service_tier = service_tier
            if (
                "object" not in payload
                or type(payload["object"]) is not str
                or payload["object"] != "chat.completion"
            ):
                raise ValueError("response_object_must_be_chat_completion")
            if (
                "id" not in payload
                or not _is_unicode_scalar_text(payload["id"])
                or not payload["id"]
                or len(payload["id"]) > MAX_PROVIDER_RESPONSE_ID_CHARACTERS
            ):
                raise ValueError("response_id_must_be_bounded_unicode_string")
            provider_response_id_sha256 = hashlib.sha256(
                payload["id"].encode("utf-8")
            ).hexdigest()
            if (
                "created" not in payload
                or type(payload["created"]) is not int
                or not 0 <= payload["created"] <= MAX_PROVIDER_CREATED_UNIX_SECONDS
            ):
                raise ValueError("response_created_must_be_bounded_unix_seconds")
            provider_created_unix_seconds = payload["created"]
            if (
                "model" not in payload
                or type(payload["model"]) is not str
                or payload["model"] != model
            ):
                raise ValueError("response_model_must_match_request")
            if "usage" not in payload or type(payload["usage"]) is not dict:
                raise ValueError("response_usage_must_be_object")
            usage = payload["usage"]
            usage_fields = set(usage)
            if (
                not TEXT_RESPONSE_USAGE_REQUIRED_FIELDS.issubset(usage_fields)
                or not usage_fields.issubset(TEXT_RESPONSE_USAGE_FIELDS)
            ):
                raise ValueError("response_usage_fields_not_supported")
            for token_field in TEXT_RESPONSE_USAGE_REQUIRED_FIELDS:
                token_count = usage[token_field]
                if (
                    type(token_count) is not int
                    or not 0 <= token_count <= MAX_PROVIDER_USAGE_TOKENS
                ):
                    raise ValueError("response_usage_must_be_bounded_integer")
            if usage["total_tokens"] != (
                usage["prompt_tokens"] + usage["completion_tokens"]
            ):
                raise ValueError("response_usage_total_must_match_components")
            provider_usage = {
                field: usage[field]
                for field in (
                    "prompt_tokens",
                    "completion_tokens",
                    "total_tokens",
                )
            }
            for detail_field, (
                detail_count_field,
                parent_count_field,
            ) in TEXT_RESPONSE_USAGE_DETAIL_FIELDS.items():
                details = usage.get(detail_field)
                if details is None:
                    continue
                if (
                    type(details) is not dict
                    or set(details) != {detail_count_field}
                ):
                    raise ValueError("response_usage_details_not_supported")
                detail_count = details[detail_count_field]
                if (
                    type(detail_count) is not int
                    or not 0 <= detail_count <= usage[parent_count_field]
                ):
                    raise ValueError(
                        "response_usage_detail_must_fit_parent_count"
                    )
                provider_usage[detail_field] = {
                    detail_count_field: detail_count
                }
            choices = payload["choices"]
            if not isinstance(choices, list) or len(choices) != 1:
                raise ValueError("response_choices_must_contain_exactly_one_choice")
            choice = choices[0]
            if not isinstance(choice, dict):
                raise ValueError("response_choice_must_be_object")
            choice_fields = set(choice)
            if (
                not TEXT_RESPONSE_CHOICE_REQUIRED_FIELDS.issubset(choice_fields)
                or not choice_fields.issubset(TEXT_RESPONSE_CHOICE_FIELDS)
            ):
                raise ValueError(
                    "response_choice_fields_not_supported_by_text_adapter"
                )
            if (
                "index" not in choice
                or type(choice["index"]) is not int
                or choice["index"] != 0
            ):
                raise ValueError("response_choice_index_not_supported")
            for metadata_field in (
                "logprobs",
                "routed_experts",
                "stop_reason",
                "token_ids",
            ):
                if choice.get(metadata_field) is not None:
                    raise ValueError(
                        "response_choice_metadata_not_supported_by_text_adapter"
                    )
            finish_reason = choice.get("finish_reason")
            if finish_reason == "length":
                raise ProviderOutputTruncated
            if finish_reason != "stop":
                raise ValueError("response_finish_reason_not_supported")
            message = choice["message"]
            if not isinstance(message, dict):
                raise ValueError("response_message_must_be_object")
            if not set(message).issubset(TEXT_RESPONSE_MESSAGE_FIELDS):
                raise ValueError("response_fields_not_supported_by_text_adapter")
            for metadata_field in TEXT_RESPONSE_MESSAGE_NULL_FIELDS:
                if message.get(metadata_field) is not None:
                    raise ValueError(
                        "response_message_metadata_not_supported_by_text_adapter"
                    )
            reasoning = message.get("reasoning")
            if reasoning is not None:
                if (
                    not _is_unicode_scalar_text(reasoning)
                    or not reasoning
                    or len(reasoning) > MAX_PROVIDER_RESPONSE_BYTES
                ):
                    raise ValueError(
                        "response_reasoning_must_be_bounded_unicode_string"
                    )
                reasoning_usage = provider_usage.get(
                    "completion_tokens_details"
                )
                if (
                    reasoning_usage is None
                    or reasoning_usage["reasoning_tokens"] == 0
                ):
                    raise ValueError(
                        "response_reasoning_requires_token_provenance"
                    )
                if (
                    reasoning_usage["reasoning_tokens"]
                    >= provider_usage["completion_tokens"]
                ):
                    raise ValueError(
                        "response_reasoning_must_leave_visible_token"
                    )
                provider_reasoning_characters = len(reasoning)
                provider_reasoning_sha256 = hashlib.sha256(
                    reasoning.encode("utf-8")
                ).hexdigest()
            if "tool_calls" in message and (
                type(message["tool_calls"]) is not list
                or message["tool_calls"]
            ):
                raise ValueError("response_tool_calls_require_typed_adapter")
            if message.get("role") != "assistant":
                raise ValueError("response_role_must_be_assistant")
            content = message["content"]
            if not _is_unicode_scalar_text(content):
                raise ValueError("response_content_must_be_unicode_scalar_string")
            if not content.strip():
                raise ValueError("response_content_must_be_nonempty_string")
            lifecycle.extend(["VERIFIED", "DONE"])
            outcome = "success"
            cooldown_seconds = 0
            retryable = False
    except urllib.error.HTTPError as exc:
        content = None
        finished = _passive_clock_value_or_none(now)
        candidate_status = _transport_metadata_or_none(exc, "code")
        if not _is_valid_http_status(candidate_status):
            status = None
            outcome = "invalid_provider_response"
            cooldown_seconds = 15
            retryable = False
        elif candidate_status == PAYMENT_REQUIRED_STATUS:
            status = candidate_status
            lifecycle.append("EXECUTED")
            (
                payment_latch_active,
                payment_latch_publication_failed,
            ) = _publish_payment_latch(
                latches, _payment_latch_key(selected, env)
            )
            outcome = "payment_required_hard_stop"
            cooldown_seconds = 0
            retryable = False
        elif candidate_status == 429:
            status = candidate_status
            lifecycle.append("EXECUTED")
            outcome = "rate_limited"
            cooldown_seconds = _retry_after_seconds(
                _transport_metadata_or_none(exc, "headers"),
                _passive_clock_value_or_none(wall_time),
            )
            retryable = False
        else:
            status = candidate_status
            lifecycle.append("EXECUTED")
            outcome = "provider_error"
            cooldown_seconds = 15
            retryable = False
    except ProviderResponseTooLarge:
        content = None
        outcome = "provider_response_too_large"
        cooldown_seconds = 15
        retryable = False
    except ProviderOutputTruncated:
        content = None
        outcome = "provider_output_truncated"
        cooldown_seconds = 0
        retryable = False
    except ProviderReportedError:
        content = None
        outcome = "provider_error"
        cooldown_seconds = 15
        retryable = False
    except (
        json.JSONDecodeError,
        KeyError,
        IndexError,
        RecursionError,
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
        retryable = False
    except Exception:
        # Custom transport adapters are not constrained to urllib's exception
        # hierarchy. Fail closed with a receipt without catching BaseException.
        content = None
        outcome = (
            "incomplete_provider_response"
            if response_started
            else "unreachable_provider"
        )
        cooldown_seconds = 15
        retryable = False

    if finished is None:
        finished = _passive_clock_value_or_none(now)
    if finished is None:
        # Execution evidence is more important than duration telemetry.  A
        # failed post-response clock read must not suppress the receipt.
        finished = started
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
        "provider_response_id_sha256": provider_response_id_sha256,
        "provider_reasoning_characters": provider_reasoning_characters,
        "provider_reasoning_sha256": provider_reasoning_sha256,
        "provider_service_tier": provider_service_tier,
        "provider_system_fingerprint_sha256": (
            provider_system_fingerprint_sha256
        ),
        "provider_created_unix_seconds": provider_created_unix_seconds,
        "provider_usage": provider_usage,
        "attempt_id": _safe_attempt_id(
            # The nonce supplies attempt uniqueness.  Keeping an unbounded
            # injected integer clock out of string formatting prevents a
            # successful execution from losing its mandatory receipt.
            f"{request_id}:{attempt_nonce}"
        ),
        "status": status,
        "outcome": outcome,
        "lifecycle": lifecycle,
        "retryable": retryable,
        "cooldown_seconds": cooldown_seconds,
        "payment_latch_active": payment_latch_active,
        "payment_latch_publication_failed": (
            payment_latch_publication_failed
        ),
        "duration_ms": _bounded_duration_ms(started, finished),
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
