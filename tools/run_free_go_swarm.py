#!/usr/bin/env python3
"""Admission-safe facade for the existing adaptive FREE_ONLY swarm implementation.

Authority order: a typed ENTITYOS_PROVIDER_ADMISSION/v1 object from the active
EntityOS/HCU control plane is required before any provider key/secret lookup or
provider network path can become reachable. Legacy *_FREE_ATTESTED environment
variables are compatibility outputs only and never authority.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
import sys
from typing import Any

import _run_free_go_swarm_impl as _legacy
import free_swarm_provider_admission as _admission

_ORIGINAL_COLLECT_KEYS = _legacy.collect_keys

ROOT = Path(__file__).resolve().parents[1]

# Re-export compatibility API expected by run_24h_entityos_swarm.py.
ProviderSpec = _legacy.ProviderSpec
PROVIDERS = _legacy.PROVIDERS
split_values = _legacy.split_values
unique = _legacy.unique
key_fingerprint = _legacy.key_fingerprint
truthy = _legacy.truthy
parse_args = _legacy.parse_args
ProviderRuntime = _legacy.ProviderRuntime
JsonlSink = _legacy.JsonlSink

# Mutable hooks are deliberately mirrored into the legacy implementation at run time.
DEFAULT_ROLES = _legacy.DEFAULT_ROLES
OWNER_DIRECTIVE_PATH = _legacy.OWNER_DIRECTIVE_PATH
request_chat = _legacy.request_chat
build_state_context = _legacy.build_state_context
worker_prompt = _legacy.worker_prompt


def _spec(provider: str) -> ProviderSpec | None:
    provider = provider.lower()
    return next((item for item in PROVIDERS if item.name == provider), None)


def _typed_admission() -> _admission.Admission | None:
    return _admission.load_admission()


def _prepare_provider_environment(spec: ProviderSpec, admission: _admission.Admission) -> None:
    # Secret files are data, never shell-sourced. This call is unreachable unless
    # the provider has explicit cost_class=FREE + admitted=true.
    _admission.load_provider_secret_environment(spec.name, ROOT, admission=admission)
    # Compatibility only: legacy code still checks this flag after key collection.
    os.environ[spec.attestation_env] = "1"


def collect_keys(spec: ProviderSpec) -> list[str]:
    """Admission-gated key collection used by both live discovery and workers."""
    admission = _typed_admission()
    if not _admission.provider_is_admitted_free(spec.name, admission):
        return []
    _prepare_provider_environment(spec, admission)
    # Count/read environment key material only after typed admission. We keep the
    # legacy normalizer to preserve multi-key compatibility and dedup semantics.
    _admission.read_provider_env_keys(spec.name, admission=admission)
    return _ORIGINAL_COLLECT_KEYS(spec)


def _sync_legacy_hooks(admission: _admission.Admission) -> None:
    _legacy.DEFAULT_ROLES = DEFAULT_ROLES
    _legacy.OWNER_DIRECTIVE_PATH = OWNER_DIRECTIVE_PATH
    _legacy.request_chat = request_chat
    _legacy.build_state_context = build_state_context
    _legacy.worker_prompt = worker_prompt
    _legacy.collect_keys = collect_keys

    # Remove env-only authority then recreate compatibility flags strictly from
    # the typed decision. Existing env attestations cannot broaden admission.
    os.environ["CLAY_FREE_ONLY_ATTESTED"] = "1"
    for spec in PROVIDERS:
        if _admission.provider_is_admitted_free(spec.name, admission):
            os.environ[spec.attestation_env] = "1"
        else:
            os.environ.pop(spec.attestation_env, None)


async def run(args: Any) -> int:
    admission = _typed_admission()
    if admission is None:
        print("Refusing to start: missing/invalid ENTITYOS_PROVIDER_ADMISSION/v1.", file=sys.stderr)
        return 3
    if not admission.admitted_free_providers:
        print("Refusing to start: typed admission contains no admitted FREE provider.", file=sys.stderr)
        return 4
    _sync_legacy_hooks(admission)
    return await _legacy.run(args)


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(run(parse_args())))
    except KeyboardInterrupt:
        raise SystemExit(130)
