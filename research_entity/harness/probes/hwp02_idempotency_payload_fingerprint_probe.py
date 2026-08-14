#!/usr/bin/env python3
"""H-WP-02 red probe: idempotency must bind semantic request identity.

This probe targets the current H1 reference StateLedger implementation. It is expected
to FAIL against the vulnerable implementation and PASS only after retries with the same
idempotency key + event_id but changed event semantics are rejected.

It is a Harness research probe, not production-FRANK evidence.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from research_entity.harness.reference_state_ledger import LedgerError, Mutation, StateLedger

PROV = {
    "origin_actor": "chatgpt-secondary",
    "research_entity": "frank-project-global-research-entity",
    "target": "FRANK H1 reference harness",
    "source_ref": "H-WP-02-IDEMPOTENCY-FINGERPRINT",
}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="hwp02-idem-fp-") as td:
        ledger = StateLedger(Path(td) / "ledger.sqlite")
        first = ledger.commit(
            event_id="event-1",
            idempotency_key="idem-1",
            base_epoch=0,
            event_type="TEST",
            mutations=[Mutation("world", "door", "closed")],
            provenance=PROV,
            committed_at="2026-08-09T10:14:00Z",
            writer_node="probe-a",
        )
        if first["status"] != "COMMITTED":
            print("FAIL: first commit did not commit", first)
            return 2

        try:
            second = ledger.commit(
                event_id="event-1",
                idempotency_key="idem-1",
                base_epoch=0,
                event_type="TEST",
                mutations=[Mutation("world", "door", "open")],
                provenance=PROV,
                committed_at="2026-08-09T10:14:01Z",
                writer_node="probe-b",
            )
        except LedgerError as exc:
            row = ledger.read("world", "door")
            if row is None or row["value"] != "closed" or ledger.head()["epoch"] != 1:
                print("FAIL: conflict was rejected but committed state changed", row, ledger.head())
                return 3
            print("PASS: semantically changed retry rejected:", type(exc).__name__, str(exc))
            return 0

        print("FAIL: changed retry was accepted as", second)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
