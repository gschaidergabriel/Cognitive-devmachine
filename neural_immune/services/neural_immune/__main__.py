"""
Neural Immune System — Entry Point (EntityOS / frank-api deployment)
=======================================================================
Run as: python3 -m services.neural_immune

Integrates with systemd via sd_notify:
  - READY=1      after initialization
  - WATCHDOG=1   every WatchdogSec/2 (30s)

This deployed copy is self-contained: it does NOT import Frank's
`config.paths` / `config.logging_config` modules (they only exist in
Gabriel's ~/repo, not on this VPS). All paths are anchored to the
project root this file lives under (services/neural_immune/__main__.py
-> parents[2] = the neural_immune deploy root), so everything the
immune system writes (db, model weights, logs) stays inside
/opt/entityos/neural_immune/ as required — never wiki.db, never
/opt/unifieddb, never /etc/entityos/tresor.

Hardware-agnostic: runs on any Linux with systemd + Python 3.10+.
"""

import logging
import logging.handlers
import os
import sys
import threading
import time
from pathlib import Path

# Project root = two levels above this file (services/neural_immune/__main__.py)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

LOG_DIR = Path(os.environ.get("IMMUNE_LOG_DIR", str(_PROJECT_ROOT / "logs")))
DB_PATH = Path(os.environ.get("IMMUNE_DB_PATH", str(_PROJECT_ROOT / "immune.db")))
MODEL_PATH = Path(os.environ.get("IMMUNE_MODEL_PATH", str(_PROJECT_ROOT / "immune_model.pt")))

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s %(levelname)s: %(message)s",
    handlers=[
        logging.handlers.RotatingFileHandler(
            LOG_DIR / "immune_system.log",
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
        ),
        logging.StreamHandler(),
    ],
)
LOG = logging.getLogger("immune")


def _sd_notify(msg: str):
    """Send sd_notify message (portable: works with or without systemd)."""
    sock_path = os.environ.get("NOTIFY_SOCKET")
    if not sock_path:
        return
    try:
        import socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
            if sock_path.startswith("@"):
                sock_path = "\0" + sock_path[1:]
            sock.connect(sock_path)
            sock.sendall(msg.encode())
        finally:
            sock.close()
    except Exception:
        pass


def _watchdog_thread(interval: float = 30.0):
    """Background thread sending WATCHDOG=1 every interval seconds."""
    while True:
        _sd_notify("WATCHDOG=1")
        time.sleep(interval)


def main():
    LOG.info("Neural Immune System starting (EntityOS deployment)...")
    LOG.info("db=%s model=%s log=%s", DB_PATH, MODEL_PATH, LOG_DIR)

    from services.neural_immune.supervisor import ImmuneSystem
    immune = ImmuneSystem(db_path=DB_PATH, model_path=MODEL_PATH)

    # Start watchdog pinger (daemon thread — dies with main)
    wd_thread = threading.Thread(target=_watchdog_thread, args=(30.0,), daemon=True)
    wd_thread.start()

    # Signal ready to systemd
    _sd_notify("READY=1")
    LOG.info("sd_notify READY=1 sent")

    # Run main loop (blocking)
    immune.run()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        LOG.critical("Fatal error in immune system", exc_info=True)
        sys.exit(1)
