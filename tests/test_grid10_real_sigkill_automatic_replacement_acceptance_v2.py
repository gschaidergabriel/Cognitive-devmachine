from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from grid10_real_sigkill_automatic_replacement_acceptance_v2 import run_acceptance


def test_real_sigkill_automatic_replacement_v2(tmp_path: Path) -> None:
    result = run_acceptance(tmp_path)
    assert result["pass"] is True
    checks = result["checks"]
    assert checks["real_child_pid_bound_in_fabric"] is True
    assert checks["old_coordinator_sigkilled"] is True
    assert checks["post_admission_pre_ack_window_proven"] is True
    assert checks["replacement_blocked_before_ttl"] is True
    assert checks["replacement_elected_after_retained_ttl"] is True
    assert checks["replacement_is_different_node"] is True
    assert checks["recovery_receipt_pass"] is True
    assert checks["exactly_one_admission_after_recovery"] is True
    assert checks["outbox_consumed_after_recovery"] is True
    assert checks["recovery_does_not_move_s1_epoch"] is True
    assert checks["recovery_does_not_change_s1_digest"] is True
    assert checks["identical_replay_plus_zero_epoch"] is True
    assert checks["identical_replay_plus_zero_digest"] is True
    assert result["provider_calls"] == 0
    assert result["secret_lookups"] == 0
    assert result["physical_grid10_credit"] == 0
    assert result["whole_hcu_credit"] == 0
