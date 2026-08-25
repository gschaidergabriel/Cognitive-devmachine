from __future__ import annotations

from copy import deepcopy
import json

import pytest

from tools.trigger2_fused_membership_two_phase_adapter_v1 import (
    AdapterError,
    attach_two_phase_authority,
    atomic_fused_two_phase_commit,
    atomic_fused_two_phase_source_fixture_commit,
    validate_two_phase_cohort,
)
from tools.trigger2_grid10_fused_physical_membership_cohort_acceptance_v1 import (
    FusedFabric,
    N,
    SCOPE,
    dg,
    snapshot_identity,
)
from tools.trigger2_node_result_model_call_two_phase_authority_v1 import (
    SCHEMA as PHASE_SCHEMA,
    canonical_sha256,
)


def _phase_hash(label: str) -> str:
    return dg({"label": label})


def _packet(start, node_id: str, task: dict, pid: int) -> dict:
    payload = {
        "node": node_id,
        "process_pid": pid,
        "task_id": task["task_id"],
        "observation": f"source-fixture:{node_id}",
        "useful": True,
    }
    task_digest = dg(task)
    receipt_core = {
        "producer_pid": pid,
        "source_node_id": node_id,
        "consumed_state_epoch": start.epoch,
        "consumed_state_digest": start.state_digest,
        "consumed_generation": start.generation,
        "consumed_task_digest": task_digest,
        "payload_digest": dg(payload),
    }
    core = {
        "schema": "NODE_RESULT/v1",
        "source_kind": "ORDINARY_NODE",
        "source_node_id": node_id,
        "scope": SCOPE,
        "generation": start.generation,
        "state_epoch": start.epoch,
        "state_digest": start.state_digest,
        "producer_pid": pid,
        "consumed_state_epoch": start.epoch,
        "consumed_state_digest": start.state_digest,
        "consumed_generation": start.generation,
        "consumed_task_digest": task_digest,
        "read_receipt_digest": dg(receipt_core),
        "payload": payload,
    }
    return {**core, "packet_digest": dg(core), "s1_write_intent": False}


def _phase_authority(packet: dict, membership: dict, idx: int) -> dict:
    # Equal call/output content across members is intentional: invocation multiplicity is
    # carried by launch + executor observation, not by content/evidence digest inequality.
    body = {
        "schema": PHASE_SCHEMA,
        "raw_node_result_packet_digest": packet["packet_digest"],
        "source_bound_model_call_identity_sha256": _phase_hash("shared-call-content"),
        "model_output_identity_sha256": _phase_hash("shared-model-output"),
        "abi_v2_receipt_sha256": _phase_hash(f"abi-{idx}"),
        "source_identity_sha256": _phase_hash("source"),
        "launch_descriptor_sha256": _phase_hash(f"launch-{idx}"),
        "executor_observation_sha256": _phase_hash(f"executor-observation-{idx}"),
        "cohort_plan_id": _phase_hash("plan"),
        "grid_cell_id": f"cell-{idx:02d}",
        "controller_observed_node_id": packet["source_node_id"],
        "controller_observed_pid": packet["producer_pid"],
        "source_node_admission_id": membership["membership_id"],
        "source_node_admission_revision": membership["serial"],
        "source_runtime_generation": membership["generation"],
        "raw_generation": packet["generation"],
        "raw_state_epoch": packet["state_epoch"],
        "raw_state_digest": packet["state_digest"],
    }
    return {
        **body,
        "authority_envelope_sha256": canonical_sha256(body),
        "model_generated": False,
        "canonical_truth": False,
        "effect_authority": False,
        "credit_boundary": {},
    }


def _synthetic_source_proof(start, envelopes: list[dict]) -> dict:
    # This is deliberately a deterministic source-path fixture, NOT physical GRID10 evidence.
    # The real FusedFabric commit code is exercised, but no OS-process/procfs claim is minted.
    return {
        "all_alive_at_barrier": True,
        "distinct_os_pids": N,
        "parent_child_pid_binding": True,
        "same_snapshot_identity": True,
        "all_transactions_open_at_barrier": True,
        "all_hold_readonly_s1_fd_at_barrier": True,
        "writer_free_identity_stable": True,
        "process_intervals_overlap_release": True,
        "synthetic_source_fixture_only": True,
        "ready_by_node": {
            envelope["node_result"]["source_node_id"]: {
                "pid": envelope["node_result"]["producer_pid"],
                "read_receipt_digest": envelope["node_result"]["read_receipt_digest"],
                "generation": start.generation,
                "state_epoch": start.epoch,
                "state_digest": start.state_digest,
            }
            for envelope in envelopes
        },
    }


def _structural_members(envelopes: list[dict]) -> list[dict]:
    return [
        {
            "source_node_id": envelope["node_result"]["source_node_id"],
            "source_membership_id": envelope["source_membership_id"],
            "producer_pid": int(envelope["node_result"]["producer_pid"]),
            "node_result_digest": envelope["node_result_digest"],
            "envelope_digest": envelope["envelope_digest"],
        }
        for envelope in envelopes
    ]


def _fixture(tmp_path, label: str):
    fabric = FusedFabric(tmp_path / f"{label}.sqlite")
    node_ids = [f"x{i:02d}" for i in range(1, N + 1)]
    memberships = {
        node_id: fabric.runtime_register_node(node_id, "reason")
        for node_id in node_ids
    }
    fabric.seed_scope(SCOPE)
    for i in range(N):
        fabric.seed_task(f"t{i:02d}", SCOPE, 100 - i, "reason", {"q": i})
    lease, token = fabric.elect_coordinator(SCOPE)
    start = fabric.snapshot()
    membership_start = fabric.membership_snapshot()

    tasks = {task["task_id"]: task for task in start.tasks}
    base_envelopes: list[dict] = []
    extended_envelopes: list[dict] = []
    for idx, node_id in enumerate(node_ids, 1):
        task = tasks[f"t{idx - 1:02d}"]
        packet = _packet(start, node_id, task, 9000 + idx)
        membership = memberships[node_id]
        base = fabric.make_envelope(packet, membership["membership_id"])
        extended = attach_two_phase_authority(
            base,
            _phase_authority(packet, membership, idx),
        )
        base_envelopes.append(base)
        extended_envelopes.append(extended)

    proof = _synthetic_source_proof(start, extended_envelopes)
    cohort_id = fabric.derive_cohort_id(
        _structural_members(extended_envelopes),
        lease=lease,
        expected_identity=snapshot_identity(start),
        membership_digest=membership_start["digest"],
    )
    return {
        "fabric": fabric,
        "lease": lease,
        "token": token,
        "start": start,
        "membership_start": membership_start,
        "base_envelopes": base_envelopes,
        "extended_envelopes": extended_envelopes,
        "proof": proof,
        "cohort_id": cohort_id,
    }


def _commit(fx, envelopes: list[dict]):
    start = fx["start"]
    return atomic_fused_two_phase_source_fixture_commit(
        fx["fabric"],
        envelopes=envelopes,
        lease=fx["lease"],
        token=fx["token"],
        proof=fx["proof"],
        expected_generation=start.generation,
        expected_epoch=start.epoch,
        expected_digest=start.state_digest,
        expected_membership_digest=fx["membership_start"]["digest"],
        expected_cohort_id=fx["cohort_id"],
    )


def _reseal_phase(phase: dict) -> dict:
    out = deepcopy(phase)
    body = {
        key: out[key]
        for key in out
        if key
        not in (
            "authority_envelope_sha256",
            "model_generated",
            "canonical_truth",
            "effect_authority",
            "credit_boundary",
        )
    }
    out["authority_envelope_sha256"] = canonical_sha256(body)
    return out


def _reseal_proof(envelope: dict) -> dict:
    out = deepcopy(envelope)
    core = {key: out[key] for key in out if key != "envelope_digest"}
    out["envelope_digest"] = dg(core)
    return out


def test_resealed_two_phase_authority_is_persisted_by_real_fusedfabric_and_replay_is_zero(tmp_path):
    fx = _fixture(tmp_path, "positive")
    fabric: FusedFabric = fx["fabric"]
    try:
        forward_validation = validate_two_phase_cohort(fx["extended_envelopes"])
        reverse_validation = validate_two_phase_cohort(list(reversed(fx["extended_envelopes"])))
        assert forward_validation["validation_digest_sha256"] == reverse_validation["validation_digest_sha256"]

        reverse_cohort_id = fabric.derive_cohort_id(
            _structural_members(list(reversed(fx["extended_envelopes"]))),
            lease=fx["lease"],
            expected_identity=snapshot_identity(fx["start"]),
            membership_digest=fx["membership_start"]["digest"],
        )
        assert reverse_cohort_id == fx["cohort_id"]

        first = _commit(fx, fx["extended_envelopes"])
        assert first["physical_witness_admitted"] is False
        assert first["source_fixture_receipt"]["evidence_class"] == "SOURCE_FIXTURE_ONLY"
        assert first["source_fixture_receipt"]["physical_grid10_runtime_credit"] == 0
        fused = first["fused_coordinator_receipt"]
        assert fused["replay"] is False
        assert fused["state_delta"] == 1
        assert fused["cohort_id"] == fx["cohort_id"]

        row = fabric.con.execute(
            "SELECT envelope_digests_json FROM fused_cohort_admissions WHERE cohort_id=?",
            (fx["cohort_id"],),
        ).fetchone()
        assert row is not None
        canonical_members = sorted(
            _structural_members(fx["extended_envelopes"]),
            key=lambda member: (
                member["source_node_id"],
                member["node_result_digest"],
                member["source_membership_id"],
            ),
        )
        persisted = json.loads(row["envelope_digests_json"])
        assert persisted == [member["envelope_digest"] for member in canonical_members]
        assert persisted != [
            envelope["envelope_digest"] for envelope in fx["base_envelopes"]
        ]

        replay_result = _commit(fx, fx["extended_envelopes"])
        assert replay_result["source_fixture_receipt"]["evidence_class"] == "SOURCE_FIXTURE_ONLY"
        replay = replay_result["fused_coordinator_receipt"]
        assert replay["replay"] is True
        assert replay["state_delta"] == 0
        assert fabric.snapshot().epoch == fx["start"].epoch + 1
    finally:
        fabric.close()


def test_all_true_synthetic_source_proof_cannot_enter_physical_adapter_or_mutate(tmp_path):
    fx = _fixture(tmp_path, "raw-proof-physical-reject")
    fabric: FusedFabric = fx["fabric"]
    try:
        start = fx["start"]
        before_epoch = fabric.snapshot().epoch
        with pytest.raises(AdapterError, match="^RAW_PHYSICAL_COHORT_PROOF_NOT_ADMITTED$"):
            atomic_fused_two_phase_commit(
                fabric,
                envelopes=fx["extended_envelopes"],
                lease=fx["lease"],
                token=fx["token"],
                proof=fx["proof"],
                expected_generation=start.generation,
                expected_epoch=start.epoch,
                expected_digest=start.state_digest,
                expected_membership_digest=fx["membership_start"]["digest"],
                expected_cohort_id=fx["cohort_id"],
            )

        assert fabric.snapshot().epoch == before_epoch
        assert (
            fabric.con.execute("SELECT COUNT(*) AS n FROM fused_cohort_admissions").fetchone()["n"]
            == 0
        )
        assert (
            fabric.con.execute("SELECT COUNT(*) AS n FROM admitted_results").fetchone()["n"]
            == 0
        )
    finally:
        fabric.close()


def test_transplanted_membership_authority_fails_before_real_fusedfabric_mutation(tmp_path):
    fx = _fixture(tmp_path, "negative")
    fabric: FusedFabric = fx["fabric"]
    try:
        before_epoch = fabric.snapshot().epoch
        bad = deepcopy(fx["extended_envelopes"])
        phase = deepcopy(
            bad[0]["authority_extensions"]["two_phase_model_call_authority"]
        )
        phase["source_node_admission_id"] = bad[1]["source_membership_id"]
        bad[0]["authority_extensions"]["two_phase_model_call_authority"] = _reseal_phase(phase)
        bad[0] = _reseal_proof(bad[0])

        with pytest.raises(AdapterError, match="^TWO_PHASE_ADMISSION_MEMBERSHIP_ID_MISMATCH$"):
            _commit(fx, bad)

        assert fabric.snapshot().epoch == before_epoch
        assert (
            fabric.con.execute("SELECT COUNT(*) AS n FROM fused_cohort_admissions").fetchone()["n"]
            == 0
        )
        assert (
            fabric.con.execute("SELECT COUNT(*) AS n FROM admitted_results").fetchone()["n"]
            == 0
        )
    finally:
        fabric.close()
