#!/usr/bin/env python3
"""H1 Reference Harness canonical state/event ledger.

Research-Entity implementation for FRANK Harness H-WP-02.
This module is deliberately separate from FRANK itself. It provides:
- deterministic canonical JSON and SHA-256 state identity;
- append-only event receipts with hash chaining;
- monotonic epochs with compare-and-swap base_epoch checks;
- transaction-safe semantic idempotency;
- explicit epistemic state preservation;
- provenance-bound mutations;
- deterministic snapshot/export and verified restore.

It is a reference harness component, not production FRANK evidence.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "h1-ledger-0.1"
ALLOWED_EPISTEMIC_STATES = {
    "KNOWN", "UNKNOWN", "CONFLICT", "REVOKED", "HYPOTHESIS", "OBSERVED",
}
GENESIS_HASH = "0" * 64


class LedgerError(RuntimeError):
    pass


class StaleEpoch(LedgerError):
    pass


class TamperDetected(LedgerError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_hex(value: Any) -> str:
    if isinstance(value, bytes):
        blob = value
    elif isinstance(value, str):
        blob = value.encode("utf-8")
    else:
        blob = canonical_bytes(value)
    return hashlib.sha256(blob).hexdigest()


@dataclass(frozen=True)
class Mutation:
    domain: str
    key: str
    value: Any
    epistemic_state: str = "KNOWN"

    def normalized(self) -> dict[str, Any]:
        if self.epistemic_state not in ALLOWED_EPISTEMIC_STATES:
            raise LedgerError(f"unsupported epistemic_state={self.epistemic_state!r}")
        if not self.domain or not self.key:
            raise LedgerError("domain and key must be non-empty")
        return {
            "domain": self.domain,
            "key": self.key,
            "value": self.value,
            "epistemic_state": self.epistemic_state,
        }


class StateLedger:
    def __init__(self, db_path: str | Path):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=8.0, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=8000")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self._install()

    def close(self) -> None:
        self.db.close()

    def _install(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS ledger_meta(
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ledger_epochs(
              epoch INTEGER PRIMARY KEY,
              parent_epoch INTEGER,
              event_id TEXT UNIQUE,
              root_hash TEXT NOT NULL,
              event_hash TEXT NOT NULL,
              committed_at TEXT NOT NULL,
              writer_node TEXT NOT NULL,
              FOREIGN KEY(parent_epoch) REFERENCES ledger_epochs(epoch)
            );
            CREATE TABLE IF NOT EXISTS ledger_events(
              event_id TEXT PRIMARY KEY,
              idempotency_key TEXT NOT NULL UNIQUE,
              base_epoch INTEGER NOT NULL,
              committed_epoch INTEGER NOT NULL UNIQUE,
              event_type TEXT NOT NULL,
              mutations_json TEXT NOT NULL,
              provenance_json TEXT NOT NULL,
              previous_event_hash TEXT NOT NULL,
              event_hash TEXT NOT NULL UNIQUE,
              post_root_hash TEXT NOT NULL,
              committed_at TEXT NOT NULL,
              writer_node TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ledger_state(
              domain TEXT NOT NULL,
              state_key TEXT NOT NULL,
              value_json TEXT NOT NULL,
              epistemic_state TEXT NOT NULL,
              source_event_id TEXT NOT NULL,
              source_epoch INTEGER NOT NULL,
              provenance_json TEXT NOT NULL,
              PRIMARY KEY(domain,state_key)
            );
            CREATE TABLE IF NOT EXISTS ledger_snapshots(
              snapshot_id TEXT PRIMARY KEY,
              epoch INTEGER NOT NULL,
              root_hash TEXT NOT NULL,
              event_hash TEXT NOT NULL,
              payload_hash TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              created_at TEXT NOT NULL,
              created_by TEXT NOT NULL,
              recovery_test_state TEXT NOT NULL DEFAULT 'UNTESTED'
            );
            """
        )
        row = self.db.execute("SELECT COUNT(*) AS n FROM ledger_epochs").fetchone()
        if row["n"] == 0:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                self.db.execute(
                    "INSERT INTO ledger_epochs(epoch,parent_epoch,event_id,root_hash,event_hash,committed_at,writer_node)"
                    " VALUES(0,NULL,NULL,?,?,?,?)",
                    (self._root_hash([]), GENESIS_HASH, "1970-01-01T00:00:00Z", "GENESIS"),
                )
                self.db.execute(
                    "INSERT OR REPLACE INTO ledger_meta(key,value) VALUES('schema_version',?)",
                    (SCHEMA_VERSION,),
                )
                self.db.execute("COMMIT")
            except Exception:
                self.db.execute("ROLLBACK")
                raise

    @staticmethod
    def _root_hash(rows: Iterable[dict[str, Any]]) -> str:
        normalized = [
            {
                "domain": r["domain"],
                "key": r["key"],
                "value": r["value"],
                "epistemic_state": r["epistemic_state"],
            }
            for r in rows
        ]
        normalized.sort(key=lambda r: (r["domain"], r["key"]))
        return sha256_hex({"schema": SCHEMA_VERSION, "state": normalized})

    def _state_rows(self) -> list[dict[str, Any]]:
        rows = self.db.execute(
            "SELECT domain,state_key,value_json,epistemic_state,source_event_id,source_epoch,provenance_json"
            " FROM ledger_state ORDER BY domain,state_key"
        ).fetchall()
        return [
            {
                "domain": r["domain"],
                "key": r["state_key"],
                "value": json.loads(r["value_json"]),
                "epistemic_state": r["epistemic_state"],
                "source_event_id": r["source_event_id"],
                "source_epoch": r["source_epoch"],
                "provenance": json.loads(r["provenance_json"]),
            }
            for r in rows
        ]

    def head(self) -> dict[str, Any]:
        r = self.db.execute(
            "SELECT epoch,root_hash,event_hash,committed_at,writer_node FROM ledger_epochs ORDER BY epoch DESC LIMIT 1"
        ).fetchone()
        return dict(r)

    def read(self, domain: str, key: str) -> dict[str, Any] | None:
        r = self.db.execute(
            "SELECT domain,state_key,value_json,epistemic_state,source_event_id,source_epoch,provenance_json"
            " FROM ledger_state WHERE domain=? AND state_key=?",
            (domain, key),
        ).fetchone()
        if not r:
            return None
        return {
            "domain": r["domain"],
            "key": r["state_key"],
            "value": json.loads(r["value_json"]),
            "epistemic_state": r["epistemic_state"],
            "source_event_id": r["source_event_id"],
            "source_epoch": r["source_epoch"],
            "provenance": json.loads(r["provenance_json"]),
        }

    @staticmethod
    def _same_semantic_request(
        existing: sqlite3.Row,
        *,
        event_id: str,
        base_epoch: int,
        event_type: str,
        mutations_json: str,
        provenance_json: str,
    ) -> bool:
        return (
            existing["event_id"] == event_id
            and existing["base_epoch"] == base_epoch
            and existing["event_type"] == event_type
            and existing["mutations_json"] == mutations_json
            and existing["provenance_json"] == provenance_json
        )

    def commit(
        self,
        *,
        event_id: str,
        idempotency_key: str,
        base_epoch: int,
        event_type: str,
        mutations: Iterable[Mutation],
        provenance: dict[str, Any],
        committed_at: str,
        writer_node: str,
    ) -> dict[str, Any]:
        if not event_id or not idempotency_key or not event_type or not writer_node:
            raise LedgerError("event_id, idempotency_key, event_type and writer_node are required")
        if not provenance:
            raise LedgerError("provenance must be explicit and non-empty")
        norm_mutations = [m.normalized() for m in mutations]
        if not norm_mutations:
            raise LedgerError("at least one mutation is required")
        provenance_json = canonical_bytes(provenance).decode("utf-8")
        mutations_json = canonical_bytes(norm_mutations).decode("utf-8")

        # Resolve idempotency under the same write lock as the first commit. This closes
        # the pre-lock TOCTOU race and rejects same-key retries whose semantic request
        # differs. Execution-local retry metadata (writer/timestamp) is deliberately not
        # part of semantic identity.
        self.db.execute("BEGIN IMMEDIATE")
        try:
            existing = self.db.execute(
                "SELECT event_id,base_epoch,event_type,mutations_json,provenance_json,"
                "committed_epoch,event_hash,post_root_hash FROM ledger_events WHERE idempotency_key=?",
                (idempotency_key,),
            ).fetchone()
            if existing:
                if not self._same_semantic_request(
                    existing,
                    event_id=event_id,
                    base_epoch=base_epoch,
                    event_type=event_type,
                    mutations_json=mutations_json,
                    provenance_json=provenance_json,
                ):
                    raise LedgerError("idempotency key reused with changed semantic request")
                self.db.execute("COMMIT")
                return {
                    "status": "IDEMPOTENT_REPLAY",
                    "event_id": existing["event_id"],
                    "epoch": existing["committed_epoch"],
                    "event_hash": existing["event_hash"],
                    "root_hash": existing["post_root_hash"],
                }

            head = self.head()
            if head["epoch"] != base_epoch:
                raise StaleEpoch(f"base_epoch={base_epoch} current_epoch={head['epoch']}")
            new_epoch = base_epoch + 1

            for m in norm_mutations:
                self.db.execute(
                    """
                    INSERT INTO ledger_state(domain,state_key,value_json,epistemic_state,source_event_id,source_epoch,provenance_json)
                    VALUES(?,?,?,?,?,?,?)
                    ON CONFLICT(domain,state_key) DO UPDATE SET
                      value_json=excluded.value_json,
                      epistemic_state=excluded.epistemic_state,
                      source_event_id=excluded.source_event_id,
                      source_epoch=excluded.source_epoch,
                      provenance_json=excluded.provenance_json
                    """,
                    (
                        m["domain"], m["key"], canonical_bytes(m["value"]).decode("utf-8"),
                        m["epistemic_state"], event_id, new_epoch, provenance_json,
                    ),
                )

            post_root = self._root_hash(self._state_rows())
            event_body = {
                "schema": SCHEMA_VERSION,
                "event_id": event_id,
                "idempotency_key": idempotency_key,
                "base_epoch": base_epoch,
                "committed_epoch": new_epoch,
                "event_type": event_type,
                "mutations": norm_mutations,
                "provenance": provenance,
                "previous_event_hash": head["event_hash"],
                "post_root_hash": post_root,
                "committed_at": committed_at,
                "writer_node": writer_node,
            }
            event_hash = sha256_hex(event_body)
            self.db.execute(
                """
                INSERT INTO ledger_events(
                  event_id,idempotency_key,base_epoch,committed_epoch,event_type,mutations_json,
                  provenance_json,previous_event_hash,event_hash,post_root_hash,committed_at,writer_node
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    event_id, idempotency_key, base_epoch, new_epoch, event_type, mutations_json,
                    provenance_json, head["event_hash"], event_hash, post_root, committed_at, writer_node,
                ),
            )
            self.db.execute(
                """
                INSERT INTO ledger_epochs(epoch,parent_epoch,event_id,root_hash,event_hash,committed_at,writer_node)
                VALUES(?,?,?,?,?,?,?)
                """,
                (new_epoch, base_epoch, event_id, post_root, event_hash, committed_at, writer_node),
            )
            self.db.execute("COMMIT")
            return {
                "status": "COMMITTED",
                "event_id": event_id,
                "epoch": new_epoch,
                "event_hash": event_hash,
                "root_hash": post_root,
            }
        except Exception:
            try:
                self.db.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise

    def verify(self) -> dict[str, Any]:
        events = self.db.execute("SELECT * FROM ledger_events ORDER BY committed_epoch").fetchall()
        prev = GENESIS_HASH
        expected_epoch = 1
        for e in events:
            if e["committed_epoch"] != expected_epoch:
                raise TamperDetected("non-contiguous epoch sequence")
            if e["previous_event_hash"] != prev:
                raise TamperDetected("event hash chain broken")
            body = {
                "schema": SCHEMA_VERSION,
                "event_id": e["event_id"],
                "idempotency_key": e["idempotency_key"],
                "base_epoch": e["base_epoch"],
                "committed_epoch": e["committed_epoch"],
                "event_type": e["event_type"],
                "mutations": json.loads(e["mutations_json"]),
                "provenance": json.loads(e["provenance_json"]),
                "previous_event_hash": e["previous_event_hash"],
                "post_root_hash": e["post_root_hash"],
                "committed_at": e["committed_at"],
                "writer_node": e["writer_node"],
            }
            actual = sha256_hex(body)
            if actual != e["event_hash"]:
                raise TamperDetected(f"event hash mismatch at epoch {expected_epoch}")
            prev = actual
            expected_epoch += 1

        calculated_root = self._root_hash(self._state_rows())
        head = self.head()
        if calculated_root != head["root_hash"]:
            raise TamperDetected("canonical state root hash mismatch")
        if prev != head["event_hash"]:
            raise TamperDetected("head event hash mismatch")
        return {
            "status": "PASS", "events": len(events), "epoch": head["epoch"],
            "root_hash": head["root_hash"], "event_hash": head["event_hash"],
        }

    def snapshot(self, *, snapshot_id: str, created_at: str, created_by: str) -> dict[str, Any]:
        verified = self.verify()
        payload = {
            "schema": SCHEMA_VERSION,
            "epoch": verified["epoch"],
            "root_hash": verified["root_hash"],
            "event_hash": verified["event_hash"],
            "state": self._state_rows(),
        }
        payload_json = canonical_bytes(payload).decode("utf-8")
        payload_hash = sha256_hex(payload_json)
        self.db.execute(
            """
            INSERT INTO ledger_snapshots(snapshot_id,epoch,root_hash,event_hash,payload_hash,payload_json,created_at,created_by,recovery_test_state)
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                snapshot_id, payload["epoch"], payload["root_hash"], payload["event_hash"],
                payload_hash, payload_json, created_at, created_by, "UNTESTED",
            ),
        )
        return {"snapshot_id": snapshot_id, "payload_hash": payload_hash, **payload}

    def export_snapshot(self, snapshot_id: str, path: str | Path) -> Path:
        r = self.db.execute(
            "SELECT payload_hash,payload_json FROM ledger_snapshots WHERE snapshot_id=?",
            (snapshot_id,),
        ).fetchone()
        if not r:
            raise LedgerError("snapshot not found")
        p = Path(path)
        p.write_text(r["payload_json"], encoding="utf-8")
        if sha256_hex(p.read_text(encoding="utf-8")) != r["payload_hash"]:
            raise TamperDetected("snapshot write verification failed")
        return p

    @classmethod
    def restore_snapshot(cls, snapshot_path: str | Path, db_path: str | Path) -> "StateLedger":
        raw = Path(snapshot_path).read_text(encoding="utf-8")
        payload = json.loads(raw)
        if payload.get("schema") != SCHEMA_VERSION:
            raise LedgerError("snapshot schema mismatch")
        ledger = cls(db_path)
        ledger.db.execute("BEGIN IMMEDIATE")
        try:
            ledger.db.execute("DELETE FROM ledger_state")
            ledger.db.execute("DELETE FROM ledger_events")
            ledger.db.execute("DELETE FROM ledger_epochs")
            ledger.db.execute(
                "INSERT INTO ledger_epochs(epoch,parent_epoch,event_id,root_hash,event_hash,committed_at,writer_node)"
                " VALUES(0,NULL,NULL,?,?,?,?)",
                (ledger._root_hash([]), GENESIS_HASH, "1970-01-01T00:00:00Z", "GENESIS"),
            )
            provenance = {
                "class": "SNAPSHOT_RECOVERY",
                "source_snapshot_hash": sha256_hex(raw),
                "source_epoch": payload["epoch"],
                "source_event_hash": payload["event_hash"],
                "source_root_hash": payload["root_hash"],
            }
            event_id = f"restore:{sha256_hex(raw)[:24]}"
            muts = [
                Mutation(r["domain"], r["key"], r["value"], r["epistemic_state"])
                for r in payload["state"]
            ]
            if not muts:
                ledger.db.execute("COMMIT")
                return ledger
            ledger.db.execute("ROLLBACK")
            receipt = ledger.commit(
                event_id=event_id,
                idempotency_key=event_id,
                base_epoch=0,
                event_type="SNAPSHOT_RECOVERY",
                mutations=muts,
                provenance=provenance,
                committed_at="1970-01-01T00:00:01Z",
                writer_node="RECOVERY",
            )
            if receipt["root_hash"] != payload["root_hash"]:
                raise TamperDetected("snapshot payload state does not match declared root_hash")
            return ledger
        except Exception:
            try:
                ledger.db.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            ledger.close()
            raise
