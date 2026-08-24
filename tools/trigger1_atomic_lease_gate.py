#!/usr/bin/env python3
"""Fail-closed canonical atomic-lease admission for Trigger1 V2.

This coordination gate does not acquire a lease and does not run an intervention. It
only verifies that the dispatch references an already-created canonical claim for the
current Trigger1 V2 midlayer causal experiment.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

RID_RE = re.compile(r"^rid_[0-9a-f]{64}$")
TS_RE = re.compile(r"^ts_([0-9]{8}T[0-9]{12}Z)__p_([0-9a-f]{64})$")
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")
BODY_KEY_RE = re.compile(r"(?m)^trigger_key:\s*(\S+)\s*$")
LEGACY_MINUTE_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})([+-])(\d{2})-(\d{2})__(?:go__)?([0-9a-f]{12,64})$"
)
LEGACY_SECOND_RE = re.compile(r"^(\d{8}T\d{6})([+-])(\d{2})(\d{2})_([0-9a-f]{12,64})$")
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


def _digest_alias(a: str, b: str) -> bool:
    """Historical keys used shortened payload hashes; a prefix match is ambiguous."""
    if len(a) < 12 or len(b) < 12:
        return False
    return a.startswith(b) or b.startswith(a)


def _canonical_ts_parts(trigger_key: str) -> tuple[datetime, str] | None:
    match = TS_RE.fullmatch(trigger_key)
    if not match:
        return None
    stamp, payload_sha = match.groups()
    parsed = datetime.strptime(stamp, "%Y%m%dT%H%M%S%fZ").replace(tzinfo=timezone.utc)
    return parsed, payload_sha


def _legacy_semantic_alias(candidate_key: str, canonical_key: str) -> bool:
    """Detect historical/noncanonical aliases of a canonical timestamp key.

    Old claims used minute-local timestamps and shortened payload hashes. They cannot
    become a second lease merely because a later formatter is stricter. Minute-level
    legacy keys therefore close the overlapping minute for the same payload digest.
    """
    if candidate_key == canonical_key:
        return True
    canonical = _canonical_ts_parts(canonical_key)
    if canonical is None:
        return False
    canonical_time, canonical_payload_sha = canonical

    minute = LEGACY_MINUTE_RE.fullmatch(candidate_key)
    if minute:
        year, month, day, hour, minute_value, sign, off_h, off_m, digest = minute.groups()
        offset_minutes = int(off_h) * 60 + int(off_m)
        if sign == "-":
            offset_minutes = -offset_minutes
        local = datetime(
            int(year), int(month), int(day), int(hour), int(minute_value),
            tzinfo=timezone(timedelta(minutes=offset_minutes)),
        )
        legacy_utc = local.astimezone(timezone.utc)
        same_minute = canonical_time.replace(second=0, microsecond=0) == legacy_utc.replace(second=0, microsecond=0)
        return same_minute and _digest_alias(digest, canonical_payload_sha)

    second = LEGACY_SECOND_RE.fullmatch(candidate_key)
    if second:
        stamp, sign, off_h, off_m, digest = second.groups()
        offset_minutes = int(off_h) * 60 + int(off_m)
        if sign == "-":
            offset_minutes = -offset_minutes
        naive = datetime.strptime(stamp, "%Y%m%dT%H%M%S")
        legacy = naive.replace(tzinfo=timezone(timedelta(minutes=offset_minutes))).astimezone(timezone.utc)
        return canonical_time.replace(microsecond=0) == legacy.replace(microsecond=0) and _digest_alias(
            digest, canonical_payload_sha
        )

    return False


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

        # Historical coordination was encoded in both filenames and payload fields.
        # A damaged/non-JSON legacy file with an aliasing filename remains ambiguous
        # evidence and must fail closed rather than silently reopening the budget.
        filename_key = sibling.name[:-5]
        if filename_key == trigger_key or _legacy_semantic_alias(filename_key, trigger_key):
            duplicates.append(str(sibling))
            continue

        try:
            candidate = json.loads(sibling.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(candidate, dict):
            continue
        candidate_key = str(candidate.get("trigger_key") or "")
        if candidate_key == trigger_key or _legacy_semantic_alias(candidate_key, trigger_key):
            duplicates.append(str(sibling))
    if duplicates:
        return {
            "pass": False,
            "reason": "EXPERIMENT_BUDGET_RACE_VIOLATION",
            "trigger_key": trigger_key,
            "claim_path": str(claim_path),
            "semantic_duplicate_claims": sorted(duplicates),
        }

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
