#!/usr/bin/env python3
"""Fail-closed validation for the one unusual-experiment lease of an exact `go`.

This module never creates or repairs a lease. It only verifies that a launcher is
covered by an already-created canonical claim and that the claim has not already
produced a terminal result. The atomic CREATE-ONLY write remains external and
must happen before this guard is called.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CLAIMS_ROOT = ROOT / "research_entity/continuity/go_experiment_claims"
CLAIM_SCHEMA = "clay-go-experiment-claim/v1"
RID_RE = re.compile(r"^rid_[0-9a-f]{64}$")
TS_RE = re.compile(r"^ts_[0-9]{20}Z__p_[0-9a-f]{64}$")


def canonical_trigger_key(value: str) -> bool:
    return bool(RID_RE.fullmatch(value) or TS_RE.fullmatch(value))


def validate_claim(
    *,
    trigger_key: str,
    experiment_name: str,
    expected_intervention_contract: dict[str, Any],
    claims_root: Path = CLAIMS_ROOT,
) -> dict[str, Any]:
    """Validate one exact already-created claim; never grant authority on ambiguity."""
    if not canonical_trigger_key(trigger_key):
        return {"ok": False, "reason": "GO_EXPERIMENT_TRIGGER_KEY_NONCANONICAL"}

    claim_path = claims_root / f"{trigger_key}.json"
    result_path = claims_root / f"{trigger_key}.result.json"
    if result_path.exists():
        return {"ok": False, "reason": "GO_EXPERIMENT_LEASE_ALREADY_TERMINAL"}
    try:
        payload = json.loads(claim_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"ok": False, "reason": "GO_EXPERIMENT_CANONICAL_CLAIM_MISSING_OR_INVALID"}
    if not isinstance(payload, dict):
        return {"ok": False, "reason": "GO_EXPERIMENT_CANONICAL_CLAIM_MISSING_OR_INVALID"}
    if payload.get("schema") != CLAIM_SCHEMA:
        return {"ok": False, "reason": "GO_EXPERIMENT_CLAIM_SCHEMA_INVALID"}
    if payload.get("trigger_key") != trigger_key or payload.get("trigger") != "go":
        return {"ok": False, "reason": "GO_EXPERIMENT_CLAIM_IDENTITY_MISMATCH"}
    if payload.get("status") != "CLAIMED":
        return {"ok": False, "reason": "GO_EXPERIMENT_CLAIM_NOT_ACTIVE"}
    if payload.get("experiment_name") != experiment_name:
        return {"ok": False, "reason": "GO_EXPERIMENT_NAME_NOT_CLAIMED"}
    claimant = payload.get("claimant_organ")
    claimed_at = payload.get("claimed_at")
    observed_main = payload.get("observed_canonical_main")
    if not all(isinstance(x, str) and x.strip() for x in (claimant, claimed_at, observed_main)):
        return {"ok": False, "reason": "GO_EXPERIMENT_CLAIM_REQUIRED_IDENTITY_MISSING"}
    if payload.get("intervention_contract") != expected_intervention_contract:
        return {"ok": False, "reason": "GO_EXPERIMENT_INTERVENTION_CONTRACT_MISMATCH"}
    return {
        "ok": True,
        "trigger_key": trigger_key,
        "claim_path": str(claim_path),
        "claimant_organ": claimant,
        "claimed_at": claimed_at,
        "observed_canonical_main": observed_main,
    }
