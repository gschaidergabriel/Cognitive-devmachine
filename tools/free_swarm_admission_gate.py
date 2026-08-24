#!/usr/bin/env python3
"""Fail-closed typed provider admission for the EntityOS/HCU FREE swarm.

This module is deliberately non-secret and network-free.  It reads only the
canonical supervisor control surface and returns an allow decision only for an
exact typed provider admission whose cost class is FREE at the same authority
epoch.  PAID, SUBSCRIPTION, UNKNOWN, malformed, missing and stale admissions all
deny before provider-key lookup and before provider network I/O.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY_PATH = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
ADMISSION_SCHEMA = "ENTITYOS_PROVIDER_ADMISSION/v1"
KNOWN_COST_CLASSES = {"FREE", "PAID", "SUBSCRIPTION", "UNKNOWN"}


@dataclass(frozen=True)
class ProviderAdmissionDecision:
    provider: str
    allowed: bool
    cost_class: str
    reason: str
    admission_id: str
    authority_epoch: str
    policy_epoch: str
    secret_lookup_allowed: bool
    network_allowed: bool


def _deny(provider: str, reason: str, *, cost_class: str = "UNKNOWN",
          admission_id: str = "", authority_epoch: str = "",
          policy_epoch: str = "") -> ProviderAdmissionDecision:
    return ProviderAdmissionDecision(
        provider=provider,
        allowed=False,
        cost_class=cost_class if cost_class in KNOWN_COST_CLASSES else "UNKNOWN",
        reason=reason,
        admission_id=admission_id,
        authority_epoch=authority_epoch,
        policy_epoch=policy_epoch,
        secret_lookup_allowed=False,
        network_allowed=False,
    )


def load_policy(path: Path = DEFAULT_POLICY_PATH) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
        obj = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return {}
    return obj if isinstance(obj, dict) else {}


def resolve_provider_admission(provider: str, path: Path = DEFAULT_POLICY_PATH) -> ProviderAdmissionDecision:
    """Resolve a provider without reading provider env vars, key files, or network."""
    provider = provider.strip().lower()
    if not provider:
        return _deny(provider, "PROVIDER_EMPTY")

    policy = load_policy(path)
    if not policy:
        return _deny(provider, "POLICY_MISSING_OR_MALFORMED")

    policy_epoch = str(policy.get("schema_version", ""))
    free_only = policy.get("free_only")
    if not isinstance(free_only, dict):
        return _deny(provider, "FREE_ONLY_CONTROL_MISSING", policy_epoch=policy_epoch)
    if free_only.get("enabled") is not True:
        return _deny(provider, "FREE_ONLY_NOT_EXPLICIT_TRUE", policy_epoch=policy_epoch)
    if free_only.get("provider_execution_requires_typed_explicit_free_classification") is not True:
        return _deny(provider, "TYPED_PROVIDER_ADMISSION_NOT_REQUIRED_BY_POLICY", policy_epoch=policy_epoch)

    admissions = free_only.get("provider_admissions")
    if not isinstance(admissions, dict):
        return _deny(provider, "PROVIDER_ADMISSIONS_MISSING", policy_epoch=policy_epoch)
    item = admissions.get(provider)
    if not isinstance(item, dict):
        return _deny(provider, "PROVIDER_ADMISSION_MISSING", policy_epoch=policy_epoch)

    schema = item.get("schema")
    item_provider = str(item.get("provider", "")).strip().lower()
    authority_epoch = str(item.get("authority_epoch", ""))
    admission_id = str(item.get("admission_id", "")).strip()
    cost_class = str(item.get("cost_class", "UNKNOWN")).upper()

    if schema != ADMISSION_SCHEMA:
        return _deny(provider, "ADMISSION_SCHEMA_MISMATCH", cost_class=cost_class,
                     admission_id=admission_id, authority_epoch=authority_epoch,
                     policy_epoch=policy_epoch)
    if item_provider != provider:
        return _deny(provider, "ADMISSION_PROVIDER_MISMATCH", cost_class=cost_class,
                     admission_id=admission_id, authority_epoch=authority_epoch,
                     policy_epoch=policy_epoch)
    if not admission_id:
        return _deny(provider, "ADMISSION_ID_MISSING", cost_class=cost_class,
                     authority_epoch=authority_epoch, policy_epoch=policy_epoch)
    if authority_epoch != policy_epoch or not policy_epoch:
        return _deny(provider, "ADMISSION_AUTHORITY_EPOCH_STALE_OR_MISSING", cost_class=cost_class,
                     admission_id=admission_id, authority_epoch=authority_epoch,
                     policy_epoch=policy_epoch)
    if cost_class not in KNOWN_COST_CLASSES:
        return _deny(provider, "ADMISSION_COST_CLASS_INVALID", admission_id=admission_id,
                     authority_epoch=authority_epoch, policy_epoch=policy_epoch)
    if cost_class != "FREE":
        return _deny(provider, f"COST_CLASS_{cost_class}_FAIL_CLOSED", cost_class=cost_class,
                     admission_id=admission_id, authority_epoch=authority_epoch,
                     policy_epoch=policy_epoch)
    if item.get("secret_lookup_allowed") is not True:
        return _deny(provider, "SECRET_LOOKUP_NOT_EXPLICITLY_ALLOWED", cost_class=cost_class,
                     admission_id=admission_id, authority_epoch=authority_epoch,
                     policy_epoch=policy_epoch)
    if item.get("network_allowed") is not True:
        return _deny(provider, "NETWORK_NOT_EXPLICITLY_ALLOWED", cost_class=cost_class,
                     admission_id=admission_id, authority_epoch=authority_epoch,
                     policy_epoch=policy_epoch)

    return ProviderAdmissionDecision(
        provider=provider,
        allowed=True,
        cost_class="FREE",
        reason="EXACT_TYPED_FREE_ADMISSION",
        admission_id=admission_id,
        authority_epoch=authority_epoch,
        policy_epoch=policy_epoch,
        secret_lookup_allowed=True,
        network_allowed=True,
    )


def admitted_providers(path: Path = DEFAULT_POLICY_PATH) -> list[str]:
    policy = load_policy(path)
    free_only = policy.get("free_only") if isinstance(policy, dict) else None
    admissions = free_only.get("provider_admissions") if isinstance(free_only, dict) else None
    if not isinstance(admissions, dict):
        return []
    return sorted(
        provider for provider in admissions
        if resolve_provider_admission(str(provider), path).allowed
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Resolve fail-closed EntityOS FREE provider admission")
    p.add_argument("--provider", default="", help="provider name to resolve")
    p.add_argument("--policy", default=str(DEFAULT_POLICY_PATH), help="canonical supervisor JSON path")
    p.add_argument("--list-admitted", action="store_true", help="print admitted provider names")
    p.add_argument("--json", action="store_true", help="print decision JSON")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.policy)
    if args.list_admitted:
        providers = admitted_providers(path)
        print(json.dumps({"schema": "ENTITYOS_PROVIDER_ADMISSION_SET/v1", "providers": providers}, sort_keys=True))
        return 0
    decision = resolve_provider_admission(args.provider, path)
    if args.json:
        print(json.dumps(asdict(decision), sort_keys=True))
    else:
        print(decision.reason)
    return 0 if decision.allowed else 3


if __name__ == "__main__":
    raise SystemExit(main())
