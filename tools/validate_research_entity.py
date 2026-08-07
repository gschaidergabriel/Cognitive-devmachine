#!/usr/bin/env python3
"""Strict runtime validation for RAE-8.8 canonical JSON, JSONL ledgers and Topic Packets.

Git/raw ledgers remain canonical. This validator fails CI on malformed structured state.
Schemas deliberately permit forward-compatible extra fields while enforcing required
identity/status/provenance structure and value domains.
"""
from __future__ import annotations
import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def load_schema(name: str):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def validate_obj(obj, schema, label: str, errors: list[str]):
    validator = Draft202012Validator(schema)
    for e in sorted(validator.iter_errors(obj), key=lambda x: list(x.path)):
        loc = ".".join(str(x) for x in e.path) or "<root>"
        errors.append(f"{label}:{loc}: {e.message}")


def read_jsonl(path: Path):
    for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="strict").splitlines(), 1):
        if not line.strip():
            continue
        try:
            yield lineno, json.loads(line)
        except json.JSONDecodeError as e:
            yield lineno, e


def main() -> int:
    errors: list[str] = []

    canonical_schema = load_schema("canonical.schema.json")
    claim_schema = load_schema("claim.schema.json")
    event_schema = load_schema("event.schema.json")
    packet_schema = load_schema("topic_packet.schema.json")

    canonical_path = ROOT / "research_entity" / "continuity" / "RESEARCH_ENTITY_CANONICAL.json"
    try:
        canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
        validate_obj(canonical, canonical_schema, str(canonical_path.relative_to(ROOT)), errors)
    except Exception as e:
        errors.append(f"{canonical_path.relative_to(ROOT)}: {e}")

    claims_path = ROOT / "research_entity" / "ledgers" / "CLAIMS.jsonl"
    if claims_path.exists():
        ids = set()
        for lineno, item in read_jsonl(claims_path):
            label = f"{claims_path.relative_to(ROOT)}:{lineno}"
            if isinstance(item, Exception):
                errors.append(f"{label}: invalid JSON: {item}")
                continue
            validate_obj(item, claim_schema, label, errors)
            cid = item.get("claim_id")
            if cid in ids:
                errors.append(f"{label}: duplicate claim_id {cid}")
            ids.add(cid)

    events_root = ROOT / "research_entity" / "events"
    if events_root.exists():
        seen = set()
        for path in sorted(events_root.rglob("*.jsonl")):
            for lineno, item in read_jsonl(path):
                label = f"{path.relative_to(ROOT)}:{lineno}"
                if isinstance(item, Exception):
                    errors.append(f"{label}: invalid JSON: {item}")
                    continue
                validate_obj(item, event_schema, label, errors)
                eid = item.get("event_id")
                if eid and eid in seen:
                    errors.append(f"{label}: duplicate event_id {eid}")
                if eid:
                    seen.add(eid)

    packets_root = ROOT / "research_entity" / "topic_packets"
    if packets_root.exists():
        pids = set()
        for path in sorted(packets_root.rglob("PACKET.json")):
            label = str(path.relative_to(ROOT))
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
            except Exception as e:
                errors.append(f"{label}: invalid JSON: {e}")
                continue
            validate_obj(item, packet_schema, label, errors)
            pid = item.get("packet_id")
            if pid in pids:
                errors.append(f"{label}: duplicate packet_id {pid}")
            pids.add(pid)

    if errors:
        print("RAE schema validation FAILED")
        for e in errors:
            print(" -", e)
        return 1
    print("RAE schema validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
