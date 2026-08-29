#!/usr/bin/env python3
"""Deterministic durable-work cursor primitives for interruption-safe re-entry.

This module grants no authority and executes no external effects. It validates durable
run state, applies evidence-backed node transitions, and computes the next re-entry
classification so a worker does not restart completed work after interruption.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "DURABLE_WORK_CURSOR/v1"
STATES = {
    "PENDING",
    "RUNNING_UNCONFIRMED",
    "COMPLETED",
    "FAILED_RETRYABLE",
    "FAILED_TERMINAL",
    "BLOCKED_EXTERNAL",
    "SUPERSEDED",
}
REENTER_VERIFY = "VERIFY_EXTERNAL_RESULT_BEFORE_RETRY"
REENTER_RESUME = "RESUME_NEXT_NODE"
REENTER_DONE = "RUN_TERMINAL"

ALLOWED_TRANSITIONS = {
    "PENDING": {"RUNNING_UNCONFIRMED", "COMPLETED", "FAILED_RETRYABLE", "FAILED_TERMINAL", "BLOCKED_EXTERNAL", "SUPERSEDED"},
    "RUNNING_UNCONFIRMED": {"COMPLETED", "FAILED_RETRYABLE", "FAILED_TERMINAL", "BLOCKED_EXTERNAL", "SUPERSEDED"},
    "FAILED_RETRYABLE": {"RUNNING_UNCONFIRMED", "COMPLETED", "FAILED_TERMINAL", "BLOCKED_EXTERNAL", "SUPERSEDED"},
    "BLOCKED_EXTERNAL": {"PENDING", "RUNNING_UNCONFIRMED", "COMPLETED", "FAILED_RETRYABLE", "FAILED_TERMINAL", "SUPERSEDED"},
    "COMPLETED": {"SUPERSEDED"},
    "FAILED_TERMINAL": {"SUPERSEDED"},
    "SUPERSEDED": set(),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate(data)
    return data


def validate(cursor: dict[str, Any]) -> None:
    if cursor.get("schema") != SCHEMA:
        raise ValueError(f"schema must be {SCHEMA}")
    for key in ("run_id", "objective", "authority_generation", "nodes"):
        if not cursor.get(key):
            raise ValueError(f"missing required cursor field: {key}")
    if not isinstance(cursor["nodes"], list):
        raise ValueError("nodes must be a list")
    ids: set[str] = set()
    for node in cursor["nodes"]:
        if not isinstance(node, dict):
            raise ValueError("node must be object")
        nid = str(node.get("node_id") or "")
        if not nid or nid in ids:
            raise ValueError("node_id must be non-empty and unique")
        ids.add(nid)
        status = node.get("status")
        if status not in STATES:
            raise ValueError(f"invalid node status for {nid}: {status}")
        attempts = node.get("attempts", 0)
        if not isinstance(attempts, int) or attempts < 0:
            raise ValueError(f"invalid attempts for {nid}")
        if status == "COMPLETED" and not node.get("evidence_refs"):
            raise ValueError(f"completed node requires evidence_refs: {nid}")
    next_id = cursor.get("next_node_id")
    if next_id is not None and next_id not in ids:
        raise ValueError("next_node_id must reference a node or be null")


def new_cursor(run_id: str, objective: str, authority_generation: str,
               nodes: list[dict[str, Any]], source_generation: str | None = None) -> dict[str, Any]:
    normalized = []
    for raw in nodes:
        node = dict(raw)
        node.setdefault("status", "PENDING")
        node.setdefault("attempts", 0)
        node.setdefault("idempotency_key", node.get("node_id"))
        node.setdefault("evidence_refs", [])
        normalized.append(node)
    first = next((n["node_id"] for n in normalized if n["status"] not in {"COMPLETED", "SUPERSEDED"}), None)
    cursor = {
        "schema": SCHEMA,
        "run_id": run_id,
        "objective": objective,
        "authority_generation": authority_generation,
        "source_generation": source_generation,
        "updated_at": now(),
        "nodes": normalized,
        "next_node_id": first,
        "resume_rule": "VERIFY_THEN_CONTINUE",
        "final_message_delivered": False,
    }
    validate(cursor)
    return cursor


def _node(cursor: dict[str, Any], node_id: str) -> dict[str, Any]:
    for node in cursor["nodes"]:
        if node["node_id"] == node_id:
            return node
    raise ValueError(f"unknown node_id: {node_id}")


def _recompute_next(cursor: dict[str, Any]) -> None:
    current = cursor.get("next_node_id")
    if current:
        node = _node(cursor, current)
        if node["status"] in {"PENDING", "RUNNING_UNCONFIRMED", "FAILED_RETRYABLE", "BLOCKED_EXTERNAL"}:
            return
    cursor["next_node_id"] = next(
        (n["node_id"] for n in cursor["nodes"] if n["status"] in {"PENDING", "RUNNING_UNCONFIRMED", "FAILED_RETRYABLE", "BLOCKED_EXTERNAL"}),
        None,
    )


def transition(cursor: dict[str, Any], node_id: str, new_status: str, *,
               evidence_refs: list[str] | None = None, next_discriminator: str | None = None,
               external_identity: str | None = None) -> dict[str, Any]:
    validate(cursor)
    if new_status not in STATES:
        raise ValueError(f"invalid new status: {new_status}")
    out = copy.deepcopy(cursor)
    node = _node(out, node_id)
    old = node["status"]
    if new_status != old and new_status not in ALLOWED_TRANSITIONS[old]:
        raise ValueError(f"illegal transition {old}->{new_status} for {node_id}")
    if new_status == "RUNNING_UNCONFIRMED" and old != "RUNNING_UNCONFIRMED":
        node["attempts"] = int(node.get("attempts", 0)) + 1
    if evidence_refs is not None:
        node["evidence_refs"] = list(evidence_refs)
    if new_status == "COMPLETED" and not node.get("evidence_refs"):
        raise ValueError("COMPLETED requires durable evidence_refs")
    if next_discriminator is not None:
        node["next_discriminator"] = next_discriminator
    if external_identity is not None:
        node["external_identity"] = external_identity
    node["status"] = new_status
    node["updated_at"] = now()
    if out.get("next_node_id") == node_id and new_status in {"COMPLETED", "FAILED_TERMINAL", "SUPERSEDED"}:
        out["next_node_id"] = None
    _recompute_next(out)
    out["updated_at"] = now()
    validate(out)
    return out


def reentry_plan(cursor: dict[str, Any], current_authority_generation: str) -> dict[str, Any]:
    validate(cursor)
    authority_current = cursor["authority_generation"] == current_authority_generation
    unconfirmed = [n for n in cursor["nodes"] if n["status"] == "RUNNING_UNCONFIRMED"]
    if unconfirmed:
        return {
            "classification": REENTER_VERIFY,
            "authority_current": authority_current,
            "verify_node_ids": [n["node_id"] for n in unconfirmed],
            "next_node_id": cursor.get("next_node_id"),
            "completed_node_ids": [n["node_id"] for n in cursor["nodes"] if n["status"] == "COMPLETED"],
        }
    _recompute_next(cursor)
    if cursor.get("next_node_id") is None:
        return {
            "classification": REENTER_DONE,
            "authority_current": authority_current,
            "next_node_id": None,
            "completed_node_ids": [n["node_id"] for n in cursor["nodes"] if n["status"] == "COMPLETED"],
        }
    return {
        "classification": REENTER_RESUME,
        "authority_current": authority_current,
        "requires_execution_surface_reresolution": not authority_current,
        "next_node_id": cursor["next_node_id"],
        "completed_node_ids": [n["node_id"] for n in cursor["nodes"] if n["status"] == "COMPLETED"],
    }


def write_atomic(path: Path, cursor: dict[str, Any]) -> None:
    validate(cursor)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(cursor, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("cursor", type=Path)
    p.add_argument("--current-authority-generation", required=True)
    t = sub.add_parser("transition")
    t.add_argument("cursor", type=Path)
    t.add_argument("node_id")
    t.add_argument("status", choices=sorted(STATES))
    t.add_argument("--evidence-ref", action="append", default=None)
    t.add_argument("--next-discriminator")
    t.add_argument("--external-identity")
    t.add_argument("--write", action="store_true")
    args = ap.parse_args()
    cursor = load(args.cursor)
    if args.cmd == "plan":
        out = reentry_plan(cursor, args.current_authority_generation)
    else:
        out = transition(cursor, args.node_id, args.status, evidence_refs=args.evidence_ref,
                         next_discriminator=args.next_discriminator, external_identity=args.external_identity)
        if args.write:
            write_atomic(args.cursor, out)
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
