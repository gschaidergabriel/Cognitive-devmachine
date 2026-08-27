from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

ANCHOR_PROTOCOL = "UCM2_EVENT_HEAD_ANCHOR_V1"


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class EventHeadAnchor:
    protocol: str
    root_module: str
    schema_version: int
    seq: int
    epoch: int
    event_hash: str
    provenance: dict[str, Any]
    receipt_hash: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "protocol": self.protocol,
            "root_module": self.root_module,
            "schema_version": self.schema_version,
            "seq": self.seq,
            "epoch": self.epoch,
            "event_hash": self.event_hash,
            "provenance": self.provenance,
            "receipt_hash": self.receipt_hash,
        }


def capture_event_head(machine: Any, *, provenance: dict[str, Any]) -> EventHeadAnchor:
    """Create a portable receipt for an externally admitted UCM2 event head.

    This receipt is not authority by itself. Its value is that a caller can
    persist/admit it outside the mutable UCM2 database and later require an
    exact match before accepting replay/recovery state.
    """
    stream = machine.event_stream()
    terminal_hash = machine.verify_event_stream(stream)
    last = stream[-1]
    body = {
        "protocol": ANCHOR_PROTOCOL,
        "root_module": machine.self_read()["root_module"],
        "schema_version": 2,
        "seq": int(last["seq"]),
        "epoch": int(last["epoch"]),
        "event_hash": terminal_hash,
        "provenance": provenance,
    }
    receipt_hash = hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()
    return EventHeadAnchor(**body, receipt_hash=receipt_hash)


def parse_anchor(data: dict[str, Any]) -> EventHeadAnchor:
    required = {
        "protocol",
        "root_module",
        "schema_version",
        "seq",
        "epoch",
        "event_hash",
        "provenance",
        "receipt_hash",
    }
    if set(data) != required:
        raise RuntimeError("EVENT_HEAD_ANCHOR_SHAPE_INVALID")
    anchor = EventHeadAnchor(
        protocol=str(data["protocol"]),
        root_module=str(data["root_module"]),
        schema_version=int(data["schema_version"]),
        seq=int(data["seq"]),
        epoch=int(data["epoch"]),
        event_hash=str(data["event_hash"]),
        provenance=dict(data["provenance"]),
        receipt_hash=str(data["receipt_hash"]),
    )
    body = anchor.as_dict().copy()
    observed_receipt_hash = body.pop("receipt_hash")
    expected_receipt_hash = hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()
    if observed_receipt_hash != expected_receipt_hash:
        raise RuntimeError("EVENT_HEAD_ANCHOR_RECEIPT_HASH_MISMATCH")
    if anchor.protocol != ANCHOR_PROTOCOL:
        raise RuntimeError("EVENT_HEAD_ANCHOR_PROTOCOL_INVALID")
    if anchor.schema_version != 2:
        raise RuntimeError("EVENT_HEAD_ANCHOR_SCHEMA_INVALID")
    if len(anchor.event_hash) != 64 or any(c not in "0123456789abcdef" for c in anchor.event_hash):
        raise RuntimeError("EVENT_HEAD_ANCHOR_EVENT_HASH_INVALID")
    return anchor


def verify_machine_against_anchor(machine: Any, anchor: EventHeadAnchor | dict[str, Any]) -> str:
    anchor = parse_anchor(anchor) if isinstance(anchor, dict) else parse_anchor(anchor.as_dict())
    state = machine.self_read()
    if state["root_module"] != anchor.root_module:
        raise RuntimeError("EVENT_HEAD_ANCHOR_ROOT_MISMATCH")
    stream = machine.event_stream()
    terminal_hash = machine.verify_event_stream(stream)
    last = stream[-1]
    if int(last["seq"]) != anchor.seq:
        raise RuntimeError("EVENT_HEAD_ANCHOR_SEQ_MISMATCH")
    if int(last["epoch"]) != anchor.epoch:
        raise RuntimeError("EVENT_HEAD_ANCHOR_EPOCH_MISMATCH")
    if terminal_hash != anchor.event_hash:
        raise RuntimeError("EVENT_HEAD_ANCHOR_HASH_MISMATCH")
    return terminal_hash
