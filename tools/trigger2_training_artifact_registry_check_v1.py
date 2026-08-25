#!/usr/bin/env python3
"""Fail-closed structural validator for Trigger-2 training artifact registry v1.

This checks registry consistency only. It cannot admit training rows or mint runtime,
J-Space, HCU, EntityOS, training, or canonical-truth credit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "CLAY_TRIGGER2_TRAINING_ARTIFACT_REGISTRY/v1"
REQUIRED_ENTRY_FIELDS = {
    "artifact_id",
    "artifact_type",
    "version",
    "status",
    "training_eligible",
    "architecture_target",
    "provenance",
    "predecessor_ids",
    "successor_ids",
    "revision_reason",
    "blockers",
}
NON_ELIGIBLE_STATUSES = {
    "RETROFIT_REQUIRED",
    "COMPONENT_ONLY",
    "QUARANTINE",
    "SUPERSEDED",
    "BLOCKED",
    "PENDING_REVIEW",
    "STALE_RECHECK",
}
PINNED_NEGATIVE = {
    "T2-BINDING-ROUTER-V3": "QUARANTINE",
}
PINNED_CURRENT_CONTRACT = {
    "T2-SEMANTIC-HYPERPOSITION-CONTRACT-V1": "CURRENT_CONTRACT",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def validate(data: dict) -> dict:
    if data.get("schema") != SCHEMA:
        fail(f"schema mismatch: {data.get('schema')!r}")
    status_vocab = set(data.get("status_vocabulary") or [])
    if not status_vocab:
        fail("empty status_vocabulary")
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        fail("entries must be a nonempty list")

    by_id = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            fail(f"entry[{index}] is not an object")
        missing = REQUIRED_ENTRY_FIELDS - set(entry)
        if missing:
            fail(f"{entry.get('artifact_id', index)} missing fields: {sorted(missing)}")
        artifact_id = entry["artifact_id"]
        if artifact_id in by_id:
            fail(f"duplicate artifact_id: {artifact_id}")
        by_id[artifact_id] = entry

        if entry["status"] not in status_vocab:
            fail(f"{artifact_id} unknown status {entry['status']!r}")
        if not isinstance(entry["provenance"], dict) or not entry["provenance"]:
            fail(f"{artifact_id} missing provenance")
        if not isinstance(entry["revision_reason"], str) or not entry["revision_reason"].strip():
            fail(f"{artifact_id} missing revision_reason")
        if not isinstance(entry["architecture_target"], str) or not entry["architecture_target"].strip():
            fail(f"{artifact_id} missing architecture_target")
        if entry["status"] in NON_ELIGIBLE_STATUSES and entry["training_eligible"]:
            fail(f"{artifact_id} cannot be training_eligible while status={entry['status']}")

    for artifact_id, entry in by_id.items():
        for predecessor in entry["predecessor_ids"]:
            if predecessor not in by_id:
                fail(f"{artifact_id} unknown predecessor {predecessor}")
            if artifact_id not in by_id[predecessor]["successor_ids"]:
                fail(f"{artifact_id}<->{predecessor} predecessor/successor lineage not reciprocal")
        for successor in entry["successor_ids"]:
            if successor not in by_id:
                fail(f"{artifact_id} unknown successor {successor}")
            if artifact_id not in by_id[successor]["predecessor_ids"]:
                fail(f"{artifact_id}<->{successor} successor/predecessor lineage not reciprocal")

    for artifact_id, expected in PINNED_NEGATIVE.items():
        actual = by_id.get(artifact_id, {}).get("status")
        if actual != expected:
            fail(f"{artifact_id} negative evidence regression: expected {expected}, got {actual}")

    for artifact_id, expected in PINNED_CURRENT_CONTRACT.items():
        actual = by_id.get(artifact_id, {}).get("status")
        if actual != expected:
            fail(f"{artifact_id} contract regression: expected {expected}, got {actual}")

    if data.get("current_training_credit") != 0:
        fail("registry v1 must not mint training credit")
    if data.get("accepted_dataset_tokens") != 0:
        fail("registry v1 must not claim accepted dataset tokens")

    return {
        "pass": True,
        "schema": SCHEMA,
        "entries": len(entries),
        "statuses": {status: sum(e["status"] == status for e in entries) for status in sorted(status_vocab)},
        "training_eligible_entries": [e["artifact_id"] for e in entries if e["training_eligible"]],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "registry",
        nargs="?",
        default="research_entity/claycode/training/TRIGGER2_TRAINING_ARTIFACT_REGISTRY_V1.json",
    )
    args = parser.parse_args()
    data = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    print(json.dumps(validate(data), sort_keys=True))


if __name__ == "__main__":
    main()
