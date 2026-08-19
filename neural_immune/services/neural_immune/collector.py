"""
Neural Immune System — Health Metric Collector
================================================
Collects per-service health metrics every tick (15s):
  - systemctl is-active          (active/inactive/failed; scope per-entry: system|user)
  - TCP port check                (0.1s timeout)
  - HTTP /health endpoint         (response time)
  - Process metrics via /proc     (CPU%, RSS — with fallback)

Maintains 8-step sliding window per service.
Hardware-agnostic: works on any Linux with systemd.

EntityOS deployment note (frank-api):
  The service registry is loaded from an external JSON config
  (config/services.json under the project root, or $IMMUNE_SERVICES_CONFIG)
  instead of being hardcoded here. This lets the monitored-service list
  and restart-vs-observe policy be edited without touching code. Every
  registry entry additionally carries "policy" (restart|observe) and
  "scope" (system|user, i.e. whether to call `systemctl` or
  `systemctl --user`). If no config file is found, this falls back to
  the original Frank service registry (FRANK_SERVICE_REGISTRY below),
  which uses `systemctl --user` as before.
"""

import collections
import json
import logging
import math
import os
import socket
import subprocess
import time

# Clean environment for subprocess calls — strip NOTIFY_SOCKET to prevent
# child processes from leaking sd_notify messages to systemd
_CLEAN_ENV = {k: v for k, v in os.environ.items() if k != "NOTIFY_SOCKET"}
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

LOG = logging.getLogger("immune.collector")

# ── Service Registry (original Frank fallback) ─────────────────────
# Ported from frank_watchdog.py MONITORED_SERVICES + llm_guard.py
# Each entry: (service_name, port_or_None, health_endpoint_or_None,
#              critical, default_delay, default_cooldown, default_max_restarts, tier)
# Used only if no external services.json config is found (see _load_service_registry).

FRANK_SERVICE_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Tier 0 — Infrastructure (standalone, no Frank deps)
    "aicore-llama3-gpu":        {"port": 8101, "health": "/health", "critical": True,
                                 "delay": 2, "cooldown": 15, "max_restarts": 20,
                                 "reset_after": 300, "tier": 0},
    "aicore-whisper-gpu":       {"port": 8103, "health": "/health", "critical": True,
                                 "delay": 2, "cooldown": 60, "max_restarts": 10,
                                 "reset_after": 600, "tier": 0},
    "aicore-modeld":            {"port": 8090, "health": "/health", "critical": True,
                                 "delay": 1, "cooldown": 15, "max_restarts": 20,
                                 "reset_after": 300, "tier": 0},
    "aicore-toolboxd":          {"port": 8096, "health": None, "critical": True,
                                 "delay": 1, "cooldown": 15, "max_restarts": 20,
                                 "reset_after": 300, "tier": 0},
    "aicore-webd":              {"port": 8093, "health": None, "critical": True,
                                 "delay": 1, "cooldown": 10, "max_restarts": 30,
                                 "reset_after": 300, "tier": 0},
    "aicore-desktopd":          {"port": 8092, "health": None, "critical": True,
                                 "delay": 2, "cooldown": 30, "max_restarts": 15,
                                 "reset_after": 600, "tier": 0},
    "aicore-ingestd":           {"port": 8094, "health": None, "critical": True,
                                 "delay": 1, "cooldown": 15, "max_restarts": 20,
                                 "reset_after": 300, "tier": 0},
    "aicore-webui":             {"port": 8099, "health": None, "critical": True,
                                 "delay": 1, "cooldown": 15, "max_restarts": 20,
                                 "reset_after": 300, "tier": 0},
    "aicore-quantum-reflector": {"port": 8097, "health": "/health", "critical": True,
                                 "delay": 2, "cooldown": 30, "max_restarts": 10,
                                 "reset_after": 600, "tier": 0},
    "aura-headless":            {"port": 8098, "health": "/health", "critical": True,
                                 "delay": 2, "cooldown": 30, "max_restarts": 10,
                                 "reset_after": 600, "tier": 0},
    "frank-sentinel":           {"port": None, "health": None, "critical": False,
                                 "delay": 2, "cooldown": 30, "max_restarts": 10,
                                 "reset_after": 600, "tier": 0},
    "aicore-micro-llm":         {"port": 8105, "health": "/health", "critical": True,
                                 "delay": 2, "cooldown": 15, "max_restarts": 20,
                                 "reset_after": 300, "tier": 0},

    # Tier 1 — Router
    "aicore-router":            {"port": 8091, "health": "/health", "critical": True,
                                 "delay": 1, "cooldown": 15, "max_restarts": 20,
                                 "reset_after": 300, "tier": 1},

    # Tier 2 — Core
    "aicore-core":              {"port": 8088, "health": "/health", "critical": True,
                                 "delay": 1, "cooldown": 15, "max_restarts": 20,
                                 "reset_after": 300, "tier": 2},

    # Tier 3 — Daemons (depend on core+router)
    "aicore-consciousness":     {"port": None, "health": None, "critical": True,
                                 "delay": 2, "cooldown": 30, "max_restarts": 10,
                                 "reset_after": 600, "tier": 3},
    "aicore-rooms":             {"port": None, "health": None, "critical": True,
                                 "delay": 2, "cooldown": 30, "max_restarts": 15,
                                 "reset_after": 600, "tier": 3},
    "aicore-asrs":              {"port": None, "health": None, "critical": True,
                                 "delay": 2, "cooldown": 30, "max_restarts": 15,
                                 "reset_after": 600, "tier": 3},
    "aicore-gaming-mode":       {"port": None, "health": None, "critical": False,
                                 "delay": 2, "cooldown": 60, "max_restarts": 5,
                                 "reset_after": 600, "tier": 3},
    "aicore-genesis":           {"port": None, "health": None, "critical": True,
                                 "delay": 3, "cooldown": 60, "max_restarts": 10,
                                 "reset_after": 600, "tier": 3},
    "aicore-genesis-watchdog":  {"port": None, "health": None, "critical": False,
                                 "delay": 2, "cooldown": 60, "max_restarts": 5,
                                 "reset_after": 600, "tier": 3},
    "aicore-invariants":        {"port": None, "health": None, "critical": True,
                                 "delay": 2, "cooldown": 30, "max_restarts": 15,
                                 "reset_after": 600, "tier": 3},
    "aicore-dream":             {"port": None, "health": None, "critical": False,
                                 "delay": 5, "cooldown": 120, "max_restarts": 5,
                                 "reset_after": 1800, "tier": 3},
    "aura-analyzer":            {"port": None, "health": None, "critical": True,
                                 "delay": 2, "cooldown": 30, "max_restarts": 10,
                                 "reset_after": 600, "tier": 3},
    "aicore-room-dispatcher":   {"port": None, "health": None, "critical": False,
                                 "delay": 2, "cooldown": 60, "max_restarts": 5,
                                 "reset_after": 600, "tier": 3},
    "aicore-nerd-physics":      {"port": 8100, "health": "/health", "critical": True,
                                 "delay": 2, "cooldown": 30, "max_restarts": 10,
                                 "reset_after": 600, "tier": 3},

    # Tier 4 — Overlay (last to start)
    "frank-overlay":            {"port": None, "health": None, "critical": True,
                                 "delay": 3, "cooldown": 30, "max_restarts": 15,
                                 "reset_after": 600, "tier": 4},
}
# Frank fallback registry uses --user scope + restart policy everywhere (original behavior).
for _name, _info in FRANK_SERVICE_REGISTRY.items():
    _info.setdefault("scope", "user")
    _info.setdefault("policy", "restart")
    _info.setdefault("kind", "service")
del _name, _info


# ── External config loader (EntityOS + anyone else) ────────────────

# Default location: <project_root>/config/services.json
# (project_root = two levels above this file: services/neural_immune/collector.py)
_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "services.json"


def _load_service_registry() -> Dict[str, Dict[str, Any]]:
    """Load SERVICE_REGISTRY from an external JSON config if present.

    Config format (config/services.json):
        {
          "services": {
            "<unit-name-without-.service>": {
                "policy": "restart"|"observe",   # restart = circuit-breaker-guarded auto-restart;
                                                  # observe = never restarted, only logged
                "critical": true|false,
                "delay": 3, "max_restarts": 20, "reset_after": 300, "tier": 0,
                "scope": "system"|"user"          # systemctl vs systemctl --user (default: system)
            }, ...
          },
          "timers": ["some.timer", ...],           # observed separately, see check_timers()
          "extras": { "docker_container": {...}, "warm_pool": {...} }  # observed separately
        }

    Falls back to FRANK_SERVICE_REGISTRY (original hardcoded Frank services,
    --user scope) if no config file is found or it fails to parse — so the
    module keeps working standalone on Gabriel's PC without a config file.
    """
    config_path = Path(os.environ.get("IMMUNE_SERVICES_CONFIG", str(_DEFAULT_CONFIG_PATH)))
    if not config_path.exists():
        LOG.info("No services.json at %s — using built-in Frank service registry", config_path)
        return dict(FRANK_SERVICE_REGISTRY)

    try:
        raw = json.loads(config_path.read_text())
        services = raw.get("services", {})
        registry: Dict[str, Dict[str, Any]] = {}
        for unit, info in services.items():
            entry = dict(info)
            entry.setdefault("port", None)
            entry.setdefault("health", None)
            entry.setdefault("critical", False)
            entry.setdefault("delay", 3)
            entry.setdefault("cooldown", 15)
            entry.setdefault("max_restarts", 20)
            entry.setdefault("reset_after", 300)
            entry.setdefault("tier", 0)
            entry.setdefault("scope", "system")
            entry.setdefault("policy", "observe")
            entry.setdefault("kind", "service")
            registry[unit] = entry
        LOG.info("Loaded %d services from %s", len(registry), config_path)
        return registry
    except Exception as e:
        LOG.error("Failed to load %s (%s) — falling back to Frank registry", config_path, e)
        return dict(FRANK_SERVICE_REGISTRY)


def load_timer_units() -> List[str]:
    """Load the list of .timer units to observe (never restarted) from config."""
    config_path = Path(os.environ.get("IMMUNE_SERVICES_CONFIG", str(_DEFAULT_CONFIG_PATH)))
    if not config_path.exists():
        return []
    try:
        raw = json.loads(config_path.read_text())
        return list(raw.get("timers", []))
    except Exception as e:
        LOG.error("Failed to load timer list from %s: %s", config_path, e)
        return []


def load_extras_config() -> Dict[str, Any]:
    """Load the 'extras' block (docker_container, warm_pool) from config."""
    config_path = Path(os.environ.get("IMMUNE_SERVICES_CONFIG", str(_DEFAULT_CONFIG_PATH)))
    if not config_path.exists():
        return {}
    try:
        raw = json.loads(config_path.read_text())
        return raw.get("extras", {})
    except Exception as e:
        LOG.error("Failed to load extras config from %s: %s", config_path, e)
        return {}


SERVICE_REGISTRY: Dict[str, Dict[str, Any]] = _load_service_registry()


# Feature vector size per timestep
FEATURES_PER_STEP = 12
WINDOW_SIZE = 8  # 8 timesteps = 2 min at 15s intervals

# Delta-based system CPU tracking (cumulative counters need delta)
_prev_sys_idle = 0
_prev_sys_total = 0


# ── Low-Level Health Checks ───────────────────────────────────────

def _systemctl_prefix(scope: str = "user") -> List[str]:
    """Build the systemctl command prefix for a given scope (system|user)."""
    return ["systemctl"] if scope == "system" else ["systemctl", "--user"]


def is_service_installed(service_name: str, scope: str = "user") -> bool:
    """Check if a systemd service unit file exists (not-found = not installed).

    scope="system" → plain `systemctl` (root-owned units, e.g. EntityOS on frank-api)
    scope="user"   → `systemctl --user` (Frank's original per-user units)
    """
    try:
        result = subprocess.run(
            _systemctl_prefix(scope) + ["show", service_name, "-p", "LoadState"],
            capture_output=True, text=True, timeout=10, env=_CLEAN_ENV,
        )
        return "not-found" not in result.stdout
    except Exception:
        return True  # Assume installed on error


def get_service_state(service_name: str, scope: str = "user") -> str:
    """Get systemd service state (portable: any Linux with systemd; system or user scope)."""
    try:
        result = subprocess.run(
            _systemctl_prefix(scope) + ["is-active", service_name],
            capture_output=True, text=True, timeout=10, env=_CLEAN_ENV,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def check_port(port: int, timeout: float = 0.1) -> bool:
    """TCP port reachability check (hardware-agnostic)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect(("127.0.0.1", port))
        return True
    except (OSError, socket.timeout):
        return False


def check_http_health(port: int, path: str = "/health",
                      timeout: float = 2.0) -> Tuple[bool, float]:
    """HTTP health check. Returns (ok, response_time_seconds)."""
    url = f"http://127.0.0.1:{port}{path}"
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read()
            return True, time.monotonic() - t0
    except Exception:
        return False, time.monotonic() - t0


def get_service_pid(service_name: str, scope: str = "user") -> Optional[int]:
    """Get MainPID of a systemd service (portable, system or user scope)."""
    try:
        result = subprocess.run(
            _systemctl_prefix(scope) + ["show", "-p", "MainPID", "--value", service_name],
            capture_output=True, text=True, timeout=5, env=_CLEAN_ENV,
        )
        pid = int(result.stdout.strip())
        return pid if pid > 0 else None
    except Exception:
        return None


# CPU tracking for delta-based percentage calculation
_prev_cpu_jiffies: Dict[int, Tuple[int, float]] = {}  # pid → (total_jiffies, timestamp)
_JIFFIES_STALE_S = 300  # Remove PID entries not updated in 5 minutes


def _cleanup_stale_pid_jiffies():
    """Remove stale PID entries from _prev_cpu_jiffies to prevent unbounded growth."""
    now = time.monotonic()
    stale = [pid for pid, (_, ts) in _prev_cpu_jiffies.items()
             if now - ts > _JIFFIES_STALE_S]
    for pid in stale:
        del _prev_cpu_jiffies[pid]


def get_process_metrics(pid: int) -> Dict[str, float]:
    """Get CPU% and RSS from /proc (Linux-portable, no external deps).

    CPU% uses delta between samples (requires 2+ calls for accurate reading).
    Falls back to zeros if /proc unavailable (non-Linux).
    """
    metrics = {"cpu_pct": 0.0, "rss_mb": 0.0, "fd_count": 0}
    try:
        # RSS from /proc/PID/statm (pages → MB)
        with open(f"/proc/{pid}/statm", "r") as f:
            parts = f.read().split()
            if len(parts) >= 2:
                page_size = os.sysconf("SC_PAGE_SIZE")
                metrics["rss_mb"] = int(parts[1]) * page_size / (1024 * 1024)

        # FD count
        try:
            metrics["fd_count"] = len(os.listdir(f"/proc/{pid}/fd"))
        except PermissionError:
            pass

        # CPU% from /proc/PID/stat — delta-based
        try:
            with open(f"/proc/{pid}/stat", "r") as f:
                stat = f.read().split(")")[-1].split()
                utime = int(stat[11])
                stime = int(stat[12])
                total_jiffies = utime + stime
                now = time.monotonic()
                clk_tck = os.sysconf("SC_CLK_TCK")

                prev = _prev_cpu_jiffies.get(pid)
                if prev is not None:
                    prev_jiffies, prev_time = prev
                    dt = now - prev_time
                    if dt > 0.1:  # Avoid division by near-zero
                        djiffies = total_jiffies - prev_jiffies
                        cpu_seconds = djiffies / clk_tck
                        metrics["cpu_pct"] = min(100.0, (cpu_seconds / dt) * 100.0)

                _prev_cpu_jiffies[pid] = (total_jiffies, now)
        except (IndexError, ValueError):
            pass
    except FileNotFoundError:
        pass  # Not Linux or process gone
    return metrics


def get_system_metrics() -> Dict[str, float]:
    """Get system-wide CPU and RAM usage (portable, delta-based)."""
    global _prev_sys_idle, _prev_sys_total
    metrics = {"cpu_system": 0.0, "ram_system_pct": 0.0}
    try:
        with open("/proc/stat", "r") as f:
            line = f.readline()
            parts = line.split()
            if len(parts) >= 5:
                user = int(parts[1])
                nice = int(parts[2])
                system = int(parts[3])
                idle = int(parts[4])
                iowait = int(parts[5]) if len(parts) > 5 else 0
                irq = int(parts[6]) if len(parts) > 6 else 0
                softirq = int(parts[7]) if len(parts) > 7 else 0
                steal = int(parts[8]) if len(parts) > 8 else 0
                total = user + nice + system + idle + iowait + irq + softirq + steal
                total_idle = idle + iowait
                # Delta-based CPU: compare to previous reading
                d_total = total - _prev_sys_total
                d_idle = total_idle - _prev_sys_idle
                if d_total > 0 and _prev_sys_total > 0:
                    metrics["cpu_system"] = (d_total - d_idle) / d_total * 100.0
                _prev_sys_total = total
                _prev_sys_idle = total_idle

        with open("/proc/meminfo", "r") as f:
            total = available = 0
            for line in f:
                if line.startswith("MemTotal:"):
                    total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    available = int(line.split()[1])
            if total > 0:
                metrics["ram_system_pct"] = (total - available) / total * 100.0
    except FileNotFoundError:
        pass  # Non-Linux
    return metrics


# ── Health Collector ──────────────────────────────────────────────

class HealthCollector:
    """Collects health metrics for all monitored services."""

    def __init__(self, services: Optional[Dict] = None):
        self.services = services or SERVICE_REGISTRY
        # Sliding windows: service_name → deque of feature vectors
        self.windows: Dict[str, collections.deque] = {
            name: collections.deque(maxlen=WINDOW_SIZE)
            for name in self.services
        }
        # Track uptime per service
        self._last_seen_active: Dict[str, float] = {}
        self._restart_counts: Dict[str, int] = {}
        # Cached system metrics (refreshed every tick)
        self._system_metrics: Dict[str, float] = {"cpu_system": 0.0, "ram_system_pct": 0.0}
        self._system_metrics_ts: float = 0.0

    def collect_service(self, name: str) -> List[float]:
        """Collect 12 health features for one service.

        Features: [is_active, cpu_pct, rss_mb_norm, response_time_norm,
                   restart_count_norm, uptime_norm, error_rate, fd_count_norm,
                   port_reachable, dependency_health, time_sin, time_cos]
        """
        info = self.services.get(name, {})
        scope = info.get("scope", "user")
        now = time.time()

        # 1. systemctl status
        state = get_service_state(name, scope=scope)
        is_active = 1.0 if state == "active" else 0.0

        # Track uptime
        if is_active:
            if name not in self._last_seen_active:
                self._last_seen_active[name] = now
        else:
            self._last_seen_active.pop(name, None)

        # 2. Process metrics (CPU, RSS, FD)
        cpu_pct = 0.0
        rss_mb = 0.0
        fd_count = 0
        if is_active:
            pid = get_service_pid(name, scope=scope)
            if pid:
                pm = get_process_metrics(pid)
                cpu_pct = pm["cpu_pct"]
                rss_mb = pm["rss_mb"]
                fd_count = pm["fd_count"]

        # 3. Port check
        port = info.get("port")
        port_reachable = 1.0
        if port:
            port_reachable = 1.0 if check_port(port) else 0.0

        # 4. HTTP health + response time
        response_time = 0.0
        health_endpoint = info.get("health")
        if port and health_endpoint and is_active:
            ok, rt = check_http_health(port, health_endpoint)
            response_time = rt
            if not ok:
                port_reachable = 0.5  # Port open but health failing

        # 5. Uptime
        start = self._last_seen_active.get(name, now)
        uptime_s = now - start if is_active else 0.0

        # 6. Dependency health (average of upstream tier services)
        tier = info.get("tier", 0)
        dep_health = self._calc_dependency_health(tier)

        # 7. Time of day (cyclical encoding)
        hour = time.localtime().tm_hour + time.localtime().tm_min / 60.0
        time_sin = math.sin(2 * math.pi * hour / 24.0)
        time_cos = math.cos(2 * math.pi * hour / 24.0)

        # 8. Restart count (from external tracker)
        restart_count = self._restart_counts.get(name, 0)

        # Normalize features
        return [
            is_active,                           # [0,1]
            min(cpu_pct / 100.0, 1.0),          # [0,1]
            min(rss_mb / 4096.0, 1.0),          # [0,1] (4GB max)
            min(response_time / 5.0, 1.0),      # [0,1] (5s max)
            min(restart_count / 20.0, 1.0),     # [0,1]
            min(uptime_s / 86400.0, 1.0),       # [0,1] (1 day max)
            0.0,                                 # error_rate (future)
            min(fd_count / 1000.0, 1.0),        # [0,1]
            port_reachable,                      # [0,1]
            dep_health,                          # [0,1]
            time_sin,                            # [-1,1]
            time_cos,                            # [-1,1]
        ]

    def _calc_dependency_health(self, tier: int) -> float:
        """Health of services in lower tiers (dependencies)."""
        if tier == 0:
            return 1.0  # No dependencies
        dep_active = 0
        dep_total = 0
        for name, info in self.services.items():
            if info.get("tier", 0) < tier:
                dep_total += 1
                if self._last_seen_active.get(name):
                    dep_active += 1
        return dep_active / max(dep_total, 1)

    def collect_all(self) -> Dict[str, List[float]]:
        """Collect metrics for all services and update sliding windows.

        Returns current snapshot (service → feature vector).
        """
        # Refresh system metrics once per tick
        self._system_metrics = get_system_metrics()
        self._system_metrics_ts = time.time()

        snapshot = {}
        for name in self.services:
            features = self.collect_service(name)
            self.windows[name].append(features)
            snapshot[name] = features

        # Periodic cleanup of stale PID jiffies entries (every ~5 min = 20 ticks)
        _cleanup_stale_pid_jiffies()

        return snapshot

    def get_system_metrics_cached(self) -> Dict[str, float]:
        """Get cached system metrics (refreshed every collect_all tick)."""
        return self._system_metrics

    def get_window(self, name: str) -> List[float]:
        """Get flattened 8-step window for a service (96 floats).

        Pads with zeros if fewer than 8 timesteps collected.
        """
        window = self.windows.get(name, collections.deque(maxlen=WINDOW_SIZE))
        # Flatten and pad
        flat = []
        for step in window:
            flat.extend(step)
        # Pad to full size
        target_len = WINDOW_SIZE * FEATURES_PER_STEP
        while len(flat) < target_len:
            flat.insert(0, 0.0)  # Pad at front (oldest)
        return flat[:target_len]

    def get_baseline_vector(self) -> List[float]:
        """Get system-wide snapshot vector for BaselineNet (120 floats).

        30 services × 4 metrics [is_active, cpu, rss, response_time].
        """
        vec = []
        service_names = sorted(self.services.keys())[:30]
        for name in service_names:
            window = self.windows.get(name)
            if window and len(window) > 0:
                latest = window[-1]
                vec.extend([latest[0], latest[1], latest[2], latest[3]])
            else:
                vec.extend([0.0, 0.0, 0.0, 0.0])
        # Pad to 120 (30 services × 4 metrics)
        while len(vec) < 120:
            vec.append(0.0)
        return vec[:120]

    def update_restart_count(self, service: str, count: int):
        """Update restart count for a service (called from supervisor)."""
        self._restart_counts[service] = count

    def is_user_active(self) -> bool:
        """Check if user recently interacted (presence signals)."""
        try:
            from config.paths import TEMP_FILES
            hb = TEMP_FILES.get("overlay_heartbeat")
            if hb and hb.exists():
                age = time.time() - float(hb.read_text().strip())
                return age < 60  # Active if heartbeat < 60s
        except Exception:
            pass
        return False
