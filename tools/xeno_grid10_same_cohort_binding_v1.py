#!/usr/bin/env python3
"""Fail-closed same-cohort binding acceptance for physical GRID10.

This layer closes a proof-splicing gap in ``xeno_physical_grid10_acceptance_v2``:
the ten simultaneously live barrier processes must be the causal evidence cohort later
consumed by coordinator integration. It does not relabel their original observations as
current after S1 advances. Instead, exact immutable NODE_RESULT packet digests and their
original snapshot identity are preserved inside fresh coordinator summaries.

Local PASS is deterministic component/source evidence only. It mints no repository-bound
physical GRID10, HCU, EntityOS, J-Space, training, canonical-truth, or effect credit.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import Any

from xeno_physical_grid10_acceptance_v2 import (
    ExactSnapshotFabric,
    N,
    concurrent_probe,
)
from xeno_self_organizing_fabric_acceptance_v1 import (
    FabricError,
    coordinator_summary,
    dg,
)

SCHEMA = "XENO_GRID10_SAME_COHORT_BINDING_ACCEPTANCE/v1"
PROTOCOL = "PRESERVED_COHORT_EVIDENCE_TO_CURRENT_COORDINATOR_SUMMARY/v1"


def _packet_core(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        k: packet[k]
        for k in packet
        if k not in ("packet_digest", "s1_write_intent")
    }


def _expect_error(fn, code: str) -> None:
    got = None
    try:
        fn()
    except FabricError as exc:
        got = str(exc)
    if got != code:
        raise AssertionError(f"expected {code}, got {got}")


def verify_same_cohort_packets(
    packets: list[dict[str, Any]],
    proof: dict[str, Any],
    expected_scopes: dict[str, str],
) -> dict[str, Any]:
    """Bind barrier PID/process evidence to the exact NODE_RESULT packet set."""
    if len(packets) != N:
        raise FabricError("COHORT_PACKET_COUNT_INVALID")

    ready = proof.get("ready")
    if not isinstance(ready, list) or len(ready) != N:
        raise FabricError("COHORT_READY_PROOF_INVALID")

    ready_by_node = {str(r["node_id"]): r for r in ready}
    if len(ready_by_node) != N:
        raise FabricError("COHORT_READY_NODE_ID_DUPLICATE")

    packet_by_node: dict[str, dict[str, Any]] = {}
    packet_digests: set[str] = set()
    snapshot_identities: set[tuple[int, int, str]] = set()

    for packet in packets:
        if packet.get("schema") != "NODE_RESULT/v1":
            raise FabricError("COHORT_PACKET_SCHEMA_INVALID")
        if packet.get("source_kind") != "ORDINARY_NODE":
            raise FabricError("COHORT_SOURCE_KIND_INVALID")
        if packet.get("s1_write_intent") is not False:
            raise FabricError("COHORT_SOURCE_PACKET_MUST_NOT_SELF_WRITE")

        node_id = str(packet.get("source_node_id"))
        if node_id in packet_by_node:
            raise FabricError("COHORT_PACKET_NODE_ID_DUPLICATE")
        if node_id not in ready_by_node:
            raise FabricError("COHORT_PACKET_NODE_NOT_IN_BARRIER")
        if packet.get("scope") != expected_scopes.get(node_id):
            raise FabricError("COHORT_SCOPE_BINDING_INVALID")

        core = _packet_core(packet)
        if packet.get("packet_digest") != dg(core):
            raise FabricError("COHORT_PACKET_DIGEST_MISMATCH")

        payload = packet.get("payload")
        if not isinstance(payload, dict):
            raise FabricError("COHORT_PAYLOAD_INVALID")
        try:
            packet_pid = int(payload["process_pid"])
            ready_pid = int(ready_by_node[node_id]["pid"])
        except (KeyError, TypeError, ValueError) as exc:
            raise FabricError("COHORT_PID_BINDING_INVALID") from exc
        if packet_pid != ready_pid:
            raise FabricError("COHORT_PID_PACKET_BINDING_MISMATCH")

        identity = (
            int(packet.get("generation")),
            int(packet.get("state_epoch")),
            str(packet.get("state_digest")),
        )
        ready_identity = (
            int(ready_by_node[node_id]["generation"]),
            int(ready_by_node[node_id]["state_epoch"]),
            str(ready_by_node[node_id]["state_digest"]),
        )
        if identity != ready_identity:
            raise FabricError("COHORT_READY_PACKET_SNAPSHOT_MISMATCH")

        packet_digest = str(packet["packet_digest"])
        if packet_digest in packet_digests:
            raise FabricError("COHORT_PACKET_DIGEST_DUPLICATE")
        packet_digests.add(packet_digest)
        snapshot_identities.add(identity)
        packet_by_node[node_id] = packet

    if len(packet_by_node) != N:
        raise FabricError("COHORT_NODE_COVERAGE_INVALID")
    if len(snapshot_identities) != 1:
        raise FabricError("COHORT_SNAPSHOT_IDENTITY_NOT_SINGLETON")

    if proof.get("distinct_os_pids") != N:
        raise FabricError("COHORT_DISTINCT_PID_PROOF_MISSING")
    if proof.get("all_alive_at_barrier") is not True:
        raise FabricError("COHORT_LIVENESS_PROOF_MISSING")
    if proof.get("pid_binding_ok") is not True:
        raise FabricError("COHORT_PARENT_PID_BINDING_MISSING")
    if proof.get("packet_pid_binding_ok") is not True:
        raise FabricError("COHORT_PACKET_PID_BINDING_MISSING")
    if proof.get("all_hold_readonly_s1_fd_at_barrier") is not True:
        raise FabricError("COHORT_READONLY_S1_FD_PROOF_MISSING")
    if proof.get("writer_free_until_barrier") is not True:
        raise FabricError("COHORT_WRITER_FREE_BARRIER_PROOF_MISSING")

    identity = next(iter(snapshot_identities))
    return {
        "packet_by_node": packet_by_node,
        "packet_digests": sorted(packet_digests),
        "snapshot_identity": {
            "generation": identity[0],
            "state_epoch": identity[1],
            "state_digest": identity[2],
        },
    }


def _summary_payload(
    *,
    scope: str,
    packets: list[dict[str, Any]],
    source_snapshot_identity: dict[str, Any],
) -> dict[str, Any]:
    ordered = sorted(packets, key=lambda p: str(p["source_node_id"]))
    return {
        "protocol": PROTOCOL,
        "scope": scope,
        "source_observation_identity": source_snapshot_identity,
        "cohort_packet_count": len(ordered),
        "cohort_packet_digests": [str(p["packet_digest"]) for p in ordered],
        "cohort_members": [
            {
                "source_node_id": str(p["source_node_id"]),
                "process_pid": int(p["payload"]["process_pid"]),
                "packet_digest": str(p["packet_digest"]),
                "observation": p["payload"],
            }
            for p in ordered
        ],
        "observation_relabelled_as_current": False,
        "canonical_truth": False,
        "effect_authority": False,
    }


def run() -> dict[str, Any]:
    tests: dict[str, bool] = {}

    with tempfile.TemporaryDirectory(prefix="xeno-grid10-same-cohort-") as td:
        root = Path(td)
        db = root / "grid10.sqlite"
        barrier = root / "barrier"
        fabric = ExactSnapshotFabric(db)
        try:
            ids = [f"x{i:02d}" for i in range(1, N + 1)]
            scopes = ["branch:a" if i % 2 == 0 else "branch:b" for i in range(N)]
            expected_scopes = dict(zip(ids, scopes, strict=True))

            for node_id in ids:
                fabric.runtime_register_node(node_id, "reason")
            for scope in ("branch:a", "branch:b", "GLOBAL"):
                fabric.seed_scope(scope)
            for i, scope in enumerate(scopes):
                fabric.seed_task(f"t{i:02d}", scope, 100 - i, "reason", {"q": i})

            source_script = Path(__file__).resolve().with_name(
                "xeno_physical_grid10_acceptance_v2.py"
            )
            cohort_packets, proof = concurrent_probe(
                script=source_script,
                db=db,
                ids=ids,
                scopes=scopes,
                barrier_dir=barrier,
            )
            verified = verify_same_cohort_packets(
                cohort_packets, proof, expected_scopes
            )
            tests["C1_SAME_COHORT_PID_PACKET_SNAPSHOT_BINDING"] = True

            # Hard negative: same logical node id but a different process identity is not the
            # barrier cohort, even if every other packet field is internally re-digested.
            disjoint = [dict(p) for p in cohort_packets]
            disjoint[0] = dict(disjoint[0])
            disjoint[0]["payload"] = dict(disjoint[0]["payload"])
            disjoint[0]["payload"]["process_pid"] = (
                int(disjoint[0]["payload"]["process_pid"]) + 1000000
            )
            disjoint[0]["packet_digest"] = dg(_packet_core(disjoint[0]))
            _expect_error(
                lambda: verify_same_cohort_packets(
                    disjoint, proof, expected_scopes
                ),
                "COHORT_PID_PACKET_BINDING_MISMATCH",
            )
            tests["C2_DISJOINT_PROCESS_COHORT_REJECTED"] = True

            # Hard negative: payload tamper with the original digest cannot silently leave the
            # integration proof unchanged.
            tampered = [dict(p) for p in cohort_packets]
            tampered[0] = dict(tampered[0])
            tampered[0]["payload"] = dict(tampered[0]["payload"])
            tampered[0]["payload"]["observation"] = "tampered-after-barrier"
            _expect_error(
                lambda: verify_same_cohort_packets(
                    tampered, proof, expected_scopes
                ),
                "COHORT_PACKET_DIGEST_MISMATCH",
            )
            tests["C3_UNUSED_PACKET_TAMPER_REJECTED"] = True

            # The original NODE_RESULT observations remain immutable evidence of their old
            # snapshot. Coordinator election advances S1, so no barrier packet is relabelled or
            # committed as if it were a current observation.
            lease_a, token_a = fabric.elect_coordinator("branch:a")
            lease_b, token_b = fabric.elect_coordinator("branch:b")

            integrated_packet_digests: set[str] = set()
            summary_receipts: list[dict[str, Any]] = []
            for scope, lease, token in (
                ("branch:a", lease_a, token_a),
                ("branch:b", lease_b, token_b),
            ):
                scoped_packets = [
                    p for p in cohort_packets if p["scope"] == scope
                ]
                payload = _summary_payload(
                    scope=scope,
                    packets=scoped_packets,
                    source_snapshot_identity=verified["snapshot_identity"],
                )
                current = fabric.snapshot()
                summary = coordinator_summary(
                    lease["node_id"], current, scope, payload
                )
                receipt = fabric.coordinator_commit(
                    lease=lease,
                    token=token,
                    packet=summary,
                    expected_epoch=current.epoch,
                    expected_digest=current.state_digest,
                )
                integrated_packet_digests.update(
                    payload["cohort_packet_digests"]
                )
                summary_receipts.append(
                    {
                        "scope": scope,
                        "summary_packet_digest": summary["packet_digest"],
                        "cohort_packet_digests": payload["cohort_packet_digests"],
                        "prior_epoch": receipt["prior_epoch"],
                        "new_epoch": receipt["new_epoch"],
                    }
                )

            tests["C4_EXACT_BARRIER_PACKET_SET_REFERENCED_BY_INTEGRATION"] = (
                integrated_packet_digests == set(verified["packet_digests"])
            )
            tests["C5_ORIGINAL_OBSERVATION_IDENTITY_PRESERVED"] = all(
                p["state_epoch"]
                == verified["snapshot_identity"]["state_epoch"]
                and p["state_digest"]
                == verified["snapshot_identity"]["state_digest"]
                for p in cohort_packets
            )
            tests["C6_NO_BARRIER_PACKET_SELF_WRITES_S1"] = all(
                p.get("s1_write_intent") is False for p in cohort_packets
            )

            passed = all(tests.values())
            return {
                "schema": SCHEMA,
                "pass": passed,
                "tests": tests,
                "cohort_protocol": PROTOCOL,
                "cohort_snapshot_identity": verified["snapshot_identity"],
                "cohort_packet_digests": verified["packet_digests"],
                "summary_receipts": summary_receipts,
                "proof_scope": {
                    "same_concurrent_process_cohort_bound_to_coordinator_evidence_set": passed,
                    "stale_observation_relabelled_as_current": False,
                    "raw_cohort_packets_directly_committed_after_epoch_advance": False,
                },
                "credit_boundary": {
                    "local_component_candidate": "PASS" if passed else "FAIL",
                    "repository_bound_physical_grid10_runtime_credit": False,
                    "whole_hcu": False,
                    "entityos_whole_runtime": False,
                    "semantic_jspace": False,
                    "training": False,
                    "canonical_truth": False,
                    "effect_authority": False,
                },
            }
        finally:
            fabric.close()


def main() -> int:
    result = run()
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
