#!/usr/bin/env python3
"""Credential loader for FRANK/RAE external tools.

Lookup priority for non-provider secrets:
1. process environment
2. designated private repository credential stores

External LLM-provider credentials are different: the canonical EntityOS/HCU typed
FREE provider admission must allow the provider *before* this module inspects the
process environment or repository credential stores for that provider. This gives
legacy/direct callers the same fail-closed pre-secret boundary as the guarded swarm
and distillery entrypoints.

The loader never prints secret values. Runtime secret managers can inject process
environment variables and therefore automatically take priority over repo fallbacks
only after the provider has been admitted FREE.
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
PRIVATE_STORES = [
    PRIVATE_DIR / "API_TOKENS.env",
    PRIVATE_DIR / "GROQ_API.env",
]
NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")

# Credential-name -> canonical typed provider identity. Keep this deliberately
# narrow: non-LLM tool credentials are not silently reclassified as LLM providers.
# Providers absent from the canonical admission allowlist intentionally fail closed.
PROVIDER_SECRET_NAMES = {
    "GROQ_API_KEY": "groq",
    "GROQ_API_KEYS": "groq",
    "MISTRAL_API_KEY": "mistral",
    "MISTRAL_API_KEYS": "mistral",
    "NVIDIA_API_KEY": "nvidia",
    "NVIDIA_API_KEYS": "nvidia",
    "NVIDIA_NIM_API_KEY": "nvidia",
    "NGC_API_KEY": "nvidia",
    "OPENROUTER_API_KEY": "openrouter",
    "HF_TOKEN": "huggingface",
    "HUGGINGFACE_API_KEY": "huggingface",
    "TOGETHER_API_KEY": "together",
}
PROVIDER_SECRET_PREFIXES = (
    ("GROQ_API_KEY_", "groq"),
    ("MISTRAL_API_KEY_", "mistral"),
    ("NVIDIA_API_KEY_", "nvidia"),
    ("NGC_API_KEY_", "nvidia"),
)


class SecretError(RuntimeError):
    pass


def _provider_for_secret(name: str) -> str | None:
    provider = PROVIDER_SECRET_NAMES.get(name)
    if provider is not None:
        return provider
    for prefix, candidate in PROVIDER_SECRET_PREFIXES:
        if name.startswith(prefix):
            return candidate
    return None


def _provider_secret_is_admitted(name: str) -> bool:
    """Resolve admission without touching the credential value itself.

    Import is intentionally lazy so generic non-provider secret use stays independent
    of the EntityOS/HCU admission module. Any admission-resolution failure is a denial.
    """
    provider = _provider_for_secret(name)
    if provider is None:
        return True
    try:
        from free_provider_admission import provider_is_admitted_free
        return bool(provider_is_admitted_free(provider))
    except Exception:
        return False


def _parse_store(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise SecretError(f"Malformed credential-store line {lineno} in {path.name}")
        name, value = line.split("=", 1)
        name = name.strip()
        if not NAME_RE.fullmatch(name):
            raise SecretError(f"Invalid credential name on line {lineno} in {path.name}")
        values[name] = value.strip()
    return values


def _repo_secrets() -> tuple[dict[str, str], dict[str, str]]:
    merged: dict[str, str] = {}
    source: dict[str, str] = {}
    for path in PRIVATE_STORES:
        for name, value in _parse_store(path).items():
            if name in merged and merged[name] != value:
                raise SecretError(f"Credential {name} is defined with conflicting values in private stores")
            merged[name] = value
            source[name] = path.name
    return merged, source


def get_secret(name: str, *, required: bool = True) -> str | None:
    if not NAME_RE.fullmatch(name):
        raise SecretError(f"Invalid credential name: {name!r}")
    provider = _provider_for_secret(name)
    if provider is not None and not _provider_secret_is_admitted(name):
        if required:
            raise SecretError(f"Provider credential denied before lookup by typed FREE admission: {provider}")
        return None
    env_value = os.environ.get(name)
    if env_value:
        return env_value
    values, _ = _repo_secrets()
    value = values.get(name)
    if value:
        return value
    if required:
        raise SecretError(f"Credential {name} is not configured")
    return None


def secret_source(name: str) -> str | None:
    if not NAME_RE.fullmatch(name):
        raise SecretError(f"Invalid credential name: {name!r}")
    if _provider_for_secret(name) is not None and not _provider_secret_is_admitted(name):
        return None
    if os.environ.get(name):
        return "process_environment"
    values, sources = _repo_secrets()
    if values.get(name):
        return f"private_repo_store:{sources[name]}"
    return None


def status(names: Iterable[str]) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for name in names:
        source = secret_source(name)
        provider = _provider_for_secret(name)
        result[name] = {
            "configured": source is not None,
            "source": source,
            "provider": provider,
            "typed_free_admission_required": provider is not None,
            "typed_free_admitted": _provider_secret_is_admitted(name) if provider is not None else None,
        }
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="Check FRANK/RAE credential availability without revealing values")
    ap.add_argument("names", nargs="+", help="credential variable names")
    args = ap.parse_args()
    print(json.dumps(status(args.names), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
