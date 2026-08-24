#!/usr/bin/env python3
"""Successor-dynamic external LLM provider call boundary for EntityOS/HCU.

Secret-free and network-free. Resolve the current supervisor through SUPERVISOR_INBOX
and combine its runtime-quarantine state with canonical typed FREE admission. Every
provider-capable caller must check this boundary before provider secret lookup and
again immediately before provider network I/O.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INBOX_PATH = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"


class ProviderCallBoundaryError(RuntimeError):
    pass


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProviderCallBoundaryError(f"{label}_UNAVAILABLE_OR_INVALID:{exc.__class__.__name__}") from exc
    if not isinstance(payload, dict):
        raise ProviderCallBoundaryError(f"{label}_OBJECT_REQUIRED")
    return payload


def current_boundary_state(*, root: Path | None = None, inbox_path: Path | None = None) -> dict[str, Any]:
    repo_root = (root or ROOT).resolve()
    inbox = _read_object(inbox_path or INBOX_PATH, "SUPERVISOR_INBOX")
    epoch = str(inbox.get("schema_version") or "").strip()
    steering_ref = inbox.get("steering")
    if not epoch or not isinstance(steering_ref, str) or not steering_ref.strip():
        raise ProviderCallBoundaryError("SUPERVISOR_IDENTITY_REQUIRED")
    rel = Path(steering_ref)
    if rel.is_absolute() or ".." in rel.parts:
        raise ProviderCallBoundaryError("SUPERVISOR_STEERING_REF_INVALID")
    steering_path = (repo_root / rel).resolve()
    try:
        steering_path.relative_to(repo_root)
    except ValueError as exc:
        raise ProviderCallBoundaryError("SUPERVISOR_STEERING_REF_OUTSIDE_REPO") from exc
    steering = _read_object(steering_path, "SUPERVISOR_STEERING")
    if str(steering.get("schema_version") or "").strip() != epoch:
        raise ProviderCallBoundaryError("SUPERVISOR_EPOCH_MISMATCH")
    if steering.get("active_program") != "ENTITYOS_HCU" or steering.get("product") != "EntityOS" or steering.get("integrated_cognition_compute_architecture") != "HCU":
        raise ProviderCallBoundaryError("SUPERVISOR_PRODUCT_AUTHORITY_MISMATCH")
    free_only = steering.get("free_only")
    if not isinstance(free_only, dict) or free_only.get("enabled") is not True:
        raise ProviderCallBoundaryError("FREE_ONLY_AUTHORITY_REQUIRED")
    execution_state = str(free_only.get("external_llm_provider_execution") or "UNKNOWN").strip().upper()
    return {
        "authority_epoch": epoch,
        "steering": steering_ref,
        "external_llm_provider_execution": execution_state,
        "runtime_quarantined": "QUARANTINED" in execution_state,
    }


def provider_call_is_allowed(provider: str) -> bool:
    """True only if both the current runtime authority and typed FREE record permit it."""
    try:
        state = current_boundary_state()
        if state["runtime_quarantined"]:
            return False
        if state["external_llm_provider_execution"] not in {"ALLOWED", "AUTHORIZED", "ENABLED"}:
            return False
        from free_provider_admission import provider_is_admitted_free
        return bool(provider_is_admitted_free(provider))
    except Exception:
        return False


def assert_provider_call_allowed(provider: str) -> None:
    if provider_call_is_allowed(provider):
        return
    try:
        state = current_boundary_state()
        epoch = state.get("authority_epoch", "UNKNOWN")
        execution = state.get("external_llm_provider_execution", "UNKNOWN")
    except Exception:
        epoch = "UNKNOWN"
        execution = "UNKNOWN"
    raise ProviderCallBoundaryError(
        f"PROVIDER_CALL_BLOCKED:{provider}:authority_epoch={epoch}:execution={execution}"
    )
