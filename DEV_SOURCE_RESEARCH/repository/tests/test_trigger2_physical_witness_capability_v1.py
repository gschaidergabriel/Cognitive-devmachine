from __future__ import annotations

import os
import pickle

import pytest

from tools.trigger2_physical_witness_capability_v1 import (
    N,
    PhysicalWitnessError,
    mint_barrier_witness,
    require_physical_witness,
    source_fixture_receipt,
)


def _ready():
    pid = os.getpid()
    return {f"x{i:02d}": {"pid": pid + i} for i in range(1, N + 1)}


def test_raw_all_true_mapping_is_rejected_before_physical_use():
    raw = {
        "all_alive_at_barrier": True,
        "distinct_os_pids": N,
        "parent_child_pid_binding": True,
        "same_snapshot_identity": True,
        "all_transactions_open_at_barrier": True,
        "all_hold_readonly_s1_fd_at_barrier": True,
        "writer_free_identity_stable": True,
        "process_intervals_overlap_release": True,
    }
    with pytest.raises(PhysicalWitnessError, match="^PHYSICAL_WITNESS_CAPABILITY_REQUIRED$"):
        require_physical_witness(raw)


def test_source_fixture_receipt_is_structurally_nonpromoting():
    receipt = source_fixture_receipt(state_delta=1, cohort_id="fixture")
    assert receipt["evidence_class"] == "SOURCE_FIXTURE_ONLY"
    assert receipt["physical_grid10_runtime_credit"] == 0
    assert receipt["model_runtime_credit"] == 0
    assert receipt["training_credit"] == 0
    assert receipt["canonical_truth"] is False
    assert receipt["effect_authority"] is False


def test_synthetic_flag_cannot_mint_even_before_pidfd_open():
    predicates = {
        "all_alive_at_barrier": True,
        "distinct_os_pids": N,
        "parent_child_pid_binding": True,
        "same_snapshot_identity": True,
        "all_transactions_open_at_barrier": True,
        "all_hold_readonly_s1_fd_at_barrier": True,
        "writer_free_identity_stable": True,
        "process_intervals_overlap_release": True,
        "synthetic_source_fixture_only": True,
    }
    ready = _ready()
    with pytest.raises(
        PhysicalWitnessError,
        match="^SYNTHETIC_PROOF_CANNOT_MINT_PHYSICAL_WITNESS$",
    ):
        mint_barrier_witness(
            ready_by_node=ready,
            readonly_s1_fd_binding={
                node: [{"fd": 3, "flags": os.O_RDONLY, "mnt_id": 1, "ino": 7}]
                for node in ready
            },
            s1_file_identity={"dev": 1, "ino": 7},
            required_physical_predicates=predicates,
        )


def test_constructor_is_not_a_plain_serializable_data_contract():
    from tools.trigger2_physical_witness_capability_v1 import PhysicalCohortWitness

    with pytest.raises(
        PhysicalWitnessError,
        match="^PHYSICAL_WITNESS_CONSTRUCTOR_FORBIDDEN$",
    ):
        PhysicalCohortWitness({}, tuple(), "0" * 64, object())


def test_pickle_is_forbidden_for_a_minted_shape(monkeypatch):
    import tools.trigger2_physical_witness_capability_v1 as mod

    fake_fds = iter(range(100, 100 + N))
    monkeypatch.setattr(mod, "_pidfd_supported", lambda: True)
    monkeypatch.setattr(mod.os, "pidfd_open", lambda pid, flags=0: next(fake_fds))
    monkeypatch.setattr(mod.os, "fstat", lambda fd: object())
    monkeypatch.setattr(mod.os, "close", lambda fd: None)

    predicates = {
        "all_alive_at_barrier": True,
        "distinct_os_pids": N,
        "parent_child_pid_binding": True,
        "same_snapshot_identity": True,
        "all_transactions_open_at_barrier": True,
        "all_hold_readonly_s1_fd_at_barrier": True,
        "writer_free_identity_stable": True,
        "process_intervals_overlap_release": True,
    }
    ready = _ready()
    witness = mint_barrier_witness(
        ready_by_node=ready,
        readonly_s1_fd_binding={
            node: [{"fd": 3, "flags": os.O_RDONLY, "mnt_id": 1, "ino": 7}]
            for node in ready
        },
        s1_file_identity={"dev": 1, "ino": 7},
        required_physical_predicates=predicates,
    )
    assert require_physical_witness(witness) is witness
    with pytest.raises(TypeError, match="PHYSICAL_COHORT_WITNESS_NOT_SERIALIZABLE"):
        pickle.dumps(witness)
