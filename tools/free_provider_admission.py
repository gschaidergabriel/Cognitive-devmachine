#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

SCHEMA = "ENTITYOS_HCU_PROVIDER_ADMISSION/v1"
CONTROL_PLANE = "ENTITYOS_HCU_CONTROL_PLANE"
KNOWN_PROVIDERS = ("groq", "mistral", "nvidia")
DENY_COST_CLASSES = {"PAID", "SUBSCRIPTION", "UNKNOWN"}


def load_admission(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"admission_unavailable:{exc.__class__.__name__}") from exc
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("admission_invalid_json") from exc
    if not isinstance(obj, dict):
        raise ValueError("admission_not_object")
    return obj


def validate_admission(obj: dict[str, Any], require_all: bool = True) -> tuple[str, ...]:
    if obj.get("schema") != SCHEMA:
        raise ValueError("admission_wrong_schema")
    if obj.get("source") != CONTROL_PLANE:
        raise ValueError("admission_wrong_source")
    if obj.get("free_only") is not True:
        raise ValueError("admission_free_only_not_true")

    providers = obj.get("providers")
    if not isinstance(providers, dict):
        raise ValueError("admission_providers_not_object")

    admitted: list[str] = []
    for provider in KNOWN_PROVIDERS:
        item = providers.get(provider)
        if item is None:
            if require_all:
                raise ValueError(f"provider_missing:{provider}")
            continue
        if not isinstance(item, dict):
            raise ValueError(f"provider_not_object:{provider}")
        cost_class = str(item.get("cost_class", "UNKNOWN")).strip().upper() or "UNKNOWN"
        if cost_class in DENY_COST_CLASSES:
            raise ValueError(f"provider_cost_class_denied:{provider}:{cost_class}")
        if cost_class != "FREE":
            raise ValueError(f"provider_cost_class_invalid:{provider}:{cost_class}")
        if item.get("admitted") is not True:
            raise ValueError(f"provider_not_admitted:{provider}")
        admitted.append(provider)

    extra = sorted(set(providers) - set(KNOWN_PROVIDERS))
    if extra:
        raise ValueError("unknown_provider_entries:" + ",".join(extra))
    if require_all and tuple(admitted) != KNOWN_PROVIDERS:
        raise ValueError("all_provider_free_admission_required")
    if not admitted:
        raise ValueError("no_provider_admitted")
    return tuple(admitted)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--allow-subset", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        admitted = validate_admission(load_admission(args.path), require_all=not args.allow_subset)
    except ValueError as exc:
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
