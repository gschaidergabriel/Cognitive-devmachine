import hashlib
import importlib.util
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = REPO_ROOT / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept"
sys.path.insert(0, str(PKG_DIR))

spec = importlib.util.spec_from_file_location(
    "frankenstein_orchestrator_v1_mutation_audit_test",
    PKG_DIR / "frankenstein_orchestrator_v1.py",
)
entry = importlib.util.module_from_spec(spec)
sys.modules["frankenstein_orchestrator_v1_mutation_audit_test"] = entry
spec.loader.exec_module(entry)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_sources(tmp_path: Path):
    donor = tmp_path / "donor.py"
    patch_guard = tmp_path / "patch_guard.py"
    preimage_guard = tmp_path / "preimage_guard.py"
    donor.write_text("DONOR = 'integrated fixture'\n")
    patch_guard.write_text("PATCH_GUARD = True\n")
    preimage_guard.write_text("PREIMAGE_GUARD = True\n")
    return donor, patch_guard, preimage_guard


def bind_paths(monkeypatch, donor, patch_guard, preimage_guard):
    monkeypatch.setattr(entry, "QUARANTINED_IMPLEMENTATION", donor)
    monkeypatch.setattr(entry, "PATCH_GUARD", patch_guard)
    monkeypatch.setattr(entry, "PREIMAGE_EDIT_GUARD", preimage_guard)


def bind_hashes(monkeypatch, donor, patch_guard, preimage_guard):
    monkeypatch.setattr(entry, "AUDITED_DONOR_SHA256", digest(donor))
    monkeypatch.setattr(entry, "AUDITED_PATCH_GUARD_SHA256", digest(patch_guard))
    monkeypatch.setattr(entry, "AUDITED_PREIMAGE_EDIT_GUARD_SHA256", digest(preimage_guard))


def test_current_source_fails_closed_with_no_audited_identities():
    state = entry.mutation_audit_state()
    assert entry.AUDITED_DONOR_SHA256 is None
    assert entry.AUDITED_PATCH_GUARD_SHA256 is None
    assert entry.AUDITED_PREIMAGE_EDIT_GUARD_SHA256 is None
    assert state["mutation_audit_admitted"] is False
    assert state["runtime_promotion"] == "NONE"
    with pytest.raises(entry.UnsafeMutationDonorBlocked):
        entry.require_mutation_audited_donor()


def test_exact_triplet_admits_only_matching_sources(tmp_path, monkeypatch):
    donor, patch_guard, preimage_guard = make_sources(tmp_path)
    bind_paths(monkeypatch, donor, patch_guard, preimage_guard)
    bind_hashes(monkeypatch, donor, patch_guard, preimage_guard)
    state = entry.require_mutation_audited_donor()
    assert state["mutation_audit_admitted"] is True
    assert state["all_required_sources_present"] is True


@pytest.mark.parametrize("changed", ["donor", "patch_guard", "preimage_guard"])
def test_any_post_audit_source_change_fails_closed(tmp_path, monkeypatch, changed):
    donor, patch_guard, preimage_guard = make_sources(tmp_path)
    bind_paths(monkeypatch, donor, patch_guard, preimage_guard)
    bind_hashes(monkeypatch, donor, patch_guard, preimage_guard)
    target = {"donor": donor, "patch_guard": patch_guard, "preimage_guard": preimage_guard}[changed]
    target.write_text(target.read_text() + "# changed after audit\n")
    assert entry.mutation_audit_state()["mutation_audit_admitted"] is False
    with pytest.raises(entry.UnsafeMutationDonorBlocked):
        entry.require_mutation_audited_donor()


@pytest.mark.parametrize("missing", ["donor", "patch_guard", "preimage_guard"])
def test_any_missing_required_source_fails_closed(tmp_path, monkeypatch, missing):
    donor, patch_guard, preimage_guard = make_sources(tmp_path)
    bind_paths(monkeypatch, donor, patch_guard, preimage_guard)
    bind_hashes(monkeypatch, donor, patch_guard, preimage_guard)
    target = {"donor": donor, "patch_guard": patch_guard, "preimage_guard": preimage_guard}[missing]
    target.unlink()
    state = entry.mutation_audit_state()
    assert state["all_required_sources_present"] is False
    assert state["mutation_audit_admitted"] is False


def test_authority_status_exposes_nonpromoting_mutation_gate():
    status = entry.authority_status()
    gate = status["mutation_audit_gate"]
    assert gate["schema"] == "FRANKENSTEIN_MUTATION_AUDIT_GATE/v1"
    assert gate["runtime_promotion"] == "NONE"
    assert gate["mutation_audit_admitted"] is False
