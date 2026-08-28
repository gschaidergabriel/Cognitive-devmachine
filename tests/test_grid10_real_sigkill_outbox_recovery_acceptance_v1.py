from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from grid10_real_sigkill_outbox_recovery_acceptance_v1 import run_acceptance


def test_real_sigkill_replacement_coordinator_converges_exactly_once(tmp_path: Path):
    result = run_acceptance(tmp_path)
    assert result["pass"] is True
    assert result["checks"]["real_separate_coordinator_process"] is True
    assert result["checks"]["old_coordinator_sigkilled"] is True
    assert result["checks"]["post_admission_pre_ack_window_proven"] is True
    assert result["checks"]["exactly_one_admission_after_recovery"] is True
    assert result["checks"]["outbox_consumed_after_recovery"] is True
    assert result["checks"]["recovery_does_not_move_s1_epoch"] is True
    assert result["checks"]["recovery_does_not_change_s1_digest"] is True
    assert result["checks"]["identical_replay_plus_zero_epoch"] is True
    assert result["checks"]["identical_replay_plus_zero_digest"] is True
    assert result["provider_calls"] == 0
    assert result["secret_lookups"] == 0
    assert result["whole_hcu_credit"] == 0
