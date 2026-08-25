from __future__ import annotations

from pathlib import Path

import pytest

import tools.trigger2_grid10_physical_cohort_witness_v2 as witness_v2
from tools.trigger2_grid10_fused_physical_membership_cohort_acceptance_v1 import FusedFabric
from tools.trigger2_grid10_physical_cohort_witness_v2 import (
    ObservedPhysicalFusedFabric,
    PHYSICAL_KIND,
    PhysicalCohortWitness,
    SCHEMA,
    SOURCE_FIXTURE_KIND,
    SourceFixtureFusedFabric,
    WitnessError,
    assert_witness_source_contract,
)


def test_public_raw_dict_cannot_enter_v2_physical_commit(tmp_path):
    fabric = ObservedPhysicalFusedFabric(tmp_path / "physical-raw.sqlite")
    try:
        before = fabric.snapshot().epoch
        with pytest.raises(WitnessError, match="^PHYSICAL_COHORT_WITNESS_REQUIRED$"):
            fabric.atomic_fused_cohort_commit(proof={})
        assert fabric.snapshot().epoch == before
        assert fabric.con.execute("SELECT COUNT(*) FROM fused_cohort_admissions").fetchone()[0] == 0
    finally:
        fabric.close()


def test_physical_witness_constructor_is_not_public_mint_surface():
    with pytest.raises(WitnessError, match="^PHYSICAL_COHORT_WITNESS_CONSTRUCTOR_FORBIDDEN$"):
        PhysicalCohortWitness(object(), {}, kind=PHYSICAL_KIND)


def test_source_fixture_path_requires_explicit_nonphysical_marker(tmp_path):
    fabric = SourceFixtureFusedFabric(tmp_path / "fixture-marker.sqlite")
    try:
        before = fabric.snapshot().epoch
        with pytest.raises(WitnessError, match="^SOURCE_FIXTURE_PROOF_MARKER_REQUIRED$"):
            fabric.atomic_fused_cohort_commit(proof={})
        assert fabric.snapshot().epoch == before
    finally:
        fabric.close()


def test_source_fixture_path_cannot_self_claim_physical_observation(tmp_path):
    fabric = SourceFixtureFusedFabric(tmp_path / "fixture-claim.sqlite")
    try:
        with pytest.raises(
            WitnessError,
            match="^SOURCE_FIXTURE_CANNOT_CLAIM_PHYSICAL_OBSERVATION$",
        ):
            fabric.atomic_fused_cohort_commit(
                proof={
                    "synthetic_source_fixture_only": True,
                    "physical_observation": True,
                }
            )
    finally:
        fabric.close()


def test_observer_output_is_sealed_then_same_instance_can_delegate_source_bytes(
    tmp_path,
    monkeypatch,
):
    observed_proof = {
        "all_alive_at_barrier": True,
        "distinct_os_pids": 10,
        "synthetic_source_fixture_only": False,
        "ready_by_node": {},
    }
    calls: dict[str, object] = {}

    def fake_observer(fabric, script, db, node_ids, root):
        calls["observer_fabric"] = fabric
        calls["observer_args"] = (script, db, tuple(node_ids), root)
        return [{"packet": "p"}], observed_proof

    def fake_parent_commit(self, *, proof, **kwargs):
        calls["delegated_fabric"] = self
        calls["delegated_proof"] = proof
        calls["delegated_kwargs"] = kwargs
        return {"cohort_id": "source-only", "replay": False, "state_delta": 1}

    monkeypatch.setattr(witness_v2, "spawn_held_cohort", fake_observer)
    monkeypatch.setattr(FusedFabric, "atomic_fused_cohort_commit", fake_parent_commit)

    fabric = ObservedPhysicalFusedFabric(tmp_path / "sealed-flow.sqlite")
    try:
        packets, witness = fabric.spawn_observed_cohort(
            script=Path("probe.py"),
            db=Path("state.sqlite"),
            node_ids=["x01"],
            root=Path("barrier"),
        )
        assert packets == [{"packet": "p"}]
        assert type(witness) is PhysicalCohortWitness
        assert witness.schema == SCHEMA
        assert witness.kind == PHYSICAL_KIND
        assert calls["observer_fabric"] is fabric

        receipt = fabric.atomic_fused_cohort_commit(
            proof=witness,
            expected_generation=7,
        )
        assert calls["delegated_fabric"] is fabric
        assert calls["delegated_proof"] == observed_proof
        assert calls["delegated_proof"] is not observed_proof
        assert calls["delegated_kwargs"] == {"expected_generation": 7}
        assert receipt["physical_witness_kind"] == PHYSICAL_KIND
        assert receipt["source_fixture_only"] is False
        assert receipt["credit_boundary"]["physical_grid10_runtime_credit_added"] == 0
    finally:
        fabric.close()


def test_source_fixture_delegation_is_explicitly_nonphysical(tmp_path, monkeypatch):
    calls: dict[str, object] = {}

    def fake_parent_commit(self, *, proof, **kwargs):
        calls["proof"] = proof
        calls["kwargs"] = kwargs
        return {"cohort_id": "fixture", "replay": False, "state_delta": 1}

    monkeypatch.setattr(FusedFabric, "atomic_fused_cohort_commit", fake_parent_commit)
    fabric = SourceFixtureFusedFabric(tmp_path / "fixture-flow.sqlite")
    try:
        raw = {"synthetic_source_fixture_only": True, "ready_by_node": {}}
        receipt = fabric.atomic_fused_cohort_commit(proof=raw, expected_epoch=11)
        assert calls["proof"] == raw
        assert calls["proof"] is not raw
        assert calls["kwargs"] == {"expected_epoch": 11}
        assert receipt["physical_witness_kind"] == SOURCE_FIXTURE_KIND
        assert receipt["source_fixture_only"] is True
        assert receipt["credit_boundary"]["source_fixture_is_physical_grid10_runtime_credit"] is False
        assert receipt["credit_boundary"]["physical_grid10_runtime_credit_added"] == 0
    finally:
        fabric.close()


def test_static_contract_preserves_single_authority_and_zero_credit():
    contract = assert_witness_source_contract()
    assert contract["pass"] is True
    assert contract["physical_commit_requires_exact_witness_type"] is True
    assert contract["source_fixture_path_explicitly_nonphysical"] is True
    assert contract["second_cohort_authority_created"] is False
    assert contract["second_state_or_effect_authority_created"] is False
    assert set(contract["credit_boundary"].values()) == {0}
