#!/usr/bin/env python3
"""Fail-closed verifier for the Trigger-3 AI host integration contract.

This tool does not install hooks, call providers, inspect secrets, make network calls,
or create project authority. It verifies a caller-supplied host capability/evidence
record against the current repository entry surfaces and prints one of:
NATIVE, ADAPTED, DEGRADED, BLOCKED.

The repository path is mandatory. No home/Downloads/CWD/clone-path assumption exists.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_STATIC = [
    "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
    "HUMAN_READ_THIS/README.md",
    "DEV_SOURCE_RESEARCH/README.md",
    "DEV_SOURCE_RESEARCH/repository/FRANKENSTEIN_EVIDENCE_INDEX_2026-08-27.json",
]

BOOL_CAPS = [
    "can_read_files",
    "can_write_files",
    "can_run_commands",
    "can_use_git",
    "can_persist_state",
    "can_register_hooks",
    "native_repo_lifecycle",
    "adapter_lifecycle_available",
    "can_make_external_effects",
]

BOOL_EVIDENCE = [
    "minimum_reads_verified",
    "authority_resolved_from_current_inbox",
    "hook_fire_verified",
    "adapter_lifecycle_verified",
    "durable_state_write_verified",
    "effect_request_receipt_verified",
    "effect_result_receipt_verified",
]


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def get_bool(obj: dict[str, Any], key: str) -> bool:
    value = obj.get(key)
    if type(value) is not bool:  # bool only; do not coerce strings/numbers
        raise ValueError(f"{key!r} must be a JSON boolean")
    return value


def resolve_steering(repo: Path, inbox: dict[str, Any]) -> tuple[Path | None, str | None]:
    steering = inbox.get("steering")
    if not isinstance(steering, str) or not steering.strip():
        return None, "SUPERVISOR_INBOX has no concrete steering path"
    steering_path = repo / steering
    if not steering_path.is_file():
        return None, f"selected steering file is missing: {steering}"
    return steering_path, None


def verify_repo(repo: Path) -> dict[str, Any]:
    missing = [rel for rel in REQUIRED_STATIC if not (repo / rel).is_file()]
    if missing:
        return {
            "minimum_repository_entry": False,
            "missing": missing,
            "steering": None,
            "authority_summary": None,
        }

    inbox_path = repo / REQUIRED_STATIC[0]
    try:
        inbox = load_json(inbox_path)
    except Exception as exc:  # fail closed on malformed authority surface
        return {
            "minimum_repository_entry": False,
            "missing": [],
            "steering": None,
            "authority_summary": None,
            "error": f"cannot parse SUPERVISOR_INBOX: {exc}",
        }

    steering_path, steering_error = resolve_steering(repo, inbox)
    if steering_error:
        return {
            "minimum_repository_entry": False,
            "missing": [],
            "steering": None,
            "authority_summary": None,
            "error": steering_error,
        }

    try:
        steering = load_json(steering_path)
    except Exception as exc:
        return {
            "minimum_repository_entry": False,
            "missing": [],
            "steering": str(steering_path.relative_to(repo)),
            "authority_summary": None,
            "error": f"cannot parse selected steering: {exc}",
        }

    return {
        "minimum_repository_entry": True,
        "missing": [],
        "steering": str(steering_path.relative_to(repo)),
        "authority_summary": {
            "inbox_schema_version": inbox.get("schema_version"),
            "supervisor_delta": inbox.get("supervisor_delta"),
            "latest_cycle": inbox.get("latest_cycle"),
            "free_only": inbox.get("free_only"),
            "steering_authority": steering.get("authority"),
            "provider_authority_epoch": steering.get("provider_authority_epoch"),
            "canonical_provider_state": steering.get("canonical_provider_state"),
        },
    }


def classify(cap: dict[str, Any], ev: dict[str, Any], repo_ok: bool) -> tuple[str, list[str]]:
    reasons: list[str] = []

    if not repo_ok:
        return "BLOCKED", ["minimum repository entry/current steering could not be resolved"]

    for key in BOOL_CAPS:
        get_bool(cap, key)
    for key in BOOL_EVIDENCE:
        get_bool(ev, key)

    if not cap["can_read_files"]:
        return "BLOCKED", ["host record says can_read_files=false"]
    if not ev["minimum_reads_verified"]:
        return "BLOCKED", ["minimum_reads_verified=false"]
    if not ev["authority_resolved_from_current_inbox"]:
        return "BLOCKED", ["authority_resolved_from_current_inbox=false"]

    effects_ok = True
    if cap["can_make_external_effects"]:
        effects_ok = bool(ev["effect_request_receipt_verified"] and ev["effect_result_receipt_verified"])
        if not effects_ok:
            reasons.append("external effects are available but request/result receipts are not both verified")

    state_ok = bool(cap["can_persist_state"] and ev["durable_state_write_verified"])
    if not state_ok:
        reasons.append("durable state capability/write evidence is incomplete")

    native_ok = bool(
        cap["native_repo_lifecycle"]
        and cap["can_register_hooks"]
        and ev["hook_fire_verified"]
        and state_ok
        and effects_ok
    )
    if native_ok:
        return "NATIVE", ["native lifecycle, observed hook fire, durable state and required effect receipts verified"]

    adapted_ok = bool(
        cap["adapter_lifecycle_available"]
        and ev["adapter_lifecycle_verified"]
        and state_ok
        and effects_ok
    )
    if adapted_ok:
        return "ADAPTED", ["adapter lifecycle, durable state and required effect receipts verified"]

    if not reasons:
        if cap["native_repo_lifecycle"] and not ev["hook_fire_verified"]:
            reasons.append("native lifecycle claimed but hook fire is not observed")
        if cap["adapter_lifecycle_available"] and not ev["adapter_lifecycle_verified"]:
            reasons.append("adapter lifecycle available but not observed")
        if not cap["native_repo_lifecycle"] and not cap["adapter_lifecycle_available"]:
            reasons.append("no verified native or adapter lifecycle")
    return "DEGRADED", reasons or ["required integration evidence is incomplete"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="Explicit/discovered repository root")
    parser.add_argument("--record", required=True, help="Host capability/evidence JSON record")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    record_path = Path(args.record).expanduser().resolve()

    if not repo.is_dir():
        print(json.dumps({"classification": "BLOCKED", "reason": "repo path is not a directory"}, indent=2))
        return 2

    try:
        record = load_json(record_path)
        cap = record.get("capabilities")
        ev = record.get("evidence")
        if not isinstance(cap, dict) or not isinstance(ev, dict):
            raise ValueError("record must contain JSON objects 'capabilities' and 'evidence'")
        repo_result = verify_repo(repo)
        classification, reasons = classify(cap, ev, bool(repo_result["minimum_repository_entry"]))
    except Exception as exc:
        print(json.dumps({"classification": "BLOCKED", "reason": str(exc)}, indent=2, sort_keys=True))
        return 2

    output = {
        "schema": "FRANKENSTEIN_AI_HOST_INTEGRATION_VERDICT/v1",
        "host": record.get("host") or cap.get("host") or "unknown",
        "classification": classification,
        "reasons": reasons,
        "repository_entry": repo_result,
        "rules": [
            "configuration != observed hook fire",
            "request != effect",
            "effect != reobserved result",
            "this verdict does not grant project/provider/effect authority",
        ],
    }
    print(json.dumps(output, indent=2, sort_keys=True, default=str))
    return 0 if classification in {"NATIVE", "ADAPTED", "DEGRADED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
