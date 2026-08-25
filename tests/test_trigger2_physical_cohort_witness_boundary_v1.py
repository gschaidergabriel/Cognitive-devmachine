from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

import pytest

import tools.trigger2_physical_cohort_witness_boundary_v1 as boundary_module
from tools.trigger2_physical_cohort_witness_boundary_v1 import (
    N,
    PhysicalCohortWitnessBoundary,
    PhysicalWitnessError,
)


def h(label: str) -> str:
    return sha256(label.encode()).hexdigest()


class FakeFabric:
    def __init__(self):
        self.calls = 0
        self.last_proof = None
        self.last_envelopes = None

    def atomic_fused_cohort_commit(self, *, envelopes, proof, marker):
        self.calls += 1
        self.last_proof = proof
        self.last_envelopes = envelopes
        return {"cohort_id": "existing-fused-cohort", "marker": marker}


def observed_fixture():
    node_ids = [f"x{i:02d}" for i in range(1, N + 1)]
    packets = [{"packet_digest": h(f"packet-{i}")} for i in range(1, N + 1)]
    proof = {
        "all_alive_at_barrier": True,
        "distinct_os_pids": N,
        "parent_child_pid_binding": True,
        "same_snapshot_identity": True,
        "all_transactions_open_at_barrier": True,
        "all_hold_readonly_s1_fd_at_barrier": True,
        "writer_free_identity_stable": True,
        "process_intervals_overlap_release": True,
        "ready_by_node": {node: {"pid": 9000 + i} for i, node in enumerate(node_ids, 1)},
    }
    envelopes = [
        {
            "node_result_digest": packet["packet_digest"],
            "node_result": {"packet_digest": packet["packet_digest"]},
        }
        for packet in packets
    ]
    return node_ids, packets, proof, envelopes


def mint_with_stub(monkeypatch, tmp_path):
    node_ids, packets, proof, envelopes = observed_fixture()
    monkeypatch.setattr(
        boundary_module,
        "spawn_held_cohort",
        lambda fabric, script, db, node_ids, root: (packets, proof),
    )
    script = tmp_path / "observer.py"
    script.write_text("# exact fixture bytes\n", encoding="utf-8")
    db = tmp_path / "s1.sqlite"
    db.write_bytes(b"fixture-db")
    boundary = PhysicalCohortWitnessBoundary()
    fabric = FakeFabric()
    witness_packets, witness = boundary.observe(
        fabric,
        script=script,
        db=db,
        node_ids=node_ids,
        root=tmp_path / "barrier",
    )
    assert witness_packets == packets
    return boundary, fabric, witness, envelopes, proof


def test_raw_proof_dictionary_cannot_enter_physical_commit_boundary():
    boundary = PhysicalCohortWitnessBoundary()
    fabric = FakeFabric()
    _, _, proof, envelopes = observed_fixture()
    with pytest.raises(PhysicalWitnessError, match="^PHYSICAL_COHORT_WITNESS_REQUIRED$"):
        boundary.atomic_fused_physical_commit(
            fabric,
            witness=proof,  # type: ignore[arg-type]
            envelopes=envelopes,
            marker="no",
        )
    assert fabric.calls == 0


def test_synthetic_source_fixture_cannot_mint_physical_witness(monkeypatch, tmp_path):
    node_ids, packets, proof, _ = observed_fixture()
    proof["synthetic_source_fixture_only"] = True
    monkeypatch.setattr(
        boundary_module,
        "spawn_held_cohort",
        lambda fabric, script, db, node_ids, root: (packets, proof),
    )
    script = tmp_path / "observer.py"
    script.write_text("# fixture\n", encoding="utf-8")
    db = tmp_path / "s1.sqlite"
    db.write_bytes(b"x")
    boundary = PhysicalCohortWitnessBoundary()
    with pytest.raises(
        PhysicalWitnessError,
        match="^SYNTHETIC_SOURCE_FIXTURE_FORBIDDEN_AT_PHYSICAL_BOUNDARY$",
    ):
        boundary.observe(
            FakeFabric(),
            script=script,
            db=db,
            node_ids=node_ids,
            root=tmp_path / "barrier",
        )


def test_sealed_observer_witness_delegates_exactly_once(monkeypatch, tmp_path):
    boundary, fabric, witness, envelopes, proof = mint_with_stub(monkeypatch, tmp_path)
    out = boundary.atomic_fused_physical_commit(
        fabric,
        witness=witness,
        envelopes=envelopes,
        marker="ok",
    )
    assert fabric.calls == 1
    assert fabric.last_proof == proof
    assert fabric.last_envelopes == envelopes
    assert out["raw_proof_dictionary_accepted_at_physical_boundary"] is False
    assert out["fused_coordinator_receipt"]["cohort_id"] == "existing-fused-cohort"
    assert out["credit_boundary"]["physical_grid10_runtime_credit"] == 0


def test_witness_boundary_and_fabric_transplants_fail_before_delegation(monkeypatch, tmp_path):
    boundary, fabric, witness, envelopes, _ = mint_with_stub(monkeypatch, tmp_path)

    other_boundary = PhysicalCohortWitnessBoundary()
    with pytest.raises(PhysicalWitnessError, match="^PHYSICAL_WITNESS_BOUNDARY_TRANSPLANT$"):
        other_boundary.atomic_fused_physical_commit(
            fabric,
            witness=witness,
            envelopes=envelopes,
            marker="no",
        )
    assert fabric.calls == 0

    other_fabric = FakeFabric()
    with pytest.raises(PhysicalWitnessError, match="^PHYSICAL_WITNESS_FABRIC_TRANSPLANT$"):
        boundary.atomic_fused_physical_commit(
            other_fabric,
            witness=witness,
            envelopes=envelopes,
            marker="no",
        )
    assert other_fabric.calls == 0


def test_witness_tamper_fails_before_delegation(monkeypatch, tmp_path):
    boundary, fabric, witness, envelopes, _ = mint_with_stub(monkeypatch, tmp_path)
    tampered = replace(witness, proof_json='{"all_alive_at_barrier":true}')
    with pytest.raises(PhysicalWitnessError):
        boundary.atomic_fused_physical_commit(
            fabric,
            witness=tampered,
            envelopes=envelopes,
            marker="no",
        )
    assert fabric.calls == 0


def test_observed_packet_set_is_bound_to_commit_envelopes(monkeypatch, tmp_path):
    boundary, fabric, witness, envelopes, _ = mint_with_stub(monkeypatch, tmp_path)
    bad = [dict(envelope) for envelope in envelopes]
    bad[0] = {
        "node_result_digest": h("foreign-packet"),
        "node_result": {"packet_digest": h("foreign-packet")},
    }
    with pytest.raises(
        PhysicalWitnessError,
        match="^PHYSICAL_WITNESS_ENVELOPE_PACKET_SET_MISMATCH$",
    ):
        boundary.atomic_fused_physical_commit(
            fabric,
            witness=witness,
            envelopes=bad,
            marker="no",
        )
    assert fabric.calls == 0
