#!/usr/bin/env python3
"""Fail-closed canonical atomic-lease admission for Trigger1 V2.

This coordination gate does not acquire a lease and does not run an intervention. It
only verifies that the dispatch references an already-created canonical claim for the
current Trigger1 V2 midlayer causal experiment. Production admission additionally
proves from Git history that the canonical claim path was added exactly once and has
never been modified, replacing content-only trust with create-once provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

RID_RE = re.compile(r"^rid_[0-9a-f]{64}$")
TS_RE = re.compile(r"^ts_[0-9]{8}T[0-9]{12}Z__p_[0-9a-f]{64}$")
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


def _git(cwd: Path, *args: str) -> tuple[int, str, str]:
    try:
        p = subprocess.run(
            ["git", "-C", str(cwd), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as exc:
        return 127, "", f"{type(exc).__name__}:{str(exc)[:300]}"


def _create_once_provenance(claim_path: Path) -> tuple[bool, str, dict[str, Any]]:
    """Prove the current claim blob was added once and never rewritten.

    The canonical Git commit graph is used as a deterministic migration/race fence.
    This does not create a lease; it only prevents a mutable/replaced claim from being
    treated as the create-only lock required by GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.
    """
    rc, root_text, _ = _git(claim_path.parent, "rev-parse", "--show-toplevel")
    if rc or not root_text:
        return False, "CLAIM_GIT_REPO_UNAVAILABLE", {}
    repo_root = Path(root_text).resolve()
    try:
        rel = claim_path.resolve().relative_to(repo_root)
    except ValueError:
        return False, "CLAIM_PATH_OUTSIDE_GIT_REPO", {}
    rel_text = rel.as_posix()

    rc, _, _ = _git(repo_root, "ls-files", "--error-unmatch", "--", rel_text)
    if rc:
        return False, "CLAIM_NOT_TRACKED_AT_EXECUTION_SOURCE", {}

    rc, touches_text, _ = _git(repo_root, "log", "--format=%H", "--", rel_text)
    if rc:
        return False, "CLAIM_GIT_HISTORY_UNAVAILABLE", {}
    touches = [line for line in touches_text.splitlines() if line]

    rc, adds_text, _ = _git(repo_root, "log", "--diff-filter=A", "--format=%H", "--", rel_text)
    if rc:
        return False, "CLAIM_CREATE_HISTORY_UNAVAILABLE", {}
    adds = [line for line in adds_text.splitlines() if line]
    if len(adds) != 1:
        return False, "CLAIM_CREATE_COMMIT_NOT_UNIQUE", {
            "claim_touch_commits": touches,
            "claim_add_commits": adds,
        }
    create_commit = adds[0]
    if len(touches) != 1 or touches[0] != create_commit:
        return False, "CLAIM_NOT_CREATE_ONCE", {
            "claim_touch_commits": touches,
            "claim_add_commit": create_commit,
        }

    rc, current_blob, _ = _git(repo_root, "rev-parse", f"HEAD:{rel_text}")
    if rc or not current_blob:
        return False, "CLAIM_HEAD_BLOB_UNAVAILABLE", {}
    rc, created_blob, _ = _git(repo_root, "rev-parse", f"{create_commit}:{rel_text}")
    if rc or not created_blob:
        return False, "CLAIM_CREATE_BLOB_UNAVAILABLE", {}
    if current_blob != created_blob:
        return False, "CLAIM_CREATE_BLOB_CHANGED", {"claim_create_commit": create_commit}

    rc, worktree_blob, _ = _git(repo_root, "hash-object", rel_text)
    if rc or not worktree_blob:
        return False, "CLAIM_WORKTREE_BLOB_UNAVAILABLE", {}
    if worktree_blob != current_blob:
        return False, "CLAIM_WORKTREE_DIFFERS_FROM_TRACKED_CREATE", {
            "claim_create_commit": create_commit,
            "claim_blob_oid": current_blob,
        }

    return True, "CLAIM_CREATE_ONCE_PROVEN", {
        "claim_create_commit": create_commit,
        "claim_blob_oid": current_blob,
        "claim_touch_commit_count": len(touches),
    }


def parse_trigger_key(issue_body: str) -> str:
    matches = BODY_KEY_RE.findall(issue_body or "")
    if len(matches) != 1:
        raise ValueError("ISSUE_BODY_REQUIRES_EXACTLY_ONE_TRIGGER_KEY")
    key = matches[0]
    if not (RID_RE.fullmatch(key) or TS_RE.fullmatch(key)):
        raise ValueError("TRIGGER_KEY_NONCANONICAL")
    return key


def validate_claim(
    *,
    issue_body: str,
    claims_root: Path,
    expected_experiment: str = EXPECTED_EXPERIMENT,
    require_create_once_provenance: bool = False,
) -> dict[str, Any]:
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
        if isinstance(candidate, dict) and candidate.get("trigger_key") == trigger_key:
            duplicates.append(str(sibling))
    if duplicates:
        return {"pass": False, "reason": "EXPERIMENT_BUDGET_RACE_VIOLATION", "trigger_key": trigger_key, "claim_path": str(claim_path), "semantic_duplicate_claims": sorted(duplicates)}

    provenance: dict[str, Any] = {}
    if require_create_once_provenance:
        provenance_ok, provenance_reason, provenance = _create_once_provenance(claim_path)
        if not provenance_ok:
            return {
                "pass": False,
                "reason": provenance_reason,
                "trigger_key": trigger_key,
                "claim_path": str(claim_path),
                **provenance,
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
        "claim_create_once_provenance_verified": bool(require_create_once_provenance),
        **provenance,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue-body", required=True)
    ap.add_argument("--claims-root", type=Path, default=Path("research_entity/continuity/go_experiment_claims"))
    ap.add_argument("--expected-experiment", default=EXPECTED_EXPERIMENT)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = validate_claim(
        issue_body=args.issue_body,
        claims_root=args.claims_root,
        expected_experiment=args.expected_experiment,
        require_create_once_provenance=True,
    )
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result.get("pass") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
