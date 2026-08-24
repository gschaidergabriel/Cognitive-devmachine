#!/usr/bin/env python3
"""Fail-closed canonical atomic-lease admission for Trigger1 V2.

This coordination gate does not acquire a lease and does not run an intervention. It
only verifies that the dispatch references an already-created canonical claim for the
current Trigger1 V2 midlayer causal experiment.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

RID_RE = re.compile(r"^rid_[0-9a-f]{64}$")
TS_RE = re.compile(r"^ts_[0-9]{8}T[0-9]{12}Z__p_[0-9a-f]{64}$")
TS_PARTS_RE = re.compile(r"^ts_([0-9]{8}T[0-9]{12}Z)__p_([0-9a-f]{64})$")
LEGACY_SHORT_TS_RE = re.compile(r"^ts_([0-9]{8}T[0-9]{12}Z)__p_([0-9a-f]{8,63})$")
LEGACY_OFFSET_KEY_RE = re.compile(r"^([0-9]{8}T[0-9]{6})([+-][0-9]{4}|Z)_([0-9a-f]{8,64})$")
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")
BODY_KEY_RE = re.compile(r"(?m)^trigger_key:\s*(\S+)\s*$")
CLAIM_SCHEMA = "clay-go-experiment-claim/v1"
EXPECTED_EXPERIMENT = "CLAY_TRIGGER1_LOCAL_QWEN06_MIDLAYER_CAUSAL_EXPERIMENT/v1"


def _nonempty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (dict, list)):
        return bool(value)
    return value is not None


def parse_trigger_key(issue_body: str) -> str:
    matches = BODY_KEY_RE.findall(issue_body or "")
    if len(matches) != 1:
        raise ValueError("ISSUE_BODY_REQUIRES_EXACTLY_ONE_TRIGGER_KEY")
    key = matches[0]
    if not (RID_RE.fullmatch(key) or TS_RE.fullmatch(key)):
        raise ValueError("TRIGGER_KEY_NONCANONICAL")
    return key


def _legacy_offset_timestamp_to_canonical_utc(timestamp: str, offset: str) -> str | None:
    try:
        if offset == "Z":
            value = datetime.strptime(timestamp + "+0000", "%Y%m%dT%H%M%S%z")
        else:
            value = datetime.strptime(timestamp + offset, "%Y%m%dT%H%M%S%z")
    except ValueError:
        return None
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S000000Z")


def _semantic_duplicate(trigger_key: str, candidate: dict[str, Any]) -> bool:
    candidate_key = candidate.get("trigger_key")
    if candidate_key == trigger_key:
        return True
    if not isinstance(candidate_key, str):
        return False

    canonical_ts = TS_PARTS_RE.fullmatch(trigger_key)
    if canonical_ts is None:
        # For rid_ identities the immutable source identifier itself is intentionally not
        # persisted by the protocol, so only an exact digest-equivalent key is provable.
        return False

    timestamp, payload_sha256 = canonical_ts.groups()
    trigger = candidate.get("trigger")
    if not isinstance(trigger, str):
        return False
    if hashlib.sha256(trigger.encode("utf-8")).hexdigest() != payload_sha256:
        return False

    short_ts = LEGACY_SHORT_TS_RE.fullmatch(candidate_key)
    if short_ts is not None:
        legacy_timestamp, legacy_payload_prefix = short_ts.groups()
        return legacy_timestamp == timestamp and payload_sha256.startswith(legacy_payload_prefix)

    legacy = LEGACY_OFFSET_KEY_RE.fullmatch(candidate_key)
    if legacy is None:
        return False
    legacy_timestamp, legacy_offset, legacy_payload_prefix = legacy.groups()
    normalized = _legacy_offset_timestamp_to_canonical_utc(legacy_timestamp, legacy_offset)
    return normalized == timestamp and payload_sha256.startswith(legacy_payload_prefix)


def validate_claim(*, issue_body: str, claims_root: Path, expected_experiment: str = EXPECTED_EXPERIMENT) -> dict[str, Any]:
    try:
        trigger_key = parse_trigger_key(issue_body)
    except ValueError as exc:
        return {"pass": False, "reason": str(exc)}

    claim_path = claims_root / f"{trigger_key}.json"
    result_path = claims_root / f"{trigger_key}.result.json"
    if not claim_path.is_file():
        return {"pass": False, "reason": "CANONICAL_ATOMIC_CLAIM_MISSING", "trigger_key": trigger_key, "claim_path": str(claim_path)}
    if result_path.exists():
        return {"pass": False, "reason": "UNUSUAL_EXPERIMENT_RESULT_ALREADY_EXISTS", "trigger_key": trigger_key, "claim_path": str(claim_path), "result_path": str(result_path)}

    raw = claim_path.read_bytes()
    try:
        claim = json.loads(raw.decode("utf-8"))
    except Exception:
        return {"pass": False, "reason": "CLAIM_JSON_INVALID", "trigger_key": trigger_key}
    if not isinstance(claim, dict):
        return {"pass": False, "reason": "CLAIM_NOT_OBJECT", "trigger_key": trigger_key}

    checks = [
        (claim.get("schema") == CLAIM_SCHEMA, "CLAIM_SCHEMA_MISMATCH"),
        (claim.get("trigger_key") == trigger_key, "CLAIM_TRIGGER_KEY_MISMATCH"),
        (claim.get("trigger") == "go", "CLAIM_TRIGGER_MISMATCH"),
        (claim.get("experiment_name") == expected_experiment, "CLAIM_EXPERIMENT_MISMATCH"),
        (claim.get("status") == "CLAIMED", "CLAIM_STATUS_NOT_CLAIMED"),
        (_nonempty(claim.get("claimant_organ")), "CLAIMANT_ORGAN_MISSING"),
        (_nonempty(claim.get("claimed_at")), "CLAIMED_AT_MISSING"),
        (bool(HEAD_RE.fullmatch(str(claim.get("observed_canonical_main", "")))), "OBSERVED_MAIN_INVALID"),
        (_nonempty(claim.get("intervention_contract")), "INTERVENTION_CONTRACT_MISSING"),
    ]
    for ok, reason in checks:
        if not ok:
            return {"pass": False, "reason": reason, "trigger_key": trigger_key, "claim_path": str(claim_path)}

    duplicates: list[str] = []
    for sibling in claims_root.glob("*.json") if claims_root.is_dir() else []:
        if sibling == claim_path or sibling.name.endswith(".result.json"):
            continue
        try:
            candidate = json.loads(sibling.read_text(encoding="utf-8"))
        except Exception:
            continue
        if (
            isinstance(candidate, dict)
            and candidate.get("schema") == CLAIM_SCHEMA
            and _semantic_duplicate(trigger_key, candidate)
        ):
            duplicates.append(str(sibling))
    if duplicates:
        return {"pass": False, "reason": "EXPERIMENT_BUDGET_RACE_VIOLATION", "trigger_key": trigger_key, "claim_path": str(claim_path), "semantic_duplicate_claims": sorted(duplicates)}

    return {
        "pass": True,
        "reason": "CANONICAL_ATOMIC_LEASE_ADMITTED",
        "trigger_key": trigger_key,
        "claim_path": str(claim_path),
        "claim_sha256": hashlib.sha256(raw).hexdigest(),
        "claimant_organ": claim["claimant_organ"],
        "claimed_at": claim["claimed_at"],
        "observed_canonical_main": claim["observed_canonical_main"],
        "experiment_name": claim["experiment_name"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue-body", required=True)
    ap.add_argument("--claims-root", type=Path, default=Path("research_entity/continuity/go_experiment_claims"))
    ap.add_argument("--expected-experiment", default=EXPECTED_EXPERIMENT)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = validate_claim(issue_body=args.issue_body, claims_root=args.claims_root, expected_experiment=args.expected_experiment)
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result.get("pass") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
