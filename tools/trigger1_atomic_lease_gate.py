#!/usr/bin/env python3
"""Fail-closed canonical atomic-lease admission for Trigger1 V2.

This coordination gate does not acquire a lease and does not run an intervention. It
only verifies that the dispatch references an already-created canonical claim for the
current Trigger1 V2 midlayer causal experiment.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
from typing import Any

RID_RE = re.compile(r"^rid_([0-9a-f]{64})$")
TS_RE = re.compile(r"^ts_(\d{8}T\d{12}Z)__p_([0-9a-f]{64})$")
LEGACY_DASHED_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})(?:-(\d{2}))?"
    r"([+-])(\d{2})-(\d{2})(?:__go)?__([0-9a-f]{12,64})$"
)
LEGACY_COMPACT_RE = re.compile(
    r"^(\d{8})T(\d{6})([+-])(\d{4})_([0-9a-f]{12,64})$"
)
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


def _parse_utc_stamp(stamp: str) -> dt.datetime:
    value = dt.datetime.strptime(stamp, "%Y%m%dT%H%M%S%fZ").replace(tzinfo=dt.timezone.utc)
    if value.strftime("%Y%m%dT%H%M%S%fZ") != stamp:
        raise ValueError("CANONICAL_TRIGGER_TIMESTAMP_NONCANONICAL")
    return value


def _canonical_trigger_identity(trigger_key: str) -> dict[str, str]:
    rid = RID_RE.fullmatch(trigger_key)
    if rid:
        return {"kind": "rid", "request_digest": rid.group(1)}
    timestamp = TS_RE.fullmatch(trigger_key)
    if timestamp:
        stamp, payload_digest = timestamp.groups()
        try:
            _parse_utc_stamp(stamp)
        except ValueError as exc:
            raise ValueError("TRIGGER_KEY_NONCANONICAL") from exc
        return {"kind": "ts", "utc_stamp": stamp, "payload_digest": payload_digest}
    raise ValueError("TRIGGER_KEY_NONCANONICAL")


def parse_trigger_key(issue_body: str) -> str:
    matches = BODY_KEY_RE.findall(issue_body or "")
    if len(matches) != 1:
        raise ValueError("ISSUE_BODY_REQUIRES_EXACTLY_ONE_TRIGGER_KEY")
    key = matches[0]
    _canonical_trigger_identity(key)
    return key


def _to_utc_stamp(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
    sign: str,
    offset_hour: int,
    offset_minute: int,
) -> str:
    if offset_hour > 23 or offset_minute > 59:
        raise ValueError("invalid offset")
    offset_seconds = (offset_hour * 60 + offset_minute) * 60
    if sign == "-":
        offset_seconds *= -1
    zone = dt.timezone(dt.timedelta(seconds=offset_seconds))
    value = dt.datetime(year, month, day, hour, minute, second, tzinfo=zone)
    return value.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%S000000Z")


def _legacy_trigger_identity(trigger_key: str) -> dict[str, str] | None:
    dashed = LEGACY_DASHED_RE.fullmatch(trigger_key)
    if dashed:
        (
            year,
            month,
            day,
            hour,
            minute,
            second,
            sign,
            offset_hour,
            offset_minute,
            payload_prefix,
        ) = dashed.groups()
        try:
            stamp = _to_utc_stamp(
                int(year),
                int(month),
                int(day),
                int(hour),
                int(minute),
                int(second or "0"),
                sign,
                int(offset_hour),
                int(offset_minute),
            )
        except ValueError:
            return None
        return {"kind": "ts_legacy", "utc_stamp": stamp, "payload_prefix": payload_prefix}

    compact = LEGACY_COMPACT_RE.fullmatch(trigger_key)
    if compact:
        date_part, time_part, sign, offset_part, payload_prefix = compact.groups()
        try:
            stamp = _to_utc_stamp(
                int(date_part[0:4]),
                int(date_part[4:6]),
                int(date_part[6:8]),
                int(time_part[0:2]),
                int(time_part[2:4]),
                int(time_part[4:6]),
                sign,
                int(offset_part[0:2]),
                int(offset_part[2:4]),
            )
        except ValueError:
            return None
        return {"kind": "ts_legacy", "utc_stamp": stamp, "payload_prefix": payload_prefix}
    return None


def _semantic_trigger_match(current_key: str, candidate_key: str) -> bool:
    current = _canonical_trigger_identity(current_key)
    try:
        candidate = _canonical_trigger_identity(candidate_key)
    except ValueError:
        candidate = None

    if candidate is not None:
        if current["kind"] == "rid":
            return candidate.get("kind") == "rid" and candidate.get("request_digest") == current["request_digest"]
        return (
            candidate.get("kind") == "ts"
            and candidate.get("utc_stamp") == current["utc_stamp"]
            and candidate.get("payload_digest") == current["payload_digest"]
        )

    legacy = _legacy_trigger_identity(candidate_key)
    if legacy is None or current["kind"] != "ts":
        return False
    payload_prefix = legacy["payload_prefix"]
    return legacy["utc_stamp"] == current["utc_stamp"] and current["payload_digest"].startswith(payload_prefix)


def _candidate_trigger_key(path: Path) -> str:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return path.stem
    if isinstance(candidate, dict):
        key = candidate.get("trigger_key")
        if isinstance(key, str) and key:
            return key
    return path.stem


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
        if _semantic_trigger_match(trigger_key, _candidate_trigger_key(sibling)):
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
