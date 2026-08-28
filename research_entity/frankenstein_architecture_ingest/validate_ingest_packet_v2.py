#!/usr/bin/env python3
"""Fail-closed Triggerword-5 packet admission validator.

This validates two separate things:
1) the minimum packet shape inherited from INGEST_PACKET_SCHEMA.json; and
2) the v2 ingest-time authority binding against a REFRESHED local `main` ref.

It does not fetch the network and does not execute provider/model/runtime work.
The caller must `git fetch origin main` (or otherwise prove `main` is current)
before using a PASS as current-authority admission evidence.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SUPERVISOR_INBOX = "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
PROVIDER_AUTHORITY = "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
ALLOWED_ACTIONS = {
    "KEEP",
    "REPAIR",
    "ADAPT_TO_GRID",
    "REPLACE_WITH_VERIFIED_SUCCESSOR",
    "COMPATIBILITY_ONLY",
    "RETIRE_WITH_EVIDENCE",
    "UNDECIDED",
}
REQUIRED_PACKET = {
    "packet_id", "created_at", "worker_id", "donor_repo", "donor_sha", "scope",
    "files_examined", "atoms", "hypotheses", "counterhypotheses", "contradictions",
    "critical_unknowns", "recommended_next_spans",
}
REQUIRED_ATOM = {
    "atom_id", "subsystem", "path", "commit_sha", "line_start", "line_end",
    "source_kind", "what_it_does", "runtime_reachable", "target_2_0_action",
}
REQUIRED_AUTH = {
    "authority_epoch", "canonical_main_sha", "supervisor_inbox_path",
    "supervisor_inbox_blob_sha", "selected_steering_path", "selected_steering_blob_sha",
    "free_provider_admission_path", "free_provider_admission_blob_sha",
    "provider_execution_state", "mode", "provider_routes_admitted", "together",
}


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout.strip()


def git_json(repo: Path, ref: str, path: str) -> dict[str, Any]:
    return json.loads(git(repo, "show", f"{ref}:{path}"))


def blob(repo: Path, ref: str, path: str) -> str:
    return git(repo, "rev-parse", f"{ref}:{path}")


def require(cond: bool, errors: list[str], message: str) -> None:
    if not cond:
        errors.append(message)


def validate_shape(packet: dict[str, Any], errors: list[str]) -> None:
    missing = sorted(REQUIRED_PACKET - packet.keys())
    require(not missing, errors, f"missing v1 fields: {missing}")
    require(packet.get("schema_version") == 2, errors, "schema_version must equal 2")
    require(packet.get("authority_classification") in {"CURRENT_AUTHORITY_BOUND", "HISTORICAL_SOURCE_EPOCH"},
            errors, "invalid/missing authority_classification")
    auth = packet.get("authority_binding")
    require(isinstance(auth, dict), errors, "authority_binding must be an object")
    if isinstance(auth, dict):
        missing_auth = sorted(REQUIRED_AUTH - auth.keys())
        require(not missing_auth, errors, f"missing authority_binding fields: {missing_auth}")

    for i, f in enumerate(packet.get("files_examined") or []):
        require(isinstance(f, dict), errors, f"files_examined[{i}] must be object")
        if not isinstance(f, dict):
            continue
        require(all(k in f for k in ("path", "sha_or_blob", "spans_examined")), errors,
                f"files_examined[{i}] missing path/sha_or_blob/spans_examined")
        for j, span in enumerate(f.get("spans_examined") or []):
            require(isinstance(span, dict) and isinstance(span.get("line_start"), int)
                    and isinstance(span.get("line_end"), int), errors,
                    f"files_examined[{i}].spans_examined[{j}] needs integer line_start/line_end")

    for i, atom in enumerate(packet.get("atoms") or []):
        require(isinstance(atom, dict), errors, f"atoms[{i}] must be object")
        if not isinstance(atom, dict):
            continue
        missing_atom = sorted(REQUIRED_ATOM - atom.keys())
        require(not missing_atom, errors, f"atoms[{i}] missing fields: {missing_atom}")
        require(atom.get("target_2_0_action") in ALLOWED_ACTIONS, errors,
                f"atoms[{i}] invalid target_2_0_action={atom.get('target_2_0_action')!r}")
        require(isinstance(atom.get("line_start"), int) and isinstance(atom.get("line_end"), int), errors,
                f"atoms[{i}] line_start/line_end must be integers")


def validate_authority(packet: dict[str, Any], repo: Path, errors: list[str]) -> dict[str, Any]:
    main_sha = git(repo, "rev-parse", "main")
    inbox = git_json(repo, "main", SUPERVISOR_INBOX)
    inbox_blob = blob(repo, "main", SUPERVISOR_INBOX)
    steering_path = str(inbox.get("steering") or "")
    provider_path = str(inbox.get("provider_authority") or PROVIDER_AUTHORITY)
    require(bool(steering_path), errors, "SUPERVISOR_INBOX steering path missing")
    steering_blob = blob(repo, "main", steering_path) if steering_path else ""
    provider_blob = blob(repo, "main", provider_path)
    provider = git_json(repo, "main", provider_path)

    providers = provider.get("providers") or {}
    any_provider_admitted = any(bool(v.get("admitted")) for v in providers.values() if isinstance(v, dict))
    together_obj = provider.get("together") or {}
    together_admitted = bool(together_obj.get("admitted")) if isinstance(together_obj, dict) else False
    expected_routes = any_provider_admitted or together_admitted
    expected_together = "ADMITTED" if together_admitted else "FORBIDDEN"

    auth = packet.get("authority_binding") or {}
    expected = {
        "authority_epoch": str(provider.get("authority_epoch") or inbox.get("schema_version") or ""),
        "canonical_main_sha": main_sha,
        "supervisor_inbox_path": SUPERVISOR_INBOX,
        "supervisor_inbox_blob_sha": inbox_blob,
        "selected_steering_path": steering_path,
        "selected_steering_blob_sha": steering_blob,
        "free_provider_admission_path": provider_path,
        "free_provider_admission_blob_sha": provider_blob,
        "provider_execution_state": str(provider.get("execution_state") or ""),
        "mode": str(provider.get("mode") or ""),
        "provider_routes_admitted": expected_routes,
        "together": expected_together,
    }
    for key, value in expected.items():
        require(auth.get(key) == value, errors,
                f"authority mismatch {key}: packet={auth.get(key)!r} expected={value!r}")

    return {
        "canonical_main_sha": main_sha,
        "supervisor_inbox_blob_sha": inbox_blob,
        "selected_steering_path": steering_path,
        "selected_steering_blob_sha": steering_blob,
        "free_provider_admission_path": provider_path,
        "free_provider_admission_blob_sha": provider_blob,
        "authority_epoch": expected["authority_epoch"],
        "provider_execution_state": expected["provider_execution_state"],
        "mode": expected["mode"],
        "provider_routes_admitted": expected_routes,
        "together": expected_together,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("packet", type=Path)
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    args = ap.parse_args()

    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    errors: list[str] = []
    validate_shape(packet, errors)
    authority: dict[str, Any] = {}
    try:
        authority = validate_authority(packet, args.repo, errors)
    except Exception as exc:
        errors.append(f"authority resolution failed: {type(exc).__name__}: {exc}")

    result = {
        "schema": "TRIGGERWORD5_PACKET_ADMISSION_RESULT/v2",
        "packet_id": packet.get("packet_id"),
        "admitted": not errors,
        "errors": errors,
        "resolved_authority": authority,
        "runtime_credit_delta": 0,
        "note": "PASS proves packet shape/current-authority binding only; it is not donor/runtime/model/training evidence.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
