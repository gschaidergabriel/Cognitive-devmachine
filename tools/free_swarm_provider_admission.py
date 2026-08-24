#!/usr/bin/env python3
"""Typed FREE_ONLY provider admission for the EntityOS/HCU Free Swarm.

This module is deliberately secret-blind: it reads only repository control-plane
metadata. Callers MUST invoke it before reading provider credential environment
variables, sourcing provider secret files, or opening provider network sockets.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ADMISSION_PATH = ROOT / "research_entity/claycode/autonomous/FREE_SWARM_PROVIDER_ADMISSION.json"
SUPERVISOR_PATH = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
EXPECTED_SCHEMA = "ENTITYOS_HCU_FREE_SWARM_PROVIDER_ADMISSION/v1"
EXPECTED_MODE = "FREE_ONLY"
EXPECTED_PRODUCT = "EntityOS"
EXPECTED_ARCHITECTURE = "HCU"
EXPECTED_BOUNDARY = "BEFORE_SECRET_OR_KEY_LOOKUP_AND_BEFORE_NETWORK_IO"
POSITIVE_EVIDENCE_STATUS = "VERIFIED_ZERO_MONETARY_COST"
BLOCKED_COST_CLASSES = {"PAID", "SUBSCRIPTION", "UNKNOWN"}
ENV_BY_PROVIDER = {
    "groq": "CLAY_GROQ_FREE_ATTESTED",
    "mistral": "CLAY_MISTRAL_FREE_ATTESTED",
    "nvidia": "CLAY_NVIDIA_FREE_ATTESTED",
}


class ProviderAdmissionError(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProviderAdmissionError(f"CONTROL_JSON_UNAVAILABLE:{path}:{exc.__class__.__name__}") from exc
    if not isinstance(value, dict):
        raise ProviderAdmissionError(f"CONTROL_JSON_OBJECT_REQUIRED:{path}")
    return value


def _parse_time(value: Any, field: str) -> dt.datetime:
    if not isinstance(value, str) or not value.strip():
        raise ProviderAdmissionError(f"{field}:RFC3339_REQUIRED")
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ProviderAdmissionError(f"{field}:RFC3339_INVALID") from exc
    if parsed.tzinfo is None:
        raise ProviderAdmissionError(f"{field}:OFFSET_REQUIRED")
    return parsed.astimezone(dt.timezone.utc)


def load_control(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    admission = _read_json(root / ADMISSION_PATH.relative_to(ROOT))
    supervisor = _read_json(root / SUPERVISOR_PATH.relative_to(ROOT))

    if admission.get("schema") != EXPECTED_SCHEMA:
        raise ProviderAdmissionError("ADMISSION_SCHEMA_UNSUPPORTED")
    if admission.get("mode") != EXPECTED_MODE:
        raise ProviderAdmissionError("ADMISSION_MODE_NOT_FREE_ONLY")
    if admission.get("product") != EXPECTED_PRODUCT:
        raise ProviderAdmissionError("ADMISSION_PRODUCT_MISMATCH")
    if admission.get("compute_architecture") != EXPECTED_ARCHITECTURE:
        raise ProviderAdmissionError("ADMISSION_ARCHITECTURE_MISMATCH")
    if admission.get("admission_boundary") != EXPECTED_BOUNDARY:
        raise ProviderAdmissionError("ADMISSION_BOUNDARY_MISMATCH")

    supervisor_epoch = str(supervisor.get("schema_version", ""))
    if not supervisor_epoch or str(admission.get("authority_epoch", "")) != supervisor_epoch:
        raise ProviderAdmissionError("ADMISSION_AUTHORITY_EPOCH_DRIFT")
    if supervisor.get("active_program") != "ENTITYOS_HCU":
        raise ProviderAdmissionError("SUPERVISOR_PROGRAM_MISMATCH")
    if supervisor.get("product") != EXPECTED_PRODUCT:
        raise ProviderAdmissionError("SUPERVISOR_PRODUCT_MISMATCH")
    if supervisor.get("integrated_cognition_compute_architecture") != EXPECTED_ARCHITECTURE:
        raise ProviderAdmissionError("SUPERVISOR_ARCHITECTURE_MISMATCH")

    free_only = supervisor.get("free_only")
    if not isinstance(free_only, dict):
        raise ProviderAdmissionError("SUPERVISOR_FREE_ONLY_OBJECT_REQUIRED")
    if free_only.get("enabled") is not True:
        raise ProviderAdmissionError("SUPERVISOR_FREE_ONLY_DISABLED")
    if free_only.get("provider_execution_requires_typed_explicit_free_classification") is not True:
        raise ProviderAdmissionError("SUPERVISOR_TYPED_PROVIDER_ADMISSION_REQUIRED")
    if free_only.get("environment_attestation_flag_alone_is_not_provider_admission") is not True:
        raise ProviderAdmissionError("SUPERVISOR_ENV_ATTESTATION_BOUNDARY_MISSING")
    if free_only.get("admission_boundary") != EXPECTED_BOUNDARY:
        raise ProviderAdmissionError("SUPERVISOR_ADMISSION_BOUNDARY_MISMATCH")
    return admission, supervisor


def _record_is_current_free(record: Any, now: dt.datetime) -> bool:
    if not isinstance(record, dict):
        return False
    cost_class = str(record.get("cost_class", "UNKNOWN")).upper()
    if cost_class != "FREE":
        return False
    evidence = record.get("cost_evidence")
    if not isinstance(evidence, dict) or evidence.get("status") != POSITIVE_EVIDENCE_STATUS:
        return False
    sources = evidence.get("sources")
    if not isinstance(sources, list) or not sources or any(not isinstance(x, str) or not x.strip() for x in sources):
        return False
    try:
        checked_at = _parse_time(evidence.get("checked_at"), "cost_evidence.checked_at")
        valid_until = _parse_time(evidence.get("valid_until"), "cost_evidence.valid_until")
    except ProviderAdmissionError:
        return False
    if valid_until <= checked_at or now > valid_until:
        return False
    if evidence.get("scope") != "CURRENT_CONNECTED_ACCOUNT_AND_DECLARED_ENDPOINTS":
        return False
    return True


def provider_is_explicit_free(
    provider: str,
    endpoint: str,
    *,
    root: Path = ROOT,
    now: dt.datetime | None = None,
) -> bool:
    admission, _supervisor = load_control(root)
    providers = admission.get("providers")
    if not isinstance(providers, dict):
        return False
    record = providers.get(provider)
    moment = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    if not _record_is_current_free(record, moment):
        return False
    endpoints = record.get("endpoints") if isinstance(record, dict) else None
    return isinstance(endpoints, list) and endpoint in endpoints


def admitted_provider_names(*, root: Path = ROOT, now: dt.datetime | None = None) -> list[str]:
    admission, _supervisor = load_control(root)
    providers = admission.get("providers")
    if not isinstance(providers, dict):
        return []
    moment = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    return sorted(name for name, record in providers.items() if name in ENV_BY_PROVIDER and _record_is_current_free(record, moment))


def admitted_secret_sources(*, root: Path = ROOT, now: dt.datetime | None = None) -> list[tuple[str, str]]:
    admission, _supervisor = load_control(root)
    providers = admission.get("providers")
    if not isinstance(providers, dict):
        return []
    moment = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    out: list[tuple[str, str]] = []
    for name in sorted(ENV_BY_PROVIDER):
        record = providers.get(name)
        if not _record_is_current_free(record, moment):
            continue
        raw_sources = record.get("secret_sources", []) if isinstance(record, dict) else []
        if not isinstance(raw_sources, list):
            raise ProviderAdmissionError(f"{name}:SECRET_SOURCES_LIST_REQUIRED")
        for source in raw_sources:
            if not isinstance(source, str) or not source or "\x00" in source or "\n" in source or "\r" in source:
                raise ProviderAdmissionError(f"{name}:SECRET_SOURCE_INVALID")
            path = Path(source)
            if path.is_absolute():
                raise ProviderAdmissionError(f"{name}:SECRET_SOURCE_MUST_BE_REPOSITORY_RELATIVE")
            normalized = Path(*path.parts)
            if ".." in normalized.parts:
                raise ProviderAdmissionError(f"{name}:SECRET_SOURCE_TRAVERSAL_FORBIDDEN")
            out.append((name, str(root / normalized)))
    return out


def shell_exports(*, root: Path = ROOT, now: dt.datetime | None = None) -> str:
    admitted = set(admitted_provider_names(root=root, now=now))
    lines = [f"export CLAY_FREE_ONLY_ATTESTED={'1' if admitted else '0'}"]
    for name, env_name in ENV_BY_PROVIDER.items():
        lines.append(f"export {env_name}={'1' if name in admitted else '0'}")
    return "\n".join(lines)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect typed EntityOS/HCU Free Swarm provider admission without reading secrets")
    parser.add_argument("command", choices=("list-free", "secret-sources", "shell-exports", "status"))
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        admitted = admitted_provider_names(root=root)
        if args.command == "list-free":
            for name in admitted:
                print(name)
        elif args.command == "secret-sources":
            for name, source in admitted_secret_sources(root=root):
                print(f"{name}\t{source}")
        elif args.command == "shell-exports":
            print(shell_exports(root=root))
        else:
            print(json.dumps({
                "schema": "ENTITYOS_HCU_FREE_SWARM_PROVIDER_ADMISSION_STATUS/v1",
                "mode": "FREE_ONLY",
                "admitted_providers": admitted,
                "provider_runtime_credit": 0,
                "whole_product_pass": False,
            }, sort_keys=True))
    except ProviderAdmissionError as exc:
        print(f"FREE_SWARM_PROVIDER_ADMISSION_REJECTED:{exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
