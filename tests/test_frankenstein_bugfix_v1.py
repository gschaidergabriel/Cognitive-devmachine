"""Tests for the real Bugfix-Frankenstein logic (the "quarantined donor"
implementation frankenstein_bugfix_v1_PROVIDER_QUARANTINED_854f6bc.py --
same content as frankenstein-master-cognition-concept/historical_tests/
frankenstein_bugfix_v1_tests_854f6bc.py, loaded via importlib by explicit
file path since `import frankenstein_bugfix_v1` now resolves to the thin
canonical authority-gate entrypoint, not the real logic -- see
frankenstein_authority_gate_v1.py and test_frankenstein_orchestrator_v1.py's
module docstring for the same rationale.

Git-based self-versioning/rollback mechanism (real local git repo, tmp_path
-- no mocking), the two-tier baseline/checkpoint promotion logic, and the
stuck-task detection wiring against a real tmp Fabric. Network calls
(_call_one_tier / wait_for_any_tier_available) are monkeypatched.
"""
import importlib.util
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
PKG_DIR = REPO_ROOT / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(PKG_DIR))


def _load(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


from grid10_fabric import Fabric  # noqa: E402

bugfix = _load("frankenstein_bugfix_v1_real", PKG_DIR / "frankenstein_bugfix_v1_PROVIDER_QUARANTINED_854f6bc.py")


def _git(repo_dir, *args):
    return subprocess.run(["git", "-C", str(repo_dir), *args], capture_output=True, text=True, check=True)


def test_ensure_bugfix_repo_sets_immutable_ur_baseline_and_moving_checkpoint_once(tmp_path):
    repo_dir = tmp_path / "bugfix_repo"
    log_path = tmp_path / "log.txt"
    bugfix.ensure_bugfix_repo(repo_dir, log_path)
    tags = _git(repo_dir, "tag", "--list").stdout.split()
    assert bugfix.UR_BASELINE_TAG in tags
    assert bugfix.CHECKPOINT_TAG in tags
    first_baseline_sha = _git(repo_dir, "rev-list", "-n", "1", bugfix.UR_BASELINE_TAG).stdout.strip()

    (repo_dir / "some_change.txt").write_text("change")
    bugfix.bugfix_commit_after(repo_dir, "unrelated change", log_path)
    bugfix.ensure_bugfix_repo(repo_dir, log_path)
    second_baseline_sha = _git(repo_dir, "rev-list", "-n", "1", bugfix.UR_BASELINE_TAG).stdout.strip()
    assert first_baseline_sha == second_baseline_sha, "UR_BASELINE_TAG must never move once set"


def test_bugfix_commit_before_after_and_rollback_last(tmp_path):
    repo_dir = tmp_path / "bugfix_repo"
    log_path = tmp_path / "log.txt"
    bugfix.ensure_bugfix_repo(repo_dir, log_path)

    before_sha = bugfix.bugfix_commit_before(repo_dir, "attempting a fix", log_path)
    (repo_dir / "broken_fix.txt").write_text("this fix is bad")
    after_sha = bugfix.bugfix_commit_after(repo_dir, "applied a bad fix", log_path)
    assert before_sha != after_sha

    new_head = bugfix.bugfix_rollback_last(repo_dir, log_path)
    assert new_head != after_sha
    log = _git(repo_dir, "log", "--oneline").stdout
    assert "applied a bad fix" in log


def test_rollback_to_last_checkpoint_and_rollback_to_ur_baseline_are_distinct(tmp_path):
    repo_dir = tmp_path / "bugfix_repo"
    log_path = tmp_path / "log.txt"
    bugfix.ensure_bugfix_repo(repo_dir, log_path)
    baseline_sha = _git(repo_dir, "rev-parse", bugfix.UR_BASELINE_TAG).stdout.strip()

    (repo_dir / "improvement.txt").write_text("v1")
    bugfix.bugfix_commit_after(repo_dir, "improvement 1", log_path)
    _git(repo_dir, "tag", "-f", bugfix.CHECKPOINT_TAG)
    checkpoint_sha = _git(repo_dir, "rev-parse", bugfix.CHECKPOINT_TAG).stdout.strip()
    assert checkpoint_sha != baseline_sha

    (repo_dir / "improvement.txt").write_text("v2-bad")
    bugfix.bugfix_commit_after(repo_dir, "improvement 2 (bad)", log_path)

    head_after_rollback_to_checkpoint = bugfix.rollback_to_last_checkpoint(repo_dir, log_path)
    assert head_after_rollback_to_checkpoint == checkpoint_sha

    head_after_rollback_to_baseline = bugfix.rollback_to_ur_baseline(repo_dir, log_path)
    assert head_after_rollback_to_baseline == baseline_sha
    assert head_after_rollback_to_baseline != checkpoint_sha


def test_promote_checkpoint_if_strictly_better_promotes_on_all_metrics_improved(tmp_path):
    repo_dir = tmp_path / "bugfix_repo"
    log_path = tmp_path / "log.txt"
    bugfix.ensure_bugfix_repo(repo_dir, log_path)
    (repo_dir / "x.txt").write_text("better version")
    bugfix.bugfix_commit_after(repo_dir, "candidate improvement", log_path)

    promoted = bugfix.promote_checkpoint_if_strictly_better(
        repo_dir,
        metrics_before={"latency_s": 8.3, "ram_mb": 900, "error_count": 2},
        metrics_after={"latency_s": 6.1, "ram_mb": 850, "error_count": 0},
        metric_directions={"latency_s": "lower_better", "ram_mb": "lower_better", "error_count": "lower_better"},
        log_path=log_path,
    )
    assert promoted is True
    head = _git(repo_dir, "rev-parse", "HEAD").stdout.strip()
    checkpoint = _git(repo_dir, "rev-parse", bugfix.CHECKPOINT_TAG).stdout.strip()
    assert head == checkpoint


def test_promote_checkpoint_if_strictly_better_denies_on_any_single_regression(tmp_path):
    repo_dir = tmp_path / "bugfix_repo"
    log_path = tmp_path / "log.txt"
    bugfix.ensure_bugfix_repo(repo_dir, log_path)
    checkpoint_before = _git(repo_dir, "rev-parse", bugfix.CHECKPOINT_TAG).stdout.strip()

    (repo_dir / "x.txt").write_text("mixed version")
    bugfix.bugfix_commit_after(repo_dir, "candidate with one regression", log_path)

    promoted = bugfix.promote_checkpoint_if_strictly_better(
        repo_dir,
        metrics_before={"latency_s": 8.3, "throughput_per_s": 10.0},
        metrics_after={"latency_s": 6.1, "throughput_per_s": 9.0},
        metric_directions={"latency_s": "lower_better", "throughput_per_s": "higher_better"},
        log_path=log_path,
    )
    assert promoted is False
    checkpoint_after = _git(repo_dir, "rev-parse", bugfix.CHECKPOINT_TAG).stdout.strip()
    assert checkpoint_after == checkpoint_before, "checkpoint tag must not move when even one metric regressed"


def test_call_with_explicit_fallback_walks_all_three_tiers_in_order(monkeypatch):
    calls = []

    def fake_call_one_tier(tier_label, messages, **kwargs):
        calls.append(tier_label)
        if tier_label == "mistral":
            return "success from mistral"
        return None

    monkeypatch.setattr(bugfix, "_call_one_tier", fake_call_one_tier)
    content, tier_used = bugfix.call_with_explicit_fallback([{"role": "user", "content": "hi"}])
    assert calls == ["nvidia", "groq", "mistral"]
    assert tier_used == "mistral"
    assert content == "success from mistral"


def test_call_with_explicit_fallback_raises_when_all_tiers_fail(monkeypatch):
    monkeypatch.setattr(bugfix, "_call_one_tier", lambda *a, **k: None)
    try:
        bugfix.call_with_explicit_fallback([{"role": "user", "content": "hi"}])
        assert False, "must raise AllTiersUnavailable when every tier fails"
    except bugfix.AllTiersUnavailable:
        pass


def test_wait_for_any_tier_available_never_gives_up_and_backs_off(monkeypatch, tmp_path):
    attempts = {"n": 0}

    def flaky(messages, **kwargs):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise bugfix.AllTiersUnavailable("simulated outage")
        return "recovered", "groq"

    monkeypatch.setattr(bugfix, "call_with_explicit_fallback", flaky)
    monkeypatch.setattr(time, "sleep", lambda s: None)

    content, tier = bugfix.wait_for_any_tier_available([{"role": "user", "content": "hi"}], tmp_path / "log.txt")
    assert attempts["n"] == 3
    assert content == "recovered"


def test_scan_for_stuck_work_reclaims_via_real_fabric(tmp_path):
    fabric = Fabric(tmp_path / "s1.sqlite")
    fabric.seed_scope(bugfix.BUILD_SCOPE)
    fabric.runtime_join("dead-node", "worker", pid=1)
    fabric.seed_task("stuck-task-1", bugfix.BUILD_SCOPE, 0, "worker", {"x": 1})
    snap = fabric.snapshot()
    fabric.runtime_claim_task("stuck-task-1", "dead-node", expected_epoch=snap.epoch)
    fabric.runtime_heartbeat("dead-node", healthy=False)

    reclaimed = bugfix.scan_for_stuck_work(fabric, tmp_path / "log.txt", stale_after_seconds=0.0)
    assert reclaimed == ["stuck-task-1"]


def test_poll_intensity_regulator_read_default_and_bump(tmp_path):
    fabric = Fabric(tmp_path / "s1.sqlite")
    assert bugfix._read_poll_intensity(fabric) == 1.0
    bugfix._bump_poll_intensity(fabric, 3.0)
    assert bugfix._read_poll_intensity(fabric) == 3.0
