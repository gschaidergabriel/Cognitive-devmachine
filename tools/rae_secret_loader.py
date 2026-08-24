#!/usr/bin/env python3
"""Credential loader for EntityOS/HCU external tools.

Lookup priority after authorization:
1. process environment
2. designated private repository credential stores

External LLM-provider credentials are protected by the canonical typed FREE provider
admission boundary. Provider authority is resolved before checking environment values,
private stores, or credential provenance. The loader never prints secret values.
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


class SecretError(RuntimeError):
    pass


def _provider_for_secret_name(name: str) -> str | None:
    """Map known external-provider credentials to canonical admission identities.

    Keep this mapping narrower than a generic suffix heuristic: unrelated secrets must
    not accidentally inherit provider semantics. Numbered legacy key aliases are covered
    because they have historically been used by swarm adapters.
    """
    if name == "HF_TOKEN":
        return "huggingface"
    if re.fullmatch(r"GROQ\d*_API_KEY", name) or name in {"GROQ_API_KEY", "GROQ_API_KEYS"}:
        return "groq"
    if re.fullmatch(r"MISTRAL\d*_API_KEY", name) or name in {"MISTRAL_API_KEY", "MISTRAL_API_KEYS"}:
        return "mistral"
    if name in {
        "NVIDIA_API_KEY", "NVIDIA_API_KEYS", "NVIDIA_NIM_API_KEY", "NGC_API_KEY",
        "NVIDIA2_API_KEY", "NVIDIA3_API_KEY",
    }:
        return "nvidia"
    if name == "OPENROUTER_API_KEY":
        return "openrouter"
    return None


def _require_provider_secret_admission(name: str) -> None:
    """Fail closed before any provider credential lookup or provenance inspection."""
    provider = _provider_for_secret_name(name)
    if provider is None:
        return
    try:
        # Lazy import keeps the credential layer reusable and avoids import-order cycles.
        from free_provider_admission import provider_is_admitted_free
    except Exception as exc:  # import/authority failure must never open credential access
        raise SecretError(f"PROVIDER_ADMISSION_UNAVAILABLE:{provider}") from exc
    if not provider_is_admitted_free(provider):
        raise SecretError(f"PROVIDER_SECRET_REQUIRES_TYPED_FREE_ADMISSION:{provider}")


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
    _require_provider_secret_admission(name)
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
    _require_provider_secret_admission(name)
    if os.environ.get(name):
        return "process_environment"
    values, sources = _repo_secrets()
    if values.get(name):
        return f"private_repo_store:{sources[name]}"
    return None


def status(names: Iterable[str]) -> dict[str, dict[str, object]]:
    return {
        name: {"configured": secret_source(name) is not None, "source": secret_source(name)}
        for name in names
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Check EntityOS/HCU credential availability without revealing values")
    ap.add_argument("names", nargs="+", help="credential variable names")
    args = ap.parse_args()
    print(json.dumps(status(args.names), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
