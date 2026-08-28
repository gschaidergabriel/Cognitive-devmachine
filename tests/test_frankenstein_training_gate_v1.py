"""Tests for the hard, code-enforced training-run precondition gate
(Gabriel's direct 2026-08-28 instruction: the ONE authorized Together run
may only become technically possible once (a) GRID10 is fully done OR (b)
the swarm has genuinely stalled for hours, AND every named training example
has 30 real, documented, sequential revisions -- enforced in code, not just
as a model instruction). Real tmp Fabric + real tmp sqlite revision log, no
mocking of the enforcement logic itself.
"""
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
PKG_DIR = Path(__file__).resolve().parents[1] / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(PKG_DIR))

from grid10_fabric import Fabric  # noqa: E402
import frankenstein_packages_v1 as packages  # noqa: E402
import frankenstein_training_gate_v1 as gate  # noqa: E402


def _fabric(tmp_path):
    return Fabric(tmp_path / "s1.sqlite")


def _revise_n_times(db_path, example_id, n, note_prefix="reviewed carefully and confirmed correct"):
    for i in range(n):
        gate.record_revision(db_path, example_id, "reviewer-1", f"{note_prefix} pass {i+1}",
                              before_text=f"before-{i}", after_text=f"after-{i}")
        time.sleep(gate.MIN_SECONDS_BETWEEN_REVISIONS)


# ---- revision log enforcement ----

def test_record_revision_rejects_short_note(tmp_path):
    db = tmp_path / "revisions.sqlite3"
    try:
        gate.record_revision(db, "ex-1", "reviewer", "ok", "a", "b")
        assert False, "must reject a rubber-stamp-length note"
    except gate.RevisionRejected:
        pass
    assert gate.example_revision_count(db, "ex-1") == 0


def test_record_revision_sequential_numbering(tmp_path):
    db = tmp_path / "revisions.sqlite3"
    r1 = gate.record_revision(db, "ex-1", "reviewer", "first real careful review pass of this example", "a", "b")
    assert r1["revision_number"] == 1
    time.sleep(gate.MIN_SECONDS_BETWEEN_REVISIONS)
    r2 = gate.record_revision(db, "ex-1", "reviewer", "second real careful review pass, fixed a typo", "b", "c")
    assert r2["revision_number"] == 2


def test_record_revision_rejects_too_fast_second_pass(tmp_path):
    db = tmp_path / "revisions.sqlite3"
    gate.record_revision(db, "ex-1", "reviewer", "first real careful review pass of this example", "a", "b")
    try:
        gate.record_revision(db, "ex-1", "reviewer", "instant second pass right after the first one", "b", "c")
        assert False, "must reject a revision arriving faster than MIN_SECONDS_BETWEEN_REVISIONS"
    except gate.RevisionRejected:
        pass
    assert gate.example_revision_count(db, "ex-1") == 1


def test_record_revision_cannot_replay_same_number(tmp_path):
    db = tmp_path / "revisions.sqlite3"
    gate.record_revision(db, "ex-1", "reviewer", "first real careful review pass of this example", "a", "b")
    # Manually forge a duplicate revision_number=1 insert attempt by resetting
    # the clock check via a fresh example_id is not possible here -- instead
    # directly exercise the INTEGRITY path via sqlite3 to prove PRIMARY KEY holds.
    import sqlite3
    con = sqlite3.connect(str(db))
    try:
        con.execute(
            "INSERT INTO revisions(example_id,revision_number,reviewer,revision_note,before_hash,after_hash,ts) "
            "VALUES('ex-1',1,'attacker','forged replay of revision 1','x','y',9999999999)"
        )
        con.commit()
        assert False, "PRIMARY KEY(example_id, revision_number) must prevent a replayed/duplicate revision"
    except sqlite3.IntegrityError:
        pass
    finally:
        con.close()
    assert gate.example_revision_count(db, "ex-1") == 1


def test_is_example_fully_revised_exact_threshold(tmp_path):
    db = tmp_path / "revisions.sqlite3"
    _revise_n_times(db, "ex-1", gate.REQUIRED_REVISIONS_PER_EXAMPLE - 1)
    assert gate.is_example_fully_revised(db, "ex-1") is False
    gate.record_revision(db, "ex-1", "reviewer", "the thirtieth and final careful revision pass", "x", "y")
    assert gate.is_example_fully_revised(db, "ex-1") is True


def test_all_examples_fully_revised_requires_every_example(tmp_path):
    db = tmp_path / "revisions.sqlite3"
    _revise_n_times(db, "ex-1", gate.REQUIRED_REVISIONS_PER_EXAMPLE)
    _revise_n_times(db, "ex-2", gate.REQUIRED_REVISIONS_PER_EXAMPLE - 1)
    assert gate.all_examples_fully_revised(db, ["ex-1", "ex-2"]) is False
    gate.record_revision(db, "ex-2", "reviewer", "the thirtieth and final careful revision pass", "x", "y")
    assert gate.all_examples_fully_revised(db, ["ex-1", "ex-2"]) is True


def test_all_examples_fully_revised_empty_list_is_never_vacuously_true(tmp_path):
    db = tmp_path / "revisions.sqlite3"
    assert gate.all_examples_fully_revised(db, []) is False


# ---- progress-condition enforcement ----

def test_grid10_fully_capable_false_until_all_packages_done(tmp_path):
    f = _fabric(tmp_path)
    packages.seed_all_packages(f)
    assert gate.grid10_fully_capable(f) is False
    for pid in packages._all_package_ids():
        packages.mark_package_done(f, pid, ok=True, node_id="tester")
    assert gate.grid10_fully_capable(f) is True


def test_swarm_genuinely_stalled_false_when_no_progress_marker_yet(tmp_path):
    f = _fabric(tmp_path)
    assert gate.swarm_genuinely_stalled(f, hours_threshold=0.001) is False


def test_swarm_genuinely_stalled_true_after_threshold_elapsed(tmp_path):
    f = _fabric(tmp_path)
    gate.bump_progress_marker(f, "tester")
    assert gate.swarm_genuinely_stalled(f, hours_threshold=0.0) is True
    assert gate.swarm_genuinely_stalled(f, hours_threshold=100.0) is False


def test_mark_package_done_bumps_progress_marker(tmp_path):
    f = _fabric(tmp_path)
    packages.seed_all_packages(f)
    before = f.get_regulator(gate.LAST_PROGRESS_REGULATOR, default=None)
    assert before is None
    first_pkg_id = packages._all_package_ids()[0]
    packages.mark_package_done(f, first_pkg_id, ok=True, node_id="tester")
    after = f.get_regulator(gate.LAST_PROGRESS_REGULATOR, default=None)
    assert after is not None


# ---- combined precondition + marker-writing ----

def test_training_run_technically_possible_false_when_neither_progress_condition_holds(tmp_path):
    f = _fabric(tmp_path)
    packages.seed_all_packages(f)
    db = tmp_path / "revisions.sqlite3"
    _revise_n_times(db, "ex-1", gate.REQUIRED_REVISIONS_PER_EXAMPLE)
    allowed, reason = gate.training_run_technically_possible(f, db, ["ex-1"])
    assert allowed is False
    assert "neither condition" in reason


def test_training_run_technically_possible_false_when_data_not_fully_revised(tmp_path):
    f = _fabric(tmp_path)
    packages.seed_all_packages(f)
    for pid in packages._all_package_ids():
        packages.mark_package_done(f, pid, ok=True, node_id="tester")
    db = tmp_path / "revisions.sqlite3"
    _revise_n_times(db, "ex-1", 5)  # far short of 30
    allowed, reason = gate.training_run_technically_possible(f, db, ["ex-1"])
    assert allowed is False
    assert "not met" in reason


def test_training_run_technically_possible_true_when_grid10_done_and_data_revised(tmp_path):
    f = _fabric(tmp_path)
    packages.seed_all_packages(f)
    for pid in packages._all_package_ids():
        packages.mark_package_done(f, pid, ok=True, node_id="tester")
    db = tmp_path / "revisions.sqlite3"
    _revise_n_times(db, "ex-1", gate.REQUIRED_REVISIONS_PER_EXAMPLE)
    allowed, reason = gate.training_run_technically_possible(f, db, ["ex-1"])
    assert allowed is True
    assert "GRID10_FULLY_DONE" in reason


def test_training_run_technically_possible_true_when_genuinely_stalled_and_data_revised(tmp_path):
    f = _fabric(tmp_path)
    packages.seed_all_packages(f)
    gate.bump_progress_marker(f, "tester")
    db = tmp_path / "revisions.sqlite3"
    _revise_n_times(db, "ex-1", gate.REQUIRED_REVISIONS_PER_EXAMPLE)
    allowed, reason = gate.training_run_technically_possible(f, db, ["ex-1"], hours_threshold=0.0)
    assert allowed is True
    assert "GENUINE_MULTI_HOUR_STALL" in reason


def test_attempt_training_run_raises_and_writes_nothing_when_blocked(tmp_path):
    f = _fabric(tmp_path)
    packages.seed_all_packages(f)
    db = tmp_path / "revisions.sqlite3"
    marker = tmp_path / "TRAINING_RUN_READY_FOR_LAUNCH.json"
    try:
        gate.attempt_training_run(f, db, ["ex-1"], marker)
        assert False, "must raise TrainingRunBlocked, not silently no-op"
    except gate.TrainingRunBlocked:
        pass
    assert not marker.exists()


def test_attempt_training_run_writes_marker_only_when_genuinely_allowed(tmp_path):
    f = _fabric(tmp_path)
    packages.seed_all_packages(f)
    for pid in packages._all_package_ids():
        packages.mark_package_done(f, pid, ok=True, node_id="tester")
    db = tmp_path / "revisions.sqlite3"
    _revise_n_times(db, "ex-1", gate.REQUIRED_REVISIONS_PER_EXAMPLE)
    marker = tmp_path / "TRAINING_RUN_READY_FOR_LAUNCH.json"

    payload = gate.attempt_training_run(f, db, ["ex-1"], marker)
    assert marker.exists()
    assert payload["example_ids"] == ["ex-1"]
    assert payload["revision_counts"]["ex-1"] == gate.REQUIRED_REVISIONS_PER_EXAMPLE

    import json
    on_disk = json.loads(marker.read_text())
    assert on_disk["schema"] == "TRAINING_RUN_READY_FOR_LAUNCH/v1"
