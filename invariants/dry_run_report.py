#!/usr/bin/env python3
"""
dry_run_report.py — Observation-only orchestrator for the invariants engine
against EntityOS' wiki.db.

WHAT THIS DOES
    Each cycle it:
      1. Opens wiki.db READ-ONLY through adapter.WikiDBTitanAdapter.
      2. Runs the engine's pure MEASUREMENT methods:
           - EnergyConservation.check_conservation()   (SELECT only)
           - EntropyBound.measure_entropy()             (SELECT only)
           - CoreKernel.build_core()                    (SELECT wiki.db,
                                                           INSERT into invariants'
                                                           OWN core_kernel table)
      3. Writes one row into `iv_dry_run_reports` in invariants.db (its own,
         separate database) summarizing the cycle.
      4. Logs a human-readable line.

WHAT THIS NEVER DOES (by construction, not just by policy)
    - EnergyConservation.enforce_conservation()   [would UPDATE wiki.db]
    - EntropyBound.soft_consolidation()           [would UPDATE wiki.db]
    - EntropyBound.hard_consolidation()           [would UPDATE + quarantine]
    - QuarantineDimension.quarantine_item/_region [would DELETE wiki.db rows]
    - QuarantineDimension.restore_item            [would INSERT into wiki.db]
    - TripleReality (not imported at all)          [would sqlite3.backup() a
                                                      full copy of "primary";
                                                      not meaningfully
                                                      adaptable to a read-only
                                                      source without inventing
                                                      write semantics wiki.db
                                                      doesn't have -- left
                                                      disabled, see README]
    None of these functions are even called in this file. This is not a
    runtime flag; the call sites simply do not exist here.

    Even if one of them WERE called by a bug: the adapter's connection to
    wiki.db is opened with `mode=ro`, and `nodes`/`edges` are SQL VIEWs, not
    tables. Both would independently cause SQLite to reject the write with
    an exception, which the engine's own try/except swallows. Nothing gets
    corrupted; the cycle just logs an error and continues.

MODE SWITCH
    /opt/entityos/invariants/config/config.json has a "mode" key.
    This script only implements "dry_run" and REFUSES TO START (exits
    non-zero) for any other value. There is no enforcing code path built
    yet -- flipping the config value alone cannot turn this into a
    write-capable service. That is intentional per the operator's
    instruction: the owner decides when/if an enforcing mode gets built,
    after the dry run has proven detection is correct.
"""

import json
import logging
import os
import signal
import socket
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# INVARIANTS_BASE_DIR env override exists only to make this script testable
# off-box (local synthetic-data verification runs). The deployed systemd
# unit on frank-api does not set it, so it always resolves to the real path.
BASE_DIR = Path(os.environ.get("INVARIANTS_BASE_DIR", "/opt/entityos/invariants"))
DATA_DIR = BASE_DIR / "data"
CONFIG_PATH = BASE_DIR / "config" / "config.json"
LOG_PATH = DATA_DIR / "invariants-dry-run.log"

sys.path.insert(0, str(BASE_DIR))

DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)
LOG = logging.getLogger("invariants.dry_run")


def sd_notify(message: str) -> bool:
    notify_socket = os.environ.get("NOTIFY_SOCKET")
    if not notify_socket:
        return False
    try:
        if notify_socket.startswith("@"):
            notify_socket = "\0" + notify_socket[1:]
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
            sock.connect(notify_socket)
            sock.sendall(message.encode("utf-8"))
            return True
        finally:
            sock.close()
    except Exception:
        return False


def load_run_config() -> dict:
    default = {
        "mode": "dry_run",
        "wiki_db_path": "/var/lib/clay/wiki.db",
        "check_interval_seconds": 300,
    }
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text())
            default.update(data)
        except Exception as e:
            LOG.error("Could not parse %s: %s -- using defaults", CONFIG_PATH, e)
    return default


# --- Engine imports, with own-directory paths patched BEFORE any
#     InvariantsConfig()/InvariantsStore() gets constructed anywhere. ---
import engine.config as engine_cfg  # noqa: E402

engine_cfg.INVARIANTS_DIR = DATA_DIR
engine_cfg.QUARANTINE_DIR = DATA_DIR / "quarantine"
engine_cfg.STATE_FILE = DATA_DIR / "invariants_state.json"
engine_cfg.INVARIANTS_DB = DATA_DIR / "invariants.db"
# Bookkeeping only -- adapter.py opens wiki.db itself via mode=ro; nothing in
# this script ever calls sqlite3.connect() on TITAN_* paths directly.
engine_cfg.TITAN_PRIMARY_DB = Path("/var/lib/clay/wiki.db")
engine_cfg.TITAN_SHADOW_DB = DATA_DIR / "unused_shadow.db"
engine_cfg.TITAN_VALIDATOR_DB = DATA_DIR / "unused_validator.db"

from engine.config import InvariantsConfig  # noqa: E402
from engine.db_schema import InvariantsStore  # noqa: E402
from engine.energy import EnergyConservation  # noqa: E402
from engine.entropy import EntropyBound, ConsolidationMode  # noqa: E402
from engine.core_kernel import CoreKernel  # noqa: E402

from adapter import get_titan  # noqa: E402


REPORTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS iv_dry_run_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    source_db TEXT NOT NULL,
    article_count INTEGER,
    edge_count INTEGER,
    contradiction_edge_count INTEGER,
    energy_current REAL,
    energy_expected REAL,
    energy_conserved INTEGER,
    entropy_value REAL,
    entropy_max REAL,
    entropy_ratio REAL,
    entropy_mode TEXT,
    core_size INTEGER,
    would_quarantine_json TEXT,
    error TEXT
);
"""


def ensure_reports_table(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(REPORTS_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def write_report(db_path: Path, row: dict):
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            INSERT INTO iv_dry_run_reports
            (timestamp, source_db, article_count, edge_count, contradiction_edge_count,
             energy_current, energy_expected, energy_conserved,
             entropy_value, entropy_max, entropy_ratio, entropy_mode,
             core_size, would_quarantine_json, error)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                row["timestamp"], row["source_db"], row["article_count"],
                row["edge_count"], row["contradiction_edge_count"],
                row["energy_current"], row["energy_expected"], row["energy_conserved"],
                row["entropy_value"], row["entropy_max"], row["entropy_ratio"],
                row["entropy_mode"], row["core_size"],
                json.dumps(row["would_quarantine"]), row.get("error"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def prune_own_db(db_path: Path, keep: int = 2000):
    """Keep invariants.db's own append-only tables bounded. Runs against
    invariants.db ONLY -- never touches wiki.db."""
    try:
        conn = sqlite3.connect(str(db_path))
        for table in ("energy_ledger", "entropy_history", "iv_dry_run_reports"):
            conn.execute(
                f"DELETE FROM {table} WHERE id NOT IN "
                f"(SELECT id FROM {table} ORDER BY id DESC LIMIT ?)", (keep,)
            )
        conn.commit()
        conn.close()
        LOG.info("pruned invariants.db own tables to last %s rows each", keep)
    except Exception as e:
        LOG.warning("prune_own_db failed: %s", e)


def run_cycle(config: InvariantsConfig, store: InvariantsStore,
              energy: EnergyConservation, entropy: EntropyBound,
              core: CoreKernel, wiki_db_path: str) -> dict:
    ts = datetime.now(timezone.utc).isoformat()
    titan = get_titan(wiki_db_path)
    result = {
        "timestamp": ts, "source_db": wiki_db_path,
        "article_count": None, "edge_count": None, "contradiction_edge_count": None,
        "energy_current": None, "energy_expected": None, "energy_conserved": None,
        "entropy_value": None, "entropy_max": None, "entropy_ratio": None,
        "entropy_mode": None, "core_size": None, "would_quarantine": [], "error": None,
    }
    try:
        desc = titan.describe()
        result["article_count"] = desc["articles_as_nodes"]
        result["edge_count"] = desc["edges"]
        result["contradiction_edge_count"] = desc["contradiction_edges"]

        # --- INVARIANT 1: Energy Conservation (read-only check) ---
        is_conserved, current, expected = energy.check_conservation(titan)
        result["energy_current"] = current
        result["energy_expected"] = expected
        result["energy_conserved"] = is_conserved

        # --- INVARIANT 2: Entropy Bound (read-only measurement) ---
        measurement = entropy.measure_entropy(titan)
        result["entropy_value"] = measurement.entropy
        result["entropy_max"] = measurement.entropy_max
        result["entropy_ratio"] = measurement.ratio
        result["entropy_mode"] = measurement.mode.value

        # Report (not act on) what SOFT/HARD consolidation would target --
        # mirrors entropy._find_contradictions()'s own logic, read-only.
        if measurement.mode != ConsolidationMode.NONE:
            with titan.sqlite._get_conn() as conn:
                rows = conn.execute(
                    "SELECT src, dst, relation FROM edges "
                    "WHERE relation IN ('contradicts','conflicts_with','negates') LIMIT 50"
                ).fetchall()
                result["would_quarantine"] = [
                    {"src": r["src"], "dst": r["dst"], "relation": r["relation"]}
                    for r in rows
                ]

        # --- INVARIANT 4: Core Kernel (reads wiki.db, writes ONLY to
        #     invariants.db's own core_kernel table -- never touches wiki.db) ---
        members = core.build_core(titan)
        result["core_size"] = len(members)

        LOG.info(
            "cycle ok: articles=%s edges=%s contradictions=%s "
            "energy_conserved=%s (%.2f/%.2f) entropy=%.1f%% mode=%s core=%s",
            result["article_count"], result["edge_count"],
            result["contradiction_edge_count"], is_conserved, current, expected,
            measurement.ratio * 100, measurement.mode.value, result["core_size"],
        )

    except Exception as e:
        LOG.error("cycle failed: %s", e, exc_info=True)
        result["error"] = str(e)

    return result


def main():
    run_cfg = load_run_config()

    if run_cfg.get("mode") != "dry_run":
        LOG.error(
            "config mode=%r is not supported by this build -- refusing to "
            "start. Only 'dry_run' is implemented; there is no enforcing "
            "code path in this script at all.", run_cfg.get("mode"),
        )
        sys.exit(1)

    wiki_db_path = run_cfg["wiki_db_path"]
    interval = float(run_cfg.get("check_interval_seconds", 300))

    ensure_reports_table(engine_cfg.INVARIANTS_DB)

    config = InvariantsConfig()
    store = InvariantsStore(db_path=engine_cfg.INVARIANTS_DB)
    energy = EnergyConservation(config=config, store=store)
    entropy = EntropyBound(config=config, store=store)
    core = CoreKernel(config=config, store=store)

    LOG.info("=" * 60)
    LOG.info("invariants DRY-RUN daemon starting (mode=dry_run, read-only)")
    LOG.info("wiki_db=%s interval=%ss", wiki_db_path, interval)
    LOG.info("invariants own db: %s", engine_cfg.INVARIANTS_DB)
    LOG.info("=" * 60)

    running = {"flag": True}

    def _stop(signum, frame):
        LOG.info("received signal %s, stopping", signum)
        running["flag"] = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    sd_notify("READY=1")
    last_watchdog = time.monotonic()

    once = "--once" in sys.argv
    cycle_count = 0
    while running["flag"]:
        row = run_cycle(config, store, energy, entropy, core, wiki_db_path)
        try:
            write_report(engine_cfg.INVARIANTS_DB, row)
        except Exception as e:
            LOG.error("failed to write report row: %s", e)

        sd_notify(f"STATUS=last cycle {row['timestamp']} mode={row['entropy_mode']}")

        cycle_count += 1
        if cycle_count % 50 == 0:
            prune_own_db(engine_cfg.INVARIANTS_DB)

        if once:
            break

        slept = 0.0
        while slept < interval and running["flag"]:
            time.sleep(min(5.0, interval - slept))
            slept += 5.0
            now = time.monotonic()
            if now - last_watchdog >= 25:
                sd_notify("WATCHDOG=1")
                last_watchdog = now

    sd_notify("STOPPING=1")
    LOG.info("invariants DRY-RUN daemon stopped")


if __name__ == "__main__":
    main()
