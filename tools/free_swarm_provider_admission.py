#!/usr/bin/env python3
"""Fail-closed EntityOS/HCU provider admission for FREE_ONLY swarm execution.

This module intentionally has no provider-key or network dependencies. It must run
before any credential lookup or socket/network operation. It validates the shape of
a typed control-plane admission object; it does not prove the external billing state
or authenticity of the control plane by itself.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA = "ENTITYOS_HCU_PROVIDER_ADMISSION/v1"
AUTHORITY = "ENTITYOS_HCU_CONTROL_PLANE"
MODE = "FREE_ONLY"
COST_CLASSES = frozenset({"FREE", "PAID", "SUBSCRIPTION", "UNKNOWN"})
KNOWN_PROVIDERS = frozenset({"groq", "mistral", "nvidia"})


class AdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class ProviderAdmission:
    provider: str
    cost_class: str
    valid_until: dt.datetime | None
    evidence: dict[str, Any]


@dataclass(frozen=True)
class AdmissionDocument:
    admission_id: str
    generation: int
    source_ref: str
    sha256: str
    providers: dict[str, ProviderAdmission]


def _parse_time(value: Any) -> dt.datetime | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise AdmissionError("valid_until must be an ISO-8601 string")
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError as exc:
        raise AdmissionError("invalid valid_until") from exc
    if parsed.tzinfo is None:
        raise AdmissionError("valid_until must be timezone-aware")
    return parsed.astimezone(dt.timezone.utc)


def load_admission(path: str | Path | None) -> AdmissionDocument:
    if not path:
        raise AdmissionError("provider admission file is required")
    p = Path(path)
    try:
        raw = p.read_bytes()
    except OSError as exc:
        raise AdmissionError(f"provider admission unavailable: {exc.__class__.__name__}") from exc
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdmissionError("provider admission is not valid UTF-8 JSON") from exc
    if not isinstance(data, dict):
        raise AdmissionError("provider admission must be an object")
    if data.get("schema") != SCHEMA:
        raise AdmissionError("provider admission schema mismatch")
    if data.get("authority") != AUTHORITY:
        raise AdmissionError("provider admission authority mismatch")
    if data.get("mode") != MODE:
        raise AdmissionError("provider admission mode mismatch")
    admission_id = data.get("admission_id")
    source_ref = data.get("source_ref")
    generation = data.get("generation")
    if not isinstance(admission_id, str) or not admission_id.strip():
        raise AdmissionError("admission_id required")
    if not isinstance(source_ref, str) or not source_ref.strip():
        raise AdmissionError("source_ref required")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
        raise AdmissionError("non-negative integer generation required")
    rows = data.get("providers")
    if not isinstance(rows, dict):
        raise AdmissionError("providers object required")
    providers: dict[str, ProviderAdmission] = {}
    for provider, row in rows.items():
        if provider not in KNOWN_PROVIDERS or not isinstance(row, dict):
            continue
        raw_class = row.get("cost_class", "UNKNOWN")
        cost_class = raw_class.strip().upper() if isinstance(raw_class, str) else "UNKNOWN"
        if cost_class not in COST_CLASSES:
            cost_class = "UNKNOWN"
        try:
            valid_until = _parse_time(row.get("valid_until"))
        except AdmissionError:
            valid_until = dt.datetime.min.replace(tzinfo=dt.timezone.utc)
            cost_class = "UNKNOWN"
        evidence = row.get("cost_evidence")
        if not isinstance(evidence, dict):
            evidence = {}
        providers[provider] = ProviderAdmission(provider, cost_class, valid_until, evidence)
    return AdmissionDocument(
        admission_id=admission_id.strip(),
        generation=generation,
        source_ref=source_ref.strip(),
        sha256=hashlib.sha256(raw).hexdigest(),
        providers=providers,
    )


def effective_cost_class(doc: AdmissionDocument, provider: str, now: dt.datetime | None = None) -> str:
    row = doc.providers.get(provider)
    if row is None:
        return "UNKNOWN"
    if row.cost_class != "FREE":
        return row.cost_class
    instant = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    if row.valid_until is not None and row.valid_until <= instant:
        return "UNKNOWN"
    return "FREE"


def admitted_free_providers(doc: AdmissionDocument, now: dt.datetime | None = None) -> tuple[str, ...]:
    return tuple(sorted(p for p in KNOWN_PROVIDERS if effective_cost_class(doc, p, now) == "FREE"))


def require_provider_free(doc: AdmissionDocument, provider: str, now: dt.datetime | None = None) -> None:
    if effective_cost_class(doc, provider, now) != "FREE":
        raise AdmissionError(f"provider {provider} is not admitted as FREE")


def _main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--list-free", action="store_true")
    ap.add_argument("--provider", choices=sorted(KNOWN_PROVIDERS))
    args = ap.parse_args()
    try:
        doc = load_admission(args.file)
        if args.provider:
            require_provider_free(doc, args.provider)
            print(args.provider)
        elif args.list_free:
            print("\n".join(admitted_free_providers(doc)))
        else:
            print(json.dumps({
                "schema": SCHEMA,
                "admission_id": doc.admission_id,
                "generation": doc.generation,
                "source_ref": doc.source_ref,
                "sha256": doc.sha256,
                "free_providers": admitted_free_providers(doc),
            }, sort_keys=True))
        return 0
    except AdmissionError as exc:
        print(f"ADMISSION_BLOCKED:{exc}")
        return 3


if __name__ == "__main__":
    raise SystemExit(_main())
