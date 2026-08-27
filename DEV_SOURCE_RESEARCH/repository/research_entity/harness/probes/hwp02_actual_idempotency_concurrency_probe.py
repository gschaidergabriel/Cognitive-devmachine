#!/usr/bin/env python3
"""Exercise concurrent same-key retries against the actual H1 reference StateLedger.

Evidence boundary: this is a deterministic Harness probe. A run outside the target Ubuntu
project host is not target-host validation and must be receipted as such.
"""
from __future__ import annotations

import multiprocessing as mp
import tempfile
from pathlib import Path

from research_entity.harness.reference_state_ledger import Mutation, StateLedger

PROV = {
    "origin_actor": "chatgpt-secondary",
    "research_entity": "frank-project-global-research-entity",
    "target": "FRANK H1 reference harness",
    "source_ref": "H-WP-02-IDEMPOTENCY-CONCURRENCY",
}


def worker(db: str, ready: mp.Queue, go: mp.Event, results: mp.Queue, writer: str) -> None:
    ledger = StateLedger(db)
    ready.put(writer)
    go.wait()
    try:
        receipt = ledger.commit(
            event_id="event-1",
            idempotency_key="idem-1",
            base_epoch=0,
            event_type="TEST",
            mutations=[Mutation("world", "door", "closed")],
            provenance=PROV,
            committed_at="2026-08-09T10:20:00Z",
            writer_node=writer,
        )
        results.put((writer, "OK", receipt["status"], receipt["epoch"]))
    except Exception as exc:
        results.put((writer, "ERR", type(exc).__name__, str(exc)))
    finally:
        ledger.close()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="hwp02-concurrency-") as td:
        db = str(Path(td) / "ledger.sqlite")
        seed = StateLedger(db)
        seed.close()
        ready: mp.Queue = mp.Queue()
        results: mp.Queue = mp.Queue()
        go = mp.Event()
        workers = [
            mp.Process(target=worker, args=(db, ready, go, results, "writer-a")),
            mp.Process(target=worker, args=(db, ready, go, results, "writer-b")),
        ]
        for process in workers:
            process.start()
        ready.get(timeout=5)
        ready.get(timeout=5)
        go.set()
        for process in workers:
            process.join(10)
        observed = [results.get(timeout=5), results.get(timeout=5)]

        ledger = StateLedger(db)
        head = ledger.head()
        event_rows = ledger.db.execute("SELECT COUNT(*) FROM ledger_events").fetchone()[0]
        ledger.close()

        statuses = sorted(item[2] for item in observed if item[1] == "OK")
        passed = (
            statuses == ["COMMITTED", "IDEMPOTENT_REPLAY"]
            and head["epoch"] == 1
            and event_rows == 1
        )
        print({"pass": passed, "results": observed, "head": head, "event_rows": event_rows})
        return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
