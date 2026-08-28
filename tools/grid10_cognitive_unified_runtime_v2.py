#!/usr/bin/env python3
"""Production-oriented GRID10 cognitive runtime entry with one physical SQLite authority.

This entry point closes the split-database gap in the v1 demo path. Fabric state,
cognitive-heartbeat checkpoint/telemetry, and persistent AgencyState/GoalContract control
state are opened against the same physical SQLite file. The check is deterministic and
fail-closed: resolved path plus device/inode identity must agree before cognition starts.

This module does not grant canonical truth or external effect authority. GRID/model
outputs remain candidate cognition; EffectGate/EffectJournal remain the external-effect
authority defined by the surrounding EntityOS/Frankenstein architecture.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from typing import Any

from grid10_fabric import Fabric
from grid10_cognitive_heartbeat_v1 import (
    CognitiveHeartbeatRuntime,
    CognitiveHeartbeatStore,
    HeartbeatConfig,
    _trusted_normal_axes,
    append_frame_jsonl,
)
from grid10_persistent_agency_v1 import PersistentAgencyStore


@dataclass(frozen=True)
class UnifiedDbFingerprint:
    realpath: str
    device: int
    inode: int
    main_db_path: str
    schema_digest: str


def _schema_digest(path: Path) -> tuple[str, str]:
    con = sqlite3.connect(str(path), timeout=5.0)
    try:
        db_rows = con.execute("PRAGMA database_list").fetchall()
        main_rows = [r for r in db_rows if str(r[1]) == "main"]
        if len(main_rows) != 1:
            raise RuntimeError("UNIFIEDDB_MAIN_DATABASE_UNRESOLVED")
        main_db_path = str(Path(str(main_rows[0][2])).resolve())
        schema_rows = con.execute(
            "SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name,tbl_name"
        ).fetchall()
    finally:
        con.close()
    encoded = json.dumps(schema_rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return main_db_path, hashlib.sha256(encoded).hexdigest()


def fingerprint_sqlite(path: Path) -> UnifiedDbFingerprint:
    resolved = Path(path).expanduser().resolve(strict=True)
    st = resolved.stat()
    main_db_path, schema_digest = _schema_digest(resolved)
    if Path(main_db_path).resolve() != resolved:
        raise RuntimeError(
            f"UNIFIEDDB_SQLITE_MAIN_PATH_MISMATCH:{main_db_path}!={resolved}"
        )
    return UnifiedDbFingerprint(
        realpath=str(resolved),
        device=int(st.st_dev),
        inode=int(st.st_ino),
        main_db_path=main_db_path,
        schema_digest=schema_digest,
    )


def assert_shared_unifieddb_authority(
    fabric: Fabric,
    store: CognitiveHeartbeatStore,
    agency: PersistentAgencyStore | None = None,
) -> UnifiedDbFingerprint:
    fingerprints = {
        "fabric": fingerprint_sqlite(Path(fabric.path)),
        "heartbeat": fingerprint_sqlite(Path(store.path)),
    }
    if agency is not None:
        fingerprints["agency"] = fingerprint_sqlite(Path(agency.path))

    physical_keys = {
        (fp.realpath, fp.device, fp.inode, fp.main_db_path)
        for fp in fingerprints.values()
    }
    if len(physical_keys) != 1:
        raise RuntimeError(
            "UNIFIEDDB_AUTHORITY_SPLIT:"
            + json.dumps(
                {name: asdict(fp) for name, fp in fingerprints.items()},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    schema_digests = {fp.schema_digest for fp in fingerprints.values()}
    if len(schema_digests) != 1:
        raise RuntimeError("UNIFIEDDB_SCHEMA_VIEW_MISMATCH")
    return fingerprints["fabric"]


def build_shared_runtime(
    unified_db: Path,
    *,
    allow_regulator_writes: bool = False,
) -> tuple[
    Fabric,
    CognitiveHeartbeatStore,
    PersistentAgencyStore,
    CognitiveHeartbeatRuntime,
    UnifiedDbFingerprint,
]:
    db = Path(unified_db).expanduser()
    db.parent.mkdir(parents=True, exist_ok=True)
    fabric = Fabric(db)
    store = CognitiveHeartbeatStore(db)
    agency = PersistentAgencyStore(db)
    fingerprint = assert_shared_unifieddb_authority(fabric, store, agency)
    runtime = CognitiveHeartbeatRuntime(
        fabric,
        store,
        config=HeartbeatConfig(allow_regulator_writes=bool(allow_regulator_writes)),
    )
    return fabric, store, agency, runtime, fingerprint


def run_bounded(
    *,
    unified_db: Path,
    frames_jsonl: Path,
    ticks: int,
    interval: float,
    allow_regulator_writes: bool = False,
    trusted_normal_test_fixture: bool = False,
) -> list[dict[str, Any]]:
    _, _, _, runtime, fingerprint = build_shared_runtime(
        unified_db,
        allow_regulator_writes=allow_regulator_writes,
    )
    print(json.dumps({
        "schema": "GRID10_UNIFIED_RUNTIME_AUTHORITY/v2",
        "status": "PASS",
        "scope": "ONE_PHYSICAL_SQLITE_AUTHORITY_FOR_FABRIC_HEARTBEAT_AND_AGENCY",
        "fingerprint": asdict(fingerprint),
        "external_effect_authority_changed": False,
    }, sort_keys=True))

    trusted = _trusted_normal_axes() if trusted_normal_test_fixture else None
    rows: list[dict[str, Any]] = []
    for i in range(max(0, int(ticks))):
        tick_id = f"unified-heartbeat-{time.time_ns()}-{i}"
        result = runtime.tick_once(tick_id=tick_id, trusted_axes=trusted)
        append_frame_jsonl(Path(frames_jsonl), result.frame_json)
        row = {
            "tick_id": result.tick_id,
            "state_epoch": result.state_epoch,
            "assurance_mode": result.assurance_mode.value,
            "next_action": result.next_action,
            "reasons": result.reasons,
            "regulator_proposals": result.regulator_proposals,
            "regulator_cycle": result.regulator_cycle,
        }
        rows.append(row)
        print(json.dumps(row, sort_keys=True))
        if i + 1 < ticks:
            time.sleep(max(0.05, float(interval)))
    return rows


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--unified-db", required=True)
    p.add_argument("--frames-jsonl", required=True)
    p.add_argument("--ticks", type=int, default=1)
    p.add_argument("--interval", type=float, default=1.0)
    p.add_argument("--allow-regulator-writes", action="store_true")
    p.add_argument(
        "--trusted-normal-test-fixture",
        action="store_true",
        help="TEST/DEMO ONLY: supplies synthetic verified-normal semantic axes",
    )
    args = p.parse_args()
    run_bounded(
        unified_db=Path(args.unified_db),
        frames_jsonl=Path(args.frames_jsonl),
        ticks=args.ticks,
        interval=args.interval,
        allow_regulator_writes=bool(args.allow_regulator_writes),
        trusted_normal_test_fixture=bool(args.trusted_normal_test_fixture),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
