"""Hard, code-enforced precondition gate for the ONE authorized Together
training run (Gabriel's direct, explicit instruction 2026-08-28, relayed via
coordinator, after he personally adjusted the project-wide provider
emergency stop). His own words, preserved precisely because they set the
actual bar this module must enforce technically, not just document:

  "Der Together-Trainingslauf darf ERST ausgeloest werden, wenn entweder
  (a) GRID10 fertig ist und alles kann, was es koennen soll, ODER (b) der
  Schwarm wirklich seit Stunden nachweislich nicht mehr weiterkommt (echter
  Stillstand) -- und selbst dann NUR nach langer Forschung UND peniblem
  Erstellen der Trainingsdaten UND 30-facher Revision JEDES EINZELNEN
  Trainingsbeispiels. [...] baue das als echte, geprueft durchgesetzte
  Vorbedingung ins Script/den Bugfixer/Bauleiter ein [...], nicht nur als
  Anweisung an die Modelle, die sie theoretisch ignorieren koennten."

Design consequence of "not just an instruction models could ignore": the
ONLY function in this whole codebase permitted to write
TRAINING_RUN_READY_FOR_LAUNCH.json (the marker frankenstein_orchestrator_v1's
quarantined donor already checks for and stops on) is
attempt_training_run() below, and it refuses unless BOTH real, independently
checkable conditions hold:

  1. training_run_technically_possible() -- (GRID10 fully done, reusing the
     already-real, already-tested frankenstein_packages_v1.all_packages_done())
     OR (the swarm has made zero real progress for hours, reusing a real
     regulator timestamp bumped by frankenstein_packages_v1.mark_package_done()
     on every genuine completion -- not a model's self-report).
  2. all_examples_fully_revised() -- every named training example has
     AT LEAST 30 real, sequential, individually-noted revision records in
     its own dedicated SQLite revision log (own file, separate from the
     GRID10 fabric -- this is data-curation provenance, not coordination
     state). "Documented" is enforced structurally: each revision record
     requires a non-trivial written note and the example's actual before/
     after content hash, sequential revision numbers (no skipping straight
     to 30), and INSERT-only storage (PRIMARY KEY on (example_id,
     revision_number) -- a revision can never silently overwrite or be
     replayed to fake reaching 30).

Even when both conditions hold, this module still does NOT call the
Together API itself -- it only makes it possible for
TRAINING_RUN_READY_FOR_LAUNCH.json to exist, which the Bauleiter's own loop
already treats as "stop and hand back to the coordinator" (see
run_bauleiter_instance() in the quarantined donor). Firing the real,
paid Together call remains a deliberate, separate, human-reviewed action --
consistent with every other paid-run decision this whole session, and with
the fact that the emergency-stop adjustment Gabriel authorized was about
DEPLOYING the loops, not about handing the actual spend decision to
autonomous code.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from grid10_fabric import Fabric  # noqa: E402
import frankenstein_packages_v1 as packages  # noqa: E402

REQUIRED_REVISIONS_PER_EXAMPLE = 30
DEFAULT_STALL_HOURS = 3.0
MIN_REVISION_NOTE_LENGTH = 20  # rejects rubber-stamp notes like "ok" or "done"
MIN_SECONDS_BETWEEN_REVISIONS = 0.05  # rejects a same-instant/replayed 30x loop with zero real gap
LAST_PROGRESS_REGULATOR = "frankenstein:last_progress_ts"


class TrainingRunBlocked(RuntimeError):
    pass


class RevisionRejected(ValueError):
    pass


def _connect(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS revisions(
          example_id TEXT NOT NULL,
          revision_number INTEGER NOT NULL,
          reviewer TEXT NOT NULL,
          revision_note TEXT NOT NULL,
          before_hash TEXT NOT NULL,
          after_hash TEXT NOT NULL,
          ts REAL NOT NULL,
          PRIMARY KEY(example_id, revision_number)
        )
        """
    )
    con.commit()
    return con


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def example_revision_count(db_path: Path, example_id: str) -> int:
    con = _connect(db_path)
    try:
        row = con.execute(
            "SELECT COUNT(*) AS n FROM revisions WHERE example_id=?", (example_id,)
        ).fetchone()
        return int(row["n"])
    finally:
        con.close()


def _last_revision(con: sqlite3.Connection, example_id: str) -> sqlite3.Row | None:
    return con.execute(
        "SELECT * FROM revisions WHERE example_id=? ORDER BY revision_number DESC LIMIT 1",
        (example_id,),
    ).fetchone()


def record_revision(db_path: Path, example_id: str, reviewer: str, revision_note: str,
                     before_text: str, after_text: str) -> dict[str, Any]:
    """Records exactly ONE real revision pass for one example. Structurally
    enforces "documented" and "sequential" -- raises RevisionRejected (never
    silently no-ops or overwrites) if:
      - the note is empty/whitespace/shorter than MIN_REVISION_NOTE_LENGTH
      - this would not be the very next sequential revision_number for this
        example_id (no skipping ahead, no re-doing an old number)
      - it arrives less than MIN_SECONDS_BETWEEN_REVISIONS after the
        previous revision of the SAME example (blocks an instant fake loop)
    Returns the inserted row as a dict, including the computed
    revision_number so the caller never has to guess/race on it themselves.
    """
    note = (revision_note or "").strip()
    if len(note) < MIN_REVISION_NOTE_LENGTH:
        raise RevisionRejected(
            f"revision_note too short ({len(note)} chars, need >= {MIN_REVISION_NOTE_LENGTH}) "
            "-- a real revision must explain what was actually reviewed/changed, not a rubber stamp"
        )
    con = _connect(db_path)
    try:
        last = _last_revision(con, example_id)
        next_number = 1 if last is None else int(last["revision_number"]) + 1
        now = time.time()
        if last is not None and (now - float(last["ts"])) < MIN_SECONDS_BETWEEN_REVISIONS:
            raise RevisionRejected(
                f"revision arrived only {now - float(last['ts']):.3f}s after the previous one "
                f"for example_id={example_id!r} -- too fast to be a real, separate review pass"
            )
        row = {
            "example_id": example_id,
            "revision_number": next_number,
            "reviewer": reviewer,
            "revision_note": note,
            "before_hash": _hash(before_text),
            "after_hash": _hash(after_text),
            "ts": now,
        }
        con.execute(
            "INSERT INTO revisions(example_id,revision_number,reviewer,revision_note,before_hash,after_hash,ts) "
            "VALUES(:example_id,:revision_number,:reviewer,:revision_note,:before_hash,:after_hash,:ts)",
            row,
        )
        con.commit()
        return row
    except sqlite3.IntegrityError as e:
        raise RevisionRejected(
            f"revision_number {next_number} already recorded for example_id={example_id!r} "
            f"(INSERT-only storage, cannot overwrite/replay): {e}"
        ) from e
    finally:
        con.close()


def is_example_fully_revised(db_path: Path, example_id: str,
                              required_revisions: int = REQUIRED_REVISIONS_PER_EXAMPLE) -> bool:
    return example_revision_count(db_path, example_id) >= required_revisions


def all_examples_fully_revised(db_path: Path, example_ids: list[str],
                                required_revisions: int = REQUIRED_REVISIONS_PER_EXAMPLE) -> bool:
    """Deliberately returns False (never vacuously True) for an empty
    example_ids list -- 'no examples named yet' must never read as 'nothing
    left to revise'."""
    if not example_ids:
        return False
    return all(is_example_fully_revised(db_path, eid, required_revisions) for eid in example_ids)


def bump_progress_marker(fabric: Fabric, writer: str) -> None:
    """Real progress signal, independent of any model's self-report: called
    by frankenstein_packages_v1.mark_package_done() every time a package is
    genuinely marked done (ok=True), so swarm_genuinely_stalled() below has
    an honest, code-driven 'last real progress' timestamp to compare
    against."""
    reg = fabric.get_regulator(LAST_PROGRESS_REGULATOR, default=0.0)
    try:
        fabric.set_regulator(LAST_PROGRESS_REGULATOR, time.time(), writer=writer,
                              expected_version=reg["version"] if reg and reg["version"] else None)
    except Exception:  # noqa: BLE001 - best-effort signal, must never block real work
        pass


def grid10_fully_capable(fabric: Fabric) -> bool:
    """Condition (a): GRID10 is done and can do everything it should --
    reuses the already-real, already-tested
    frankenstein_packages_v1.all_packages_done(), which is True only once
    every phase (alignment mechanic, reflex layer, Claude bridge, web UI,
    operational layer) has a genuinely marked-done package, per that
    module's own race-safe, CAS-checked bookkeeping."""
    return packages.all_packages_done(fabric)


def swarm_genuinely_stalled(fabric: Fabric, hours_threshold: float = DEFAULT_STALL_HOURS) -> bool:
    """Condition (b): real stall for hours -- reads the SAME
    LAST_PROGRESS_REGULATOR that bump_progress_marker() (called from real
    completions only) writes. If the regulator was never set, that itself
    counts as 'no progress recorded yet', which after hours_threshold since
    process start is indistinguishable from a real stall for this check's
    purposes -- callers should treat a freshly-seeded fabric as not stalled
    by construction (see tests) since real work only just started."""
    reg = fabric.get_regulator(LAST_PROGRESS_REGULATOR, default=None)
    if reg is None or reg.get("ts_ms") is None:
        return False  # nothing has run long enough yet to call this a stall
    last_progress_s = float(reg["ts_ms"]) / 1000.0
    return (time.time() - last_progress_s) >= hours_threshold * 3600.0


def training_run_technically_possible(fabric: Fabric, revision_db_path: Path, example_ids: list[str],
                                       hours_threshold: float = DEFAULT_STALL_HOURS,
                                       required_revisions: int = REQUIRED_REVISIONS_PER_EXAMPLE) -> tuple[bool, str]:
    """Combines both of Gabriel's real conditions. Returns (allowed, reason)
    -- reason is always populated, including on success, so every check is
    auditable rather than a bare boolean."""
    cond_a = grid10_fully_capable(fabric)
    cond_b = swarm_genuinely_stalled(fabric, hours_threshold)
    cond_progress_gate = cond_a or cond_b
    cond_data = all_examples_fully_revised(revision_db_path, example_ids, required_revisions)

    if not cond_progress_gate:
        return False, (
            "BLOCKED: neither condition (a) GRID10 fully done nor (b) genuine "
            f">= {hours_threshold}h stall is currently true"
        )
    if not cond_data:
        return False, (
            "BLOCKED: training data precondition not met -- not every named example "
            f"has {required_revisions} documented, sequential revisions yet"
        )
    reason = "GRID10_FULLY_DONE" if cond_a else "GENUINE_MULTI_HOUR_STALL"
    return True, f"ALLOWED: progress condition={reason}, all {len(example_ids)} examples fully revised"


def attempt_training_run(fabric: Fabric, revision_db_path: Path, example_ids: list[str],
                          marker_path: Path, hours_threshold: float = DEFAULT_STALL_HOURS,
                          required_revisions: int = REQUIRED_REVISIONS_PER_EXAMPLE,
                          log_fn=None) -> dict[str, Any]:
    """The ONLY function in this codebase permitted to write
    TRAINING_RUN_READY_FOR_LAUNCH.json. Raises TrainingRunBlocked (does NOT
    silently no-op) if the real precondition is not met -- callers (the
    Bauleiter loop) should catch this and simply continue normal work,
    trying again on a later cycle, never treating a blocked attempt as an
    error worth stopping the whole run over.

    Does NOT call the Together API itself -- writing the marker only makes
    the eventual real API call POSSIBLE for a human-reviewed next step,
    matching this whole session's established rule that a paid training
    run is always a deliberate, separately-authorized action."""
    allowed, reason = training_run_technically_possible(
        fabric, revision_db_path, example_ids, hours_threshold, required_revisions
    )
    if log_fn:
        log_fn(f"TRAINING_GATE_CHECK allowed={allowed} reason={reason}")
    if not allowed:
        raise TrainingRunBlocked(reason)

    marker_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "TRAINING_RUN_READY_FOR_LAUNCH/v1",
        "reason": reason,
        "example_ids": example_ids,
        "required_revisions_per_example": required_revisions,
        "revision_counts": {eid: example_revision_count(revision_db_path, eid) for eid in example_ids},
        "written_ts": time.time(),
        "note": "Marker only -- the Together API call itself still requires a separate, "
                "human-reviewed action. See frankenstein_training_gate_v1.py module docstring.",
    }
    marker_path.write_text(json.dumps(payload, indent=2))
    if log_fn:
        log_fn(f"TRAINING_RUN_READY_FOR_LAUNCH_WRITTEN {marker_path}")
    return payload
