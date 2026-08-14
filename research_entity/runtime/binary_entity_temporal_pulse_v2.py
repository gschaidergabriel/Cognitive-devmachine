from __future__ import annotations

"""Binary-entity identity lineage + temporal orientation substrate (research candidate).

The central separation is deliberate:

    immutable artifact/build identity
    != copy/incarnation entity identity
    != current runtime lease identity
    != temporal/cognitive trajectory.

Copying an admitted entity therefore does *not* rewrite executable bytes. The copy keeps the
artifact digest but receives a fresh entity id/version and an explicit parent edge. Runtime
execution is protected by a per-entity lease epoch. Actual Pulse time is evidenced only by
committed entity_pulses rows; missed logical slots are counters and never phantom cognition.
"""

import hashlib
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "2.1"

SCHEMA = r'''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS binary_artifacts(
  artifact_digest TEXT PRIMARY KEY,
  build_label TEXT NOT NULL,
  admitted_at_utc_ns INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS binary_entities(
  entity_id TEXT PRIMARY KEY,
  entity_version TEXT NOT NULL UNIQUE,
  artifact_digest TEXT NOT NULL REFERENCES binary_artifacts(artifact_digest),
  lineage_root_id TEXT NOT NULL,
  parent_entity_id TEXT REFERENCES binary_entities(entity_id),
  generation INTEGER NOT NULL,
  admitted_state_lineage_hash TEXT NOT NULL,
  born_at_utc_ns INTEGER NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('CURRENT','DORMANT','RETIRED','QUARANTINED'))
);
CREATE INDEX IF NOT EXISTS ix_binary_entities_lineage
  ON binary_entities(lineage_root_id,generation,entity_id);
CREATE INDEX IF NOT EXISTS ix_binary_entities_parent
  ON binary_entities(parent_entity_id,entity_id);
CREATE TABLE IF NOT EXISTS entity_copy_edges(
  parent_entity_id TEXT NOT NULL REFERENCES binary_entities(entity_id),
  child_entity_id TEXT NOT NULL UNIQUE REFERENCES binary_entities(entity_id),
  copy_kind TEXT NOT NULL,
  copied_at_utc_ns INTEGER NOT NULL,
  PRIMARY KEY(parent_entity_id,child_entity_id)
);
CREATE TABLE IF NOT EXISTS entity_runtime_lease(
  entity_id TEXT PRIMARY KEY REFERENCES binary_entities(entity_id),
  lease_id TEXT NOT NULL UNIQUE,
  lease_epoch INTEGER NOT NULL,
  host_id TEXT NOT NULL,
  boot_id TEXT NOT NULL,
  invocation_id TEXT NOT NULL,
  claimed_at_utc_ns INTEGER NOT NULL,
  released_at_utc_ns INTEGER,
  active INTEGER NOT NULL CHECK(active IN (0,1))
);
CREATE TABLE IF NOT EXISTS entity_pulses(
  entity_id TEXT NOT NULL REFERENCES binary_entities(entity_id),
  pulse_seq INTEGER NOT NULL,
  pulse_id TEXT NOT NULL UNIQUE,
  event_id TEXT UNIQUE,
  event_epoch INTEGER,
  lease_id TEXT NOT NULL,
  lease_epoch INTEGER NOT NULL,
  observed_at_utc_ns INTEGER NOT NULL,
  boottime_ns INTEGER NOT NULL,
  monotonic_ns INTEGER NOT NULL,
  host_id TEXT NOT NULL,
  boot_id TEXT NOT NULL,
  invocation_id TEXT NOT NULL,
  entity_age_ns INTEGER NOT NULL,
  wall_gap_ns INTEGER,
  boottime_gap_ns INTEGER,
  monotonic_gap_ns INTEGER,
  inferred_suspend_ns INTEGER,
  gap_class TEXT NOT NULL,
  missed_logical_slots INTEGER NOT NULL,
  clock_confidence TEXT NOT NULL,
  continuity_class TEXT NOT NULL,
  PRIMARY KEY(entity_id,pulse_seq)
);
CREATE INDEX IF NOT EXISTS ix_entity_pulses_time
  ON entity_pulses(entity_id,observed_at_utc_ns,pulse_seq);
'''


class IdentityCollision(RuntimeError):
    pass


class StaleLease(RuntimeError):
    pass


class TemporalInvariantError(RuntimeError):
    pass


def _hash_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _entity_version(entity_id: str, generation: int) -> str:
    # A full-identity digest avoids timestamp-prefix collisions during copy storms.
    return f"e{generation}-{_hash_text(entity_id)[:20]}"


def _new_entity_id() -> str:
    return str(uuid.uuid4())


def read_linux_boot_id() -> str:
    try:
        with open("/proc/sys/kernel/random/boot_id", "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "boot-unknown"


def read_systemd_invocation_id() -> str:
    return os.getenv("INVOCATION_ID") or f"pid-{os.getpid()}"


def clock_snapshot() -> dict[str, int]:
    return {
        "utc_ns": time.time_ns(),
        "boottime_ns": (
            time.clock_gettime_ns(time.CLOCK_BOOTTIME)
            if hasattr(time, "CLOCK_BOOTTIME")
            else time.monotonic_ns()
        ),
        "monotonic_ns": time.monotonic_ns(),
    }


@dataclass(frozen=True)
class TemporalOrientation:
    entity_id: str
    entity_version: str
    artifact_digest: str
    lineage_root_id: str
    generation: int
    pulse_seq: int
    pulse_id: str
    lease_id: str
    lease_epoch: int
    host_id: str
    boot_id: str
    invocation_id: str
    observed_at_utc_ns: int
    boottime_ns: int
    monotonic_ns: int
    entity_age_ns: int
    wall_gap_ns: int | None
    boottime_gap_ns: int | None
    monotonic_gap_ns: int | None
    inferred_suspend_ns: int | None
    gap_class: str
    missed_logical_slots: int
    clock_confidence: str
    continuity_class: str
    peer_count: int


class BinaryEntityTemporalStore:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(SCHEMA)

    @classmethod
    def open(cls, path: str):
        con = sqlite3.connect(path, timeout=30, isolation_level=None)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=FULL")
        con.execute("PRAGMA busy_timeout=30000")
        return cls(con)

    def _tx(self, fn):
        if self.conn.in_transaction:
            return fn()
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            result = fn()
            self.conn.execute("COMMIT")
            return result
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def admit_artifact(self, digest: str, build_label: str, now_ns: int | None = None):
        if len(digest) < 16:
            raise ValueError("artifact digest too short")
        when = now_ns if now_ns is not None else time.time_ns()
        return self._tx(
            lambda: self.conn.execute(
                "INSERT OR IGNORE INTO binary_artifacts VALUES(?,?,?)",
                (digest, build_label, when),
            )
        )

    def mint_root(
        self, *, artifact_digest: str, state_lineage_hash: str, now_ns: int | None = None
    ) -> dict[str, Any]:
        when = now_ns if now_ns is not None else time.time_ns()

        def op():
            if self.conn.execute(
                "SELECT 1 FROM binary_artifacts WHERE artifact_digest=?", (artifact_digest,)
            ).fetchone() is None:
                raise KeyError("unknown artifact")
            eid = _new_entity_id()
            ver = _entity_version(eid, 0)
            self.conn.execute(
                "INSERT INTO binary_entities VALUES(?,?,?,?,?,?,?,?,?)",
                (eid, ver, artifact_digest, eid, None, 0, state_lineage_hash, when, "CURRENT"),
            )
            return eid

        eid = self._tx(op)
        return self.entity(eid)

    def copy_entity(
        self,
        parent_entity_id: str,
        *,
        state_lineage_hash: str | None = None,
        copy_kind: str = "AUTHORIZED_COPY",
        now_ns: int | None = None,
    ) -> dict[str, Any]:
        when = now_ns if now_ns is not None else time.time_ns()

        def op():
            p = self.conn.execute(
                "SELECT * FROM binary_entities WHERE entity_id=?", (parent_entity_id,)
            ).fetchone()
            if p is None:
                raise KeyError(parent_entity_id)
            eid = _new_entity_id()
            generation = int(p["generation"]) + 1
            version = _entity_version(eid, generation)
            lineage_hash = state_lineage_hash or str(p["admitted_state_lineage_hash"])
            self.conn.execute(
                "INSERT INTO binary_entities VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    eid,
                    version,
                    p["artifact_digest"],
                    p["lineage_root_id"],
                    parent_entity_id,
                    generation,
                    lineage_hash,
                    when,
                    "CURRENT",
                ),
            )
            # O(1) copy write: no all-pairs peer materialization.
            self.conn.execute(
                "INSERT INTO entity_copy_edges VALUES(?,?,?,?)",
                (parent_entity_id, eid, copy_kind, when),
            )
            return eid

        eid = self._tx(op)
        return self.entity(eid)

    def entity(self, entity_id: str) -> dict[str, Any]:
        row = self.conn.execute(
            "SELECT * FROM binary_entities WHERE entity_id=?", (entity_id,)
        ).fetchone()
        if row is None:
            raise KeyError(entity_id)
        return dict(row)

    def peers(self, entity_id: str) -> list[dict[str, Any]]:
        entity = self.entity(entity_id)
        return [
            dict(r)
            for r in self.conn.execute(
                "SELECT * FROM binary_entities "
                "WHERE lineage_root_id=? AND entity_id<>? "
                "ORDER BY generation,entity_id",
                (entity["lineage_root_id"], entity_id),
            )
        ]

    def peer_count(self, entity_id: str) -> int:
        entity = self.entity(entity_id)
        return int(
            self.conn.execute(
                "SELECT count(*) FROM binary_entities WHERE lineage_root_id=? AND entity_id<>?",
                (entity["lineage_root_id"], entity_id),
            ).fetchone()[0]
        )

    def ancestry(self, entity_id: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        current = self.entity(entity_id)
        while current["parent_entity_id"]:
            current = self.entity(str(current["parent_entity_id"]))
            out.append(current)
        return out

    def lineage_relations(self, entity_id: str) -> list[dict[str, Any]]:
        """Derive copy-family awareness without storing an O(n^2) peer matrix."""
        own = self.entity(entity_id)
        ancestors = {x["entity_id"] for x in self.ancestry(entity_id)}
        children = {
            str(r[0])
            for r in self.conn.execute(
                "SELECT child_entity_id FROM entity_copy_edges WHERE parent_entity_id=?",
                (entity_id,),
            )
        }
        rows = self.peers(entity_id)
        out = []
        for peer in rows:
            pid = peer["entity_id"]
            if pid == own["parent_entity_id"]:
                relation = "PARENT"
            elif pid in children:
                relation = "CHILD"
            elif pid in ancestors:
                relation = "ANCESTOR"
            elif own["parent_entity_id"] is not None and peer["parent_entity_id"] == own["parent_entity_id"]:
                relation = "SIBLING"
            else:
                relation = "LINEAGE_PEER"
            out.append(
                {
                    "entity_id": pid,
                    "entity_version": peer["entity_version"],
                    "artifact_digest": peer["artifact_digest"],
                    "generation": int(peer["generation"]),
                    "relation": relation,
                }
            )
        return out

    def current_lease(self, entity_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM entity_runtime_lease WHERE entity_id=?", (entity_id,)
        ).fetchone()
        return dict(row) if row else None

    def claim_runtime(
        self,
        entity_id: str,
        *,
        lease_id: str,
        host_id: str,
        boot_id: str,
        invocation_id: str,
        expected_previous_lease_id: str | None = None,
        allow_supersede: bool = False,
        now_ns: int | None = None,
    ) -> dict[str, Any]:
        when = now_ns if now_ns is not None else time.time_ns()
        self.entity(entity_id)

        def op():
            old = self.conn.execute(
                "SELECT * FROM entity_runtime_lease WHERE entity_id=?", (entity_id,)
            ).fetchone()
            if old and int(old["active"]) and old["lease_id"] != lease_id:
                exact_cas = (
                    expected_previous_lease_id is not None
                    and old["lease_id"] == expected_previous_lease_id
                )
                reboot_proof = old["host_id"] == host_id and old["boot_id"] != boot_id
                if not allow_supersede or not (exact_cas or reboot_proof):
                    raise IdentityCollision(
                        f"entity {entity_id} already has active lease {old['lease_id']}"
                    )
            lease_epoch = int(old["lease_epoch"]) + 1 if old else 1
            self.conn.execute(
                "INSERT INTO entity_runtime_lease VALUES(?,?,?,?,?,?,?,?,1) "
                "ON CONFLICT(entity_id) DO UPDATE SET "
                "lease_id=excluded.lease_id,lease_epoch=excluded.lease_epoch,"
                "host_id=excluded.host_id,boot_id=excluded.boot_id,"
                "invocation_id=excluded.invocation_id,"
                "claimed_at_utc_ns=excluded.claimed_at_utc_ns,"
                "released_at_utc_ns=NULL,active=1",
                (
                    entity_id,
                    lease_id,
                    lease_epoch,
                    host_id,
                    boot_id,
                    invocation_id,
                    when,
                    None,
                ),
            )

        self._tx(op)
        return self.current_lease(entity_id) or {}

    def release_runtime(self, entity_id: str, lease_id: str, now_ns: int | None = None):
        when = now_ns if now_ns is not None else time.time_ns()

        def op():
            current = self.current_lease(entity_id)
            if not current or not current["active"] or current["lease_id"] != lease_id:
                raise StaleLease("not current lease")
            self.conn.execute(
                "UPDATE entity_runtime_lease SET active=0,released_at_utc_ns=? "
                "WHERE entity_id=? AND lease_id=?",
                (when, entity_id, lease_id),
            )

        return self._tx(op)

    def last_pulse(self, entity_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM entity_pulses WHERE entity_id=? "
            "ORDER BY pulse_seq DESC LIMIT 1",
            (entity_id,),
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def classify_gap(
        prev: dict[str, Any] | None,
        *,
        utc_ns: int,
        boottime_ns: int,
        monotonic_ns: int,
        boot_id: str,
        invocation_id: str,
        interval_ns: int,
    ) -> dict[str, Any]:
        if prev is None:
            return {
                "wall_gap_ns": None,
                "boottime_gap_ns": None,
                "monotonic_gap_ns": None,
                "inferred_suspend_ns": None,
                "gap_class": "GENESIS",
                "missed_logical_slots": 0,
                "clock_confidence": "HIGH",
                "continuity_class": "ENTITY_LINEAGE_CONTINUES_ACTUAL_PULSE_GENESIS",
            }
        wall = utc_ns - int(prev["observed_at_utc_ns"])
        if wall < 0:
            return {
                "wall_gap_ns": wall,
                "boottime_gap_ns": None,
                "monotonic_gap_ns": None,
                "inferred_suspend_ns": None,
                "gap_class": "WALL_CLOCK_REGRESSION",
                "missed_logical_slots": 0,
                "clock_confidence": "LOW",
                "continuity_class": "ENTITY_LINEAGE_CONTINUES_CLOCK_ORDER_UNCERTAIN",
            }
        missed = max(0, wall // max(1, interval_ns) - 1)
        if boot_id != prev["boot_id"]:
            return {
                "wall_gap_ns": wall,
                "boottime_gap_ns": None,
                "monotonic_gap_ns": None,
                "inferred_suspend_ns": None,
                "gap_class": "BOOT_OR_POWER_GAP",
                "missed_logical_slots": int(missed),
                "clock_confidence": "MEDIUM",
                "continuity_class": "ENTITY_LINEAGE_CONTINUES_COMPUTE_NOT_EVIDENCED_DURING_GAP",
            }
        boot_gap = boottime_ns - int(prev["boottime_ns"])
        mono_gap = monotonic_ns - int(prev["monotonic_ns"])
        if boot_gap < 0 or mono_gap < 0:
            return {
                "wall_gap_ns": wall,
                "boottime_gap_ns": boot_gap,
                "monotonic_gap_ns": mono_gap,
                "inferred_suspend_ns": None,
                "gap_class": "MONOTONIC_RESET_OR_CORRUPTION",
                "missed_logical_slots": int(missed),
                "clock_confidence": "LOW",
                "continuity_class": "ENTITY_LINEAGE_CONTINUES_CLOCK_ORDER_UNCERTAIN",
            }
        suspend = max(0, boot_gap - mono_gap)
        if invocation_id != prev["invocation_id"]:
            gap_class = "PROCESS_RESTART_SAME_BOOT"
        elif suspend > max(5_000_000, interval_ns // 2):
            gap_class = "SUSPEND_GAP"
        else:
            gap_class = "SAME_INVOCATION"
        confidence = (
            "HIGH"
            if abs(wall - boot_gap) < max(2_000_000_000, interval_ns * 2)
            else "MEDIUM"
        )
        return {
            "wall_gap_ns": wall,
            "boottime_gap_ns": boot_gap,
            "monotonic_gap_ns": mono_gap,
            "inferred_suspend_ns": suspend,
            "gap_class": gap_class,
            "missed_logical_slots": int(missed),
            "clock_confidence": confidence,
            "continuity_class": "ENTITY_LINEAGE_CONTINUES_ACTUAL_PULSES_ONLY",
        }

    def preview_orientation(
        self,
        entity_id: str,
        *,
        pulse_id: str,
        lease_id: str,
        interval_ns: int,
        utc_ns: int,
        boottime_ns: int,
        monotonic_ns: int,
        boot_id: str,
        invocation_id: str,
    ) -> TemporalOrientation:
        entity = self.entity(entity_id)
        lease = self.current_lease(entity_id)
        if not lease or not lease["active"] or lease["lease_id"] != lease_id:
            raise StaleLease("pulse requires current active lease")
        if lease["boot_id"] != boot_id or lease["invocation_id"] != invocation_id:
            raise StaleLease("pulse runtime identity differs from lease")
        prev = self.last_pulse(entity_id)
        gap = self.classify_gap(
            prev,
            utc_ns=utc_ns,
            boottime_ns=boottime_ns,
            monotonic_ns=monotonic_ns,
            boot_id=boot_id,
            invocation_id=invocation_id,
            interval_ns=interval_ns,
        )
        pulse_seq = int(prev["pulse_seq"]) + 1 if prev else 1
        return TemporalOrientation(
            entity_id=entity_id,
            entity_version=entity["entity_version"],
            artifact_digest=entity["artifact_digest"],
            lineage_root_id=entity["lineage_root_id"],
            generation=int(entity["generation"]),
            pulse_seq=pulse_seq,
            pulse_id=pulse_id,
            lease_id=lease_id,
            lease_epoch=int(lease["lease_epoch"]),
            host_id=str(lease["host_id"]),
            boot_id=boot_id,
            invocation_id=invocation_id,
            observed_at_utc_ns=utc_ns,
            boottime_ns=boottime_ns,
            monotonic_ns=monotonic_ns,
            entity_age_ns=max(0, utc_ns - int(entity["born_at_utc_ns"])),
            peer_count=self.peer_count(entity_id),
            **gap,
        )
