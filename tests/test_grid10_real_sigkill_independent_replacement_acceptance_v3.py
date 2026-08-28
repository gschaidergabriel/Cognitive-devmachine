from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from grid10_real_sigkill_independent_replacement_acceptance_v3 import run_acceptance


def test_independent_replacement_process_closes_v2_proof_splice(tmp_path):
    result = run_acceptance(tmp_path)
    assert result["pass"] is True
    checks = result["checks"]
    assert checks["old_real_child_pid_bound"] is True
    assert checks["new_real_child_pid_bound"] is True
    assert checks["replacement_process_is_independent"] is True
    assert checks["old_coordinator_sigkilled"] is True
    assert checks["post_admission_pre_ack_window_proven"] is True
    assert checks["replacement_blocked_before_ttl"] is True
    assert checks["replacement_election_executed_by_new_child"] is True
    assert checks["replacement_recovery_executed_by_new_child"] is True
    assert checks["exactly_one_admission_after_recovery"] is True
    assert checks["outbox_consumed_after_recovery"] is True
    assert checks["recovery_does_not_move_s1_epoch"] is True
    assert checks["recovery_does_not_change_s1_digest"] is True
    assert checks["identical_replay_plus_zero_epoch"] is True
    assert checks["identical_replay_plus_zero_digest"] is True
    assert result["old_coordinator_pid"] != result["new_coordinator_pid"]
    assert result["new_coordinator_pid"] != result["parent_pid"]
    assert result["physical_grid10_credit"] == 0
    assert result["whole_hcu_credit"] == 0
