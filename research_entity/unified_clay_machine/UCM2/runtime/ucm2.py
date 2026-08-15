from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT_MODULE = "UCM2_CORE"
SCHEMA_VERSION = 1


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


class UCM2:
    """Minimal executable Unified Clay Machine 2 research body.

    One semantic root (`UCM2_CORE`) contains typed objects for state, wiki,
    world/self model, Hyperpositions and other future surfaces. Graph edges
    and experiences are stored in the same isolated SQLite fabric. This is a
    research prototype, not main-instance authority.
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
        self.db.execute(
            "INSERT OR IGNORE INTO meta(key,value) VALUES('schema_version',?)",
            (str(SCHEMA_VERSION),),
        )
        self.db.execute("INSERT OR IGNORE INTO meta(key,value) VALUES('epoch','0')")
        self.db.execute(
            "INSERT OR IGNORE INTO objects VALUES(?,?,?,?,?,?,?)",
            (
                ROOT_MODULE,
                ROOT_MODULE,
                "clay_machine_key_module",
                "ACTIVE",
                json.dumps({"identity": "ClayMachine2", "role": "unified key module"}),
                1,
                now(),
            ),
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

    def _event(self, epoch: int, event_type: str, object_id: str | None, payload: dict) -> None:
        raw = json.dumps([epoch, event_type, object_id, payload], sort_keys=True, separators=(",", ":"))
        event_hash = hashlib.sha256(raw.encode()).hexdigest()
        self.db.execute(
            "INSERT INTO events(epoch,event_type,object_id,payload_json,event_hash,created_at) VALUES(?,?,?,?,?,?)",
            (epoch, event_type, object_id, json.dumps(payload, sort_keys=True), event_hash, now()),
        )

    def upsert(self, object_id: str, kind: str, payload: dict, status: str = "ACTIVE") -> int:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT version FROM objects WHERE object_id=?", (object_id,)).fetchone()
            version = (int(row["version"]) + 1) if row else 1
            epoch = self._next_epoch()
            self.db.execute(
                """INSERT INTO objects(object_id,root_module,kind,status,payload_json,version,updated_at)
                   VALUES(?,?,?,?,?,?,?)
                   ON CONFLICT(object_id) DO UPDATE SET
                   kind=excluded.kind,status=excluded.status,payload_json=excluded.payload_json,
                   version=excluded.version,updated_at=excluded.updated_at""",
                (object_id, ROOT_MODULE, kind, status, json.dumps(payload, sort_keys=True), version, now()),
            )
            self._event(epoch, "UPSERT", object_id, {"kind": kind, "status": status, "version": version})
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
            self.db.execute(
                "INSERT OR REPLACE INTO edges VALUES(?,?,?,?,?,?)",
                (edge_id, ROOT_MODULE, src, rel, dst, json.dumps(payload, sort_keys=True)),
            )
            self._event(epoch, "LINK", src, {"rel": rel, "dst": dst})
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
            self.db.execute(
                "INSERT INTO experiences VALUES(?,?,?,?,?,?,?,?,?)",
                (exp_id, epoch, actor, observation, prediction, outcome, lesson, claim_class, created_at),
            )
            self._event(epoch, "EXPERIENCE", None, {"exp_id": exp_id, "actor": actor, "claim_class": claim_class})
            self.db.commit()
            return exp_id, epoch
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
