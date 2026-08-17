from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence

CLAYVERSE_ID = "CLAYVERSE"
SCHEMA_VERSION = 1


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class EffectResult:
    effect_id: str
    returncode: int
    stdout: str
    stderr: str
    verified: bool
    epoch: int


class ClayVerse:
    """First integrated ClayVerse container core.

    This is intentionally narrow: UnifiedDB is the sole durable authority;
    ClayGraph is a derived projection; all sessions bind to one ClayVerse
    identity; causal effects re-enter state only after explicit verification.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.state_dir = self.root / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.state_dir / "clayverse.sqlite"
        self.db = sqlite3.connect(self.db_path, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self._init_schema()
        self.verify_event_stream()
        self._verify_identity()

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "ClayVerse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _init_schema(self) -> None:
        self.db.executescript(
            """
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=FULL;
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS meta(
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS objects(
              object_id TEXT PRIMARY KEY,
              kind TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              version INTEGER NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events(
              seq INTEGER PRIMARY KEY AUTOINCREMENT,
              epoch INTEGER NOT NULL UNIQUE,
              event_type TEXT NOT NULL,
              object_id TEXT,
              payload_json TEXT NOT NULL,
              prev_hash TEXT NOT NULL,
              event_hash TEXT NOT NULL UNIQUE,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions(
              session_id TEXT PRIMARY KEY,
              clayverse_id TEXT NOT NULL,
              opened_epoch INTEGER NOT NULL,
              last_seen_epoch INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS effects(
              effect_id TEXT PRIMARY KEY,
              request_hash TEXT NOT NULL,
              request_json TEXT NOT NULL,
              result_json TEXT NOT NULL,
              verified INTEGER NOT NULL,
              terminal_epoch INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS graph_edges(
              edge_id TEXT PRIMARY KEY,
              src TEXT NOT NULL,
              rel TEXT NOT NULL,
              dst TEXT NOT NULL,
              source_event_hash TEXT NOT NULL
            );
            """
        )
        self.db.execute(
            "INSERT OR IGNORE INTO meta(key,value) VALUES('schema_version',?)",
            (str(SCHEMA_VERSION),),
        )
        self.db.execute("INSERT OR IGNORE INTO meta(key,value) VALUES('epoch','0')")
        row = self.db.execute("SELECT value FROM meta WHERE key='identity'").fetchone()
        if row is None:
            created_at = utcnow()
            fingerprint = hashlib.sha256(
                canonical_json({"identity": CLAYVERSE_ID, "schema": SCHEMA_VERSION}).encode()
            ).hexdigest()
            self.db.execute("BEGIN IMMEDIATE")
            try:
                self.db.execute(
                    "INSERT INTO meta(key,value) VALUES('identity',?)", (CLAYVERSE_ID,)
                )
                self.db.execute(
                    "INSERT INTO meta(key,value) VALUES('core_fingerprint',?)", (fingerprint,)
                )
                self.db.execute(
                    "INSERT INTO objects VALUES(?,?,?,?,?)",
                    (
                        CLAYVERSE_ID,
                        "clayverse_root",
                        canonical_json({"identity": CLAYVERSE_ID, "core_fingerprint": fingerprint}),
                        1,
                        created_at,
                    ),
                )
                self._append_event(
                    "BOOTSTRAP_ROOT",
                    CLAYVERSE_ID,
                    {"identity": CLAYVERSE_ID, "core_fingerprint": fingerprint},
                    epoch=0,
                    created_at=created_at,
                )
                self.db.execute("COMMIT")
            except Exception:
                self.db.execute("ROLLBACK")
                raise

    def _verify_identity(self) -> None:
        identity = self.db.execute("SELECT value FROM meta WHERE key='identity'").fetchone()
        if identity is None or identity[0] != CLAYVERSE_ID:
            raise RuntimeError("IDENTITY_MISMATCH")
        root = self.db.execute(
            "SELECT payload_json FROM objects WHERE object_id=?", (CLAYVERSE_ID,)
        ).fetchone()
        if root is None or json.loads(root[0]).get("identity") != CLAYVERSE_ID:
            raise RuntimeError("ROOT_IDENTITY_MISMATCH")

    def epoch(self) -> int:
        return int(self.db.execute("SELECT value FROM meta WHERE key='epoch'").fetchone()[0])

    def core_fingerprint(self) -> str:
        return str(
            self.db.execute("SELECT value FROM meta WHERE key='core_fingerprint'").fetchone()[0]
        )

    def _next_epoch(self) -> int:
        epoch = self.epoch() + 1
        self.db.execute("UPDATE meta SET value=? WHERE key='epoch'", (str(epoch),))
        return epoch

    @staticmethod
    def _event_hash(epoch: int, event_type: str, object_id: str | None,
                    payload: dict, prev_hash: str, created_at: str) -> str:
        raw = canonical_json([epoch, event_type, object_id, payload, prev_hash, created_at])
        return hashlib.sha256(raw.encode()).hexdigest()

    def _append_event(self, event_type: str, object_id: str | None, payload: dict,
                      *, epoch: int | None = None, created_at: str | None = None) -> str:
        if epoch is None:
            epoch = self._next_epoch()
        previous = self.db.execute(
            "SELECT event_hash FROM events ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        prev_hash = previous[0] if previous else ""
        created_at = created_at or utcnow()
        event_hash = self._event_hash(epoch, event_type, object_id, payload, prev_hash, created_at)
        self.db.execute(
            "INSERT INTO events(epoch,event_type,object_id,payload_json,prev_hash,event_hash,created_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (epoch, event_type, object_id, canonical_json(payload), prev_hash, event_hash, created_at),
        )
        return event_hash

    def verify_event_stream(self) -> str:
        rows = list(self.db.execute("SELECT * FROM events ORDER BY seq"))
        if not rows:
            return ""
        prev_hash = ""
        expected_seq = 1
        expected_epoch = 0
        for row in rows:
            if int(row["seq"]) != expected_seq:
                raise RuntimeError("EVENT_SEQ_GAP")
            if int(row["epoch"]) != expected_epoch:
                raise RuntimeError("EVENT_EPOCH_GAP")
            if row["prev_hash"] != prev_hash:
                raise RuntimeError("EVENT_PREV_HASH_MISMATCH")
            payload = json.loads(row["payload_json"])
            computed = self._event_hash(
                int(row["epoch"]), row["event_type"], row["object_id"], payload,
                row["prev_hash"], row["created_at"]
            )
            if computed != row["event_hash"]:
                raise RuntimeError("EVENT_HASH_MISMATCH")
            if expected_seq == 1 and row["event_type"] != "BOOTSTRAP_ROOT":
                raise RuntimeError("EVENT_BOOTSTRAP_MISSING")
            prev_hash = row["event_hash"]
            expected_seq += 1
            expected_epoch += 1
        if int(rows[-1]["epoch"]) != self.epoch():
            raise RuntimeError("META_EPOCH_MISMATCH")
        return prev_hash

    def open_session(self, session_id: str) -> dict:
        if not session_id:
            raise ValueError("SESSION_ID_REQUIRED")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            existing = self.db.execute(
                "SELECT * FROM sessions WHERE session_id=?", (session_id,)
            ).fetchone()
            if existing is None:
                epoch = self._next_epoch()
                self.db.execute(
                    "INSERT INTO sessions VALUES(?,?,?,?)",
                    (session_id, CLAYVERSE_ID, epoch, epoch),
                )
                self._append_event(
                    "SESSION_OPEN", session_id,
                    {"session_id": session_id, "clayverse_id": CLAYVERSE_ID}, epoch=epoch
                )
            else:
                if existing["clayverse_id"] != CLAYVERSE_ID:
                    raise RuntimeError("SESSION_IDENTITY_SPLIT")
                epoch = self._next_epoch()
                self.db.execute(
                    "UPDATE sessions SET last_seen_epoch=? WHERE session_id=?", (epoch, session_id)
                )
                self._append_event(
                    "SESSION_RESUME", session_id,
                    {"session_id": session_id, "clayverse_id": CLAYVERSE_ID}, epoch=epoch
                )
            self.db.execute("COMMIT")
            return {
                "session_id": session_id,
                "clayverse_id": CLAYVERSE_ID,
                "core_fingerprint": self.core_fingerprint(),
                "epoch": epoch,
            }
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def put_memory(self, session_id: str, key: str, value: object) -> int:
        session = self.db.execute(
            "SELECT clayverse_id FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if session is None or session[0] != CLAYVERSE_ID:
            raise RuntimeError("SESSION_NOT_BOUND")
        object_id = f"memory:{key}"
        self.db.execute("BEGIN IMMEDIATE")
        try:
            old = self.db.execute(
                "SELECT version FROM objects WHERE object_id=?", (object_id,)
            ).fetchone()
            version = int(old[0]) + 1 if old else 1
            epoch = self._next_epoch()
            updated_at = utcnow()
            payload = {"key": key, "value": value, "writer_session": session_id}
            self.db.execute(
                "INSERT INTO objects VALUES(?,?,?,?,?) ON CONFLICT(object_id) DO UPDATE SET "
                "kind=excluded.kind,payload_json=excluded.payload_json,version=excluded.version,updated_at=excluded.updated_at",
                (object_id, "memory", canonical_json(payload), version, updated_at),
            )
            self._append_event(
                "MEMORY_PUT", object_id,
                {"object_id": object_id, "kind": "memory", "payload": payload,
                 "version": version, "updated_at": updated_at}, epoch=epoch
            )
            self.db.execute("COMMIT")
            return epoch
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def get_memory(self, key: str) -> object | None:
        row = self.db.execute(
            "SELECT payload_json FROM objects WHERE object_id=?", (f"memory:{key}",)
        ).fetchone()
        return None if row is None else json.loads(row[0])["value"]

    def link(self, src: str, rel: str, dst: str) -> int:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            epoch = self._next_epoch()
            payload = {"src": src, "rel": rel, "dst": dst}
            event_hash = self._append_event("LINK", src, payload, epoch=epoch)
            edge_id = hashlib.sha256(canonical_json(payload).encode()).hexdigest()
            self.db.execute(
                "INSERT OR REPLACE INTO graph_edges VALUES(?,?,?,?,?)",
                (edge_id, src, rel, dst, event_hash),
            )
            self.db.execute("COMMIT")
            return epoch
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def rebuild_graph_projection(self) -> int:
        """Rebuild ClayGraph only from authoritative UnifiedDB LINK events."""
        self.verify_event_stream()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("DELETE FROM graph_edges")
            count = 0
            for row in self.db.execute(
                "SELECT payload_json,event_hash FROM events WHERE event_type='LINK' ORDER BY seq"
            ):
                payload = json.loads(row["payload_json"])
                edge_id = hashlib.sha256(canonical_json(payload).encode()).hexdigest()
                self.db.execute(
                    "INSERT INTO graph_edges VALUES(?,?,?,?,?)",
                    (edge_id, payload["src"], payload["rel"], payload["dst"], row["event_hash"]),
                )
                count += 1
            self.db.execute("COMMIT")
            return count
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def graph_edges(self) -> list[tuple[str, str, str]]:
        return [tuple(row) for row in self.db.execute(
            "SELECT src,rel,dst FROM graph_edges ORDER BY src,rel,dst"
        )]

    def run_process_effect(
        self,
        effect_id: str,
        argv: Sequence[str],
        *,
        verifier: Callable[[subprocess.CompletedProcess[str]], bool],
        timeout: float = 5.0,
    ) -> EffectResult:
        """Execute an explicit argv effect; never invokes an implicit shell.

        Exact duplicate effect IDs are idempotent. Reusing an ID with different
        request bytes fails closed before a second process can execute.
        """
        if not effect_id or not argv or any(not isinstance(x, str) or not x for x in argv):
            raise ValueError("INVALID_EFFECT_REQUEST")
        request = {"kind": "process", "argv": list(argv), "timeout": timeout}
        request_hash = hashlib.sha256(canonical_json(request).encode()).hexdigest()
        prior = self.db.execute("SELECT * FROM effects WHERE effect_id=?", (effect_id,)).fetchone()
        if prior is not None:
            if prior["request_hash"] != request_hash:
                raise RuntimeError("EFFECT_ID_CONFLICT")
            result = json.loads(prior["result_json"])
            return EffectResult(
                effect_id, int(result["returncode"]), result["stdout"], result["stderr"],
                bool(prior["verified"]), int(prior["terminal_epoch"])
            )

        self.db.execute("BEGIN IMMEDIATE")
        try:
            request_epoch = self._next_epoch()
            self._append_event("EFFECT_REQUEST", effect_id, request, epoch=request_epoch)
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise

        completed = subprocess.run(
            list(argv), capture_output=True, text=True, timeout=timeout, check=False, shell=False,
            env={"PATH": os.environ.get("PATH", "")},
        )
        verified = bool(verifier(completed))
        result = {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }

        self.db.execute("BEGIN IMMEDIATE")
        try:
            outcome_epoch = self._next_epoch()
            self._append_event("EFFECT_OUTCOME", effect_id, result, epoch=outcome_epoch)
            verify_epoch = self._next_epoch()
            self._append_event(
                "EFFECT_VERIFIED", effect_id, {"verified": verified}, epoch=verify_epoch
            )
            if not verified:
                self.db.execute("COMMIT")
                raise RuntimeError("EFFECT_VERIFICATION_FAILED")
            reentry_epoch = self._next_epoch()
            self._append_event(
                "CAUSAL_REENTRY", effect_id,
                {"effect_id": effect_id, "outcome_epoch": outcome_epoch,
                 "verification_epoch": verify_epoch}, epoch=reentry_epoch
            )
            credit_epoch = self._next_epoch()
            credit_id = f"credit:{effect_id}"
            credit_payload = {"effect_id": effect_id, "credit": 1, "verified": True}
            self.db.execute(
                "INSERT OR REPLACE INTO objects VALUES(?,?,?,?,?)",
                (credit_id, "causal_credit", canonical_json(credit_payload), 1, utcnow()),
            )
            self._append_event("CREDIT_UPDATE", credit_id, credit_payload, epoch=credit_epoch)
            self.db.execute(
                "INSERT INTO effects VALUES(?,?,?,?,?,?)",
                (effect_id, request_hash, canonical_json(request), canonical_json(result), 1, credit_epoch),
            )
            self.db.execute("COMMIT")
            return EffectResult(
                effect_id, completed.returncode, completed.stdout, completed.stderr, True, credit_epoch
            )
        except RuntimeError as exc:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise exc
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise

    def snapshot(self) -> dict:
        return {
            "identity": CLAYVERSE_ID,
            "core_fingerprint": self.core_fingerprint(),
            "epoch": self.epoch(),
            "memories": {
                row["object_id"][7:]: json.loads(row["payload_json"])["value"]
                for row in self.db.execute(
                    "SELECT object_id,payload_json FROM objects WHERE kind='memory' ORDER BY object_id"
                )
            },
            "sessions": [dict(row) for row in self.db.execute(
                "SELECT * FROM sessions ORDER BY session_id"
            )],
            "graph_edges": self.graph_edges(),
            "event_head": self.verify_event_stream(),
        }


def selftest(root: str | Path) -> dict:
    root = Path(root)
    with ClayVerse(root) as cv:
        a = cv.open_session("A")
        cv.put_memory("A", "bootstrap", "alive")
        cv.link(CLAYVERSE_ID, "HAS_MEMORY", "memory:bootstrap")
        result = cv.run_process_effect(
            "selftest.echo",
            ["/bin/echo", "clayverse"],
            verifier=lambda p: p.returncode == 0 and p.stdout.strip() == "clayverse",
        )
        head = cv.verify_event_stream()
    with ClayVerse(root) as cv:
        b = cv.open_session("B")
        assert a["clayverse_id"] == b["clayverse_id"] == CLAYVERSE_ID
        assert a["core_fingerprint"] == b["core_fingerprint"]
        assert cv.get_memory("bootstrap") == "alive"
        assert result.verified
        return {"ok": True, "identity": CLAYVERSE_ID, "event_head_before_restart": head,
                "snapshot": cv.snapshot()}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default="/var/lib/clayverse")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        print(json.dumps(selftest(args.state), indent=2, ensure_ascii=False))
    else:
        with ClayVerse(args.state) as runtime:
            print(json.dumps(runtime.snapshot(), indent=2, ensure_ascii=False))
