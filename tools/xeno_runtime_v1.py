#!/usr/bin/env python3
"""Xeno v1 request orchestration over canonical EntityOS/HCU admission.

This module is deliberately a thin runtime spine. It does not create a second
Typed Entry authority, truth store, model authority, or effect path. Raw Entry
is admitted by the existing HCU `xeno_entry_fabric_v1`; harness state is
validated by `xeno_harness_config`; model adapters are invoked only as candidate
producers; returned candidates still require the existing deterministic
EffectGate/EffectJournal path for any real effect.
"""
from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import sys
import time
from typing import Any, Callable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
HCU_DIR = ROOT / "the artefact" / "MicroEntity" / "hcu"
for directory in (TOOLS_DIR, HCU_DIR):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))


def _import_exact_repo_module(name: str, expected_path: Path):
    module = importlib.import_module(name)
    raw_path = getattr(module, "__file__", None)
    if not raw_path:
        raise RuntimeError(f"XENO_RUNTIME_AUTHORITY_MODULE_PATH_MISSING:{name}")
    loaded = Path(raw_path).resolve()
    expected = expected_path.resolve()
    if loaded != expected:
        raise RuntimeError(
            f"XENO_RUNTIME_AUTHORITY_MODULE_SHADOWED:{name}:{loaded}:{expected}"
        )
    return module


# Import authority-bearing modules by their normal compatibility names, then
# fail closed unless Python resolved each one to the exact current repository
# path. This prevents a preloaded/ambient same-name module from silently
# replacing Typed Entry, canonicalization, or harness authority in a long-lived
# Xeno process.
_canonicalization = _import_exact_repo_module(
    "entry_canonicalization_v1", HCU_DIR / "entry_canonicalization_v1.py"
)
_entry_fabric = _import_exact_repo_module(
    "xeno_entry_fabric_v1", HCU_DIR / "xeno_entry_fabric_v1.py"
)
xeno_harness_config = _import_exact_repo_module(
    "xeno_harness_config", TOOLS_DIR / "xeno_harness_config.py"
)

CanonicalizationError = _canonicalization.CanonicalizationError
canonicalize = _canonicalization.canonicalize
EntryPacket = _entry_fabric.EntryPacket
admit_entry_json = _entry_fabric.admit_entry_json

RUNTIME_SCHEMA = "XENO_RUNTIME_RESULT/v1"
INVOCATION_SCHEMA = "XENO_ENGINE_INVOCATION/v1"
ENGINE_RESULT_SCHEMA = "XENO_ENGINE_RESULT/v1"
ACTION_CANDIDATE_SCHEMA = "XENO_ACTION_CANDIDATE/v1"
TRACE_SCHEMA = "XENO_RUNTIME_TRACE/v1"

COMPONENT_PATHS = {
    "xeno_runtime": Path(__file__).resolve(),
    "entry_canonicalization": (HCU_DIR / "entry_canonicalization_v1.py").resolve(),
    "xeno_entry_fabric": (HCU_DIR / "xeno_entry_fabric_v1.py").resolve(),
    "xeno_harness_config": (TOOLS_DIR / "xeno_harness_config.py").resolve(),
}

FORBIDDEN_SECRET_KEYS = {
    "api_key",
    "api_token",
    "access_token",
    "token",
    "secret",
    "secret_ref",
    "password",
    "authorization",
    "bearer",
    "private_key",
}


class XenoRuntimeError(ValueError):
    pass


EngineRunner = Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]]


def _file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise XenoRuntimeError(f"RUNTIME_COMPONENT_UNREADABLE:{path}") from exc


def _capture_component_binding() -> dict[str, dict[str, str]]:
    binding: dict[str, dict[str, str]] = {}
    for name, path in sorted(COMPONENT_PATHS.items()):
        try:
            relative = path.relative_to(ROOT).as_posix()
        except ValueError as exc:
            raise XenoRuntimeError(f"RUNTIME_COMPONENT_OUTSIDE_REPO:{name}:{path}") from exc
        binding[name] = {"path": relative, "sha256": _file_sha256(path)}
    return binding


INITIAL_COMPONENT_BINDING = _capture_component_binding()


def _assert_component_binding_current() -> dict[str, dict[str, str]]:
    current = _capture_component_binding()
    if current != INITIAL_COMPONENT_BINDING:
        raise XenoRuntimeError("RUNTIME_COMPONENT_BINDING_CHANGED_SINCE_IMPORT")
    return current


def _canonical_hash(value: Any, field: str) -> str:
    try:
        raw = canonicalize(value)
    except CanonicalizationError as exc:
        raise XenoRuntimeError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    return hashlib.sha256(raw).hexdigest()


def _find_secret_field(value: Any, path: str = "$") -> str | None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            low = str(key).lower()
            if low in FORBIDDEN_SECRET_KEYS:
                return f"{path}.{key}"
            found = _find_secret_field(item, f"{path}.{key}")
            if found:
                return found
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            found = _find_secret_field(item, f"{path}[{index}]")
            if found:
                return found
    return None


def _require_no_secret_fields(value: Any, field: str) -> None:
    found = _find_secret_field(value)
    if found:
        raise XenoRuntimeError(f"{field}:SECRET_FIELD_FORBIDDEN:{found}")


def _payload_bytes(payload_text: str) -> bytes:
    if not isinstance(payload_text, str):
        raise XenoRuntimeError("PAYLOAD_TEXT_REQUIRED")
    return payload_text.encode("utf-8")


def _budget(packet: EntryPacket) -> dict[str, int]:
    return {str(k): int(v) for k, v in packet.budget}


def _profile_for_selection(config: Mapping[str, Any], selection_id: str) -> dict[str, Any]:
    if selection_id == "internal_08b":
        local = config["internal_08b"]
        if local.get("enabled") is not True:
            raise XenoRuntimeError("INTERNAL_08B_SELECTED_BUT_DISABLED")
        return {
            "selection_id": "internal_08b",
            "kind": "INTERNAL_08B",
            "engine_id": local["engine_id"],
        }

    for slot in config["external_slots"]:
        if slot["slot_id"] == selection_id:
            if slot.get("enabled") is not True:
                raise XenoRuntimeError(f"EXTERNAL_SLOT_DISABLED:{selection_id}")
            # `secret_ref` is deliberately available only to the adapter boundary;
            # it is never placed in the model request, trace, or public result.
            return {
                "selection_id": selection_id,
                "kind": "EXTERNAL_SLOT",
                "adapter": slot["adapter"],
                "model": slot["model"],
                "secret_ref": slot["secret_ref"],
            }
    raise XenoRuntimeError(f"ENGINE_SELECTION_NOT_FOUND:{selection_id}")


def _public_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in profile.items() if k != "secret_ref"}


def _engine_invocation(
    *,
    role: str,
    packet: EntryPacket,
    payload_text: str,
    remaining_tokens: int,
    prestage_result: Mapping[str, Any] | None,
) -> dict[str, Any]:
    request: dict[str, Any] = {
        "schema": INVOCATION_SCHEMA,
        "role": role,
        "event_sha256": packet.event_sha256,
        "admission_sha256": packet.admission_sha256,
        "entity_generation": packet.entity_generation,
        "payload_ref": packet.payload_ref,
        "payload_sha256": packet.payload_sha256,
        "payload_text": payload_text,
        "budget": {
            "max_tokens_remaining": max(0, remaining_tokens),
        },
    }
    if prestage_result is not None:
        request["prestage_candidate"] = {
            "schema": prestage_result["schema"],
            "result_sha256": prestage_result["result_sha256"],
            "text": prestage_result["text"],
            "canonical_truth": False,
        }
    _require_no_secret_fields(request, "ENGINE_INVOCATION")
    return request


def _usage_tokens(usage: Mapping[str, Any]) -> int:
    value = usage.get("total_tokens", 0)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise XenoRuntimeError("ENGINE_USAGE_TOTAL_TOKENS_INVALID")
    return value


def _normalize_engine_result(
    *,
    role: str,
    profile: Mapping[str, Any],
    raw: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise XenoRuntimeError(f"ENGINE_RESULT_NOT_MAPPING:{role}")
    _require_no_secret_fields(raw, f"ENGINE_RESULT:{role}")
    status = raw.get("status")
    if status != "OK":
        raise XenoRuntimeError(f"ENGINE_EXECUTION_FAILED:{role}:{status}")
    text = raw.get("text")
    if not isinstance(text, str):
        raise XenoRuntimeError(f"ENGINE_RESULT_TEXT_REQUIRED:{role}")
    usage = raw.get("usage", {})
    if not isinstance(usage, Mapping):
        raise XenoRuntimeError(f"ENGINE_USAGE_NOT_MAPPING:{role}")
    usage = dict(usage)
    _usage_tokens(usage)
    request_id = raw.get("request_id")
    if request_id is not None and not isinstance(request_id, str):
        raise XenoRuntimeError(f"ENGINE_REQUEST_ID_INVALID:{role}")
    receipt_ref = raw.get("provider_receipt_ref")
    if receipt_ref is not None and not isinstance(receipt_ref, str):
        raise XenoRuntimeError(f"ENGINE_PROVIDER_RECEIPT_REF_INVALID:{role}")

    material = {
        "schema": ENGINE_RESULT_SCHEMA,
        "role": role,
        "engine": _public_profile(profile),
        "text": text,
        "usage": usage,
        "request_id": request_id,
        "provider_receipt_ref": receipt_ref,
        "canonical_truth": False,
        "effect_authority": False,
    }
    material["result_sha256"] = _canonical_hash(material, f"ENGINE_RESULT:{role}")
    return material


def _trace_hash(steps: list[dict[str, Any]]) -> str:
    return _canonical_hash({"schema": TRACE_SCHEMA, "steps": steps}, "RUNTIME_TRACE")


def execute_request(
    raw_entry: str | bytes | bytearray,
    *,
    harness_config: Mapping[str, Any],
    current_generation: int,
    expected_capability_binding_sha256: str,
    admitted_capabilities: Sequence[str],
    admitted_budget: Mapping[str, Any],
    payload_text: str,
    engine_runner: EngineRunner | None = None,
    deterministic_candidate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute one bounded Xeno request and return a non-authoritative candidate.

    Exactly one of the model path (`engine_runner`) or deterministic path
    (`deterministic_candidate`) is selected. The deterministic path exists for the
    harness mode where the deterministic scheduler has already proven model
    inference unnecessary. Neither path may create canonical truth or a real effect.
    """
    component_binding = _assert_component_binding_current()
    component_binding_sha256 = _canonical_hash(component_binding, "RUNTIME_COMPONENT_BINDING")

    if not isinstance(harness_config, Mapping):
        raise XenoRuntimeError("HARNESS_CONFIG_MAPPING_REQUIRED")
    config = dict(harness_config)
    try:
        validation = xeno_harness_config.validate(config)
    except Exception as exc:
        raise XenoRuntimeError(f"HARNESS_CONFIG_REJECTED:{exc}") from exc
    if validation.get("status") != "PASS":
        raise XenoRuntimeError("HARNESS_CONFIG_NOT_VALIDATED")

    packet = admit_entry_json(
        raw_entry,
        current_generation=current_generation,
        expected_capability_binding_sha256=expected_capability_binding_sha256,
        admitted_capabilities=admitted_capabilities,
        admitted_budget=admitted_budget,
    )
    payload_bytes = _payload_bytes(payload_text)
    if hashlib.sha256(payload_bytes).hexdigest() != packet.payload_sha256:
        raise XenoRuntimeError("PAYLOAD_BYTES_DO_NOT_MATCH_ADMITTED_DIGEST")

    steps: list[dict[str, Any]] = [
        {
            "stage": "ENTRY_ADMITTED",
            "event_sha256": packet.event_sha256,
            "admission_sha256": packet.admission_sha256,
            "entity_generation": packet.entity_generation,
            "component_binding_sha256": component_binding_sha256,
        }
    ]
    budgets = _budget(packet)
    started = time.monotonic()

    if deterministic_candidate is not None:
        if engine_runner is not None:
            raise XenoRuntimeError("DETERMINISTIC_AND_MODEL_PATH_MUTUALLY_EXCLUSIVE")
        if not isinstance(deterministic_candidate, Mapping):
            raise XenoRuntimeError("DETERMINISTIC_CANDIDATE_MAPPING_REQUIRED")
        candidate_payload = dict(deterministic_candidate)
        _require_no_secret_fields(candidate_payload, "DETERMINISTIC_CANDIDATE")
        candidate_digest = _canonical_hash(candidate_payload, "DETERMINISTIC_CANDIDATE")
        action_candidate = {
            "schema": ACTION_CANDIDATE_SCHEMA,
            "kind": "DETERMINISTIC_CONTROL_OUTPUT",
            "event_sha256": packet.event_sha256,
            "admission_sha256": packet.admission_sha256,
            "candidate_sha256": candidate_digest,
            "candidate": candidate_payload,
            "canonical_truth": False,
            "effect_authority": False,
            "requires_effect_gate": True,
        }
        steps.append({"stage": "DETERMINISTIC_CANDIDATE", "result_sha256": candidate_digest})
        trace_sha256 = _trace_hash(steps)
        return {
            "schema": RUNTIME_SCHEMA,
            "mode": "DETERMINISTIC_NO_MODEL",
            "component_binding": component_binding,
            "component_binding_sha256": component_binding_sha256,
            "entry": steps[0],
            "prestage_result": None,
            "core_result": None,
            "action_candidate": action_candidate,
            "trace": {"schema": TRACE_SCHEMA, "steps": steps, "trace_sha256": trace_sha256},
            "model_calls": 0,
            "canonical_truth": False,
            "effect_authority": False,
            "requires_effect_gate": True,
        }

    if engine_runner is None:
        raise XenoRuntimeError("ENGINE_RUNNER_REQUIRED_FOR_MODEL_PATH")

    selection = config["selection"]
    prestage_enabled = bool(selection["prestage_enabled"])
    required_calls = 2 if prestage_enabled else 1
    if budgets["max_model_calls"] < required_calls:
        raise XenoRuntimeError("MODEL_CALL_BUDGET_INSUFFICIENT")
    if budgets["max_wall_ms"] <= 0:
        raise XenoRuntimeError("MODEL_WALL_BUDGET_INSUFFICIENT")

    total_tokens = 0
    prestage_result: dict[str, Any] | None = None
    if prestage_enabled:
        prestage_profile = _profile_for_selection(config, str(selection["prestage"]))
        request = _engine_invocation(
            role="PRESTAGE",
            packet=packet,
            payload_text=payload_text,
            remaining_tokens=budgets["max_tokens"],
            prestage_result=None,
        )
        raw = engine_runner(prestage_profile, request)
        prestage_result = _normalize_engine_result(
            role="PRESTAGE", profile=prestage_profile, raw=raw
        )
        total_tokens += _usage_tokens(prestage_result["usage"])
        if total_tokens > budgets["max_tokens"]:
            raise XenoRuntimeError("MODEL_TOKEN_BUDGET_EXCEEDED_AFTER_PRESTAGE")
        if (time.monotonic() - started) * 1000.0 > budgets["max_wall_ms"]:
            raise XenoRuntimeError("MODEL_WALL_BUDGET_EXCEEDED_AFTER_PRESTAGE")
        steps.append(
            {
                "stage": "PRESTAGE_RESULT",
                "result_sha256": prestage_result["result_sha256"],
                "canonical_truth": False,
            }
        )

    core_profile = _profile_for_selection(config, str(selection["core"]))
    core_request = _engine_invocation(
        role="CORE",
        packet=packet,
        payload_text=payload_text,
        remaining_tokens=budgets["max_tokens"] - total_tokens,
        prestage_result=prestage_result,
    )
    raw_core = engine_runner(core_profile, core_request)
    core_result = _normalize_engine_result(role="CORE", profile=core_profile, raw=raw_core)
    total_tokens += _usage_tokens(core_result["usage"])
    if total_tokens > budgets["max_tokens"]:
        raise XenoRuntimeError("MODEL_TOKEN_BUDGET_EXCEEDED")
    if (time.monotonic() - started) * 1000.0 > budgets["max_wall_ms"]:
        raise XenoRuntimeError("MODEL_WALL_BUDGET_EXCEEDED")
    steps.append({"stage": "CORE_RESULT", "result_sha256": core_result["result_sha256"]})

    candidate_material = {
        "kind": "MODEL_CORE_OUTPUT",
        "event_sha256": packet.event_sha256,
        "admission_sha256": packet.admission_sha256,
        "core_result_sha256": core_result["result_sha256"],
        "text": core_result["text"],
    }
    candidate_digest = _canonical_hash(candidate_material, "ACTION_CANDIDATE")
    action_candidate = {
        "schema": ACTION_CANDIDATE_SCHEMA,
        **candidate_material,
        "candidate_sha256": candidate_digest,
        "canonical_truth": False,
        "effect_authority": False,
        "requires_effect_gate": True,
    }
    steps.append({"stage": "ACTION_CANDIDATE", "result_sha256": candidate_digest})
    trace_sha256 = _trace_hash(steps)

    result = {
        "schema": RUNTIME_SCHEMA,
        "mode": "CORE_PLUS_PRESTAGE" if prestage_enabled else "CORE_ONLY",
        "component_binding": component_binding,
        "component_binding_sha256": component_binding_sha256,
        "entry": steps[0],
        "prestage_result": prestage_result,
        "core_result": core_result,
        "action_candidate": action_candidate,
        "trace": {"schema": TRACE_SCHEMA, "steps": steps, "trace_sha256": trace_sha256},
        "model_calls": required_calls,
        "model_tokens_observed": total_tokens,
        "canonical_truth": False,
        "effect_authority": False,
        "requires_effect_gate": True,
    }
    _require_no_secret_fields(result, "RUNTIME_RESULT")
    return result
