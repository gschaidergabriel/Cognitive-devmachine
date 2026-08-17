from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import time
import uuid
from collections import Counter
from pathlib import Path

from .store import UnifiedDB


class LogicalSnapshotIntegrityError(RuntimeError):
    pass


_REQUIRED_RUNTIME_IDENTITY = {
    "source_revision",
    "image_digest",
    "entityos_sha256",
    "managed_settings_sha256",
    "managed_mcp_sha256",
    "runtime_claude_md_sha256",
    "claude_identity",
    "tmux_identity",
}
_SHA256_FIELDS = {
    "entityos_sha256",
    "managed_settings_sha256",
    "managed_mcp_sha256",
    "runtime_claude_md_sha256",
}
_MANIFEST_SCHEMA = "ClayVerseKnownGoodLogicalMachineSnapshot/v1"
_MAX_MANIFEST_BYTES = 128 * 1024


def _canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                return digest.hexdigest()
            digest.update(chunk)


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _validate_hex(value: str, length: int, label: str) -> str:
    if not isinstance(value, str) or len(value) != length or any(c not in "0123456789abcdefABCDEF" for c in value):
        raise LogicalSnapshotIntegrityError(f"invalid {label}")
    return value.lower()


def _validated_runtime_identity(runtime_identity: dict) -> dict:
    if not isinstance(runtime_identity, dict) or set(runtime_identity) != _REQUIRED_RUNTIME_IDENTITY:
        raise LogicalSnapshotIntegrityError("runtime identity fields incomplete or unexpected")
    result = {}
    for key in sorted(_REQUIRED_RUNTIME_IDENTITY):
        value = runtime_identity[key]
        if not isinstance(value, str) or not value or len(value) > 256 or "\x00" in value or "\n" in value or "\r" in value:
            raise LogicalSnapshotIntegrityError(f"invalid runtime identity value: {key}")
        if key in _SHA256_FIELDS:
            value = _validate_hex(value, 64, key)
        elif key == "source_revision":
            value = _validate_hex(value, 40, key)
        elif key == "image_digest":
            if not value.startswith("sha256:"):
                raise LogicalSnapshotIntegrityError("invalid image_digest")
            value = "sha256:" + _validate_hex(value[7:], 64, key)
        result[key] = value
    return result


def _rows(conn: sqlite3.Connection, sql: str, args=()) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(sql, args).fetchall()]


def _digest_rows(rows: list[dict]) -> str:
    return hashlib.sha256(_canonical(rows).encode("utf-8")).hexdigest()


def _snapshot_state(conn: sqlite3.Connection, checkpoint_id: str, checkpoint_state_hash: str) -> dict:
    quick = conn.execute("PRAGMA quick_check").fetchone()
    if not quick or quick[0] != "ok":
        raise LogicalSnapshotIntegrityError("snapshot SQLite quick_check failed")

    checkpoint = conn.execute(
        "SELECT checkpoint_id,state_hash,note FROM checkpoints WHERE checkpoint_id=?",
        (checkpoint_id,),
    ).fetchone()
    if not checkpoint or checkpoint[0] != checkpoint_id or checkpoint[1] != checkpoint_state_hash:
        raise LogicalSnapshotIntegrityError("snapshot lost canonical checkpoint anchor")

    generation_row = conn.execute("SELECT value FROM meta WHERE key='entity_generation'").fetchone()
    if not generation_row:
        raise LogicalSnapshotIntegrityError("snapshot missing global entity generation")
    try:
        entity_generation = int(generation_row[0])
    except (TypeError, ValueError) as exc:
        raise LogicalSnapshotIntegrityError("invalid global entity generation") from exc
    if entity_generation < 1:
        raise LogicalSnapshotIntegrityError("invalid global entity generation")

    sessions = _rows(conn, "SELECT session_id,user_id,generation,terminal_name FROM sessions ORDER BY session_id")
    active_causal = _rows(
        conn,
        "SELECT session_id,user_id,turn_id,episode_id,causal_id,generation,effect_id,workspace_selected FROM active_turns ORDER BY session_id",
    )
    effects = _rows(
        conn,
        "SELECT effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at FROM effects ORDER BY effect_id",
    )
    effect_status_counts = dict(sorted(Counter(str(row["status"]) for row in effects).items()))

    return {
        "checkpoint_anchor": {
            "checkpoint_id": checkpoint_id,
            "state_hash": checkpoint_state_hash,
            "note": checkpoint[2],
        },
        "entity_generation": entity_generation,
        "sessions": sessions,
        "active_causal": active_causal,
        "effect_journal": {
            "count": len(effects),
            "status_counts": effect_status_counts,
            "sha256": _digest_rows(effects),
        },
    }


def _readonly_snapshot_connection(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro&immutable=1", uri=True)


def _assert_self_contained(db_path: Path) -> None:
    for suffix in ("-wal", "-shm", "-journal"):
        if Path(str(db_path) + suffix).exists():
            raise LogicalSnapshotIntegrityError(f"snapshot database sidecar present: {suffix}")


def _validate_snapshot_path(snapshot_dir: Path) -> tuple[Path, Path]:
    if snapshot_dir.is_symlink() or not snapshot_dir.is_dir():
        raise LogicalSnapshotIntegrityError("snapshot directory must be a real directory")
    db_path = snapshot_dir / "unified.db"
    manifest_path = snapshot_dir / "manifest.json"
    for path in (db_path, manifest_path):
        if path.is_symlink() or not path.is_file():
            raise LogicalSnapshotIntegrityError(f"snapshot member invalid: {path.name}")
    _assert_self_contained(db_path)
    return db_path, manifest_path


class LogicalSnapshotManager:
    """Create, validate and restore bounded ClayVerse logical-machine snapshots."""

    def __init__(self, state_root: str | Path):
        self.state_root = Path(state_root)
        self.root = self.state_root / "snapshots"

    def create(self, db: UnifiedDB, *, runtime_identity: dict, reason: str) -> dict:
        runtime_identity = _validated_runtime_identity(runtime_identity)
        if not isinstance(reason, str) or not reason or len(reason) > 128 or "\x00" in reason or "\n" in reason or "\r" in reason:
            raise LogicalSnapshotIntegrityError("invalid snapshot reason")

        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        snapshot_id = f"snapshot-{time.time_ns()}-{uuid.uuid4().hex}"
        partial = self.root / f".partial-{snapshot_id}"
        final = self.root / snapshot_id
        partial.mkdir(mode=0o700)
        db_path = partial / "unified.db"
        manifest_path = partial / "manifest.json"

        try:
            checkpoint_id, checkpoint_state_hash = db.checkpoint(f"logical-snapshot:{reason}")
            destination = sqlite3.connect(db_path)
            try:
                db.db.backup(destination)
                mode = destination.execute("PRAGMA journal_mode=DELETE").fetchone()
                if not mode or str(mode[0]).lower() != "delete":
                    raise LogicalSnapshotIntegrityError("snapshot database could not leave WAL mode")
            finally:
                destination.close()
            _assert_self_contained(db_path)

            copied = _readonly_snapshot_connection(db_path)
            try:
                state = _snapshot_state(copied, checkpoint_id, checkpoint_state_hash)
            finally:
                copied.close()
            _assert_self_contained(db_path)

            db_size = db_path.stat().st_size
            db_sha256 = _sha256_file(db_path)
            manifest = {
                "schema": _MANIFEST_SCHEMA,
                "snapshot_id": snapshot_id,
                "created_ns": time.time_ns(),
                "reason": reason,
                "database": {"filename": "unified.db", "size": db_size, "sha256": db_sha256},
                "state": state,
                "runtime_identity": runtime_identity,
            }
            encoded = (_canonical(manifest) + "\n").encode("utf-8")
            if len(encoded) > _MAX_MANIFEST_BYTES:
                raise LogicalSnapshotIntegrityError("snapshot manifest exceeds bound")
            with manifest_path.open("xb") as fh:
                fh.write(encoded)
                fh.flush()
                os.fsync(fh.fileno())
            with db_path.open("rb") as fh:
                os.fsync(fh.fileno())
            _fsync_dir(partial)
            os.replace(partial, final)
            _fsync_dir(self.root)
        except Exception:
            shutil.rmtree(partial, ignore_errors=True)
            raise

        return self.validate(final)

    def validate(self, snapshot_dir: str | Path) -> dict:
        snapshot_dir = Path(snapshot_dir)
        db_path, manifest_path = _validate_snapshot_path(snapshot_dir)
        if manifest_path.stat().st_size > _MAX_MANIFEST_BYTES:
            raise LogicalSnapshotIntegrityError("snapshot manifest exceeds bound")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise LogicalSnapshotIntegrityError("snapshot manifest unreadable") from exc

        expected_top = {"schema", "snapshot_id", "created_ns", "reason", "database", "state", "runtime_identity"}
        if not isinstance(manifest, dict) or set(manifest) != expected_top:
            raise LogicalSnapshotIntegrityError("snapshot manifest shape invalid")
        if manifest["schema"] != _MANIFEST_SCHEMA or manifest["snapshot_id"] != snapshot_dir.name:
            raise LogicalSnapshotIntegrityError("snapshot identity mismatch")
        if not isinstance(manifest["created_ns"], int) or manifest["created_ns"] <= 0:
            raise LogicalSnapshotIntegrityError("snapshot timestamp invalid")
        if not isinstance(manifest["reason"], str) or not manifest["reason"] or len(manifest["reason"]) > 128 or any(x in manifest["reason"] for x in ("\x00", "\n", "\r")):
            raise LogicalSnapshotIntegrityError("snapshot reason invalid")
        _validated_runtime_identity(manifest["runtime_identity"])

        database = manifest["database"]
        if not isinstance(database, dict) or set(database) != {"filename", "size", "sha256"}:
            raise LogicalSnapshotIntegrityError("snapshot database identity shape invalid")
        if database["filename"] != "unified.db" or not isinstance(database["size"], int) or database["size"] <= 0:
            raise LogicalSnapshotIntegrityError("snapshot database identity invalid")
        expected_db_sha = _validate_hex(database["sha256"], 64, "snapshot database sha256")
        if db_path.stat().st_size != database["size"] or _sha256_file(db_path) != expected_db_sha:
            raise LogicalSnapshotIntegrityError("snapshot database digest/size mismatch")

        state = manifest["state"]
        if not isinstance(state, dict) or set(state) != {"checkpoint_anchor", "entity_generation", "sessions", "active_causal", "effect_journal"}:
            raise LogicalSnapshotIntegrityError("snapshot state shape invalid")
        anchor = state["checkpoint_anchor"]
        if not isinstance(anchor, dict) or set(anchor) != {"checkpoint_id", "state_hash", "note"}:
            raise LogicalSnapshotIntegrityError("snapshot checkpoint anchor invalid")
        _validate_hex(anchor["state_hash"], 64, "checkpoint state hash")

        copied = _readonly_snapshot_connection(db_path)
        try:
            observed = _snapshot_state(copied, anchor["checkpoint_id"], anchor["state_hash"])
        except sqlite3.DatabaseError as exc:
            raise LogicalSnapshotIntegrityError("snapshot SQLite database invalid") from exc
        finally:
            copied.close()
        _assert_self_contained(db_path)
        if observed != state:
            raise LogicalSnapshotIntegrityError("snapshot manifest/state drift")
        return manifest

    def restore_fresh(self, snapshot_dir: str | Path, *, runtime_identity: dict) -> dict:
        expected_runtime = _validated_runtime_identity(runtime_identity)
        snapshot_dir = Path(snapshot_dir)
        manifest = self.validate(snapshot_dir)
        if manifest["runtime_identity"] != expected_runtime:
            raise LogicalSnapshotIntegrityError("snapshot runtime identity does not match current runtime")

        if os.path.lexists(self.state_root):
            if self.state_root.is_symlink() or not self.state_root.is_dir():
                raise LogicalSnapshotIntegrityError("restore state root must be a real directory")
        else:
            self.state_root.mkdir(parents=True, mode=0o700)
        if self.state_root.is_symlink() or not self.state_root.is_dir():
            raise LogicalSnapshotIntegrityError("restore state root must be a real directory")

        target = self.state_root / "unified.db"
        for candidate in (target, Path(str(target) + "-wal"), Path(str(target) + "-shm"), Path(str(target) + "-journal")):
            if os.path.lexists(candidate):
                raise LogicalSnapshotIntegrityError("restore requires a fresh UnifiedDB target")

        source_db, _ = _validate_snapshot_path(snapshot_dir)
        database = manifest["database"]
        expected_size = int(database["size"])
        expected_sha = str(database["sha256"])
        temp = self.state_root / f".restore-{uuid.uuid4().hex}.db"
        copied_size = 0
        copied_hash = hashlib.sha256()
        try:
            with source_db.open("rb") as source, temp.open("xb") as destination:
                os.chmod(temp, 0o600)
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    copied_size += len(chunk)
                    copied_hash.update(chunk)
                    destination.write(chunk)
                destination.flush()
                os.fsync(destination.fileno())
            if copied_size != expected_size or copied_hash.hexdigest() != expected_sha:
                raise LogicalSnapshotIntegrityError("restored database bytes do not match snapshot manifest")
            try:
                os.link(temp, target)
            except FileExistsError as exc:
                raise LogicalSnapshotIntegrityError("restore target appeared during publication") from exc
            temp.unlink()
            _fsync_dir(self.state_root)
        except Exception:
            try:
                temp.unlink()
            except FileNotFoundError:
                pass
            raise

        return {
            "restored": True,
            "snapshot_id": manifest["snapshot_id"],
            "database_sha256": expected_sha,
            "checkpoint_id": manifest["state"]["checkpoint_anchor"]["checkpoint_id"],
            "entity_generation_before_recovery": manifest["state"]["entity_generation"],
        }

    def latest_valid(self) -> dict | None:
        if not self.root.exists():
            return None
        if self.root.is_symlink() or not self.root.is_dir():
            raise LogicalSnapshotIntegrityError("snapshot root invalid")
        candidates = [path for path in self.root.iterdir() if path.name.startswith("snapshot-")]
        candidates.sort(key=lambda path: path.name, reverse=True)
        for candidate in candidates:
            try:
                return self.validate(candidate)
            except LogicalSnapshotIntegrityError:
                continue
        return None
