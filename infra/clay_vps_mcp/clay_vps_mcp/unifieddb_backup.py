from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import time
from pathlib import Path
from typing import Any

from .history_mirror import commit_event

GIB = 1024 ** 3
DEFAULT_BUDGET = 50 * GIB
PINNED_REASONS = {"PRE_MIGRATION", "POST_MIGRATION", "PRE_DEPLOY", "POST_DEPLOY", "RECOVERY_TEST", "EXPLICIT", "RELEASE"}


def backup_root() -> Path:
    p = Path(os.getenv("FRANK_UNIFIEDDB_BACKUP_ROOT", "/srv/unifieddb-backups"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def backup_budget() -> int:
    return int(os.getenv("FRANK_UNIFIEDDB_BACKUP_BUDGET_BYTES", str(DEFAULT_BUDGET)))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _store_id(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]


def discover_sources() -> list[Path]:
    explicit = [x.strip() for x in os.getenv("FRANK_UNIFIEDDB_PATHS", "").split(",") if x.strip()]
    if explicit:
        return [Path(x).expanduser().resolve(strict=False) for x in explicit if Path(x).expanduser().exists()]

    candidates: list[Path] = []
    default = Path("/opt/frank/data/unified.db")
    if default.exists():
        candidates.append(default.resolve())
    roots = [Path(x.strip()) for x in os.getenv("FRANK_UNIFIEDDB_DISCOVERY_ROOTS", "/opt/frank,/srv/clay-mcp/workspace").split(",") if x.strip()]
    patterns = [x.strip() for x in os.getenv("FRANK_UNIFIEDDB_DISCOVERY_PATTERNS", "*unified*.db,*unified*.sqlite,*unified*.sqlite3").split(",") if x.strip()]
    for root in roots:
        if not root.exists():
            continue
        for pattern in patterns:
            for p in root.rglob(pattern):
                if p.is_file() and "backup" not in {part.lower() for part in p.parts}:
                    candidates.append(p.resolve())
    seen: set[str] = set()
    out = []
    for p in candidates:
        k = str(p)
        if k not in seen:
            seen.add(k)
            out.append(p)
    return out


def sqlite_metadata(path: Path) -> dict[str, Any]:
    uri = f"file:{path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=30)
    try:
        return {
            "user_version": int(conn.execute("PRAGMA user_version").fetchone()[0]),
            "schema_version": int(conn.execute("PRAGMA schema_version").fetchone()[0]),
            "page_size": int(conn.execute("PRAGMA page_size").fetchone()[0]),
            "page_count": int(conn.execute("PRAGMA page_count").fetchone()[0]),
            "journal_mode": str(conn.execute("PRAGMA journal_mode").fetchone()[0]),
            "quick_check": [str(r[0]) for r in conn.execute("PRAGMA quick_check").fetchall()[:100]],
        }
    finally:
        conn.close()


def verify_snapshot(path: Path, full: bool = False) -> dict[str, Any]:
    meta = sqlite_metadata(path)
    if meta["quick_check"] != ["ok"]:
        return {**meta, "ok": False, "check": "quick_check"}
    if full:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=30)
        try:
            rows = [str(r[0]) for r in conn.execute("PRAGMA integrity_check").fetchall()[:100]]
        finally:
            conn.close()
        meta["integrity_check"] = rows
        meta["ok"] = rows == ["ok"]
        meta["check"] = "integrity_check"
    else:
        meta["ok"] = True
        meta["check"] = "quick_check"
    return meta


def _online_backup(source: Path, dest: Path) -> None:
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True, timeout=60)
    dst = sqlite3.connect(dest, timeout=60)
    try:
        src.backup(dst, pages=1024, sleep=0.01)
        dst.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        dst.close()
        src.close()


def _manifest_dir(store_id: str) -> Path:
    p = backup_root() / "manifests" / store_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def _snapshot_dir(store_id: str) -> Path:
    p = backup_root() / "snapshots" / store_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_manifests(store_id: str | None = None) -> list[dict[str, Any]]:
    root = backup_root() / "manifests"
    if not root.exists():
        return []
    dirs = [root / store_id] if store_id else [p for p in root.iterdir() if p.is_dir()]
    rows: list[dict[str, Any]] = []
    for d in dirs:
        if not d.exists():
            continue
        for p in sorted(d.glob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                data["manifest_path"] = str(p)
                rows.append(data)
            except Exception:
                continue
    return sorted(rows, key=lambda x: float(x.get("created_epoch", 0)))


def _latest_physical(store_id: str) -> dict[str, Any] | None:
    for m in reversed(load_manifests(store_id)):
        p = Path(str(m.get("snapshot_path", "")))
        if p.exists() and not m.get("physical_pruned"):
            return m
    return None


def snapshot(source: Path, reason: str = "PERIODIC", full_check: bool = False) -> dict[str, Any]:
    source = source.resolve(strict=True)
    sid = _store_id(source)
    created = time.time()
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(created))
    work = _snapshot_dir(sid) / f".{stamp}-{os.getpid()}.tmp.sqlite3"
    _online_backup(source, work)
    verify = verify_snapshot(work, full=full_check or reason.upper() in PINNED_REASONS)
    if not verify.get("ok"):
        bad_hash = _sha256(work)
        rejected = work.with_name(f"REJECTED-{stamp}-{bad_hash[:16]}.sqlite3")
        os.replace(work, rejected)
        result = {"status": "REJECTED", "reason": reason, "source": str(source), "snapshot_path": str(rejected), "sha256": bad_hash, "verify": verify}
        commit_event({"time": stamp, "epoch": created, "action": "unifieddb_snapshot_rejected", "payload": {"path": str(source), "reason": reason}, "result": result})
        return result

    digest = _sha256(work)
    latest = _latest_physical(sid)
    if latest and latest.get("sha256") == digest:
        work.unlink(missing_ok=True)
        result = {"status": "UNCHANGED", "source": str(source), "store_id": sid, "sha256": digest, "reason": reason, "previous_snapshot_id": latest.get("snapshot_id")}
        commit_event({"time": stamp, "epoch": created, "action": "unifieddb_snapshot_unchanged", "payload": {"path": str(source), "reason": reason}, "result": result})
        return result

    final = _snapshot_dir(sid) / f"{stamp}-{digest[:16]}.sqlite3"
    os.replace(work, final)
    src_stat = source.stat()
    snapshot_id = f"udb-{sid}-{stamp}-{digest[:12]}"
    manifest = {
        "schema_version": "1.0",
        "snapshot_id": snapshot_id,
        "store_id": sid,
        "source_path": str(source),
        "source_size": src_stat.st_size,
        "source_mtime": src_stat.st_mtime,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(created)),
        "created_epoch": created,
        "reason": reason.upper(),
        "pinned": reason.upper() in PINNED_REASONS,
        "snapshot_path": str(final),
        "sha256": digest,
        "size": final.stat().st_size,
        "sqlite": verify,
        "previous_snapshot_id": latest.get("snapshot_id") if latest else None,
        "previous_sha256": latest.get("sha256") if latest else None,
        "provenance": "clay-vps-unifieddb-backup",
    }
    mp = _manifest_dir(sid) / f"{stamp}-{digest[:16]}.json"
    mp.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    commit_event({"time": manifest["created_at"], "epoch": created, "action": "unifieddb_snapshot", "payload": {"path": str(source), "reason": reason}, "result": {**manifest, "manifest_path": str(mp)}})
    prune()
    return {**manifest, "manifest_path": str(mp), "status": "CREATED"}


def _backup_usage() -> int:
    root = backup_root() / "snapshots"
    if not root.exists():
        return 0
    return sum(p.stat().st_size for p in root.rglob("*.sqlite3") if p.is_file())


def _retention_keep(manifests: list[dict[str, Any]]) -> set[str]:
    physical = [m for m in manifests if Path(str(m.get("snapshot_path", ""))).exists()]
    keep: set[str] = {str(m.get("snapshot_path")) for m in physical if m.get("pinned")}
    now = time.time()
    by_store: dict[str, list[dict[str, Any]]] = {}
    for m in physical:
        by_store.setdefault(str(m.get("store_id")), []).append(m)
    for rows in by_store.values():
        rows.sort(key=lambda m: float(m.get("created_epoch", 0)), reverse=True)
        keep.update(str(m.get("snapshot_path")) for m in rows[:16])
        buckets: set[tuple[str, str]] = set()
        for m in rows[16:]:
            ts = float(m.get("created_epoch", 0))
            age = max(0, now - ts)
            t = time.gmtime(ts)
            if age <= 48 * 3600:
                key = ("hour", time.strftime("%Y%m%d%H", t))
            elif age <= 30 * 86400:
                key = ("day", time.strftime("%Y%m%d", t))
            elif age <= 12 * 7 * 86400:
                key = ("week", time.strftime("%Y%W", t))
            else:
                continue
            if key not in buckets:
                buckets.add(key)
                keep.add(str(m.get("snapshot_path")))
    return keep


def prune() -> dict[str, Any]:
    manifests = load_manifests()
    keep = _retention_keep(manifests)
    usage_before = _backup_usage()
    candidates = [m for m in manifests if not m.get("pinned") and Path(str(m.get("snapshot_path", ""))).exists() and str(m.get("snapshot_path")) not in keep]
    candidates.sort(key=lambda m: float(m.get("created_epoch", 0)))
    pruned = []
    # First prune redundant snapshots outside tiered retention, then enforce budget while preserving latest 4/store + pinned.
    for m in candidates:
        p = Path(str(m["snapshot_path"]))
        if p.exists():
            p.unlink()
            pruned.append(m["snapshot_id"])
    if _backup_usage() > backup_budget():
        physical = [m for m in manifests if not m.get("pinned") and Path(str(m.get("snapshot_path", ""))).exists()]
        latest4: set[str] = set()
        stores = {str(m.get("store_id")) for m in physical}
        for sid in stores:
            rows = sorted([m for m in physical if str(m.get("store_id")) == sid], key=lambda m: float(m.get("created_epoch", 0)), reverse=True)
            latest4.update(str(m.get("snapshot_path")) for m in rows[:4])
        for m in sorted(physical, key=lambda m: float(m.get("created_epoch", 0))):
            if _backup_usage() <= backup_budget():
                break
            p = Path(str(m["snapshot_path"]))
            if str(p) in latest4 or not p.exists():
                continue
            p.unlink()
            pruned.append(m["snapshot_id"])
    usage_after = _backup_usage()
    receipt = {"usage_before": usage_before, "usage_after": usage_after, "budget": backup_budget(), "pruned_snapshot_ids": sorted(set(pruned))}
    if pruned:
        created = time.time()
        commit_event({"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(created)), "epoch": created, "action": "unifieddb_backup_retention", "payload": {}, "result": receipt})
    if usage_after > backup_budget():
        receipt["storage_pressure"] = True
    return receipt


def backup_all(reason: str = "PERIODIC", full_check: bool = False) -> dict[str, Any]:
    sources = discover_sources()
    results = []
    for src in sources:
        try:
            results.append(snapshot(src, reason=reason, full_check=full_check))
        except Exception as exc:
            results.append({"status": "ERROR", "source": str(src), "error": repr(exc)})
    return {"reason": reason, "sources": [str(p) for p in sources], "results": results, "retention": prune()}


def recovery_candidate(snapshot_path: Path, output_path: Path) -> dict[str, Any]:
    snapshot_path = snapshot_path.resolve(strict=True)
    root = backup_root().resolve(strict=True)
    try:
        snapshot_path.relative_to(root)
    except ValueError as exc:
        raise PermissionError("snapshot must come from configured backup root") from exc
    if output_path.exists():
        raise FileExistsError(str(output_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _online_backup(snapshot_path, output_path)
    verify = verify_snapshot(output_path, full=True)
    if not verify.get("ok"):
        raise RuntimeError(f"recovery candidate failed integrity check: {verify}")
    result = {"snapshot_path": str(snapshot_path), "output_path": str(output_path), "sha256": _sha256(output_path), "size": output_path.stat().st_size, "verify": verify}
    created = time.time()
    commit_event({"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(created)), "epoch": created, "action": "unifieddb_recovery_candidate", "payload": {"path": str(snapshot_path)}, "result": result})
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reason", default="PERIODIC")
    parser.add_argument("--full-check", action="store_true")
    parser.add_argument("--prune-only", action="store_true")
    args = parser.parse_args()
    result = prune() if args.prune_only else backup_all(args.reason, args.full_check)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
