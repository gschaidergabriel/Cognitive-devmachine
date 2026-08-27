import sys
from pathlib import Path

import pytest

PKG_DIR = (
    Path(__file__).resolve().parents[1]
    / "research_entity/topic_packets/frankenstein-master-cognition-concept"
)
sys.path.insert(0, str(PKG_DIR))

import frankenstein_orchestrator_v1 as orch


def test_current_quarantined_donor_is_not_safe_patch_integrated():
    status = orch.authority_status()
    assert status["direct_dispatch_safe_patch_integrated"] is False


def test_entrypoint_rejects_legacy_whole_file_dispatch_donor(tmp_path, monkeypatch):
    donor = tmp_path / "donor.py"
    donor.write_text(
        "def dispatch_helper_task_direct():\n"
        "    apply_file_blocks(root, blocks)\n"
    )
    monkeypatch.setattr(orch, "QUARANTINED_IMPLEMENTATION", donor)
    with pytest.raises(SystemExit, match="legacy whole-file apply_file_blocks"):
        orch._require_safe_direct_dispatch_donor()


def test_entrypoint_accepts_only_safe_patch_dispatch_shape(tmp_path, monkeypatch):
    donor = tmp_path / "donor.py"
    donor.write_text(
        "def dispatch_helper_task_direct():\n"
        "    safe_apply_verified_patch(root, patch)\n"
    )
    monkeypatch.setattr(orch, "QUARANTINED_IMPLEMENTATION", donor)
    orch._require_safe_direct_dispatch_donor()
