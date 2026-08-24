#!/usr/bin/env python3
"""Fail-closed EntityOS/HCU FREE_ONLY provider admission boundary.

This module is deliberately stdlib-only and must be evaluated before any provider
secret/key lookup or provider network I/O. Legacy environment attestation variables
are compatibility outputs only; they are never admission authority.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Mapping

SCHEMA = "ENTITYOS_PROVIDER_ADMISSION/v1"
SOURCE = "ENTITYOS_HCU_CONTROL_PLANE"
MODE = "FREE_ONLY"
ALLOWED_COST_CLASSES = frozenset({"FREE", "PAID", "SUBSCRIPTION", "UNKNOWN"})
DEFAULT_ADMISSION_PATH = Path("/artifacts/clay-entityos-swarm/provider_admission.json")
KNOWN_PROVIDERS = ("groq", "mistral", "nvidia")

PROVIDER_SECRET_NAMES: dict[str, tuple[str, ...]] = {
    "groq": ("GROQ_API_KEY", "GROQ2_API_KEY", "GROQ3_API_KEY", "GROQ_API_KEYS"),
    "mistral": ("MISTRAL_API_KEY", "MISTRAL2_API_KEY", "MISTRAL3_API_KEY", "MISTRAL_API_KEYS"),
    "nvidia": (
        "NVIDIA_API_KEY", "NVIDIA_NIM_API_KEY", "NVIDIA2_API_KEY", "NVIDIA3_API_KEY",
        "NGC_API_KEY", "NVIDIA_API_KEYS",
    ),
}
PROVIDER_SECRET_PREFIXES: dict[str, tuple[str, ...]] = {
    "groq": ("GROQ_API_KEY_",),
    "mistral": ("MISTRAL_API_KEY_",),
    "nvidia": ("NVIDIA_API_KEY_", "NVIDIA_NIM_API_KEY_", "NGC_API_KEY_"),
}

_SECRET_FILE_DEFAULTS = (
    "/run/secrets/clay_provider.env",
    "/artifacts/.clay_provider.env",
    "/cache/clay_provider.env",
    "{root}/.clay_provider.env",
    "{root}/research_entity/private/API_TOKENS.env",
    "{root}/research_entity/private/GROQ_API.env",
)
_ENV_ASSIGNMENT = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")

@dataclasses.dataclass(frozen=True)
class ProviderDecision:
    provider: str
    cost_class: str
    admitted: bool
    reason: str

@dataclasses.dataclass(frozen=True)
class Admission:
    schema: str
    source: str
    mode: str
    decision_id: str
    generation: int
    global_free_only: bool
    providers: Mapping[str, ProviderDecision]
    source_path: str
    source_sha256: str

    @property
    def admitted_free_providers(self) -> tuple[str, ...]:
        return tuple(
            name for name, item in self.providers.items()
            if item.admitted and item.cost_class == "FREE"
        )

@dataclasses.dataclass
class BoundaryMetrics:
    admission_reads: int = 0
    secret_lookup_count: int = 0
    network_attempt_count: int = 0

_METRICS = BoundaryMetrics()
_CACHE_KEY: tuple[str, int, int] | None = None
_CACHE_VALUE: Admission | None = None


def reset_metrics() -> None:
    global _METRICS
    _METRICS = BoundaryMetrics()


def metrics_snapshot() -> dict[str, int]:
    return dataclasses.asdict(_METRICS)


def record_network_attempt() -> None:
    """Called immediately before provider network I/O by boundary-aware code/tests."""
    _METRICS.network_attempt_count += 1


def admission_path() -> Path:
    raw = os.getenv("CLAY_PROVIDER_ADMISSION_FILE", "").strip()
    return Path(raw).expanduser() if raw else DEFAULT_ADMISSION_PATH


def _parse_expiry(value: Any) -> dt.datetime | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValueError("expires_at must be an ISO-8601 string")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("expires_at must be timezone-aware")
    return parsed.astimezone(dt.timezone.utc)


def _validate_payload(payload: Any, *, path: Path, raw: bytes) -> Admission:
    if not isinstance(payload, dict):
        raise ValueError("admission payload must be an object")
    if payload.get("schema") != SCHEMA:
        raise ValueError(f"schema must be {SCHEMA}")
    if payload.get("source") != SOURCE:
        raise ValueError(f"source must be {SOURCE}")
    if payload.get("mode") != MODE:
        raise ValueError(f"mode must be {MODE}")
    decision_id = payload.get("decision_id")
    if not isinstance(decision_id, str) or not decision_id.strip():
        raise ValueError("decision_id must be non-empty")
    generation = payload.get("generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise ValueError("generation must be a non-negative integer")
    global_free_only = payload.get("global_free_only") is True
    if not global_free_only:
        raise ValueError("global_free_only must be explicit true")
    expires = _parse_expiry(payload.get("expires_at"))
    if expires is not None and dt.datetime.now(dt.timezone.utc) >= expires:
        raise ValueError("admission expired")
    rows = payload.get("providers")
    if not isinstance(rows, dict) or not rows:
        raise ValueError("providers must be a non-empty object")
    decisions: dict[str, ProviderDecision] = {}
    for raw_name, row in rows.items():
        name = str(raw_name).strip().lower()
        if not name or not isinstance(row, dict):
            raise ValueError("provider decision malformed")
        cost = str(row.get("cost_class", "UNKNOWN")).strip().upper()
        if cost not in ALLOWED_COST_CLASSES:
            raise ValueError(f"invalid cost_class for {name}: {cost}")
        admitted = row.get("admitted") is True
        if admitted and cost != "FREE":
            raise ValueError(f"non-FREE provider cannot be admitted: {name}:{cost}")
        reason = str(row.get("reason", "")).strip()
        decisions[name] = ProviderDecision(name, cost, admitted, reason)
    return Admission(
        schema=SCHEMA,
        source=SOURCE,
        mode=MODE,
        decision_id=decision_id.strip(),
        generation=generation,
        global_free_only=True,
        providers=decisions,
        source_path=str(path),
        source_sha256=hashlib.sha256(raw).hexdigest(),
    )


def load_admission(path: Path | None = None, *, use_cache: bool = True) -> Admission | None:
    """Return a valid typed admission or None. Missing/invalid always fails closed."""
    global _CACHE_KEY, _CACHE_VALUE
    target = path or admission_path()
    try:
        stat = target.stat()
        key = (str(target.resolve()), stat.st_mtime_ns, stat.st_size)
    except OSError:
        return None
    if use_cache and _CACHE_KEY == key:
        return _CACHE_VALUE
    _METRICS.admission_reads += 1
    try:
        raw = target.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        value = _validate_payload(payload, path=target, raw=raw)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        value = None
    if use_cache:
        _CACHE_KEY, _CACHE_VALUE = key, value
    return value


def provider_is_admitted_free(provider: str, admission: Admission | None = None) -> bool:
    current = admission if admission is not None else load_admission()
    if current is None:
        return False
    item = current.providers.get(provider.lower())
    return bool(item and item.admitted and item.cost_class == "FREE")


def _provider_secret_name_allowed(provider: str, name: str) -> bool:
    if name in PROVIDER_SECRET_NAMES.get(provider, ()):
        return True
    return any(name.startswith(prefix) for prefix in PROVIDER_SECRET_PREFIXES.get(provider, ()))


def _strip_env_value(raw: str) -> str:
    value = raw.strip()
    if not value:
        return ""
    if value[0:1] in {"'", '"'} and value[-1:] == value[0]:
        return value[1:-1]
    # Deliberately do not evaluate shell syntax, command substitution or interpolation.
    if "$" in value or "`" in value:
        return ""
    return value


def secret_file_paths(root: Path) -> tuple[Path, ...]:
    override = os.getenv("CLAY_PROVIDER_SECRET_FILES", "").strip()
    if override:
        return tuple(Path(x).expanduser() for x in re.split(r"[:;\n]+", override) if x.strip())
    return tuple(Path(x.format(root=str(root))) for x in _SECRET_FILE_DEFAULTS)


def load_provider_secret_environment(provider: str, root: Path, *, admission: Admission | None = None) -> int:
    """Load only admitted provider key variables, after typed admission.

    Files are parsed as data; shell code is never sourced/evaluated. Returns number of
    environment variables newly populated. Secret metric increments only when an
    admitted provider secret variable is actually inspected/extracted.
    """
    current = admission if admission is not None else load_admission()
    provider = provider.lower()
    if not provider_is_admitted_free(provider, current):
        return 0
    loaded = 0
    for path in secret_file_paths(root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = _ENV_ASSIGNMENT.match(stripped)
            if not match:
                continue
            name, raw_value = match.groups()
            if not _provider_secret_name_allowed(provider, name):
                continue
            _METRICS.secret_lookup_count += 1
            value = _strip_env_value(raw_value)
            if value and not os.getenv(name):
                os.environ[name] = value
                loaded += 1
    return loaded


def read_provider_env_keys(provider: str, *, admission: Admission | None = None) -> dict[str, str]:
    """Read admitted provider key-bearing environment variables only after admission."""
    current = admission if admission is not None else load_admission()
    provider = provider.lower()
    if not provider_is_admitted_free(provider, current):
        return {}
    result: dict[str, str] = {}
    allowed = set(PROVIDER_SECRET_NAMES.get(provider, ()))
    prefixes = PROVIDER_SECRET_PREFIXES.get(provider, ())
    for name, value in os.environ.items():
        if name in allowed or any(name.startswith(prefix) for prefix in prefixes):
            _METRICS.secret_lookup_count += 1
            if value.strip():
                result[name] = value.strip()
    return result


def admission_summary(admission: Admission | None) -> dict[str, Any]:
    if admission is None:
        return {
            "schema": "ENTITYOS_PROVIDER_ADMISSION_STATUS/v1",
            "admitted": False,
            "admitted_free_providers": [],
            "reason": "MISSING_OR_INVALID_TYPED_ADMISSION",
        }
    return {
        "schema": "ENTITYOS_PROVIDER_ADMISSION_STATUS/v1",
        "admitted": bool(admission.admitted_free_providers),
        "decision_id": admission.decision_id,
        "generation": admission.generation,
        "source_sha256": admission.source_sha256,
        "admitted_free_providers": list(admission.admitted_free_providers),
        "providers": {
            name: {"cost_class": item.cost_class, "admitted": item.admitted, "reason": item.reason}
            for name, item in admission.providers.items()
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate EntityOS/HCU FREE_ONLY provider admission")
    p.add_argument("--file", default="")
    p.add_argument("--json", action="store_true")
    p.add_argument("--emit-providers", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    path = Path(args.file).expanduser() if args.file else None
    admission = load_admission(path, use_cache=False)
    if args.emit_providers:
        print(",".join(admission.admitted_free_providers if admission else ()))
    else:
        print(json.dumps(admission_summary(admission), ensure_ascii=False, separators=(",", ":")))
    return 0 if admission is not None and admission.admitted_free_providers else 4


if __name__ == "__main__":
    raise SystemExit(main())
