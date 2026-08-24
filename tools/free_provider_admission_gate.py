#!/usr/bin/env python3
"""Fail-closed reader for the canonical EntityOS/HCU FREE provider admission object.

This module is intentionally non-secret and network-free. It reads only
FREE_PROVIDER_ADMISSION.json and admits a provider iff the canonical control
plane says admitted=true and cost_class=FREE at the current supervisor epoch.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADMISSION_PATH = ROOT / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
DEFAULT_SUPERVISOR_PATH = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
EXPECTED_SCHEMA = "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION/v1"


@dataclass(frozen=True)
class Decision:
    provider: str
    allowed: bool
    cost_class: str
    reason: str
    authority_epoch: str
    supervisor_epoch: str
    evidence_ref: str


def _read_json(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return obj if isinstance(obj, dict) else {}


def resolve(provider: str, admission_path: Path = DEFAULT_ADMISSION_PATH,
            supervisor_path: Path = DEFAULT_SUPERVISOR_PATH) -> Decision:
    provider = provider.strip().lower()
    admission = _read_json(admission_path)
    supervisor = _read_json(supervisor_path)
    supervisor_epoch = str(supervisor.get("schema_version", ""))
    authority_epoch = str(admission.get("authority_epoch", ""))
    if admission.get("schema") != EXPECTED_SCHEMA:
        return Decision(provider, False, "UNKNOWN", "ADMISSION_SCHEMA_MISSING_OR_MISMATCH", authority_epoch, supervisor_epoch, "")
    if admission.get("mode") != "FREE_ONLY":
        return Decision(provider, False, "UNKNOWN", "ADMISSION_MODE_NOT_FREE_ONLY", authority_epoch, supervisor_epoch, "")
    if authority_epoch != supervisor_epoch or not supervisor_epoch:
        return Decision(provider, False, "UNKNOWN", "ADMISSION_AUTHORITY_EPOCH_STALE_OR_MISSING", authority_epoch, supervisor_epoch, "")
    providers = admission.get("providers")
    item = providers.get(provider) if isinstance(providers, dict) else None
    if not isinstance(item, dict):
        return Decision(provider, False, "UNKNOWN", "PROVIDER_ADMISSION_MISSING", authority_epoch, supervisor_epoch, "")
    cost_class = str(item.get("cost_class", "UNKNOWN")).upper()
    evidence_ref = str(item.get("evidence_ref", ""))
    if item.get("admitted") is not True:
        return Decision(provider, False, cost_class, "PROVIDER_NOT_ADMITTED", authority_epoch, supervisor_epoch, evidence_ref)
    if cost_class != "FREE":
        return Decision(provider, False, cost_class, f"COST_CLASS_{cost_class}_FAIL_CLOSED", authority_epoch, supervisor_epoch, evidence_ref)
    if not evidence_ref:
        return Decision(provider, False, cost_class, "FREE_ADMISSION_EVIDENCE_REF_MISSING", authority_epoch, supervisor_epoch, evidence_ref)
    return Decision(provider, True, "FREE", "EXACT_CANONICAL_FREE_ADMISSION", authority_epoch, supervisor_epoch, evidence_ref)


def admitted_providers(admission_path: Path = DEFAULT_ADMISSION_PATH,
                       supervisor_path: Path = DEFAULT_SUPERVISOR_PATH) -> list[str]:
    admission = _read_json(admission_path)
    providers = admission.get("providers") if isinstance(admission, dict) else None
    if not isinstance(providers, dict):
        return []
    return sorted(name for name in providers if resolve(str(name), admission_path, supervisor_path).allowed)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--provider", default="")
    p.add_argument("--admission", default=str(DEFAULT_ADMISSION_PATH))
    p.add_argument("--supervisor", default=str(DEFAULT_SUPERVISOR_PATH))
    p.add_argument("--list-admitted", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    admission_path, supervisor_path = Path(args.admission), Path(args.supervisor)
    if args.list_admitted:
        print(json.dumps({"schema":"ENTITYOS_HCU_FREE_PROVIDER_ADMISSION_SET/v1","providers":admitted_providers(admission_path, supervisor_path)}, sort_keys=True))
        return 0
    decision = resolve(args.provider, admission_path, supervisor_path)
    print(json.dumps(asdict(decision), sort_keys=True) if args.json else decision.reason)
    return 0 if decision.allowed else 3


if __name__ == "__main__":
    raise SystemExit(main())
