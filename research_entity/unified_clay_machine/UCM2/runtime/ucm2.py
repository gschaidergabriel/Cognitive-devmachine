from __future__ import annotations

import hashlib
import json
import sqlite3
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

ROOT_MODULE = "UCM2_CORE"
SCHEMA_VERSION = 2


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


class UCM2:
    """Minimal executable Unified Clay Machine 2 research body.

    One semantic root (`UCM2_CORE`) contains typed objects for state, wiki,
    world/self model, Hyperpositions and other future surfaces. Graph edges,
    experiences and a replay-complete hash-chained event stream live in the
    same isolated SQLite fabric. This is a research prototype, not
    main-instance authority.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.state_dir = self.root / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = (self.state_dir / "UCM2.sqlite").resolve()
        if self.db_path.name in {"FRANK_UNIFIED.sqlite", "FRANK_CLAYGRAPH.sqlite"}:
            raise RuntimeError("MAIN_INSTANCE_DB_FORBIDDEN")
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self._init()

    def _init(self) -> None:
        self.db.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS meta(
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS objects(
              object_id TEXT PRIMARY KEY,
              root_module TEXT NOT NULL,
              kind TEXT NOT NULL,
              status TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              version INTEGER NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS edges(
              edge_id TEXT PRIMARY KEY,
              root_module TEXT NOT NULL,
              src TEXT NOT NULL,
              rel TEXT NOT NULL,
              dst TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events(
              seq INTEGER PRIMARY KEY AUTOINCREMENT,
              epoch INTEGER NOT NULL,
              event_type TEXT NOT NULL,
              object_id TEXT,
              payload_json TEXT NOT NULL,
              prev_hash TEXT NOT NULL DEFAULT '',
              event_hash TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS experiences(
              exp_id TEXT PRIMARY KEY,
              epoch INTEGER NOT NULL,
              actor TEXT NOT NULL,
              observation TEXT NOT NULL,
              prediction TEXT,
              outcome TEXT,
              lesson TEXT,
              claim_class TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            """
        )
        # Fail-closed compatibility marker for an early prototype database.
        # Old streams do not contain replay-complete payloads and cannot be
        # promoted into v2 replay authority by inventing missing semantics.
        event_columns = {row[1] for row in self.db.execute("PRAGMA table_info(events)")}
        if "prev_hash" not in event_columns:
            self.db.execute("ALTER TABLE events ADD COLUMN prev_hash TEXT NOT NULL DEFAULT ''")

        self.db.execute(
            "INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version',?)",
            (str(SCHEMA_VERSION),),
        )
        self.db.execute("INSERT OR IGNORE INTO meta(key,value) VALUES('epoch','0')")

        root_row = self.db.execute(
            "SELECT * FROM objects WHERE object_id=?", (ROOT_MODULE,)
        ).fetchone()
        if root_row is None:
            root_updated_at = now()
            self.db.execute(
                "INSERT INTO objects VALUES(?,?,?,?,?,?,?)",
                (
                    ROOT_MODULE,
                    ROOT_MODULE,
                    "clay_machine_key_module",
                    "ACTIVE",
                    json.dumps({"identity": "ClayMachine2", "role": "unified key module"}),
                    1,
                    root_updated_at,
                ),
            )

        event_count = int(self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0])
        if event_count == 0:
            root = self.db.execute(
                "SELECT * FROM objects WHERE object_id=?", (ROOT_MODULE,)
            ).fetchone()
            self._event(
                0,
                "BOOTSTRAP_ROOT",
                ROOT_MODULE,
                {
                    "object_id": ROOT_MODULE,
                    "root_module": ROOT_MODULE,
                    "kind": root["kind"],
                    "status": root["status"],
                    "payload": json.loads(root["payload_json"]),
                    "version": int(root["version"]),
                    "updated_at": root["updated_at"],
                },
            )
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def epoch(self) -> int:
        return int(self.db.execute("SELECT value FROM meta WHERE key='epoch'").fetchone()[0])

    def _next_epoch(self) -> int:
        epoch = self.epoch() + 1
        self.db.execute("UPDATE meta SET value=? WHERE key='epoch'", (str(epoch),))
        return epoch

    @staticmethod
    def _compute_event_hash(
        epoch: int,
        event_type: str,
        object_id: str | None,
        payload: dict,
        prev_hash: str,
        created_at: str,
    ) -> str:
        raw = json.dumps(
            [epoch, event_type, object_id, payload, prev_hash, created_at],
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(raw.encode()).hexdigest()

    def _event(self, epoch: int, event_type: str, object_id: str | None, payload: dict) -> None:
        previous = self.db.execute(
            "SELECT event_hash FROM events ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        prev_hash = previous["event_hash"] if previous else ""
        created_at = now()
        event_hash = self._compute_event_hash(
            epoch, event_type, object_id, payload, prev_hash, created_at
        )
        self.db.execute(
            """INSERT INTO events(
                   epoch,event_type,object_id,payload_json,prev_hash,event_hash,created_at
               ) VALUES(?,?,?,?,?,?,?)""",
            (
                epoch,
                event_type,
                object_id,
                json.dumps(payload, sort_keys=True),
                prev_hash,
                event_hash,
                created_at,
            ),
        )

    def upsert(self, object_id: str, kind: str, payload: dict, status: str = "ACTIVE") -> int:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT version FROM objects WHERE object_id=?", (object_id,)).fetchone()
            version = (int(row["version"]) + 1) if row else 1
            epoch = self._next_epoch()
            updated_at = now()
            snapshot = {
                "object_id": object_id,
                "root_module": ROOT_MODULE,
                "kind": kind,
                "status": status,
                "payload": deepcopy(payload),
                "version": version,
                "updated_at": updated_at,
            }
            self.db.execute(
                """INSERT INTO objects(object_id,root_module,kind,status,payload_json,version,updated_at)
                   VALUES(?,?,?,?,?,?,?)
                   ON CONFLICT(object_id) DO UPDATE SET
                   root_module=excluded.root_module,kind=excluded.kind,status=excluded.status,
                   payload_json=excluded.payload_json,version=excluded.version,
                   updated_at=excluded.updated_at""",
                (
                    object_id,
                    ROOT_MODULE,
                    kind,
                    status,
                    json.dumps(payload, sort_keys=True),
                    version,
                    updated_at,
                ),
            )
            self._event(epoch, "UPSERT", object_id, snapshot)
            self.db.commit()
            return epoch
        except Exception:
            self.db.rollback()
            raise

    def link(self, src: str, rel: str, dst: str, payload: dict | None = None) -> int:
        payload = payload or {}
        edge_id = hashlib.sha256(f"{src}|{rel}|{dst}".encode()).hexdigest()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            epoch = self._next_epoch()
            snapshot = {
                "edge_id": edge_id,
                "root_module": ROOT_MODULE,
                "src": src,
                "rel": rel,
                "dst": dst,
                "payload": deepcopy(payload),
            }
            self.db.execute(
                "INSERT OR REPLACE INTO edges VALUES(?,?,?,?,?,?)",
                (edge_id, ROOT_MODULE, src, rel, dst, json.dumps(payload, sort_keys=True)),
            )
            self._event(epoch, "LINK", src, snapshot)
            self.db.commit()
            return epoch
        except Exception:
            self.db.rollback()
            raise

    def record_experience(
        self,
        actor: str,
        observation: str,
        prediction: str | None,
        outcome: str | None,
        lesson: str | None,
        claim_class: str = "OBSERVED",
    ) -> tuple[str, int]:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            epoch = self._next_epoch()
            created_at = now()
            raw = json.dumps(
                [epoch, actor, observation, prediction, outcome, lesson, claim_class, created_at],
                separators=(",", ":"),
            )
            exp_id = hashlib.sha256(raw.encode()).hexdigest()
            snapshot = {
                "exp_id": exp_id,
                "epoch": epoch,
                "actor": actor,
                "observation": observation,
                "prediction": prediction,
                "outcome": outcome,
                "lesson": lesson,
                "claim_class": claim_class,
                "created_at": created_at,
            }
            self.db.execute(
                "INSERT INTO experiences VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    exp_id,
                    epoch,
                    actor,
                    observation,
                    prediction,
                    outcome,
                    lesson,
                    claim_class,
                    created_at,
                ),
            )
            self._event(epoch, "EXPERIENCE", None, snapshot)
            self.db.commit()
            return exp_id, epoch
        except Exception:
            self.db.rollback()
            raise

    def event_stream(self) -> list[dict]:
        stream: list[dict] = []
        for row in self.db.execute("SELECT * FROM events ORDER BY seq"):
            item = dict(row)
            item["payload"] = json.loads(item.pop("payload_json"))
            stream.append(item)
        return stream

    def verify_event_stream(self, stream: list[dict] | None = None) -> str:
        stream = deepcopy(stream if stream is not None else self.event_stream())
        if not stream:
            raise RuntimeError("EVENT_STREAM_EMPTY")
        prev_hash = ""
        expected_seq = 1
        expected_epoch = 0
        for event in stream:
            if int(event["seq"]) != expected_seq:
                raise RuntimeError("EVENT_SEQ_GAP")
            if int(event["epoch"]) != expected_epoch:
                raise RuntimeError("EVENT_EPOCH_GAP")
            if event["prev_hash"] != prev_hash:
                raise RuntimeError("EVENT_PREV_HASH_MISMATCH")
            payload = event["payload"]
            calculated = self._compute_event_hash(
                int(event["epoch"]),
                event["event_type"],
                event["object_id"],
                payload,
                event["prev_hash"],
                event["created_at"],
            )
            if calculated != event["event_hash"]:
                raise RuntimeError("EVENT_HASH_MISMATCH")
            if expected_seq == 1 and event["event_type"] != "BOOTSTRAP_ROOT":
                raise RuntimeError("EVENT_BOOTSTRAP_MISSING")
            if expected_seq > 1 and event["event_type"] == "BOOTSTRAP_ROOT":
                raise RuntimeError("EVENT_BOOTSTRAP_DUPLICATE")
            prev_hash = event["event_hash"]
            expected_seq += 1
            expected_epoch += 1
        return prev_hash

    @staticmethod
    def _apply_event(cursor: sqlite3.Cursor, event: dict) -> None:
        payload = event["payload"]
        event_type = event["event_type"]
        if event_type in {"BOOTSTRAP_ROOT", "UPSERT"}:
            cursor.execute(
                """INSERT OR REPLACE INTO objects(
                       object_id,root_module,kind,status,payload_json,version,updated_at
                   ) VALUES(?,?,?,?,?,?,?)""",
                (
                    payload["object_id"],
                    payload["root_module"],
                    payload["kind"],
                    payload["status"],
                    json.dumps(payload["payload"], sort_keys=True),
                    int(payload["version"]),
                    payload["updated_at"],
                ),
            )
        elif event_type == "LINK":
            cursor.execute(
                "INSERT OR REPLACE INTO edges VALUES(?,?,?,?,?,?)",
                (
                    payload["edge_id"],
                    payload["root_module"],
                    payload["src"],
                    payload["rel"],
                    payload["dst"],
                    json.dumps(payload["payload"], sort_keys=True),
                ),
            )
        elif event_type == "EXPERIENCE":
            cursor.execute(
                "INSERT OR REPLACE INTO experiences VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    payload["exp_id"],
                    int(payload["epoch"]),
                    payload["actor"],
                    payload["observation"],
                    payload["prediction"],
                    payload["outcome"],
                    payload["lesson"],
                    payload["claim_class"],
                    payload["created_at"],
                ),
            )
        else:
            raise RuntimeError(f"EVENT_TYPE_UNSUPPORTED:{event_type}")

    def rebuild_materialized_from_events(self) -> str:
        stream = self.event_stream()
        terminal_hash = self.verify_event_stream(stream)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("DELETE FROM objects")
            self.db.execute("DELETE FROM edges")
            self.db.execute("DELETE FROM experiences")
            cursor = self.db.cursor()
            for event in stream:
                self._apply_event(cursor, event)
            self.db.execute(
                "UPDATE meta SET value=? WHERE key='epoch'",
                (str(int(stream[-1]["epoch"])),),
            )
            self.db.commit()
            return terminal_hash
        except Exception:
            self.db.rollback()
            raise

    def restore_from_event_stream(self, stream: list[dict]) -> str:
        stream = deepcopy(stream)
        terminal_hash = self.verify_event_stream(stream)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("DELETE FROM events")
            self.db.execute("DELETE FROM objects")
            self.db.execute("DELETE FROM edges")
            self.db.execute("DELETE FROM experiences")
            for event in stream:
                self.db.execute(
                    """INSERT INTO events(
                           seq,epoch,event_type,object_id,payload_json,prev_hash,event_hash,created_at
                       ) VALUES(?,?,?,?,?,?,?,?)""",
                    (
                        int(event["seq"]),
                        int(event["epoch"]),
                        event["event_type"],
                        event["object_id"],
                        json.dumps(event["payload"], sort_keys=True),
                        event["prev_hash"],
                        event["event_hash"],
                        event["created_at"],
                    ),
                )
            cursor = self.db.cursor()
            for event in stream:
                self._apply_event(cursor, event)
            self.db.execute(
                "UPDATE meta SET value=? WHERE key='epoch'",
                (str(int(stream[-1]["epoch"])),),
            )
            self.db.commit()
            return terminal_hash
        except Exception:
            self.db.rollback()
            raise

    def self_read(self) -> dict:
        objects = []
        for row in self.db.execute("SELECT * FROM objects ORDER BY object_id"):
            item = dict(row)
            item["payload"] = json.loads(item.pop("payload_json"))
            objects.append(item)
        edges = []
        for row in self.db.execute("SELECT * FROM edges ORDER BY edge_id"):
            item = dict(row)
            item["payload"] = json.loads(item.pop("payload_json"))
            edges.append(item)
        experiences = [dict(row) for row in self.db.execute("SELECT * FROM experiences ORDER BY epoch")]
        return {
            "root_module": ROOT_MODULE,
            "epoch": self.epoch(),
            "objects": objects,
            "edges": edges,
            "experiences": experiences,
        }


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    machine = UCM2(root)
    try:
        print(json.dumps(machine.self_read(), indent=2, ensure_ascii=False))
    finally:
        machine.close()
