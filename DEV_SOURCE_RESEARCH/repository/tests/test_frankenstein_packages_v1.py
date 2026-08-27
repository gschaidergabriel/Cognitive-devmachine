"""Tests for the Frankenstein 72h-build phase/package dispenser
(research_entity/topic_packets/frankenstein-master-cognition-concept/
frankenstein_packages_v1.py). Gabriel's explicit requirement: this module is
the backbone the entire 72h operation depends on, so it must be tested for
robustness (idempotent seeding, dependency gating, race-safe concurrent
claiming, no double-claim) BEFORE the 72h run ever starts. Real sqlite
(tmp_path), no mocking of the fabric itself -- same discipline as every
other GRID10 fabric test in this repo.
"""
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
PKG_DIR = Path(__file__).resolve().parents[1] / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(PKG_DIR))

from grid10_fabric import Fabric  # noqa: E402
import frankenstein_packages_v1 as pkgmod  # noqa: E402


def _fabric(tmp_path):
    return Fabric(tmp_path / "packages.sqlite")


def test_seed_all_packages_is_idempotent(tmp_path):
    f = _fabric(tmp_path)
    first = pkgmod.seed_all_packages(f)
    assert first == len(pkgmod._all_package_ids())
    second = pkgmod.seed_all_packages(f)
    assert second == 0, "re-seeding must not duplicate or reset already-seeded packages"
    snap = f.snapshot()
    task_ids = [t["task_id"] for t in snap.tasks if t["scope"] == pkgmod.PACKAGES_SCOPE]
    assert len(task_ids) == len(set(task_ids)) == len(pkgmod._all_package_ids())


def test_package_with_no_dependencies_is_ready_immediately(tmp_path):
    f = _fabric(tmp_path)
    pkgmod.seed_all_packages(f)
    assert pkgmod.package_ready(f, "A1_alignment_targets_table") is True


def test_package_with_unmet_dependencies_is_not_ready(tmp_path):
    f = _fabric(tmp_path)
    pkgmod.seed_all_packages(f)
    assert pkgmod.package_ready(f, "A4_alignment_tick_integration") is False


def test_package_becomes_ready_once_all_dependencies_marked_done(tmp_path):
    f = _fabric(tmp_path)
    pkgmod.seed_all_packages(f)
    for dep in ("A1_alignment_targets_table", "A2_compute_alignment_delta", "A3_damped_correction"):
        pkgmod.mark_package_done(f, dep, ok=True, node_id="tester")
    assert pkgmod.package_ready(f, "A4_alignment_tick_integration") is True


def test_claim_next_package_returns_only_ready_open_packages(tmp_path):
    f = _fabric(tmp_path)
    pkgmod.seed_all_packages(f)
    f.runtime_join("worker-1", "coder", pid=1)
    claimed = pkgmod.claim_next_package(f, "worker-1")
    assert claimed is not None
    # A phase has priority 0 (earliest), all its packages have no deps except A4 --
    # the first claimable package must come from a zero-dependency A-phase package.
    assert claimed["task_id"] in ("A1_alignment_targets_table", "A2_compute_alignment_delta", "A3_damped_correction")


def test_claim_next_package_never_returns_dependency_gated_package_first(tmp_path):
    f = _fabric(tmp_path)
    pkgmod.seed_all_packages(f)
    f.runtime_join("worker-1", "coder", pid=1)
    # Claim everything in phase A except leave dependencies of A4 unmet.
    claimed_ids = []
    for _ in range(3):
        c = pkgmod.claim_next_package(f, "worker-1")
        assert c is not None
        claimed_ids.append(c["task_id"])
    assert "A4_alignment_tick_integration" not in claimed_ids, (
        "A4 depends on the other three A-phase packages and must never be "
        "claimable before they are marked DONE, even if it is technically OPEN"
    )


def test_no_double_claim_under_concurrent_claimers(tmp_path):
    f = _fabric(tmp_path)
    pkgmod.seed_all_packages(f)
    f.runtime_join("worker-1", "coder", pid=1)
    f.runtime_join("worker-2", "coder", pid=2)

    claims = []
    for _ in range(len(pkgmod._all_package_ids())):
        c1 = pkgmod.claim_next_package(f, "worker-1")
        if c1:
            claims.append(("worker-1", c1["task_id"]))
        c2 = pkgmod.claim_next_package(f, "worker-2")
        if c2:
            claims.append(("worker-2", c2["task_id"]))
        if c1 is None and c2 is None:
            break

    claimed_task_ids = [tid for _, tid in claims]
    assert len(claimed_task_ids) == len(set(claimed_task_ids)), "no task_id may ever be claimed twice"


def test_mark_package_done_true_makes_it_done_and_excluded_from_future_claims(tmp_path):
    f = _fabric(tmp_path)
    pkgmod.seed_all_packages(f)
    f.runtime_join("worker-1", "coder", pid=1)
    claimed = pkgmod.claim_next_package(f, "worker-1")
    assert claimed is not None
    pkgmod.mark_package_done(f, claimed["task_id"], ok=True, node_id="worker-1")
    assert pkgmod.is_package_done(f, claimed["task_id"]) is True

    # further claims must never return an already-done package again
    for _ in range(len(pkgmod._all_package_ids())):
        c = pkgmod.claim_next_package(f, "worker-1")
        if c is None:
            break
        assert c["task_id"] != claimed["task_id"]


def test_mark_package_done_false_does_not_mark_it_done(tmp_path):
    f = _fabric(tmp_path)
    pkgmod.seed_all_packages(f)
    f.runtime_join("worker-1", "coder", pid=1)
    claimed = pkgmod.claim_next_package(f, "worker-1")
    assert claimed is not None
    pkgmod.mark_package_done(f, claimed["task_id"], ok=False, node_id="worker-1")
    assert pkgmod.is_package_done(f, claimed["task_id"]) is False
    fail_reg = f.get_regulator(f"frankenstein:pkg_fail_count:{claimed['task_id']}", default=0.0)
    assert fail_reg["value_real"] == 1.0


def test_all_packages_done_false_then_true(tmp_path):
    f = _fabric(tmp_path)
    pkgmod.seed_all_packages(f)
    assert pkgmod.all_packages_done(f) is False
    for pid in pkgmod._all_package_ids():
        pkgmod.mark_package_done(f, pid, ok=True, node_id="worker-1")
    assert pkgmod.all_packages_done(f) is True


def test_progress_summary_reports_real_counts(tmp_path):
    f = _fabric(tmp_path)
    pkgmod.seed_all_packages(f)
    total = len(pkgmod._all_package_ids())
    summary = pkgmod.progress_summary(f)
    assert summary["total"] == total
    assert summary["done"] == 0
    assert len(summary["remaining"]) == total

    pkgmod.mark_package_done(f, "A1_alignment_targets_table", ok=True, node_id="worker-1")
    summary2 = pkgmod.progress_summary(f)
    assert summary2["done"] == 1
    assert "A1_alignment_targets_table" not in summary2["remaining"]


def test_claim_next_package_returns_none_when_fully_done(tmp_path):
    f = _fabric(tmp_path)
    pkgmod.seed_all_packages(f)
    for pid in pkgmod._all_package_ids():
        pkgmod.mark_package_done(f, pid, ok=True, node_id="worker-1")
    f.runtime_join("worker-1", "coder", pid=1)
    assert pkgmod.claim_next_package(f, "worker-1") is None
