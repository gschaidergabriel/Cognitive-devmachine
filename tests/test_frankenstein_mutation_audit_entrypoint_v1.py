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
    contract = tmp_path / "frankenstein_edit_contract_v1.py"
    donor.write_text("DONOR = 'integrated fixture'\n")
    contract.write_text("EDIT_CONTRACT = True\n")
    return donor, contract


def bind_paths(monkeypatch, donor, contract):
    monkeypatch.setattr(entry, "QUARANTINED_IMPLEMENTATION", donor)
    monkeypatch.setattr(entry, "MUTATION_CONTRACT", contract)


def bind_hashes(monkeypatch, donor, contract):
    monkeypatch.setattr(entry, "AUDITED_DONOR_SHA256", digest(donor))
    monkeypatch.setattr(entry, "AUDITED_MUTATION_CONTRACT_SHA256", digest(contract))


def test_current_source_fails_closed_with_no_audited_identities():
    state = entry.mutation_audit_state()
    assert entry.AUDITED_DONOR_SHA256 is None
    assert entry.AUDITED_MUTATION_CONTRACT_SHA256 is None
    assert state["mutation_audit_admitted"] is False
    assert state["runtime_promotion"] == "NONE"
    with pytest.raises(entry.UnsafeMutationDonorBlocked):
        entry.require_mutation_audited_donor()


def test_exact_pair_admits_only_matching_sources(tmp_path, monkeypatch):
    donor, contract = make_sources(tmp_path)
    bind_paths(monkeypatch, donor, contract)
    bind_hashes(monkeypatch, donor, contract)
    state = entry.require_mutation_audited_donor()
    assert state["mutation_audit_admitted"] is True
    assert state["all_required_sources_present"] is True


@pytest.mark.parametrize("changed", ["donor", "mutation_contract"])
def test_any_post_audit_source_change_fails_closed(tmp_path, monkeypatch, changed):
    donor, contract = make_sources(tmp_path)
    bind_paths(monkeypatch, donor, contract)
    bind_hashes(monkeypatch, donor, contract)
    target = {"donor": donor, "mutation_contract": contract}[changed]
    target.write_text(target.read_text() + "# changed after audit\n")
    assert entry.mutation_audit_state()["mutation_audit_admitted"] is False
    with pytest.raises(entry.UnsafeMutationDonorBlocked):
        entry.require_mutation_audited_donor()


@pytest.mark.parametrize("missing", ["donor", "mutation_contract"])
def test_any_missing_required_source_fails_closed(tmp_path, monkeypatch, missing):
    donor, contract = make_sources(tmp_path)
    bind_paths(monkeypatch, donor, contract)
    bind_hashes(monkeypatch, donor, contract)
    target = {"donor": donor, "mutation_contract": contract}[missing]
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
