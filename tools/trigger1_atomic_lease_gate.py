#!/usr/bin/env python3
"""Fail-closed canonical atomic-lease admission for Trigger1 V2.

This coordination gate does not acquire a lease and does not run an intervention. It
only verifies that the dispatch references an already-created canonical claim for the
current Trigger1 V2 midlayer causal experiment and that no known legacy/alternate-key
claim encodes the same user-turn identity.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

RID_RE = re.compile(r"^rid_([0-9a-f]{64})$")
TS_RE = re.compile(r"^ts_([0-9]{8}T[0-9]{12}Z)__p_([0-9a-f]{64})$")
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")
BODY_KEY_RE = re.compile(r"(?m)^trigger_key:\s*(\S+)\s*$")
HEX_TOKEN_RE = re.compile(r"[0-9a-f]{12,64}", re.IGNORECASE)
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


def _parse_claimed_at(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _canonical_ts_datetime(trigger_key: str) -> datetime | None:
    match = TS_RE.fullmatch(trigger_key)
    if not match:
        return None
    return datetime.strptime(match.group(1), "%Y%m%dT%H%M%S%fZ").replace(tzinfo=timezone.utc)


def _hash_prefix_present(text: str, digest: str) -> bool:
    for token in HEX_TOKEN_RE.findall(text.lower()):
        if digest.startswith(token) or token.startswith(digest):
            return True
    return False


def _legacy_semantic_duplicate(*, trigger_key: str, sibling: Path, candidate: Any) -> bool:
    """Recognize known alternate-key encodings of the same immutable go turn.

    Historical races used punctuation/timezone variants and shortened/full payload or
    request digests. We require at least a 12-hex digest token before classifying a
    sibling as the same identity, and for timestamp keys we additionally require the
    sibling claim's claimed_at to normalize to the exact canonical instant.
    """
    candidate_key = candidate.get("trigger_key") if isinstance(candidate, dict) else None
    identity_text = f"{sibling.stem} {candidate_key or ''}"

    rid_match = RID_RE.fullmatch(trigger_key)
    if rid_match:
        return _hash_prefix_present(identity_text, rid_match.group(1))

    ts_match = TS_RE.fullmatch(trigger_key)
    if not ts_match:
        return False
    payload_digest = ts_match.group(2)
    if not _hash_prefix_present(identity_text, payload_digest):
        return False
    if not isinstance(candidate, dict):
        return False
    claimed_at = _parse_claimed_at(candidate.get("claimed_at"))
    canonical_time = _canonical_ts_datetime(trigger_key)
    return claimed_at is not None and canonical_time is not None and claimed_at == canonical_time


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
            candidate = None
        direct_duplicate = isinstance(candidate, dict) and candidate.get("trigger_key") == trigger_key
        semantic_duplicate = _legacy_semantic_duplicate(trigger_key=trigger_key, sibling=sibling, candidate=candidate)
        if direct_duplicate or semantic_duplicate:
            duplicates.append(str(sibling))
    if duplicates:
        return {
            "pass": False,
            "reason": "EXPERIMENT_BUDGET_RACE_VIOLATION",
            "trigger_key": trigger_key,
            "claim_path": str(claim_path),
            "semantic_duplicate_claims": sorted(set(duplicates)),
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
