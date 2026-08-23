#!/usr/bin/env python3
"""Fail-closed discriminator for HCU route causal/engine identity binding.

This is a source/component verifier. It does not mint EntityOS/HCU runtime credit.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

SCHEMA = "HCU_REACTIVE_EVENT/v1"
LOCAL_ENGINE_CLASS = "HCU_LOCAL_08B"
EXTERNAL_ENGINE_CLASS = "EXTERNAL_PROVIDER"


def _load_router(path: Path):
    spec = importlib.util.spec_from_file_location("hcu_router_under_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("ROUTER_IMPORT_SPEC_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "route_event", None)):
        raise RuntimeError("ROUTE_EVENT_CALLABLE_REQUIRED")
    return module


def _base_event(event_id: str, engine_id: str | None, engine_class: str | None = LOCAL_ENGINE_CLASS) -> dict[str, Any]:
    event: dict[str, Any] = {
        "schema": SCHEMA,
        "event_id": event_id,
        "entity_generation": 7,
        "novelty": 0.80,
        "contradiction": 0.0,
        "uncertainty": 0.10,
        "forecast_need": 0.0,
        "effect_pressure": 0.0,
        "zero_relevance": 0.80,
        "due_recheck": False,
    }
    if engine_id is not None:
        event["resolved_cognition_engine"] = {
            "engine_id": engine_id,
            "engine_class": engine_class,
        }
    return event


def _attempt(module, event: dict[str, Any]) -> tuple[str, str | None]:
    try:
        decision = module.route_event(event, current_generation=7)
    except Exception as exc:  # verifier intentionally treats explicit rejection as evidence
        return "REJECTED", f"{exc.__class__.__name__}:{exc}"
    digest = getattr(decision, "decision_sha256", None)
    if not isinstance(digest, str) or len(digest) != 64:
        return "INVALID_DECISION_DIGEST", None
    return "ACCEPTED", digest


def verify(path: Path) -> dict[str, Any]:
    module = _load_router(path)

    same_a1 = _attempt(module, _base_event("evt-A", "hcu-local-a"))
    same_a2 = _attempt(module, _base_event("evt-A", "hcu-local-a"))
    different_event = _attempt(module, _base_event("evt-B", "hcu-local-a"))
    different_engine = _attempt(module, _base_event("evt-A", "hcu-local-b"))
    missing_engine = _attempt(module, _base_event("evt-A", None))
    external_engine = _attempt(module, _base_event("evt-A", "external-nvidia", EXTERNAL_ENGINE_CLASS))

    checks = {
        "same_exact_event_replay_is_deterministic": same_a1[0] == "ACCEPTED" and same_a1 == same_a2,
        "different_causal_event_cannot_alias": (
            same_a1[0] == "ACCEPTED" and
            (different_event[0] == "REJECTED" or different_event[1] != same_a1[1])
        ),
        "different_resolved_engine_cannot_alias": (
            same_a1[0] == "ACCEPTED" and
            (different_engine[0] == "REJECTED" or different_engine[1] != same_a1[1])
        ),
        "model_route_requires_resolved_engine_identity": missing_engine[0] == "REJECTED",
        "external_engine_class_fails_closed": external_engine[0] == "REJECTED",
    }
    passed = all(checks.values())
    return {
        "schema": "HCU_ROUTE_IDENTITY_CONTRACT_CHECK/v1",
        "router": str(path),
        "status": "PASS" if passed else "FAIL",
        "checks": checks,
        "observations": {
            "same_event_engine_first": same_a1,
            "same_event_engine_replay": same_a2,
            "different_event_same_engine": different_event,
            "same_event_different_engine": different_engine,
            "missing_engine": missing_engine,
            "external_engine_class": external_engine,
        },
        "required_identity_formula": "H(canonical_event_identity,resolved_engine_identity,routing_result)",
        "runtime_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("router", type=Path)
    args = parser.parse_args()
    result = verify(args.router)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
