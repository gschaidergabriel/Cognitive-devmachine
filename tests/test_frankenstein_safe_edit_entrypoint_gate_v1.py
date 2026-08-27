import hashlib
import importlib.util
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = REPO_ROOT / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept"
sys.path.insert(0, str(PKG_DIR))

spec = importlib.util.spec_from_file_location(
    "frankenstein_orchestrator_v1_safe_entry_test",
    PKG_DIR / "frankenstein_orchestrator_v1.py",
)
entry = importlib.util.module_from_spec(spec)
sys.modules["frankenstein_orchestrator_v1_safe_entry_test"] = entry
spec.loader.exec_module(entry)


def test_current_source_fails_closed_without_audited_donor_hash():
    state = entry.safe_edit_donor_state()
    assert entry.SAFE_EDIT_AUDITED_DONOR_SHA256 is None
    assert state["safe_edit_integrated_donor_admitted"] is False
    assert state["runtime_promotion"] == "NONE"
    with pytest.raises(entry.UnsafeDonorBlocked):
        entry.require_safe_edit_integrated_donor()


def test_exact_audited_hash_admits_only_matching_donor(tmp_path, monkeypatch):
    donor = tmp_path / "donor.py"
    donor.write_text("print('safe donor fixture')\n")
    primitive = tmp_path / "frankenstein_safe_edit_v1.py"
    primitive.write_text("SAFE = True\n")
    digest = hashlib.sha256(donor.read_bytes()).hexdigest()

    monkeypatch.setattr(entry, "QUARANTINED_IMPLEMENTATION", donor)
    monkeypatch.setattr(entry, "SAFE_EDIT_PRIMITIVE", primitive)
    monkeypatch.setattr(entry, "SAFE_EDIT_AUDITED_DONOR_SHA256", digest)
    state = entry.require_safe_edit_integrated_donor()
    assert state["safe_edit_integrated_donor_admitted"] is True
    assert state["observed_donor_sha256"] == digest


def test_donor_hash_mismatch_fails_closed(tmp_path, monkeypatch):
    donor = tmp_path / "donor.py"
    donor.write_text("print('changed after audit')\n")
    primitive = tmp_path / "frankenstein_safe_edit_v1.py"
    primitive.write_text("SAFE = True\n")

    monkeypatch.setattr(entry, "QUARANTINED_IMPLEMENTATION", donor)
    monkeypatch.setattr(entry, "SAFE_EDIT_PRIMITIVE", primitive)
    monkeypatch.setattr(entry, "SAFE_EDIT_AUDITED_DONOR_SHA256", "0" * 64)
    state = entry.safe_edit_donor_state()
    assert state["safe_edit_integrated_donor_admitted"] is False
    with pytest.raises(entry.UnsafeDonorBlocked):
        entry.require_safe_edit_integrated_donor()


def test_missing_safe_edit_primitive_fails_closed_even_with_matching_hash(tmp_path, monkeypatch):
    donor = tmp_path / "donor.py"
    donor.write_text("print('fixture')\n")
    digest = hashlib.sha256(donor.read_bytes()).hexdigest()

    monkeypatch.setattr(entry, "QUARANTINED_IMPLEMENTATION", donor)
    monkeypatch.setattr(entry, "SAFE_EDIT_PRIMITIVE", tmp_path / "missing.py")
    monkeypatch.setattr(entry, "SAFE_EDIT_AUDITED_DONOR_SHA256", digest)
    assert entry.safe_edit_donor_state()["safe_edit_integrated_donor_admitted"] is False
