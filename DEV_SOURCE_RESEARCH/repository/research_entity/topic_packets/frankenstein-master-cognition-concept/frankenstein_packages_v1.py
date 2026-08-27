"""
Phase/package decomposition + dispenser for the 72h Frankenstein build.

Gabriel's explicit correction (2026-08-27, after the first version of
frankenstein_orchestrator_v1.py/frankenstein_bugfix_v1.py was written): the
72h task must NEVER be handed to a free-pool helper model as one giant,
continuous auftrag -- those models have limited context windows. It must be
decomposed into small, self-contained Phases and Pakete (packages) that are
automatically dispensed one after another, each carrying enough context to
be completed WITHOUT the receiving model needing the whole 72h history. He
further specified this decomposition/dispensing logic must be one of the
MOST ROBUST parts of the whole system (own error handling, no single point
of failure, tested before the 72h run starts) -- because if the
distribution mechanism itself is unstable, everything built on top of it
falls apart with it.

This module IS that backbone. It is deliberately its own file (imported by
frankenstein_orchestrator_v1.py, not inlined into it) so it can be tested in
complete isolation before anything else depends on it.

Design grounded directly in CONCEPT.md's own section structure (sections
3-6) plus section 1's named "aspirational, not yet built" operational layer
and section 7's pointer to sandbox/artifacts -- the phase list below is not
invented scaffolding, it is CONCEPT.md's own real content broken into
independently-completable units.

Reuses, does not reimplement:
  - tools/grid10_fabric.py's Fabric.seed_task / runtime_claim_task /
    runtime_reclaim_stale_claims for the actual claim queue (tasks table,
    OPEN/CLAIMED lifecycle, epoch-based CAS, already proven this session).
  - Fabric.get_regulator / set_regulator (versioned CAS) for completion
    tracking -- a dedicated regulator name per package
    ("frankenstein:pkg_done:<package_id>") gives an O(1), race-safe
    "is this package done" check, which the tasks table alone cannot give
    (a claimed task has no built-in DONE status -- see grid10_fabric.py,
    task lifecycle is only OPEN/CLAIMED, completion is signaled through the
    separate result-channel/scope-summary mechanism). Using a regulator
    per package avoids having to walk scope summary_json's nested
    "previous" chain just to answer "is X done yet".
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from grid10_fabric import Fabric, FabricError, result_packet  # noqa: E402

PACKAGES_SCOPE = "frankenstein:packages"
MAX_CLAIM_RETRIES = 20
MAX_MARK_DONE_RETRIES = 10
FABRIC_RETRY_SLEEP_SECONDS = 0.5


# ---------------------------------------------------------------------------
# The real decomposition. Each package is fully self-contained: a receiving
# model needs ONLY this dict's "description" (and, for helper dispatch, the
# real repo file paths it names) -- never "as discussed above", never a
# reference to prior packages' conversation. depends_on lists package_ids
# that must be marked done first (dependency-respecting claim order,
# enforced by package_ready() below, independent of seed/claim order).
# ---------------------------------------------------------------------------
PHASES: list[dict[str, Any]] = [
    {
        "phase_id": "A_alignment_regulator",
        "title": "Alignment-Mechanik (CONCEPT.md Abschnitt 3)",
        "packages": [
            {
                "package_id": "A1_alignment_targets_table",
                "capability": "coder",
                "depends_on": [],
                "description": (
                    "In tools/grid10_fabric.py, add a new SQLite table "
                    "`alignment_targets(regulator_name TEXT PRIMARY KEY, "
                    "target_value REAL NOT NULL, gain REAL NOT NULL, "
                    "max_step REAL NOT NULL)` to the CREATE TABLE block inside "
                    "init_schema(). Add two new methods to the Fabric class: "
                    "get_alignment_target(self, name: str) -> dict | None "
                    "(returns {'regulator_name','target_value','gain','max_step'} "
                    "or None if not set) and set_alignment_target(self, name: str, "
                    "target_value: float, gain: float, max_step: float) -> None "
                    "(INSERT OR REPLACE, same BEGIN IMMEDIATE / COMMIT / "
                    "except-ROLLBACK pattern already used by every other "
                    "mutating method in this class -- read set_regulator() in "
                    "the same file as the pattern to copy). Write "
                    "tests/test_grid10_fabric_alignment_targets_v1.py covering: "
                    "get on unset name returns None, set then get round-trips "
                    "all four fields, set-then-set-again (update) overwrites "
                    "correctly. Acceptance: "
                    "`python3 -m pytest tests/test_grid10_fabric_alignment_targets_v1.py -q` "
                    "exits 0."
                ),
                "acceptance_criteria": "pytest tests/test_grid10_fabric_alignment_targets_v1.py -q exits 0",
            },
            {
                "package_id": "A2_compute_alignment_delta",
                "capability": "coder",
                "depends_on": [],
                "description": (
                    "Create tools/grid10_alignment.py. Implement a pure function "
                    "compute_alignment_delta(reject_rate: float, regulator_drift: "
                    "float, reflex_trigger_rate: float, w1: float, w2: float, "
                    "w3: float) -> float that returns "
                    "w1*reject_rate + w2*regulator_drift + w3*reflex_trigger_rate "
                    "(the exact formula from CONCEPT.md section 3 -- no other "
                    "logic, no clamping, just the weighted sum). Write "
                    "tests/test_grid10_alignment_delta_v1.py with at least 4 cases "
                    "including all-zero inputs (expect 0.0) and a case where "
                    "weights sum to more than 1.0 (function must not silently "
                    "normalize -- that would silently change behavior the caller "
                    "did not ask for). Acceptance: "
                    "`python3 -m pytest tests/test_grid10_alignment_delta_v1.py -q` "
                    "exits 0."
                ),
                "acceptance_criteria": "pytest tests/test_grid10_alignment_delta_v1.py -q exits 0",
            },
            {
                "package_id": "A3_damped_correction",
                "capability": "coder",
                "depends_on": [],
                "description": (
                    "In tools/grid10_alignment.py (same file as A2), implement "
                    "damped_correction(current_value: float, target_value: float, "
                    "gain: float, max_step: float) -> float implementing exactly: "
                    "new_value = current_value + clamp(gain * (target_value - "
                    "current_value), -max_step, max_step) -- from CONCEPT.md "
                    "section 3. Write a local clamp(x, lo, hi) helper if none "
                    "exists yet in the file. Write "
                    "tests/test_grid10_alignment_damped_correction_v1.py covering: "
                    "a small delta that stays within max_step (no clamping), a "
                    "large delta that DOES get clamped to exactly max_step, and "
                    "current_value == target_value (must return current_value "
                    "unchanged). Acceptance: "
                    "`python3 -m pytest tests/test_grid10_alignment_damped_correction_v1.py -q` "
                    "exits 0."
                ),
                "acceptance_criteria": "pytest tests/test_grid10_alignment_damped_correction_v1.py -q exits 0",
            },
            {
                "package_id": "A4_alignment_tick_integration",
                "capability": "coder",
                "depends_on": ["A1_alignment_targets_table", "A2_compute_alignment_delta", "A3_damped_correction"],
                "description": (
                    "In tools/grid10_alignment.py, implement "
                    "alignment_tick(fabric, weights: dict, tau_low: float = 0.05, "
                    "tau_high: float = 0.15) -> dict. It must: read real signals "
                    "from the fabric (reject_rate/regulator_drift/"
                    "reflex_trigger_rate -- for THIS package, real-but-simple "
                    "stand-ins are acceptable and must be documented as such in a "
                    "code comment: e.g. regulator_drift computed as "
                    "abs(get_regulator(name)['value_real'] - "
                    "get_alignment_target(name)['target_value']) for every name "
                    "with a set alignment_target, averaged; reject_rate and "
                    "reflex_trigger_rate may default to 0.0 with a clear comment "
                    "that a real feedback/reflex-log source is a FUTURE package, "
                    "not invented data), call compute_alignment_delta(), and if "
                    "delta > tau_high, call set_regulator() for each drifted "
                    "regulator toward its alignment_target using "
                    "damped_correction() -- but ONLY if grid10_node.py's existing "
                    "human-pin-cooldown check (read meta_regulator_tick() in "
                    "tools/grid10_node.py for the exact pattern: a regulator whose "
                    "last writer was 'human-simulated' within the cooldown window "
                    "must NOT be overwritten) says it is not currently pinned. "
                    "Return a dict with the computed delta, zone "
                    "('safe'/'warn'/'critical'), and which regulators (if any) "
                    "were corrected. Write "
                    "tests/test_grid10_alignment_tick_v1.py using a real temporary "
                    "Fabric (tmp_path fixture), covering: safe zone does nothing, "
                    "critical zone corrects a drifted regulator, and a "
                    "human-pinned regulator is correctly left untouched even in "
                    "the critical zone. Acceptance: "
                    "`python3 -m pytest tests/test_grid10_alignment_tick_v1.py -q` "
                    "exits 0."
                ),
                "acceptance_criteria": "pytest tests/test_grid10_alignment_tick_v1.py -q exits 0",
            },
        ],
    },
    {
        "phase_id": "B_reflex_layer",
        "title": "Reflex-Schicht (CONCEPT.md Abschnitt 4)",
        "packages": [
            {
                "package_id": "B1_reflex_fabric_reachable",
                "capability": "coder",
                "depends_on": [],
                "description": (
                    "Create tools/grid10_reflex.py. Implement "
                    "reflex_check_fabric_reachable(fabric_path: str) -> dict "
                    "that attempts Fabric(Path(fabric_path)).snapshot() inside a "
                    "try/except, and returns {'triggered': bool, 'action_taken': "
                    "str|None}. On failure (any exception), 'triggered'=True and "
                    "it writes a plain alarm file to "
                    "/tmp/frankenstein_alarm_fabric_unreachable.txt with the "
                    "exception text and timestamp (this is the deterministic, "
                    "no-LLM countermeasure from CONCEPT.md's reflex table row 1 -- "
                    "do NOT call any LLM here). Must complete in well under "
                    "500ms on the success path (measure and assert this in the "
                    "test with a real time.time() delta). Write "
                    "tests/test_grid10_reflex_fabric_reachable_v1.py covering "
                    "both the success case (real tmp Fabric) and the failure "
                    "case (a fabric_path that does not exist / is not writable). "
                    "Acceptance: "
                    "`python3 -m pytest tests/test_grid10_reflex_fabric_reachable_v1.py -q` "
                    "exits 0."
                ),
                "acceptance_criteria": "pytest tests/test_grid10_reflex_fabric_reachable_v1.py -q exits 0",
            },
            {
                "package_id": "B2_reflex_free_memory",
                "capability": "coder",
                "depends_on": [],
                "description": (
                    "In tools/grid10_reflex.py (same file as B1), implement "
                    "reflex_check_free_memory(threshold_mb: float = 200.0) -> "
                    "dict. Read real free memory from /proc/meminfo "
                    "(MemAvailable field, in kB, convert to MB) -- do not use "
                    "any library that is not already a dependency of this repo. "
                    "If free memory is below threshold_mb, call "
                    "tools/grid10_node.py's existing release_idle_memory() "
                    "function (import it) and return {'triggered': True, "
                    "'action_taken': 'release_idle_memory'}; otherwise "
                    "{'triggered': False, 'action_taken': None}. Write "
                    "tests/test_grid10_reflex_free_memory_v1.py: mock/monkeypatch "
                    "the /proc/meminfo read (do not depend on the real machine's "
                    "actual free memory for test determinism) to cover both the "
                    "above-threshold and below-threshold cases, asserting "
                    "release_idle_memory() is called exactly once in the "
                    "below-threshold case (use a monkeypatched stand-in, do not "
                    "call the real one from the test). Acceptance: "
                    "`python3 -m pytest tests/test_grid10_reflex_free_memory_v1.py -q` "
                    "exits 0."
                ),
                "acceptance_criteria": "pytest tests/test_grid10_reflex_free_memory_v1.py -q exits 0",
            },
            {
                "package_id": "B3_reflex_stale_heartbeat",
                "capability": "coder",
                "depends_on": [],
                "description": (
                    "In tools/grid10_reflex.py, implement "
                    "reflex_check_stale_heartbeat(fabric, stale_after_seconds: "
                    "float = 15.0) -> dict that calls the ALREADY EXISTING "
                    "fabric.runtime_reclaim_stale_claims(reclaiming_node_id="
                    "'frankenstein-reflex', stale_after_seconds="
                    "stale_after_seconds) and returns {'triggered': "
                    "bool(reclaimed), 'action_taken': 'runtime_reclaim_stale_"
                    "claims', 'reclaimed_task_ids': reclaimed}. Do not "
                    "reimplement any staleness logic -- this package is purely "
                    "a thin, well-tested wrapper. Write "
                    "tests/test_grid10_reflex_stale_heartbeat_v1.py using a real "
                    "tmp Fabric with a manually-seeded stale claim (seed_task + "
                    "runtime_claim_task + manually backdating last_seen_ts via "
                    "direct sqlite3 access in the test, since there is no public "
                    "API to backdate -- read tests/test_grid10_fabric*.py in "
                    "this repo for existing examples of this pattern if any "
                    "exist). Acceptance: "
                    "`python3 -m pytest tests/test_grid10_reflex_stale_heartbeat_v1.py -q` "
                    "exits 0."
                ),
                "acceptance_criteria": "pytest tests/test_grid10_reflex_stale_heartbeat_v1.py -q exits 0",
            },
            {
                "package_id": "B4_reflex_tick_aggregate",
                "capability": "coder",
                "depends_on": ["B1_reflex_fabric_reachable", "B2_reflex_free_memory", "B3_reflex_stale_heartbeat"],
                "description": (
                    "In tools/grid10_reflex.py, implement reflex_tick(fabric, "
                    "fabric_path: str) -> dict that runs all three reflex checks "
                    "(B1, B2, B3) in one pass, measures real wall-clock time for "
                    "the whole pass with time.time(), and returns {'results': "
                    "[...], 'elapsed_ms': float, 'over_budget': elapsed_ms > 500}. "
                    "If over_budget, write a plain warning line to a local log "
                    "file (do not raise/crash -- exceeding budget is logged, not "
                    "fatal, since the reflex layer must never itself become a "
                    "new point of failure). Write "
                    "tests/test_grid10_reflex_tick_v1.py verifying the aggregate "
                    "return shape and that elapsed_ms is a real measured float "
                    "greater than 0. Acceptance: "
                    "`python3 -m pytest tests/test_grid10_reflex_tick_v1.py -q` "
                    "exits 0."
                ),
                "acceptance_criteria": "pytest tests/test_grid10_reflex_tick_v1.py -q exits 0",
            },
        ],
    },
    {
        "phase_id": "C_claude_bridge",
        "title": "Claude-Code-Bruecke (CONCEPT.md Abschnitt 5)",
        "packages": [
            {
                "package_id": "C1_bridge_requests_table",
                "capability": "coder",
                "depends_on": [],
                "description": (
                    "In tools/grid10_fabric.py, add a new SQLite table "
                    "`claude_bridge_requests(request_id TEXT PRIMARY KEY, "
                    "priority_vector_json TEXT NOT NULL, context_digest TEXT NOT "
                    "NULL, payload TEXT NOT NULL, answered INTEGER NOT NULL "
                    "DEFAULT 0, submitted_ts REAL NOT NULL)` to init_schema(). "
                    "Add methods submit_bridge_request(self, request_id: str, "
                    "priority_vector: dict, context_digest: str, payload: str) "
                    "-> None and read_pending_bridge_requests(self) -> list[dict] "
                    "(WHERE answered=0, ordered by submitted_ts), matching the "
                    "schema in CONCEPT.md section 5 exactly (fields: schema, "
                    "request_id, priority_vector, context_digest, payload). "
                    "Write tests/test_grid10_fabric_bridge_requests_v1.py "
                    "covering submit + read-pending round trip and that an "
                    "answered request no longer appears in read_pending. "
                    "Acceptance: "
                    "`python3 -m pytest tests/test_grid10_fabric_bridge_requests_v1.py -q` "
                    "exits 0."
                ),
                "acceptance_criteria": "pytest tests/test_grid10_fabric_bridge_requests_v1.py -q exits 0",
            },
            {
                "package_id": "C2_bridge_opt_in_caller",
                "capability": "coder",
                "depends_on": ["C1_bridge_requests_table"],
                "description": (
                    "Create tools/grid10_claude_bridge.py implementing "
                    "try_answer_pending_bridge_requests(fabric, "
                    "claude_code_available_check) -> dict where "
                    "claude_code_available_check is an injected callable (for "
                    "real use it would check whether a Claude Code process/CLI "
                    "is reachable -- for THIS package, write it as a parameter "
                    "so it is fully testable without a real Claude Code "
                    "instance). If unavailable, return {'answered': 0, "
                    "'left_pending': N} WITHOUT marking anything answered=1 "
                    "(per CONCEPT.md section 5: entries stay visible, not lost, "
                    "loop degrades but does not break). Write "
                    "tests/test_grid10_claude_bridge_v1.py covering both the "
                    "available and unavailable-injected-callable cases against "
                    "a real tmp Fabric. Acceptance: "
                    "`python3 -m pytest tests/test_grid10_claude_bridge_v1.py -q` "
                    "exits 0."
                ),
                "acceptance_criteria": "pytest tests/test_grid10_claude_bridge_v1.py -q exits 0",
            },
        ],
    },
    {
        "phase_id": "D_web_ui",
        "title": "Web-UI kognitives Lego (CONCEPT.md Abschnitt 6)",
        "packages": [
            {
                "package_id": "D1_regulator_http_wrapper",
                "capability": "coder",
                "depends_on": [],
                "description": (
                    "Create tools/grid10_web_ui.py using Python's stdlib "
                    "http.server (no new external dependency) exposing: GET "
                    "/api/regulators (returns JSON list of all rows from the "
                    "regulators table, real SELECT via a real Fabric instance -- "
                    "add a small helper method or direct sqlite3 read, whichever "
                    "fits the existing Fabric class style better) and POST "
                    "/api/regulators/<name> (body: {'value_real': float}, calls "
                    "the existing set_regulator(name, value_real, "
                    "writer='web-ui')). Write "
                    "tests/test_grid10_web_ui_v1.py using Python's own "
                    "http.client or requests against a real server instance "
                    "started on an ephemeral port in the test (start in a "
                    "thread, tear down after), covering GET returning real "
                    "values and POST actually changing a regulator's value "
                    "(verified by reading it back via Fabric directly, not just "
                    "trusting the HTTP response). Acceptance: "
                    "`python3 -m pytest tests/test_grid10_web_ui_v1.py -q` "
                    "exits 0."
                ),
                "acceptance_criteria": "pytest tests/test_grid10_web_ui_v1.py -q exits 0",
            },
            {
                "package_id": "D2_regulator_profiles",
                "capability": "coder",
                "depends_on": ["D1_regulator_http_wrapper"],
                "description": (
                    "In tools/grid10_fabric.py, add table "
                    "`regulator_profiles(profile_name TEXT PRIMARY KEY, "
                    "snapshot_json TEXT NOT NULL, created_ts REAL NOT NULL)` and "
                    "methods save_regulator_profile(self, profile_name: str) -> "
                    "None (reads ALL current regulators, stores as JSON) and "
                    "apply_regulator_profile(self, profile_name: str) -> int "
                    "(calls set_regulator with writer='user-reset' for every "
                    "regulator in the saved snapshot, returns count applied; "
                    "raises FabricError('PROFILE_NOT_FOUND') if the name does "
                    "not exist). In tools/grid10_web_ui.py (from D1), add POST "
                    "/api/profiles/<name>/save and POST /api/profiles/<name>/"
                    "apply endpoints wrapping these. Write "
                    "tests/test_grid10_fabric_regulator_profiles_v1.py (save "
                    "then apply round-trips correctly, apply on unknown name "
                    "raises) and extend test_grid10_web_ui_v1.py's coverage "
                    "with the two new endpoints. Acceptance: "
                    "`python3 -m pytest tests/test_grid10_fabric_regulator_profiles_v1.py tests/test_grid10_web_ui_v1.py -q` "
                    "exits 0."
                ),
                "acceptance_criteria": "pytest tests/test_grid10_fabric_regulator_profiles_v1.py tests/test_grid10_web_ui_v1.py -q exits 0",
            },
            {
                "package_id": "D3_live_state_view",
                "capability": "coder",
                "depends_on": ["D1_regulator_http_wrapper"],
                "description": (
                    "In tools/grid10_web_ui.py, add GET /api/state returning "
                    "real JSON for tasks/scopes/leases/regulators (reuse "
                    "Fabric.snapshot() for tasks/scopes/leases, plus the "
                    "regulators read from D1). Add a minimal static HTML page "
                    "served at GET / that polls /api/state every 2 seconds via "
                    "plain fetch()+setInterval (no framework/build step -- "
                    "single static HTML string is fine for this first version) "
                    "and renders the four tables as plain HTML tables -- this is "
                    "the concrete 'kognitive Schleife sichtbar in der WebApp' "
                    "requirement. Write tests/test_grid10_web_ui_state_v1.py "
                    "covering GET /api/state returns real, non-empty structure "
                    "against a tmp Fabric with seeded data. Acceptance: "
                    "`python3 -m pytest tests/test_grid10_web_ui_state_v1.py -q` "
                    "exits 0."
                ),
                "acceptance_criteria": "pytest tests/test_grid10_web_ui_state_v1.py -q exits 0",
            },
        ],
    },
    {
        "phase_id": "E_operational_layer",
        "title": "Permanenter Betrieb ab Boot (CONCEPT.md Abschnitt 1, aspirational->real)",
        "packages": [
            {
                "package_id": "E1_systemd_unit_and_watchdog",
                "capability": "coder",
                "depends_on": ["B4_reflex_tick_aggregate"],
                "description": (
                    "Create tools/grid10_reflex_daemon.py: a small script that "
                    "loops calling reflex_tick() (from B4) every 500ms "
                    "(time.sleep(0.5) between iterations, measuring real "
                    "elapsed time and subtracting it from the sleep so the "
                    "cadence stays close to 500ms even under load), with a "
                    "clean SIGTERM handler for graceful shutdown. Create a "
                    "systemd unit file template at "
                    "research_entity/topic_packets/frankenstein-master-"
                    "cognition-concept/systemd/frankenstein-reflex.service "
                    "(Type=simple, Restart=always, RestartSec=2 -- a real "
                    "watchdog restart policy) with clear comments on the two "
                    "environment variables it needs (fabric path, log path) "
                    "and honestly note in a comment that ENABLING this unit on "
                    "any real machine is a deliberate, separate step NOT taken "
                    "automatically by this package (installing a boot-time "
                    "daemon is exactly the kind of action that should not "
                    "silently happen as a side effect of a helper task). Write "
                    "tests/test_grid10_reflex_daemon_v1.py that runs the loop "
                    "function for a bounded number of iterations (inject "
                    "max_iterations, do not test the real infinite loop) and "
                    "verifies reflex_tick was called that many times and the "
                    "cadence stayed within a reasonable tolerance. Acceptance: "
                    "`python3 -m pytest tests/test_grid10_reflex_daemon_v1.py -q` "
                    "exits 0."
                ),
                "acceptance_criteria": "pytest tests/test_grid10_reflex_daemon_v1.py -q exits 0",
            },
        ],
    },
]


def _all_package_ids() -> list[str]:
    return [pkg["package_id"] for phase in PHASES for pkg in phase["packages"]]


def _find_package(package_id: str) -> dict[str, Any] | None:
    for phase in PHASES:
        for pkg in phase["packages"]:
            if pkg["package_id"] == package_id:
                return pkg
    return None


def _with_retry(fn, *, max_retries: int, retry_on: tuple[str, ...], log_fn=None):
    """Shared robustness primitive for this module: retries fn() on the
    named FabricError codes (real, expected races -- CAS conflicts under
    concurrent claimers), backs off briefly between attempts, and re-raises
    anything else immediately rather than masking a genuine bug as a
    transient race. This is the single place that embodies the 'no single
    point of failure' requirement for the dispenser -- every public
    function below routes its fabric writes through this."""
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            return fn()
        except FabricError as e:
            code = str(e)
            if not any(code == r or code.startswith(r) for r in retry_on):
                raise
            last_exc = e
            if log_fn:
                log_fn(f"RETRYABLE_FABRIC_ERROR attempt={attempt} code={code}")
            time.sleep(FABRIC_RETRY_SLEEP_SECONDS)
    raise last_exc if last_exc else RuntimeError("unreachable")


def seed_all_packages(fabric: Fabric, log_fn=None) -> int:
    """Idempotent: seeds every package from PHASES into PACKAGES_SCOPE as a
    real Fabric task (priority = phase index, so earlier phases sort first
    in any priority-ordered read), skipping any package_id that already
    exists as a task (checked via a real snapshot read first) so re-running
    this after a respawn never duplicates or resets already-seeded work.
    Returns the number of NEWLY seeded packages."""
    snap = fabric.snapshot()
    existing_ids = {t["task_id"] for t in snap.tasks if t["scope"] == PACKAGES_SCOPE}
    if PACKAGES_SCOPE not in {s["scope"] for s in snap.scopes}:
        fabric.seed_scope(PACKAGES_SCOPE)

    seeded = 0
    for phase_index, phase in enumerate(PHASES):
        for pkg in phase["packages"]:
            if pkg["package_id"] in existing_ids:
                continue
            fabric.seed_task(
                pkg["package_id"], PACKAGES_SCOPE, phase_index, pkg["capability"],
                {"description": pkg["description"], "acceptance_criteria": pkg["acceptance_criteria"],
                 "depends_on": pkg["depends_on"], "phase_id": phase["phase_id"]},
            )
            seeded += 1
            if log_fn:
                log_fn(f"PACKAGE_SEEDED {pkg['package_id']} phase={phase['phase_id']}")
    return seeded


def is_package_done(fabric: Fabric, package_id: str) -> bool:
    reg = fabric.get_regulator(f"frankenstein:pkg_done:{package_id}", default=0.0)
    return bool(reg and reg["value_real"] >= 1.0)


def package_ready(fabric: Fabric, package_id: str) -> bool:
    """A package is ready to claim only if every package_id in its
    depends_on list is already marked done. Dependency order is enforced
    HERE, independently of seed/claim/priority order, so a helper model
    claiming out of the 'natural' phase sequence (e.g. after a respawn)
    can never be handed a package whose prerequisites are not actually
    finished yet."""
    pkg = _find_package(package_id)
    if pkg is None:
        return False
    return all(is_package_done(fabric, dep) for dep in pkg["depends_on"])


def claim_next_package(fabric: Fabric, node_id: str, log_fn=None) -> dict[str, Any] | None:
    """Robust, race-safe claim of the next ready, not-yet-done package.
    Real CAS retry loop (re-snapshots on every attempt, so it always claims
    against the CURRENT epoch rather than a stale one) -- this is the most
    safety-critical function in this module per Gabriel's explicit
    robustness requirement, so it is deliberately conservative: any
    unexpected FabricError that is NOT a known, expected claim race is
    re-raised rather than silently swallowed. Returns the package dict
    (merged with its task payload) on success, or None if nothing is
    currently claimable (either everything is done, or every remaining
    package's dependencies are unmet -- callers should check
    all_packages_done() to distinguish those two cases)."""
    for attempt in range(1, MAX_CLAIM_RETRIES + 1):
        try:
            snap = fabric.snapshot()
        except Exception as e:  # noqa: BLE001 - the fabric file itself may be
            # transiently locked/unreadable under heavy concurrent write load;
            # that is exactly the "no single point of failure" case Gabriel
            # named explicitly -- retry with backoff rather than crashing the
            # whole dispenser on a transient OS-level hiccup.
            if log_fn:
                log_fn(f"SNAPSHOT_TRANSIENT_FAILURE attempt={attempt} err={e}")
            time.sleep(FABRIC_RETRY_SLEEP_SECONDS)
            continue

        candidates = sorted(
            (t for t in snap.tasks
             if t["scope"] == PACKAGES_SCOPE and t["status"] == "OPEN" and t["claimed_by"] is None
             and not is_package_done(fabric, t["task_id"])
             and package_ready(fabric, t["task_id"])),
            key=lambda t: (t["priority"], t["task_id"]),
        )
        if not candidates:
            return None

        for candidate in candidates:
            try:
                fabric.runtime_claim_task(candidate["task_id"], node_id, expected_epoch=snap.epoch)
                pkg = _find_package(candidate["task_id"])
                if log_fn:
                    log_fn(f"PACKAGE_CLAIMED {candidate['task_id']} by={node_id}")
                return {**pkg, "task_id": candidate["task_id"]}
            except FabricError as e:
                code = str(e)
                if code in ("TASK_CLAIM_CAS_FAILED", "TASK_NOT_CLAIMABLE"):
                    # Expected race (epoch moved, or someone else claimed it
                    # first between our snapshot and this claim) -- try the
                    # NEXT candidate in this same pass rather than restarting
                    # the whole scan immediately.
                    if log_fn:
                        log_fn(f"CLAIM_RACE_LOST {candidate['task_id']} code={code}")
                    continue
                raise  # anything else is a real bug, must not be masked
        # every candidate in this pass lost its race -- re-snapshot and retry
        time.sleep(FABRIC_RETRY_SLEEP_SECONDS)
    if log_fn:
        log_fn(f"CLAIM_EXHAUSTED_RETRIES after {MAX_CLAIM_RETRIES} attempts")
    return None


def mark_package_done(fabric: Fabric, package_id: str, ok: bool, node_id: str, log_fn=None) -> bool:
    """Marks a package done (ok=True) via a CAS-safe regulator write, OR
    records a failed attempt (ok=False) via a separate failure-count
    regulator WITHOUT marking it done -- so a failed package remains
    claimable again by a later attempt (its task row is still 'CLAIMED' by
    the failed claimer though; callers wanting true reassignment should
    also invoke fabric.runtime_reclaim_stale_claims() for it, reusing the
    same stale-claim mechanism as everything else). Also emits an audit
    result_packet into PACKAGES_SCOPE for visibility, best-effort (does not
    fail the whole call if the scope's coordinator lease is currently held
    by someone else -- that is expected under concurrency, not an error)."""
    reg_name = f"frankenstein:pkg_done:{package_id}" if ok else f"frankenstein:pkg_fail_count:{package_id}"

    def _write():
        reg = fabric.get_regulator(reg_name, default=0.0)
        new_value = 1.0 if ok else (reg["value_real"] + 1.0 if reg else 1.0)
        return fabric.set_regulator(reg_name, new_value, writer=node_id,
                                     expected_version=reg["version"] if reg and reg["version"] else None)

    _with_retry(_write, max_retries=MAX_MARK_DONE_RETRIES,
                retry_on=("REGULATOR_CAS_FAILED",), log_fn=log_fn)

    try:
        fabric.runtime_join(node_id, "frankenstein-package-dispenser", 0)
        elected = fabric.elect_coordinator(PACKAGES_SCOPE, candidate_node_ids=[node_id])
        if elected is not None:
            lease, token = elected
            snap = fabric.snapshot()
            packet = result_packet(node_id, snap, PACKAGES_SCOPE,
                                    {"event": "PACKAGE_RESULT", "package_id": package_id, "ok": ok, "ts": time.time()})
            fabric.emit_node_result(packet)
            fabric.coordinator_drain_and_commit(PACKAGES_SCOPE, lease, token)
    except FabricError as e:
        if log_fn:
            log_fn(f"PACKAGE_AUDIT_LOG_BEST_EFFORT_SKIPPED {package_id} {e}")

    if log_fn:
        log_fn(f"PACKAGE_MARKED {'DONE' if ok else 'FAILED_ATTEMPT'} {package_id}")
    return True


def all_packages_done(fabric: Fabric) -> bool:
    return all(is_package_done(fabric, pid) for pid in _all_package_ids())


def progress_summary(fabric: Fabric) -> dict[str, Any]:
    ids = _all_package_ids()
    done = [pid for pid in ids if is_package_done(fabric, pid)]
    return {"total": len(ids), "done": len(done), "remaining": sorted(set(ids) - set(done))}
