#!/usr/bin/env python3
"""Trigger-2 deterministic consumed-input bypass discriminator.

Purpose
-------
V46 narrows the current physical GRID10 source frontier to one question: can a producer
supply semantic payload derived from stale/unobserved cognition-relevant state while all
packet-level freshness, membership, process/barrier and cohort metadata look current?

This file is deliberately a GAP DETECTOR, not an acceptance harness. It constructs one
adversarial packet from the exact-current fused atomic-membership cohort source:

1. create an older S1 snapshot where task t00 is the highest-priority reason task;
2. advance S1 by adding a newer, higher-priority task current-winner;
3. obtain a real ten-process current physical cohort from the current source;
4. replace one current packet's semantic task selection/observation with the older
   snapshot's semantic selection while preserving its real current PID/membership/
   generation/epoch/state_digest and recomputing its ordinary packet digest;
5. derive the corresponding cohort id and ask the current atomic fan-in to admit it.

If current source admits the cohort, the discriminator succeeds in CONFIRMING the open
consumed-input gap. That is NOT a product PASS. It means current metadata/provenance gates
are insufficient to prove what cognition-relevant bytes produced the semantic payload.

No provider, model, network, paid surface, canonical truth or effect authority is used.
A successful gap detection mints ZERO physical GRID10/HCU/EntityOS/J-Space/training credit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
from typing import Any

import trigger2_grid10_atomic_membership_cohort_acceptance_v1 as current
from xeno_self_organizing_fabric_acceptance_v1 import FabricError, dg

SCHEMA = "TRIGGER2_DECLARED_CURRENT_CONSUMED_STALE_BYPASS_PROBE/v1"
SCOPE = current.SCOPE
N = current.N


def _stale_semantic_choice(snapshot: Any) -> dict[str, Any]:
    eligible = [
        task
        for task in snapshot.tasks
        if task["status"] == "OPEN"
        and task["claimed_by"] is None
        and task["capability"] == "reason"
        and task["scope"] == SCOPE
    ]
    eligible.sort(key=lambda task: (-int(task["priority"]), task["task_id"]))
    if not eligible:
        raise AssertionError("STALE_FIXTURE_HAS_NO_ELIGIBLE_TASK")
    return dict(eligible[0])


def _recompute_packet(packet: dict[str, Any]) -> dict[str, Any]:
    forged = dict(packet)
    forged["payload"] = dict(packet["payload"])
    forged["packet_digest"] = dg(current.packet_core(forged))
    return forged


def run() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="trigger2-consumed-stale-probe-") as td:
        root = Path(td)
        db = root / "probe.sqlite"
        barrier = root / "barrier"
        fabric = current.AtomicMembershipFabric(db)
        ids = [f"x{i:02d}" for i in range(1, N + 1)]
        memberships: dict[str, dict[str, Any]] = {}
        for node_id in ids:
            memberships[node_id] = fabric.runtime_register_node(node_id, "reason")
        fabric.seed_scope(SCOPE)
        for i in range(N):
            fabric.seed_task(
                f"t{i:02d}",
                SCOPE,
                100 - i,
                "reason",
                {"fixture": "old", "q": i},
            )
        lease, token = fabric.elect_coordinator(SCOPE)

        stale_snapshot = fabric.snapshot()
        stale_choice = _stale_semantic_choice(stale_snapshot)

        # This S1 mutation makes the prior semantic choice stale while preserving the same
        # logical nodes/membership incarnations and coordinator lease authority.
        fabric.seed_task(
            "current-winner",
            SCOPE,
            10_000,
            "reason",
            {"fixture": "new", "must_dominate_old_choice": True},
        )
        current_start = fabric.snapshot()

        packets, proof = current.concurrent_probe(
            Path(current.__file__).resolve(),
            db,
            ids,
            [SCOPE] * N,
            barrier,
        )
        packet_by_node = {packet["source_node_id"]: packet for packet in packets}
        victim = packet_by_node["x01"]
        actual_current_task_id = victim["payload"]["task_id"]
        stale_task_id = stale_choice["task_id"]
        if stale_task_id == actual_current_task_id:
            raise AssertionError("FIXTURE_DID_NOT_CREATE_SEMANTIC_STALENESS")

        forged_packets = [dict(packet) for packet in packets]
        for index, packet in enumerate(forged_packets):
            if packet["source_node_id"] != "x01":
                continue
            forged = _recompute_packet(packet)
            forged["payload"]["task_id"] = stale_task_id
            forged["payload"]["observation"] = "stale-derived-semantic-payload"
            forged["payload"]["semantic_source_snapshot"] = {
                "generation": stale_snapshot.generation,
                "epoch": stale_snapshot.epoch,
                "state_digest": stale_snapshot.state_digest,
            }
            # Keep the real current producer PID. This probe isolates the consumed semantic
            # input question from process/membership/barrier identity, all of which remain real.
            forged["packet_digest"] = dg(current.packet_core(forged))
            forged_packets[index] = forged
            break

        forged_victim = next(
            packet for packet in forged_packets if packet["source_node_id"] == "x01"
        )
        current_metadata_looks_valid = (
            forged_victim["generation"] == current_start.generation
            and forged_victim["state_epoch"] == current_start.epoch
            and forged_victim["state_digest"] == current_start.state_digest
            and forged_victim["source_membership_id"]
            == memberships["x01"]["membership_id"]
            and forged_victim["payload"]["process_pid"]
            == victim["payload"]["process_pid"]
            and forged_victim["packet_digest"] == dg(current.packet_core(forged_victim))
        )

        cohort_id, _ = fabric.derive_cohort_id(
            forged_packets,
            proof,
            lease,
            require_current_membership=True,
        )

        admitted = False
        admission_error: str | None = None
        receipt: dict[str, Any] | None = None
        try:
            receipt = fabric.atomic_membership_cohort_commit(
                lease=lease,
                token=token,
                packets=forged_packets,
                proof=proof,
                expected_cohort_id=cohort_id,
                expected_generation=current_start.generation,
                expected_epoch=current_start.epoch,
                expected_digest=current_start.state_digest,
            )
            admitted = True
        except FabricError as exc:
            admission_error = str(exc)
        finally:
            final_snapshot = fabric.snapshot()
            fabric.close()

        gap_confirmed = bool(
            admitted
            and current_metadata_looks_valid
            and stale_task_id != actual_current_task_id
            and forged_victim["payload"]["semantic_source_snapshot"]["state_digest"]
            != current_start.state_digest
        )

        return {
            "schema": SCHEMA,
            "discriminator_pass": gap_confirmed,
            "meaning_of_pass": "OPEN_CONSUMED_INPUT_GAP_CONFIRMED_NOT_PRODUCT_ACCEPTANCE",
            "current_contract_status": (
                "BLOCKED_CONSUMED_INPUT_NOT_INDEPENDENTLY_BOUND"
                if gap_confirmed
                else "BYPASS_REJECTED_OR_FIXTURE_INCONCLUSIVE"
            ),
            "bypass_admitted": admitted,
            "admission_error": admission_error,
            "receipt": receipt,
            "fixture": {
                "stale_snapshot": {
                    "generation": stale_snapshot.generation,
                    "epoch": stale_snapshot.epoch,
                    "state_digest": stale_snapshot.state_digest,
                },
                "current_snapshot": {
                    "generation": current_start.generation,
                    "epoch": current_start.epoch,
                    "state_digest": current_start.state_digest,
                },
                "stale_task_id": stale_task_id,
                "actual_current_task_id": actual_current_task_id,
                "forged_declared_task_id": forged_victim["payload"]["task_id"],
                "current_metadata_looks_valid": current_metadata_looks_valid,
                "physical_proof": {
                    "distinct_os_pids": proof.get("distinct_os_pids"),
                    "all_alive_at_barrier": proof.get("all_alive_at_barrier"),
                    "pid_binding_ok": proof.get("pid_binding_ok"),
                    "packet_pid_binding_ok": proof.get("packet_pid_binding_ok"),
                    "same_snapshot_identity": proof.get("same_snapshot_identity"),
                    "explicit_read_transaction": proof.get("explicit_read_transaction"),
                    "all_hold_readonly_s1_fd_at_barrier": proof.get(
                        "all_hold_readonly_s1_fd_at_barrier"
                    ),
                    "writer_free_full_probe": proof.get("writer_free_full_probe"),
                },
                "final_epoch": final_snapshot.epoch,
            },
            "hypothesis": (
                "Packet-level currentness plus process/membership/cohort identity does not prove "
                "which cognition-relevant bytes produced semantic payload unless consumed input "
                "is independently observed or forced through a deterministic read facade."
            ),
            "counterhypothesis": (
                "The exact-current producer source is trusted strongly enough that packet metadata "
                "is accepted as equivalent to consumed input, making a separate read attestation "
                "unnecessary for the promoted scope. This probe intentionally challenges that "
                "assumption by using an otherwise valid current cohort with stale-derived semantics."
            ),
            "next_gate_if_gap_confirmed": (
                "Introduce OBSERVED_READ_FACADE/v1 or an equivalent fabric-observed read-set ledger "
                "that binds the exact semantic input bytes/task identity to NODE_RESULT and is "
                "rechecked by atomic cohort admission. Add bypass/direct-read/tamper negatives."
            ),
            "credit_boundary": {
                "physical_grid10_runtime_credit": 0,
                "whole_hcu_runtime_credit": 0,
                "whole_entityos_runtime_credit": 0,
                "jspace_model_credit": 0,
                "positive_rows_admitted": 0,
                "accepted_dataset_tokens": 0,
                "training_credit": 0,
                "canonical_truth": False,
                "effect_authority": False,
            },
            "execution_authority": {
                "provider_execution_used": False,
                "network_execution_used": False,
                "paid_execution_used": False,
                "freeswarm_emergency_stop_respected": True,
            },
        }


def main() -> int:
    argparse.ArgumentParser().parse_args()
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    # Exit zero means the discriminator itself obtained a decisive answer. A confirmed gap
    # remains BLOCKED and MUST NOT be interpreted as acceptance.
    return 0 if result["discriminator_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
