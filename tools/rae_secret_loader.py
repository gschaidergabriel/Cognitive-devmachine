#!/usr/bin/env python3
"""Credential loader for EntityOS/HCU external tools.

Non-provider secret lookup priority:
1. process environment
2. designated private repository credential stores

External LLM credentials are different: the successor-dynamic provider-call boundary
must allow the provider before this module inspects environment or repository secret
stores. Repository fallback is deliberately selective by requested name; callers must
never bulk-materialize a mixed credential store merely to resolve one allowed secret.
This makes direct/legacy callers fail closed during runtime quarantine as well as when
typed FREE admission is absent, without co-materializing unrelated provider values.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DIR = ROOT / "research_entity" / "private"
PRIVATE_STORES = [PRIVATE_DIR / "API_TOKENS.env", PRIVATE_DIR / "GROQ_API.env"]
NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")

PROVIDER_SECRET_NAMES = {
    "GROQ_API_KEY": "groq",
    "GROQ_API_KEYS": "groq",
    "GROQ2_API_KEY": "groq",
    "GROQ3_API_KEY": "groq",
    "MISTRAL_API_KEY": "mistral",
    "MISTRAL_API_KEYS": "mistral",
    "MISTRAL2_API_KEY": "mistral",
    "MISTRAL3_API_KEY": "mistral",
    "NVIDIA_API_KEY": "nvidia",
    "NVIDIA_API_KEYS": "nvidia",
    "NVIDIA_NIM_API_KEY": "nvidia",
    "NGC_API_KEY": "nvidia",
    "NVIDIA2_API_KEY": "nvidia",
    "NVIDIA3_API_KEY": "nvidia",
    "OPENROUTER_API_KEY": "openrouter",
    "OPENROUTER_API_KEYS": "openrouter",
    "HF_TOKEN": "huggingface",
    "HUGGINGFACE_API_KEY": "huggingface",
    "TOGETHER_API_KEY": "together",
}
PROVIDER_SECRET_PATTERNS = (
    (re.compile(r"^GROQ_API_KEY_[0-9]+$"), "groq"),
    (re.compile(r"^MISTRAL_API_KEY_[0-9]+$"), "mistral"),
    (re.compile(r"^NVIDIA_API_KEY_[0-9]+$"), "nvidia"),
    (re.compile(r"^OPENROUTER_API_KEY_[0-9]+$"), "openrouter"),
)


class SecretError(RuntimeError):
    pass


def provider_for_secret_name(name: str) -> str | None:
    provider = PROVIDER_SECRET_NAMES.get(name)
    if provider is not None:
        return provider
    for pattern, candidate in PROVIDER_SECRET_PATTERNS:
        if pattern.fullmatch(name):
            return candidate
    return None


def _provider_secret_is_admitted(name: str) -> bool:
    """Resolve current execution permission without touching the credential value."""
    provider = provider_for_secret_name(name)
    if provider is None:
        return True
    try:
        from provider_call_boundary import provider_call_is_allowed
        return bool(provider_call_is_allowed(provider))
    except Exception:
        return False


def _lookup_repo_secret(name: str) -> tuple[str | None, str | None]:
    """Resolve exactly one repository secret without building a store-wide value map.

    Mixed ``*.env`` stores can contain credentials for providers whose current runtime
    boundary is closed. A dictionary-style parser would materialize every value just to
    answer one allowed lookup. This routine validates record names while retaining only
    the value for ``name`` and checks conflicts only for that requested identity.
    """
    value_found: str | None = None
    source_found: str | None = None
    for path in PRIVATE_STORES:
        if not path.exists():
            continue
        try:
            handle = path.open("r", encoding="utf-8")
        except OSError as exc:
            raise SecretError(f"Cannot open credential store {path.name}: {exc.__class__.__name__}") from exc
        with handle:
            for lineno, raw in enumerate(handle, 1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    raise SecretError(f"Malformed credential-store line {lineno} in {path.name}")
                candidate_name, _, remainder = line.partition("=")
                candidate_name = candidate_name.strip()
                if not NAME_RE.fullmatch(candidate_name):
                    raise SecretError(f"Invalid credential name on line {lineno} in {path.name}")
                if candidate_name != name:
                    # Do not normalize, retain, index, or add an unrelated secret value
                    # to a process-wide dictionary. The shared flat-file format still
                    # requires line-level scanning; application-level value materialization
                    # is limited to the exact already-authorized requested identity.
                    continue
                candidate_value = remainder.strip()
                if value_found is not None and value_found != candidate_value:
                    raise SecretError(f"Credential {name} is defined with conflicting values in private stores")
                value_found = candidate_value
                source_found = path.name
    return value_found, source_found


def get_secret(name: str, *, required: bool = True) -> str | None:
    if not NAME_RE.fullmatch(name):
        raise SecretError(f"Invalid credential name: {name!r}")
    provider = provider_for_secret_name(name)
    if provider is not None and not _provider_secret_is_admitted(name):
        if required:
            raise SecretError(f"Provider credential denied before lookup by current provider-call boundary: {provider}")
        return None
    env_value = os.environ.get(name)
    if env_value:
        return env_value
    value, _ = _lookup_repo_secret(name)
    if value:
        return value
    if required:
        raise SecretError(f"Credential {name} is not configured")
    return None


def secret_source(name: str) -> str | None:
    if not NAME_RE.fullmatch(name):
        raise SecretError(f"Invalid credential name: {name!r}")
    if provider_for_secret_name(name) is not None and not _provider_secret_is_admitted(name):
        return None
    if os.environ.get(name):
        return "process_environment"
    value, source = _lookup_repo_secret(name)
    if value and source:
        return f"private_repo_store:{source}"
    return None


def status(names: Iterable[str]) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for name in names:
        source = secret_source(name)
        provider = provider_for_secret_name(name)
        allowed = _provider_secret_is_admitted(name) if provider is not None else None
        result[name] = {
            "configured": source is not None,
            "source": source,
            "provider": provider,
            "provider_call_boundary_required": provider is not None,
            "provider_call_allowed": allowed,
        }
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="Check credential availability without revealing values")
    ap.add_argument("names", nargs="+")
    args = ap.parse_args()
    print(json.dumps(status(args.names), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
