from __future__ import annotations

import os

import pytest

import tools.trigger2_physical_witness_capability_v1 as mod


@pytest.mark.xfail(
    strict=True,
    reason=(
        "V68 source gap: mint_barrier_witness is still a public caller-data mint path; "
        "pidfd acquisition alone does not bind the supplied ready/fd/predicate payload "
        "to the retained spawn_held_cohort observation event"
    ),
)
def test_caller_fabricated_observation_payload_cannot_mint_physical_authority(monkeypatch):
    """Desired fail-closed law: physical authority must be observer-issued, not data-minted.

    This is a deterministic source-boundary regression.  It deliberately substitutes the
    OS handle provider so the discriminator isolates the mint API contract: if arbitrary
    caller mappings plus successful handle acquisition are enough to mint a witness, then
    provenance still comes from caller assertions rather than an unforgeable observer issue.
    No physical runtime credit is claimed by this test.
    """

    fake_pidfds = iter(range(500, 500 + mod.N))
    monkeypatch.setattr(mod, "_pidfd_supported", lambda: True)
    monkeypatch.setattr(mod.os, "pidfd_open", lambda pid, flags=0: next(fake_pidfds))
    monkeypatch.setattr(mod.os, "close", lambda fd: None)

    ready = {
        f"forged-node-{i:02d}": {
            "pid": 10000 + i,
            "read_receipt_digest": f"forged-receipt-{i:02d}",
            "generation": 7,
            "state_epoch": 11,
            "state_digest": "forged-state",
        }
        for i in range(1, mod.N + 1)
    }
    fd_binding = {
        node: [{"fd": 3, "flags": os.O_RDONLY, "mnt_id": 77, "ino": 12345}]
        for node in ready
    }
    predicates = {
        "all_alive_at_barrier": True,
        "distinct_os_pids": mod.N,
        "parent_child_pid_binding": True,
        "same_snapshot_identity": True,
        "all_transactions_open_at_barrier": True,
        "all_hold_readonly_s1_fd_at_barrier": True,
        "writer_free_identity_stable": True,
        "process_intervals_overlap_release": True,
    }

    with pytest.raises(
        mod.PhysicalWitnessError,
        match=(
            "^(PHYSICAL_WITNESS_OBSERVER_CAPABILITY_REQUIRED|"
            "PHYSICAL_WITNESS_PROVENANCE_INVALID)$"
        ),
    ):
        mod.mint_barrier_witness(
            ready_by_node=ready,
            readonly_s1_fd_binding=fd_binding,
            s1_file_identity={"dev": 9, "ino": 12345},
            required_physical_predicates=predicates,
        )
