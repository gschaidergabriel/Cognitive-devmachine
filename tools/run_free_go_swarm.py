#!/usr/bin/env python3
"""Canonical guarded entrypoint for the adaptive FREE_ONLY swarm.

The pre-8.67 implementation is loaded from its exact Git blob only as an
internal implementation donor. It is not exposed as a second executable file.
Canonical typed provider admission is checked before every credential read and
again immediately before provider network I/O.
"""
from __future__ import annotations

import asyncio
import subprocess
import sys
import types
from typing import Any

import free_provider_admission as _admission

LEGACY_BLOB_SHA = "6ed51e629c9b1a0b78f1fcec1daf8634487018b3"
_IMPL: types.ModuleType | None = None
_LEGACY_COLLECT_KEYS = None
_LEGACY_REQUEST_CHAT = None
_MUTABLE_HOOKS = (
    "OWNER_DIRECTIVE_PATH",
    "DEFAULT_ROLES",
    "build_state_context",
    "worker_prompt",
)


def provider_is_admitted_free(provider: str) -> bool:
    return _admission.provider_is_admitted_free(provider)


def _load_impl() -> types.ModuleType:
    global _IMPL, _LEGACY_COLLECT_KEYS, _LEGACY_REQUEST_CHAT
    if _IMPL is not None:
        return _IMPL

    # Git object storage is provenance, not a second current executable path.
    # A shallow checkout missing the exact donor fails closed rather than
    # silently using a different implementation.
    try:
        proc = subprocess.run(
            ["git", "-C", str(__file__.rsplit("/tools/", 1)[0]), "cat-file", "blob", LEGACY_BLOB_SHA],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
    except Exception as exc:
        raise RuntimeError(f"LEGACY_SWARM_DONOR_UNAVAILABLE:{exc.__class__.__name__}") from exc
    if proc.returncode != 0:
        raise RuntimeError("LEGACY_SWARM_DONOR_UNAVAILABLE_OR_SHALLOW_CHECKOUT")

    source = proc.stdout.decode("utf-8", errors="strict")
    module = types.ModuleType("clay._free_swarm_impl_867_donor")
    module.__file__ = f"git-blob:{LEGACY_BLOB_SHA}"
    module.__package__ = ""
    exec(compile(source, module.__file__, "exec"), module.__dict__)

    _LEGACY_COLLECT_KEYS = module.collect_keys
    _LEGACY_REQUEST_CHAT = module.request_chat
    module.collect_keys = collect_keys
    module.request_chat = request_chat
    _IMPL = module
    return module


def _unsafe_collect(spec: Any) -> list[str]:
    _load_impl()
    assert _LEGACY_COLLECT_KEYS is not None
    return _LEGACY_COLLECT_KEYS(spec)


def _unsafe_request(spec: Any, key: str, model: str, prompt: str, max_tokens: int, timeout: float):
    _load_impl()
    assert _LEGACY_REQUEST_CHAT is not None
    return _LEGACY_REQUEST_CHAT(spec, key, model, prompt, max_tokens, timeout)


def collect_keys(spec: Any) -> list[str]:
    # No legacy env-key read happens unless exact typed FREE admission already
    # exists in the canonical control plane.
    if not provider_is_admitted_free(spec.name):
        return []
    return _unsafe_collect(spec)


def request_chat(spec: Any, key: str, model: str, prompt: str,
                 max_tokens: int, timeout: float):
    # Re-check at the last local boundary before HTTP so an authority change or
    # stale runtime cannot keep network permission merely because a key was read.
    if not provider_is_admitted_free(spec.name):
        return 460, {}, {
            "error": {
                "type": "typed_free_provider_admission_block",
                "message": f"{spec.name} is not admitted as exact FREE by the canonical control plane",
            }
        }
    return _unsafe_request(spec, key, model, prompt, max_tokens, timeout)


def _sync_hooks(module: types.ModuleType) -> None:
    for name in _MUTABLE_HOOKS:
        if name in globals():
            setattr(module, name, globals()[name])
    module.collect_keys = collect_keys
    module.request_chat = request_chat


async def run(args: Any) -> int:
    module = _load_impl()
    _sync_hooks(module)
    return await module.run(args)


def parse_args(argv: list[str] | None = None):
    return _load_impl().parse_args(argv)


def __getattr__(name: str) -> Any:
    module = _load_impl()
    return getattr(module, name)


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(run(parse_args())))
    except KeyboardInterrupt:
        raise SystemExit(130)
