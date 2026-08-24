#!/usr/bin/env python3
"""Canonical guarded compatibility entrypoint for the adaptive Free Swarm.

The previous implementation is preserved byte-for-byte in
`run_free_go_swarm_legacy.py`. This entrypoint inserts the canonical
EntityOS/HCU typed provider-admission boundary before legacy credential reads
and again before provider network execution.
"""
from __future__ import annotations

import asyncio
import sys
from typing import Any

import free_provider_admission as _admission
import run_free_go_swarm_legacy as _legacy

ROOT = _legacy.ROOT
PROTOCOL_PATH = _legacy.PROTOCOL_PATH
BOOTSTRAP_PATH = _legacy.BOOTSTRAP_PATH
PROGRAM_STATE_PATH = _legacy.PROGRAM_STATE_PATH
SUPERVISOR_PATH = _legacy.SUPERVISOR_PATH
OWNER_DIRECTIVE_PATH = _legacy.OWNER_DIRECTIVE_PATH
PROTOCOL_BEGIN = _legacy.PROTOCOL_BEGIN
PROTOCOL_END = _legacy.PROTOCOL_END
DEFAULT_ROLES = _legacy.DEFAULT_ROLES
ProviderSpec = _legacy.ProviderSpec
PROVIDERS = _legacy.PROVIDERS
truthy = _legacy.truthy
split_values = _legacy.split_values
unique = _legacy.unique
key_fingerprint = _legacy.key_fingerprint
git_text = _legacy.git_text
read_bounded = _legacy.read_bounded
build_state_context = _legacy.build_state_context
load_protocol = _legacy.load_protocol
parse_retry_after = _legacy.parse_retry_after
extract_text = _legacy.extract_text
usage_from = _legacy.usage_from
JsonlSink = _legacy.JsonlSink
ProviderRuntime = _legacy.ProviderRuntime
worker_prompt = _legacy.worker_prompt
worker_loop = _legacy.worker_loop
status_loop = _legacy.status_loop
parse_args = _legacy.parse_args

_unsafe_collect_keys = _legacy.collect_keys
_unsafe_request_chat = _legacy.request_chat


def provider_is_admitted_free(provider: str) -> bool:
    return _admission.provider_is_admitted_free(provider)


def collect_keys(spec: ProviderSpec) -> list[str]:
    if not provider_is_admitted_free(spec.name):
        return []
    return _unsafe_collect_keys(spec)


def request_chat(spec: ProviderSpec, key: str, model: str, prompt: str,
                 max_tokens: int, timeout: float):
    if not provider_is_admitted_free(spec.name):
        return 460, {}, {
            "error": {
                "type": "typed_free_provider_admission_block",
                "message": f"{spec.name} is not admitted as exact FREE by the canonical control plane",
            }
        }
    return _unsafe_request_chat(spec, key, model, prompt, max_tokens, timeout)


async def run(args: Any) -> int:
    # Synchronize mutable compatibility hooks used by the current EntityOS/HCU
    # driver before delegating into the byte-preserved implementation.
    _legacy.OWNER_DIRECTIVE_PATH = OWNER_DIRECTIVE_PATH
    _legacy.DEFAULT_ROLES = DEFAULT_ROLES
    _legacy.request_chat = request_chat
    _legacy.build_state_context = build_state_context
    _legacy.worker_prompt = worker_prompt
    _legacy.collect_keys = collect_keys
    return await _legacy.run(args)


def __getattr__(name: str) -> Any:
    return getattr(_legacy, name)


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(run(parse_args())))
    except KeyboardInterrupt:
        raise SystemExit(130)
