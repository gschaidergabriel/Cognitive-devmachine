#!/usr/bin/env python3
"""Typed FREE_ONLY provider admission for EntityOS/HCU provider lanes.

This module is deliberately credential-blind and network-blind. It consumes only
a typed control-plane admission object. Missing, malformed, PAID, SUBSCRIPTION or
UNKNOWN provider admission fails closed before any caller is allowed to inspect a
provider credential or perform provider network I/O.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

SCHEMA = "ENTITYOS_HCU_PROVIDER_ADMISSION/v1"
CONTROL_PLANE = "ENTITYOS_HCU_CONTROL_PLANE"
KNOWN_PROVIDERS = ("groq", "mistral", "nvidia")
DENY_COST_CLASSES = {"PAID", "SUBSCRIPTION", "UNKNOWN"}
CANONICAL_ADMISSION = Path(os.getenv("CLAY_PROVIDER_ADMISSION_FILE", "/artifacts/clay-entityos-swarm/provider-admission.json"))


class ProviderAdmissionError(ValueError):
    pass


def load_admission(path: Path = CANONICAL_ADMISSION) -> dict[str, Any]:
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ProviderAdmissionError(f"admission_unavailable:{exc.__class__.__name__}") from exc
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProviderAdmissionError("admission_invalid_json") from exc
    if not isinstance(obj, dict):
        raise ProviderAdmissionError("admission_not_object")
    return obj


def validate_admission(obj: dict[str, Any], require_all: bool = False) -> tuple[str, ...]:
    if obj.get("schema") != SCHEMA:
        raise ProviderAdmissionError("admission_wrong_schema")
    if obj.get("source") != CONTROL_PLANE:
        raise ProviderAdmissionError("admission_wrong_source")
    if obj.get("free_only") is not True:
        raise ProviderAdmissionError("admission_global_free_only_missing")

    providers = obj.get("providers")
    if not isinstance(providers, dict):
        raise ProviderAdmissionError("admission_providers_not_object")

    extra = sorted(set(providers) - set(KNOWN_PROVIDERS))
    if extra:
        raise ProviderAdmissionError("unknown_provider_entries:" + ",".join(extra))

    admitted: list[str] = []
    for provider in KNOWN_PROVIDERS:
        item = providers.get(provider)
        if item is None:
            if require_all:
                raise ProviderAdmissionError(f"provider_missing:{provider}")
            continue
        if not isinstance(item, dict):
            raise ProviderAdmissionError(f"provider_not_object:{provider}")
        cost_class = str(item.get("cost_class", "UNKNOWN")).strip().upper() or "UNKNOWN"
        if cost_class in DENY_COST_CLASSES:
            raise ProviderAdmissionError(f"provider_cost_class_denied:{provider}:{cost_class}")
        if cost_class != "FREE":
            raise ProviderAdmissionError(f"provider_cost_class_invalid:{provider}:{cost_class}")
        if item.get("admitted") is not True:
            raise ProviderAdmissionError(f"provider_not_admitted:{provider}")
        admitted.append(provider)

    if require_all and tuple(admitted) != KNOWN_PROVIDERS:
        raise ProviderAdmissionError("all_provider_free_admission_required")
    if not admitted:
        raise ProviderAdmissionError("no_provider_admitted")
    return tuple(admitted)


def admitted_providers_from_path(path: Path = CANONICAL_ADMISSION) -> tuple[str, ...]:
    return validate_admission(load_admission(Path(path)), require_all=False)


def require_provider_admitted(provider: str, *, path: Path = CANONICAL_ADMISSION) -> None:
    if provider not in KNOWN_PROVIDERS:
        raise ProviderAdmissionError(f"provider_unknown:{provider}")
    admitted = admitted_providers_from_path(path)
    if provider not in admitted:
        raise ProviderAdmissionError(f"provider_missing:{provider}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=CANONICAL_ADMISSION)
    parser.add_argument("--require-all", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        admitted = validate_admission(load_admission(args.path), require_all=args.require_all)
    except ProviderAdmissionError as exc:
        if args.json:
            print(json.dumps({"schema": "FREE_PROVIDER_ADMISSION_CHECK/v1", "allowed": False, "reason": str(exc)}, sort_keys=True))
        else:
            print(f"DENY:{exc}", file=sys.stderr)
        return 3
    if args.json:
        print(json.dumps({"schema": "FREE_PROVIDER_ADMISSION_CHECK/v1", "allowed": True, "providers": admitted}, sort_keys=True))
    else:
        print(",".join(admitted))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
