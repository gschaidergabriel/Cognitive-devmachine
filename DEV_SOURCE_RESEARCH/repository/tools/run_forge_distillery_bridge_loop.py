#!/usr/bin/env python3
"""Continuously reconcile evidence-qualified Forge accepts into Distillery.

No provider/network I/O is performed here. The loop delegates every row-level
admission decision to ingest_forge_accepts_into_distillery, which in turn delegates
to Supervisor-8.71 forge_evidence_credit_871. Historical nominal accepts therefore
remain rejected unless exact source identity and isolated execution admission are
present. Reconciliation is idempotent by evaluation digest.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import signal
import time
from typing import Any

import ingest_forge_accepts_into_distillery as bridge

DEFAULT_STATUS = bridge.ARTIFACT_ROOT / "distillery/forge_execution_ingest_status.json"


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def atomic_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def source_fingerprint(path: Path) -> tuple[bool, int, int]:
    try:
        st = path.stat()
    except OSError:
        return False, 0, 0
    return True, int(st.st_mtime_ns), int(st.st_size)


def run_once(
    forge_evaluations: Path = bridge.DEFAULT_FORGE_EVAL,
    distillery_db: Path = bridge.DEFAULT_DISTILLERY_DB,
    status_path: Path = DEFAULT_STATUS,
) -> dict[str, Any]:
    result = bridge.ingest(forge_evaluations, distillery_db)
    exists, mtime_ns, size = source_fingerprint(forge_evaluations)
    out = {
        **result,
        "bridge_loop_schema": "CLAY_FORGE_DISTILLERY_LIVE_BRIDGE/v2",
        "observed_at": now_iso(),
        "source_fingerprint": {"exists": exists, "mtime_ns": mtime_ns, "size": size},
        "acceptance_semantics": "EVIDENCE_QUALIFIED_ONLY",
        "network_io": False,
        "canonical_truth": False,
        "jspace_causal_credit": 0,
        "training_credit": 0,
    }
    atomic_json(status_path, out)
    return out


def run_loop(
    forge_evaluations: Path,
    distillery_db: Path,
    status_path: Path,
    sleep_seconds: float,
    reconcile_seconds: float,
) -> int:
    stop = False

    def request_stop(_signum: int, _frame: object) -> None:
        nonlocal stop
        stop = True

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, request_stop)
        except (ValueError, OSError):
            pass

    last_source: tuple[bool, int, int] | None = None
    last_reconcile = 0.0
    while not stop:
        current_source = source_fingerprint(forge_evaluations)
        now = time.monotonic()
        due = current_source != last_source or last_source is None or now - last_reconcile >= reconcile_seconds
        if due:
            try:
                run_once(forge_evaluations, distillery_db, status_path)
                last_source = current_source
                last_reconcile = now
            except Exception as exc:
                atomic_json(
                    status_path,
                    {
                        "bridge_loop_schema": "CLAY_FORGE_DISTILLERY_LIVE_BRIDGE/v2",
                        "observed_at": now_iso(),
                        "state": "ERROR_RETRYING",
                        "error": f"{type(exc).__name__}:{str(exc)[:500]}",
                        "acceptance_semantics": "EVIDENCE_QUALIFIED_ONLY",
                        "network_io": False,
                        "canonical_truth": False,
                        "jspace_causal_credit": 0,
                        "training_credit": 0,
                    },
                )
        time.sleep(max(0.2, sleep_seconds))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-evaluations", type=Path, default=bridge.DEFAULT_FORGE_EVAL)
    ap.add_argument("--distillery-db", type=Path, default=bridge.DEFAULT_DISTILLERY_DB)
    ap.add_argument("--status-path", type=Path, default=DEFAULT_STATUS)
    ap.add_argument("--sleep-seconds", type=float, default=2.0)
    ap.add_argument("--reconcile-seconds", type=float, default=15.0)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    if args.once:
        print(json.dumps(run_once(args.forge_evaluations, args.distillery_db, args.status_path), indent=2, ensure_ascii=False))
        return 0
    return run_loop(
        args.forge_evaluations,
        args.distillery_db,
        args.status_path,
        max(0.2, args.sleep_seconds),
        max(1.0, args.reconcile_seconds),
    )


if __name__ == "__main__":
    raise SystemExit(main())
