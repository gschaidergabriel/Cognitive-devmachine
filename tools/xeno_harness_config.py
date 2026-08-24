#!/usr/bin/env python3
"""Xeno harness configuration validator.

The validator is intentionally deterministic and secret-blind. It validates the
persisted non-secret harness state while API tokens live only behind opaque
secret_ref values in a separate encrypted/OS-backed secret store.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "XENO_HARNESS_CONFIG/v1"
ALLOWED_ADAPTERS = {
    "ANTHROPIC_CLAUDE_CODE",
    "OPENAI_NATIVE",
    "OPENAI_COMPATIBLE",
    "GEMINI",
    "MISTRAL",
    "GROQ",
    "NVIDIA_NIM",
    "OPENROUTER",
    "OLLAMA",
    "LLAMA_CPP",
    "VLLM",
    "TGI",
    "LOCAL_EXEC",
    "CUSTOM_HTTP_JSON",
}
ALLOWED_ROLES = {"CORE", "PRESTAGE", "UNASSIGNED"}
FORBIDDEN_SECRET_KEYS = {
    "api_key", "token", "secret", "password", "authorization", "bearer",
    "api_token", "access_token", "private_key",
}


def _require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError(code)


def _forbidden_secret_field(obj: Any, path: str = "$") -> str | None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            low = str(key).lower()
            if low in FORBIDDEN_SECRET_KEYS:
                return f"{path}.{key}"
            nested = _forbidden_secret_field(value, f"{path}.{key}")
            if nested:
                return nested
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            nested = _forbidden_secret_field(value, f"{path}[{i}]")
            if nested:
                return nested
    return None


def validate(config: dict[str, Any]) -> dict[str, Any]:
    _require(config.get("schema") == SCHEMA, "SCHEMA_MISMATCH")
    leak = _forbidden_secret_field(config)
    _require(leak is None, f"PLAINTEXT_SECRET_FIELD_FORBIDDEN:{leak}")

    local = config.get("internal_08b")
    _require(isinstance(local, dict), "INTERNAL_08B_CONFIG_MISSING")
    _require(isinstance(local.get("enabled"), bool), "INTERNAL_08B_ENABLED_NOT_BOOL")
    _require(isinstance(local.get("engine_id"), str) and local.get("engine_id"), "INTERNAL_08B_ENGINE_ID_MISSING")

    slots = config.get("external_slots")
    _require(isinstance(slots, list), "EXTERNAL_SLOTS_NOT_LIST")
    _require(len(slots) <= 2, "MAX_TWO_EXTERNAL_SLOTS")
    slot_ids: set[str] = set()
    slot_roles: dict[str, str] = {}
    for slot in slots:
        _require(isinstance(slot, dict), "EXTERNAL_SLOT_NOT_OBJECT")
        sid = slot.get("slot_id")
        _require(isinstance(sid, str) and sid in {"slot1", "slot2"}, "INVALID_SLOT_ID")
        _require(sid not in slot_ids, "DUPLICATE_SLOT_ID")
        slot_ids.add(sid)
        role = slot.get("role", "UNASSIGNED")
        _require(role in ALLOWED_ROLES, "INVALID_SLOT_ROLE")
        slot_roles[sid] = role
        adapter = slot.get("adapter")
        _require(adapter in ALLOWED_ADAPTERS, "INVALID_ADAPTER")
        secret_ref = slot.get("secret_ref")
        _require(isinstance(secret_ref, str) and secret_ref.startswith("secret://"), "OPAQUE_SECRET_REF_REQUIRED")
        _require(isinstance(slot.get("model"), str) and slot.get("model"), "MODEL_ID_REQUIRED")
        _require(isinstance(slot.get("enabled"), bool), "SLOT_ENABLED_NOT_BOOL")

    selection = config.get("selection")
    _require(isinstance(selection, dict), "SELECTION_MISSING")
    core = selection.get("core")
    prestage = selection.get("prestage")
    prestage_enabled = selection.get("prestage_enabled")
    _require(isinstance(prestage_enabled, bool), "PRESTAGE_ENABLED_NOT_BOOL")

    allowed_core = set(slot_ids)
    if local.get("enabled"):
        allowed_core.add("internal_08b")
    _require(core in allowed_core, "SELECTED_CORE_NOT_AVAILABLE")

    if prestage_enabled:
        _require(prestage in slot_ids, "SELECTED_PRESTAGE_NOT_AVAILABLE")
        _require(prestage != core, "CORE_AND_PRESTAGE_MUST_BE_DISTINCT")
    else:
        _require(prestage in {None, "NONE"} | slot_ids, "INVALID_DISABLED_PRESTAGE_SELECTION")

    # Persisted role labels and active selection must agree when a role is assigned.
    for sid, role in slot_roles.items():
        if role == "CORE":
            _require(core == sid, "SLOT_CORE_ROLE_SELECTION_MISMATCH")
        elif role == "PRESTAGE":
            _require(prestage_enabled and prestage == sid, "SLOT_PRESTAGE_ROLE_SELECTION_MISMATCH")

    grid = config.get("grid10")
    _require(isinstance(grid, dict), "GRID10_CONFIG_MISSING")
    _require(grid.get("logical_cells") == 10, "GRID10_REQUIRES_EXACTLY_TEN_LOGICAL_CELLS")
    _require(isinstance(grid.get("enabled"), bool), "GRID10_ENABLED_NOT_BOOL")

    peer = config.get("peer_link")
    _require(isinstance(peer, dict), "PEER_LINK_CONFIG_MISSING")
    _require(isinstance(peer.get("enabled"), bool), "PEER_LINK_ENABLED_NOT_BOOL")
    _require(peer.get("protocol") == "XENO_PEER_LINK/v1", "PEER_LINK_PROTOCOL_MISMATCH")

    jspace = config.get("global_jspace")
    _require(isinstance(jspace, dict), "GLOBAL_JSPACE_CONFIG_MISSING")
    _require(jspace.get("enabled") is True, "GLOBAL_JSPACE_MUST_BE_ENABLED_FOR_XENO_V1")
    _require(isinstance(jspace.get("profile_id"), str) and jspace.get("profile_id"), "JSPACE_PROFILE_ID_MISSING")

    return {
        "schema": "XENO_HARNESS_CONFIG_VALIDATION/v1",
        "status": "PASS",
        "external_slot_count": len(slots),
        "internal_08b_enabled": local["enabled"],
        "selected_core": core,
        "prestage_enabled": prestage_enabled,
        "selected_prestage": prestage if prestage_enabled else None,
        "grid10_enabled": grid["enabled"],
        "peer_link_enabled": peer["enabled"],
        "secret_storage": "OPAQUE_SECRET_REFS_ONLY",
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("config", type=Path)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("CONFIG_NOT_OBJECT")
        result = validate(config)
    except Exception as exc:
        result = {
            "schema": "XENO_HARNESS_CONFIG_VALIDATION/v1",
            "status": "FAIL",
            "error": f"{type(exc).__name__}:{exc}",
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
