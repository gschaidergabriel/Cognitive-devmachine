#!/usr/bin/env python3
"""Safe EntityOS/HCU entrypoint for the adaptive FREE_ONLY go swarm.

The pre-8.67 implementation is retained as ``run_free_go_swarm_legacy.py`` for
behavioral reuse. This entrypoint adds the typed provider-admission boundary and
patches the legacy worker so neither credential lookup nor network execution can
occur from environment attestation flags alone.
"""
from __future__ import annotations

import asyncio
import importlib.util
import os
from pathlib import Path
import sys
from typing import Any, Callable

import free_swarm_provider_admission as admission

ROOT = Path(__file__).resolve().parents[1]
LEGACY_PATH = Path(__file__).resolve().with_name("run_free_go_swarm_legacy.py")

_spec = importlib.util.spec_from_file_location("clay_run_free_go_swarm_pre867", LEGACY_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError("legacy free-swarm controller unavailable")
legacy = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = legacy
_spec.loader.exec_module(legacy)

# Public compatibility surface used by the EntityOS/HCU driver.
ProviderSpec = legacy.ProviderSpec
PROVIDERS = legacy.PROVIDERS
split_values = legacy.split_values
unique = legacy.unique
DEFAULT_ROLES = legacy.DEFAULT_ROLES
OWNER_DIRECTIVE_PATH = legacy.OWNER_DIRECTIVE_PATH
AdmissionError = admission.AdmissionError

_legacy_collect_keys = legacy.collect_keys
_raw_request_chat = legacy.request_chat
_transport_request_chat: Callable[..., Any] = _raw_request_chat
_active_snapshot: admission.AdmissionSnapshot | None = None


def raw_request_chat(*args: Any, **kwargs: Any) -> Any:
    """Call the original transport implementation; callers must stay behind this module's guard."""
    return _raw_request_chat(*args, **kwargs)


def set_request_chat_delegate(fn: Callable[..., Any]) -> None:
    global _transport_request_chat
    _transport_request_chat = fn


def activate_provider_admission() -> admission.AdmissionSnapshot:
    """Resolve current typed admission before any provider secret/key lookup."""
    global _active_snapshot
    snapshot = admission.load_runtime_admission()
    if not admission.admitted_provider_names(snapshot):
        raise AdmissionError("no_explicit_free_provider_admitted")
    _active_snapshot = snapshot

    # Legacy booleans are derived compatibility metadata only, after typed admission.
    os.environ["CLAY_FREE_ONLY_ATTESTED"] = "1"
    for spec in PROVIDERS:
        try:
            admission.require_free_provider(snapshot, spec.name)
        except AdmissionError:
            os.environ.pop(spec.attestation_env, None)
        else:
            os.environ[spec.attestation_env] = "1"
    return snapshot


def active_provider_admission() -> admission.AdmissionSnapshot:
    if _active_snapshot is None:
        raise AdmissionError("typed_provider_admission_not_activated")
    return _active_snapshot


def require_provider_admitted(provider: str) -> admission.ProviderAdmission:
    return admission.require_free_provider(active_provider_admission(), provider)


def collect_keys(spec: ProviderSpec) -> list[str]:
    snapshot = active_provider_admission()
    return admission.with_provider_permit(
        snapshot,
        spec.name,
        lambda _permit: _legacy_collect_keys(spec),
    )


def request_chat(spec: ProviderSpec, key: str, model: str, prompt: str,
                 max_tokens: int, timeout: float):
    snapshot = active_provider_admission()
    return admission.with_provider_permit(
        snapshot,
        spec.name,
        lambda _permit: _transport_request_chat(spec, key, model, prompt, max_tokens, timeout),
    )


def _sync_legacy_runtime() -> None:
    legacy.ROOT = ROOT
    legacy.PROTOCOL_PATH = ROOT / "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md"
    legacy.BOOTSTRAP_PATH = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
    legacy.PROGRAM_STATE_PATH = ROOT / "research_entity/rooms/PROGRAM_STATE.json"
    legacy.SUPERVISOR_PATH = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    legacy.OWNER_DIRECTIVE_PATH = OWNER_DIRECTIVE_PATH
    legacy.DEFAULT_ROLES = DEFAULT_ROLES
    legacy.collect_keys = collect_keys
    legacy.request_chat = request_chat


async def run(args: Any) -> int:
    if _active_snapshot is None:
        try:
            activate_provider_admission()
        except AdmissionError as exc:
            print(f"Refusing to start: typed FREE provider admission blocked ({exc}).", file=sys.stderr)
            return 5
    _sync_legacy_runtime()
    return await legacy.run(args)


def parse_args(argv: list[str] | None = None):
    return legacy.parse_args(argv)


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(run(parse_args())))
    except KeyboardInterrupt:
        raise SystemExit(130)
