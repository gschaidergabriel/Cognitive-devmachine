#!/usr/bin/env python3
"""Shared host-wide effect fence for multiple local bridge daemons.

This is coordination infrastructure, not a competing project truth store.
It solves one narrow problem: two independently idempotent bridge daemons can
still race effects on the same physical host.

Design
------
* READ_ONLY: no global host lock; must not mutate host/application state.
* SCRATCH_ONLY: no global host lock; caller must bind an explicit scratch root.
* LIVE_MUTATION / SYSTEM_MUTATION: acquire one machine-wide advisory flock and
  one shared SQLite effect journal before execution.
* command_id + command_sha256 are immutable identity. Reusing an id with changed
  bytes fails closed.
* a RUNNING/UNKNOWN prior effect blocks replay. Human/independent reconciliation
  must classify it before another attempt.
* SUCCEEDED exact replay is suppressed, not re-executed.
* path/hash preconditions are checked after the lock is held and immediately
  before the caller enters the effect body.

Both Frank's machine-specific bridge and the generic Clay bridge must call this
same module/path for effect-bearing commands before either can claim host effect
authority. Merely installing this file does not change either daemon.
"""
from __future__ import annotations

import contextlib
from dataclasses import dataclass
from enum import Enum
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import time
from typing import Iterator, Sequence


class EffectClass(str, Enum):
    READ_ONLY = "READ_ONLY"
    SCRATCH_ONLY = "SCRATCH_ONLY"
    LIVE_MUTATION = "LIVE_MUTATION"
    SYSTEM_MUTATION = "SYSTEM_MUTATION"


class EffectFenceError(RuntimeError):
    pass


class CommandIdentityConflict(EffectFenceError):
    pass


class UnknownPriorEffect(EffectFenceError):
    pass


class LeaseBusy(EffectFenceError):
    pass


class SubjectDrift(EffectFenceError):
    pass


class ScratchBoundaryError(EffectFenceError):
    pass


@dataclass(frozen=True)
class PathHashPrecondition:
    path: Path
    sha256: str


@dataclass(frozen=True)
class EffectTicket:
    command_id: str
    command_sha256: str
    effect_class: EffectClass
    holder: str
    machine_id: str
    generation: int
    started_at: float
    duplicate_suppressed: bool = False


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;
PRAGMA busy_timeout=30000;
CREATE TABLE IF NOT EXISTS effect_attempts(
  command_id TEXT PRIMARY KEY,
  command_sha256 TEXT NOT NULL,
  effect_class TEXT NOT NULL,
  holder TEXT NOT NULL,
  machine_id TEXT NOT NULL,
  generation INTEGER NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('PREPARED','RUNNING','SUCCEEDED','FAILED','UNKNOWN','RECONCILED_SAFE')),
  started_at REAL NOT NULL,
  finished_at REAL,
  outcome_sha256 TEXT,
  note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS effect_meta(
  singleton INTEGER PRIMARY KEY CHECK(singleton=1),
  generation INTEGER NOT NULL
);
INSERT OR IGNORE INTO effect_meta(singleton,generation) VALUES(1,0);
"""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_state_root() -> Path:
    override = os.environ.get("CLAY_HOST_EFFECT_STATE_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / ".local" / "share" / "clay-host-effect-fence").resolve()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


class HostEffectFence:
    def __init__(self, state_root: Path | None = None, *, machine_id: str | None = None):
        self.state_root = (state_root or canonical_state_root()).expanduser().resolve()
        self.state_root.mkdir(parents=True, exist_ok=True)
        self.lock_path = self.state_root / "host-effect.lock"
        self.db_path = self.state_root / "host-effect.sqlite3"
        self.machine_id = machine_id or socket.gethostname()
        self.db = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def close(self) -> None:
        self.db.close()

    @contextlib.contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield self.db
        except Exception:
            self.db.execute("ROLLBACK")
            raise
        else:
            self.db.execute("COMMIT")

    @contextlib.contextmanager
    def _exclusive_host_lock(self, *, blocking: bool = False) -> Iterator[object]:
        self.lock_path.touch(exist_ok=True)
        handle = self.lock_path.open("r+")
        flags = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
        try:
            try:
                fcntl.flock(handle.fileno(), flags)
            except BlockingIOError as exc:
                raise LeaseBusy(str(self.lock_path)) from exc
            yield handle
        finally:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()

    def _assert_identity(self, command_id: str, command_sha256: str) -> sqlite3.Row | None:
        row = self.db.execute(
            "SELECT * FROM effect_attempts WHERE command_id=?", (command_id,)
        ).fetchone()
        if row and row["command_sha256"] != command_sha256:
            raise CommandIdentityConflict(
                f"{command_id}: stored={row['command_sha256']} requested={command_sha256}"
            )
        return row

    def _assert_no_unknown_effect(self, command_id: str) -> None:
        row = self.db.execute(
            "SELECT command_id,status,holder,generation FROM effect_attempts "
            "WHERE status IN ('PREPARED','RUNNING','UNKNOWN') AND command_id<>? "
            "ORDER BY started_at DESC LIMIT 1",
            (command_id,),
        ).fetchone()
        if row:
            raise UnknownPriorEffect(
                f"unreconciled effect {row['command_id']} status={row['status']} "
                f"holder={row['holder']} generation={row['generation']}"
            )

    @staticmethod
    def assert_preconditions(preconditions: Sequence[PathHashPrecondition]) -> None:
        for item in preconditions:
            path = item.path.expanduser().resolve()
            if not path.is_file():
                raise SubjectDrift(f"missing subject: {path}")
            actual = sha256_file(path)
            if actual != item.sha256:
                raise SubjectDrift(f"{path}: {actual} != {item.sha256}")

    @staticmethod
    def assert_scratch_root(scratch_root: Path | None, touched_paths: Sequence[Path]) -> None:
        if scratch_root is None:
            raise ScratchBoundaryError("SCRATCH_ONLY requires scratch_root")
        root = scratch_root.expanduser().resolve()
        for raw in touched_paths:
            path = raw.expanduser().resolve()
            if not _is_within(path, root):
                raise ScratchBoundaryError(f"{path} escapes scratch root {root}")

    def classify_replay(self, command_id: str, command_sha256: str) -> str:
        row = self._assert_identity(command_id, command_sha256)
        if not row:
            return "NEW"
        if row["status"] == "SUCCEEDED":
            return "DUPLICATE_SUPPRESSED"
        if row["status"] in {"PREPARED", "RUNNING", "UNKNOWN"}:
            raise UnknownPriorEffect(f"{command_id}: prior status {row['status']}")
        return "RETRY_ALLOWED"

    @contextlib.contextmanager
    def effect(
        self,
        *,
        command_id: str,
        command_sha256: str,
        effect_class: EffectClass,
        holder: str,
        preconditions: Sequence[PathHashPrecondition] = (),
        scratch_root: Path | None = None,
        touched_paths: Sequence[Path] = (),
        blocking: bool = False,
    ) -> Iterator[EffectTicket]:
        if effect_class is EffectClass.READ_ONLY:
            self.assert_preconditions(preconditions)
            yield EffectTicket(
                command_id, command_sha256, effect_class, holder, self.machine_id,
                generation=0, started_at=time.time(), duplicate_suppressed=False,
            )
            return

        if effect_class is EffectClass.SCRATCH_ONLY:
            self.assert_scratch_root(scratch_root, touched_paths)
            self.assert_preconditions(preconditions)
            yield EffectTicket(
                command_id, command_sha256, effect_class, holder, self.machine_id,
                generation=0, started_at=time.time(), duplicate_suppressed=False,
            )
            return

        # All live/system effects share one physical-host critical section,
        # regardless of which bridge branch or daemon requested the operation.
        with self._exclusive_host_lock(blocking=blocking) as lock_handle:
            replay = self.classify_replay(command_id, command_sha256)
            if replay == "DUPLICATE_SUPPRESSED":
                row = self.db.execute(
                    "SELECT * FROM effect_attempts WHERE command_id=?", (command_id,)
                ).fetchone()
                assert row is not None
                yield EffectTicket(
                    command_id, command_sha256, effect_class, holder, self.machine_id,
                    int(row["generation"]), float(row["started_at"]), True,
                )
                return

            self._assert_no_unknown_effect(command_id)
            self.assert_preconditions(preconditions)
            started = time.time()
            with self._tx() as db:
                generation = int(
                    db.execute("SELECT generation FROM effect_meta WHERE singleton=1").fetchone()[0]
                ) + 1
                db.execute(
                    "UPDATE effect_meta SET generation=? WHERE singleton=1", (generation,)
                )
                db.execute(
                    "INSERT INTO effect_attempts(command_id,command_sha256,effect_class,holder,machine_id,generation,status,started_at) "
                    "VALUES(?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(command_id) DO UPDATE SET "
                    "effect_class=excluded.effect_class,holder=excluded.holder,machine_id=excluded.machine_id," 
                    "generation=excluded.generation,status='PREPARED',started_at=excluded.started_at,finished_at=NULL,outcome_sha256=NULL,note=''",
                    (
                        command_id, command_sha256, effect_class.value, holder,
                        self.machine_id, generation, "PREPARED", started,
                    ),
                )
                db.execute(
                    "UPDATE effect_attempts SET status='RUNNING' WHERE command_id=? AND generation=?",
                    (command_id, generation),
                )

            lock_meta = {
                "schema": "CLAY_HOST_EFFECT_LEASE/v1",
                "machine_id": self.machine_id,
                "command_id": command_id,
                "command_sha256": command_sha256,
                "effect_class": effect_class.value,
                "holder": holder,
                "generation": generation,
                "started_at": started,
                "pid": os.getpid(),
            }
            lock_handle.seek(0)
            lock_handle.truncate()
            lock_handle.write(json.dumps(lock_meta, sort_keys=True) + "\n")
            lock_handle.flush()
            os.fsync(lock_handle.fileno())

            ticket = EffectTicket(
                command_id, command_sha256, effect_class, holder, self.machine_id,
                generation, started, False,
            )
            try:
                yield ticket
            except BaseException as exc:
                # We know the Python effect body raised, but we deliberately do
                # not claim the external world is unchanged. Reconciliation is
                # required before replay.
                with self._tx() as db:
                    db.execute(
                        "UPDATE effect_attempts SET status='UNKNOWN',finished_at=?,note=? "
                        "WHERE command_id=? AND generation=?",
                        (time.time(), f"effect body raised {type(exc).__name__}", command_id, generation),
                    )
                raise
            else:
                # Caller must separately bind/verify the real outcome. Success
                # here only means the guarded effect body returned normally.
                with self._tx() as db:
                    db.execute(
                        "UPDATE effect_attempts SET status='SUCCEEDED',finished_at=? "
                        "WHERE command_id=? AND generation=?",
                        (time.time(), command_id, generation),
                    )

    def mark_unknown_after_startup(self) -> int:
        """Fail closed after daemon/host restart.

        A crashed process releases flock automatically, so OS-lock availability
        alone cannot prove a prior external effect did not happen. Any leftover
        PREPARED/RUNNING attempt becomes UNKNOWN and blocks future live effects.
        """
        with self._tx() as db:
            cur = db.execute(
                "UPDATE effect_attempts SET status='UNKNOWN',finished_at=?,note="
                "CASE WHEN note='' THEN 'startup reconciliation required' ELSE note END "
                "WHERE status IN ('PREPARED','RUNNING')",
                (time.time(),),
            )
            return int(cur.rowcount)

    def reconcile_safe(self, command_id: str, *, note: str) -> None:
        if not note.strip():
            raise ValueError("reconciliation note required")
        with self._tx() as db:
            row = db.execute(
                "SELECT status FROM effect_attempts WHERE command_id=?", (command_id,)
            ).fetchone()
            if not row:
                raise KeyError(command_id)
            if row["status"] != "UNKNOWN":
                raise EffectFenceError(f"{command_id}: status={row['status']} is not UNKNOWN")
            db.execute(
                "UPDATE effect_attempts SET status='RECONCILED_SAFE',finished_at=?,note=? WHERE command_id=?",
                (time.time(), note, command_id),
            )
