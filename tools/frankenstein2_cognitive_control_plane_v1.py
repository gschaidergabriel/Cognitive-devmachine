#!/usr/bin/env python3
"""Typed live cognitive control plane for Frankenstein 2.0 / GRID10.

This is a functional cognition-control primitive, not a security system and not a
canonical world-state authority. It lives in the same SQLite file as the rest of the
GRID10/UnifiedDB development runtime and provides:

- one immutable ControlSnapshot per cognitive cycle;
- typed controls (mode, float, int);
- atomic multi-control patches;
- optimistic concurrency using snapshot digest + per-control versions;
- human/experiment/auto writers through the same data plane;
- optional human pins that temporarily suppress ordinary auto-tuning;
- durable revision receipts and deterministic rollback inputs.

The intended runtime pattern is:

    many signal readers/proposers -> one aggregated patch -> one batched commit
    -> next cognitive cycle latches one ControlSnapshot.

Dedicated security policy is intentionally layered later; this module does not attempt
to decide who is authorized to control a finished Frankenstein 2.0 system.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from types import MappingProxyType
from typing import Any, Mapping

SCHEMA = "FRANKENSTEIN2_COGNITIVE_CONTROL_PLANE/v1"
SNAPSHOT_SCHEMA = "FRANKENSTEIN2_CONTROL_SNAPSHOT/v1"
PATCH_SCHEMA = "FRANKENSTEIN2_CONTROL_PATCH/v1"


class ControlError(ValueError):
    pass


class ControlKind(str, Enum):
    FLOAT = "FLOAT"
    INT = "INT"
    MODE = "MODE"


class ControlMode(str, Enum):
    ON = "ON"
    COMPUTE_OFF = "COMPUTE_OFF"
    OUTPUT_OFF = "OUTPUT_OFF"
    MEMORY_OFF = "MEMORY_OFF"


WRITER_KINDS = {"HUMAN", "AUTO", "EXPERIMENT", "LATER_SECURITY"}


@dataclass(frozen=True)
class ControlSpec:
    name: str
    kind: ControlKind
    default: float | int | str
    minimum: float | None = None
    maximum: float | None = None
    choices: tuple[str, ...] = ()
    description: str = ""


@dataclass(frozen=True)
class ControlValue:
    name: str
    kind: str
    value: float | int | str
    version: int
    control_epoch: int
    writer: str | None
    writer_kind: str | None
    ts_ms: float | None
    pin_until_ts: float | None
    reason: str | None


@dataclass(frozen=True)
class ControlSnapshot:
    schema: str
    control_epoch: int
    values: Mapping[str, ControlValue]
    snapshot_digest: str

    def __post_init__(self) -> None:
        # frozen=True protects the dataclass attributes, not a mutable dict stored in
        # values. Copy before proxying so neither callers nor the constructor's source
        # mapping can mutate a latched snapshot while leaving snapshot_digest unchanged.
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))

    def get(self, name: str) -> float | int | str:
        try:
            return self.values[name].value
        except KeyError as exc:
            raise ControlError(f"UNKNOWN_CONTROL:{name}") from exc

    def mode(self, name: str) -> ControlMode:
        return ControlMode(str(self.get(name)))

    def float(self, name: str) -> float:
        return float(self.get(name))

    def int(self, name: str) -> int:
        return int(self.get(name))


@dataclass(frozen=True)
class ControlPatchItem:
    name: str
    value: float | int | str
    expected_version: int


@dataclass(frozen=True)
class ControlPatch:
    schema: str
    patch_id: str
    base_snapshot_digest: str
    writer: str
    writer_kind: str
    reason: str
    items: tuple[ControlPatchItem, ...]
    pin_seconds: float | None = None


@dataclass(frozen=True)
class ControlPatchReceipt:
    schema: str
    patch_id: str
    accepted: bool
    reason: str
    previous_digest: str
    new_digest: str | None
    control_epoch: int | None
    changed: tuple[str, ...]


def _mode(name: str, default: ControlMode = ControlMode.ON, description: str = "") -> ControlSpec:
    return ControlSpec(
        name=name,
        kind=ControlKind.MODE,
        default=default.value,
        choices=tuple(m.value for m in ControlMode),
        description=description,
    )


def _gain(name: str, default: float = 1.0, description: str = "") -> ControlSpec:
    return ControlSpec(name, ControlKind.FLOAT, default, 0.0, 4.0, (), description)


DEFAULT_CONTROL_CATALOG: dict[str, ControlSpec] = {
    "pulse.salience_threshold": ControlSpec("pulse.salience_threshold", ControlKind.FLOAT, 0.35, 0.0, 1.0, (), "minimum pulse admission salience"),
    "pulse.active_interval_seconds": ControlSpec("pulse.active_interval_seconds", ControlKind.FLOAT, 1.0, 0.05, 300.0, (), "cadence while active"),
    "pulse.hold_interval_seconds": ControlSpec("pulse.hold_interval_seconds", ControlKind.FLOAT, 15.0, 0.1, 3600.0, (), "poll cadence while HOLD"),
    "pulse.idle_interval_seconds": ControlSpec("pulse.idle_interval_seconds", ControlKind.FLOAT, 30.0, 0.1, 3600.0, (), "idle cadence without active goal"),
    **{f"grid.{name}.mode": _mode(f"grid.{name}.mode") for name in (
        "orientation", "goal", "epistemic", "hypothesis", "world", "planning",
        "retrieval", "microlab", "delegation", "critic"
    )},
    **{f"grid.{name}.gain": _gain(f"grid.{name}.gain") for name in (
        "orientation", "goal", "epistemic", "hypothesis", "world", "planning",
        "retrieval", "microlab", "delegation", "critic"
    )},
    "grid.workspace_ignition_threshold": ControlSpec("grid.workspace_ignition_threshold", ControlKind.FLOAT, 0.5, 0.0, 1.0, (), "GWT broadcast/ignition threshold"),
    "grid.counterhypothesis_pressure": ControlSpec("grid.counterhypothesis_pressure", ControlKind.FLOAT, 0.5, 0.0, 1.0, (), "pressure to preserve/generate serious alternatives"),
    "reflection.max_rounds": ControlSpec("reflection.max_rounds", ControlKind.INT, 8, 0, 64, (), "bounded reflection rounds without useful delta"),
    "recursion.max_depth": ControlSpec("recursion.max_depth", ControlKind.INT, 3, 0, 16, (), "R1/R2 recursive depth budget"),
    "recursion.max_children": ControlSpec("recursion.max_children", ControlKind.INT, 4, 0, 64, (), "recursive child fan-out budget"),
    "memory.activation_decay": ControlSpec("memory.activation_decay", ControlKind.FLOAT, 0.05, 0.0, 1.0, (), "activation degradation pressure; not hard deletion"),
    "memory.reactivation_threshold": ControlSpec("memory.reactivation_threshold", ControlKind.FLOAT, 0.55, 0.0, 1.0, (), "minimum overlap/utility for old memory reactivation"),
    "memory.max_items": ControlSpec("memory.max_items", ControlKind.INT, 64, 1, 4096, (), "max active memory items"),
    "memory.context_token_budget": ControlSpec("memory.context_token_budget", ControlKind.INT, 8192, 256, 262144, (), "context capsule budget"),
    "world.vector.mode": _mode("world.vector.mode"),
    "world.vector.gain": _gain("world.vector.gain"),
    "world.qubo.mode": _mode("world.qubo.mode"),
    "world.qubo.gain": _gain("world.qubo.gain"),
    "world.physics.mode": _mode("world.physics.mode"),
    "world.physics.gain": _gain("world.physics.gain"),
    "world.max_slice_atoms": ControlSpec("world.max_slice_atoms", ControlKind.INT, 128, 4, 8192, (), "bounded JIT WorldSlice size"),
    "microlab.expected_information_gain_min": ControlSpec("microlab.expected_information_gain_min", ControlKind.FLOAT, 0.25, 0.0, 1.0, (), "minimum expected information gain to run experiment"),
    "microlab.max_steps": ControlSpec("microlab.max_steps", ControlKind.INT, 128, 1, 100000, (), "simulation step budget"),
    "microlab.max_wall_ms": ControlSpec("microlab.max_wall_ms", ControlKind.INT, 250, 1, 60000, (), "wall-clock budget"),
    "delegation.spawn_threshold": ControlSpec("delegation.spawn_threshold", ControlKind.FLOAT, 0.55, 0.0, 1.0, (), "minimum expected value for child spawn"),
    "delegation.max_parallel": ControlSpec("delegation.max_parallel", ControlKind.INT, 4, 1, 64, (), "parallel native child workpackages"),
    "voice.initiative_gain": ControlSpec("voice.initiative_gain", ControlKind.FLOAT, 1.0, 0.0, 4.0, (), "proactive voice pressure"),
    "completion.verification_effort": ControlSpec("completion.verification_effort", ControlKind.FLOAT, 1.0, 0.0, 4.0, (), "verification effort multiplier"),
}


def _cj(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_cj(value).encode("utf-8")).hexdigest()


def _connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path), isolation_level=None, timeout=10.0)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


class CognitiveControlPlane:
    def __init__(self, path: Path, *, catalog: Mapping[str, ControlSpec] = DEFAULT_CONTROL_CATALOG, max_patch_items: int = 64) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.catalog = dict(catalog)
        self.max_patch_items = int(max_patch_items)
        if self.max_patch_items < 1:
            raise ValueError("max_patch_items must be >= 1")
        self._init_schema()

    def _init_schema(self) -> None:
        con = _connect(self.path)
        try:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS cognitive_control_meta(k TEXT PRIMARY KEY,v TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS cognitive_control_values(
                  name TEXT PRIMARY KEY,
                  kind TEXT NOT NULL,
                  value_json TEXT NOT NULL,
                  version INTEGER NOT NULL,
                  control_epoch INTEGER NOT NULL,
                  writer TEXT NOT NULL,
                  writer_kind TEXT NOT NULL,
                  ts_ms REAL NOT NULL,
                  pin_until_ts REAL,
                  reason TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS cognitive_control_revisions(
                  control_epoch INTEGER PRIMARY KEY,
                  patch_id TEXT NOT NULL UNIQUE,
                  base_snapshot_digest TEXT NOT NULL,
                  new_snapshot_digest TEXT,
                  writer TEXT NOT NULL,
                  writer_kind TEXT NOT NULL,
                  reason TEXT NOT NULL,
                  patch_json TEXT NOT NULL,
                  created_ts REAL NOT NULL
                );
                """
            )
            con.execute("INSERT OR IGNORE INTO cognitive_control_meta(k,v) VALUES('control_epoch','0')")
        finally:
            con.close()

    def _epoch(self, con: sqlite3.Connection) -> int:
        row = con.execute("SELECT v FROM cognitive_control_meta WHERE k='control_epoch'").fetchone()
        if row is None:
            raise ControlError("MISSING_CONTROL_EPOCH")
        return int(row["v"])

    def _validate_value(self, spec: ControlSpec, value: Any) -> float | int | str:
        if spec.kind == ControlKind.MODE:
            sval = str(value)
            if sval not in spec.choices:
                raise ControlError(f"INVALID_MODE:{spec.name}:{sval}")
            return sval
        if spec.kind == ControlKind.INT:
            if isinstance(value, bool):
                raise ControlError(f"INVALID_INT:{spec.name}")
            try:
                fval = float(value)
            except (TypeError, ValueError) as exc:
                raise ControlError(f"INVALID_INT:{spec.name}") from exc
            ival = int(fval)
            if abs(fval - ival) > 1e-12:
                raise ControlError(f"NON_INTEGRAL_VALUE:{spec.name}")
            if spec.minimum is not None and ival < spec.minimum:
                raise ControlError(f"BELOW_MIN:{spec.name}")
            if spec.maximum is not None and ival > spec.maximum:
                raise ControlError(f"ABOVE_MAX:{spec.name}")
            return ival
        try:
            fval = float(value)
        except (TypeError, ValueError) as exc:
            raise ControlError(f"INVALID_FLOAT:{spec.name}") from exc
        if spec.minimum is not None and fval < spec.minimum:
            raise ControlError(f"BELOW_MIN:{spec.name}")
        if spec.maximum is not None and fval > spec.maximum:
            raise ControlError(f"ABOVE_MAX:{spec.name}")
        return fval

    def _snapshot_con(self, con: sqlite3.Connection) -> ControlSnapshot:
        epoch = self._epoch(con)
        rows = {str(r["name"]): r for r in con.execute(
            "SELECT name,kind,value_json,version,control_epoch,writer,writer_kind,ts_ms,pin_until_ts,reason FROM cognitive_control_values ORDER BY name"
        )}
        values: dict[str, ControlValue] = {}
        digest_rows: list[dict[str, Any]] = []
        for name in sorted(self.catalog):
            spec = self.catalog[name]
            row = rows.get(name)
            if row is None:
                cv = ControlValue(name, spec.kind.value, self._validate_value(spec, spec.default), 0, 0, None, None, None, None, None)
            else:
                if str(row["kind"]) != spec.kind.value:
                    raise ControlError(f"CONTROL_KIND_MISMATCH:{name}")
                cv = ControlValue(
                    name=name,
                    kind=spec.kind.value,
                    value=self._validate_value(spec, json.loads(str(row["value_json"]))),
                    version=int(row["version"]),
                    control_epoch=int(row["control_epoch"]),
                    writer=str(row["writer"]),
                    writer_kind=str(row["writer_kind"]),
                    ts_ms=float(row["ts_ms"]),
                    pin_until_ts=None if row["pin_until_ts"] is None else float(row["pin_until_ts"]),
                    reason=str(row["reason"]),
                )
            values[name] = cv
            digest_rows.append(asdict(cv))
        body = {"schema": SNAPSHOT_SCHEMA, "control_epoch": epoch, "values": digest_rows}
        return ControlSnapshot(SNAPSHOT_SCHEMA, epoch, values, _digest(body))

    def snapshot(self) -> ControlSnapshot:
        con = _connect(self.path)
        try:
            con.execute("BEGIN")
            snap = self._snapshot_con(con)
            con.execute("COMMIT")
            return snap
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def build_patch(self, *, patch_id: str, writer: str, writer_kind: str, reason: str, changes: Mapping[str, Any], base: ControlSnapshot | None = None, pin_seconds: float | None = None) -> ControlPatch:
        if base is None:
            base = self.snapshot()
        items = []
        for name in sorted(changes):
            current = base.values.get(name)
            if current is None:
                raise ControlError(f"UNKNOWN_CONTROL:{name}")
            items.append(ControlPatchItem(name, changes[name], current.version))
        return ControlPatch(PATCH_SCHEMA, patch_id, base.snapshot_digest, writer, writer_kind, reason, tuple(items), pin_seconds)

    def apply_patch(self, patch: ControlPatch) -> ControlPatchReceipt:
        if patch.schema != PATCH_SCHEMA:
            raise ControlError("PATCH_SCHEMA_MISMATCH")
        if not patch.patch_id.strip():
            raise ControlError("PATCH_ID_REQUIRED")
        if not patch.writer.strip():
            raise ControlError("WRITER_REQUIRED")
        if patch.writer_kind not in WRITER_KINDS:
            raise ControlError(f"UNKNOWN_WRITER_KIND:{patch.writer_kind}")
        if not patch.reason.strip():
            raise ControlError("PATCH_REASON_REQUIRED")
        if not patch.items:
            raise ControlError("EMPTY_PATCH")
        if len(patch.items) > self.max_patch_items:
            raise ControlError("PATCH_ITEM_BUDGET_EXCEEDED")

        seen = set()
        validated = []
        for item in patch.items:
            if item.name in seen:
                raise ControlError(f"DUPLICATE_CONTROL:{item.name}")
            seen.add(item.name)
            spec = self.catalog.get(item.name)
            if spec is None:
                raise ControlError(f"UNKNOWN_CONTROL:{item.name}")
            validated.append((item, spec, self._validate_value(spec, item.value)))

        patch_json = _cj(asdict(patch))
        con = _connect(self.path)
        try:
            con.execute("BEGIN IMMEDIATE")
            existing_revision = con.execute(
                "SELECT new_snapshot_digest,control_epoch,patch_json FROM cognitive_control_revisions WHERE patch_id=?",
                (patch.patch_id,),
            ).fetchone()
            if existing_revision is not None:
                if str(existing_revision["patch_json"]) != patch_json:
                    raise ControlError("PATCH_ID_REUSE_CONFLICT")
                con.execute("COMMIT")
                return ControlPatchReceipt(
                    PATCH_SCHEMA, patch.patch_id, True, "IDEMPOTENT_REPLAY_ALREADY_COMMITTED",
                    patch.base_snapshot_digest,
                    str(existing_revision["new_snapshot_digest"]) if existing_revision["new_snapshot_digest"] is not None else None,
                    int(existing_revision["control_epoch"]), tuple(item.name for item in patch.items)
                )

            previous = self._snapshot_con(con)
            if patch.base_snapshot_digest != previous.snapshot_digest:
                raise ControlError("STALE_CONTROL_SNAPSHOT")

            now = time.time()
            for item, _, _ in validated:
                current = previous.values[item.name]
                if item.expected_version != current.version:
                    raise ControlError(f"CONTROL_VERSION_CAS_FAILED:{item.name}")
                if patch.writer_kind == "AUTO" and current.pin_until_ts is not None and current.pin_until_ts > now and current.writer_kind == "HUMAN":
                    raise ControlError(f"HUMAN_PIN_ACTIVE:{item.name}")

            epoch = previous.control_epoch + 1
            con.execute("UPDATE cognitive_control_meta SET v=? WHERE k='control_epoch'", (str(epoch),))
            pin_until = None if patch.pin_seconds is None else now + max(0.0, float(patch.pin_seconds))
            ts_ms = now * 1000.0
            for item, spec, value in validated:
                current = previous.values[item.name]
                con.execute(
                    "INSERT INTO cognitive_control_values(name,kind,value_json,version,control_epoch,writer,writer_kind,ts_ms,pin_until_ts,reason) VALUES(?,?,?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(name) DO UPDATE SET kind=excluded.kind,value_json=excluded.value_json,version=excluded.version,control_epoch=excluded.control_epoch,writer=excluded.writer,writer_kind=excluded.writer_kind,ts_ms=excluded.ts_ms,pin_until_ts=excluded.pin_until_ts,reason=excluded.reason",
                    (item.name, spec.kind.value, _cj(value), current.version + 1, epoch, patch.writer, patch.writer_kind, ts_ms, pin_until, patch.reason),
                )
            after = self._snapshot_con(con)
            con.execute(
                "INSERT INTO cognitive_control_revisions(control_epoch,patch_id,base_snapshot_digest,new_snapshot_digest,writer,writer_kind,reason,patch_json,created_ts) VALUES(?,?,?,?,?,?,?,?,?)",
                (epoch, patch.patch_id, patch.base_snapshot_digest, after.snapshot_digest, patch.writer, patch.writer_kind, patch.reason, patch_json, now),
            )
            con.execute("COMMIT")
            return ControlPatchReceipt(PATCH_SCHEMA, patch.patch_id, True, "ATOMIC_PATCH_COMMITTED", previous.snapshot_digest, after.snapshot_digest, epoch, tuple(item.name for item in patch.items))
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def revision_rows(self) -> tuple[dict[str, Any], ...]:
        con = _connect(self.path)
        try:
            return tuple(dict(r) for r in con.execute(
                "SELECT control_epoch,patch_id,base_snapshot_digest,new_snapshot_digest,writer,writer_kind,reason,created_ts FROM cognitive_control_revisions ORDER BY control_epoch"
            ))
        finally:
            con.close()


def control_snapshot_json(snapshot: ControlSnapshot) -> str:
    return _cj({
        "schema": snapshot.schema,
        "control_epoch": snapshot.control_epoch,
        "snapshot_digest": snapshot.snapshot_digest,
        "values": {name: asdict(value) for name, value in sorted(snapshot.values.items())},
    })
