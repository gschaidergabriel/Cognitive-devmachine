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

RID_RE = re.compile(r"^rid_[0-9a-f]{64}$")
TS_RE = re.compile(
    r"^ts_(?P<stamp>[0-9]{8}T[0-9]{12}Z)__p_(?P<payload>[0-9a-f]{64})$"
)
LEGACY_DASH_TS_RE = re.compile(
    r"^(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})T"
    r"(?P<hour>[0-9]{2})-(?P<minute>[0-9]{2})(?:-(?P<second>[0-9]{2}))?"
    r"(?P<sign>[+-])(?P<off_h>[0-9]{2})-(?P<off_m>[0-9]{2})"
    r"(?:__go)?__(?P<payload>[0-9a-f]{12,64})$"
)
LEGACY_COMPACT_TS_RE = re.compile(
    r"^(?P<date>[0-9]{8})T(?P<time>[0-9]{6})"
    r"(?P<sign>[+-])(?P<offset>[0-9]{4})_(?P<payload>[0-9a-f]{12,64})$"
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


def parse_trigger_key(issue_body: str) -> str:
    matches = BODY_KEY_RE.findall(issue_body or "")
    if len(matches) != 1:
        raise ValueError("ISSUE_BODY_REQUIRES_EXACTLY_ONE_TRIGGER_KEY")
    key = matches[0]
    if not (RID_RE.fullmatch(key) or TS_RE.fullmatch(key)):
        raise ValueError("TRIGGER_KEY_NONCANONICAL")
    return key


def _offset(sign: str, hour: str, minute: str) -> dt.timezone:
    delta = dt.timedelta(hours=int(hour), minutes=int(minute))
    if sign == "-":
        delta = -delta
    return dt.timezone(delta)


def _canonical_ts_identity(key: str) -> tuple[dt.datetime, str] | None:
    match = TS_RE.fullmatch(key)
    if not match:
        return None
    stamp = dt.datetime.strptime(match.group("stamp"), "%Y%m%dT%H%M%S%fZ").replace(tzinfo=dt.timezone.utc)
    return stamp, match.group("payload")


def _legacy_ts_identity(key: str) -> tuple[dt.datetime, str, str] | None:
    match = LEGACY_DASH_TS_RE.fullmatch(key)
    if match:
        year, month, day = (int(x) for x in match.group("date").split("-"))
        second_text = match.group("second")
        local = dt.datetime(
            year,
            month,
            day,
            int(match.group("hour")),
            int(match.group("minute")),
            int(second_text or "0"),
            tzinfo=_offset(match.group("sign"), match.group("off_h"), match.group("off_m")),
        )
        precision = "second" if second_text is not None else "minute"
        return local.astimezone(dt.timezone.utc), match.group("payload"), precision

    match = LEGACY_COMPACT_TS_RE.fullmatch(key)
    if match:
        date = match.group("date")
        time = match.group("time")
        offset = match.group("offset")
        local = dt.datetime(
            int(date[0:4]),
            int(date[4:6]),
            int(date[6:8]),
            int(time[0:2]),
            int(time[2:4]),
            int(time[4:6]),
            tzinfo=_offset(match.group("sign"), offset[0:2], offset[2:4]),
        )
        return local.astimezone(dt.timezone.utc), match.group("payload"), "second"
    return None


def _semantic_duplicate_trigger_key(candidate_key: Any, canonical_key: str) -> bool:
    if not isinstance(candidate_key, str):
        return False
    if candidate_key == canonical_key:
        return True

    canonical = _canonical_ts_identity(canonical_key)
    legacy = _legacy_ts_identity(candidate_key)
    if canonical is None or legacy is None:
        return False

    canonical_time, canonical_payload = canonical
    legacy_time, legacy_payload, precision = legacy
    # Historical race-era keys sometimes truncated the payload digest. A matching
    # >=12-hex prefix plus matching normalized timestamp is enough to fail closed.
    if not canonical_payload.startswith(legacy_payload):
        return False
    if precision == "minute":
        return legacy_time.replace(second=0, microsecond=0) == canonical_time.replace(second=0, microsecond=0)
    return legacy_time.replace(microsecond=0) == canonical_time.replace(microsecond=0)


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
        if isinstance(candidate, dict) and _semantic_duplicate_trigger_key(candidate.get("trigger_key"), trigger_key):
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
