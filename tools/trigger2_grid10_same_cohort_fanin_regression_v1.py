#!/usr/bin/env python3
"""Trigger-2 deterministic regression for exact-snapshot same-cohort fan-in.

Purpose
-------
Confirm the current protocol-level discriminator identified under supervisor 8.81:
multiple NODE_RESULT packets produced by one simultaneous GRID10 cohort from one exact
S1 snapshot cannot all be admitted by repeated per-packet ExactSnapshotFabric commits,
because the first successful commit advances S1 and makes untouched siblings stale.

This is an ordinary deterministic regression. It does not promote runtime, HCU, EntityOS,
J-Space, model, training, canonical-truth, or effect-authority credit.
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
from xeno_self_organizing_fabric_acceptance_v1 import FabricError, cj

SCHEMA = "TRIGGER2_GRID10_SAME_COHORT_FANIN_REGRESSION/v1"


def expect_error(fn, code: str) -> bool:
    try:
        fn()
    except FabricError as exc:
        return str(exc) == code
    return False


def packet_identity(packet: dict[str, Any]) -> tuple[int, int, str]:
    return (
        int(packet["generation"]),
        int(packet["state_epoch"]),
        str(packet["state_digest"]),
    )


def snapshot_identity(snapshot: Any) -> tuple[int, int, str]:
    return (
        int(snapshot.generation),
        int(snapshot.epoch),
        str(snapshot.state_digest),
    )


def run() -> dict[str, Any]:
    tests: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="trigger2-grid10-fanin-neg-") as td:
        root = Path(td)
        db = root / "grid10.sqlite"
        barrier = root / "barrier"
        fabric = ExactSnapshotFabric(db)
        try:
            ids = [f"x{i:02d}" for i in range(1, N + 1)]
            scopes = ["branch:a" if i % 2 == 0 else "branch:b" for i in range(N)]
            for node_id in ids:
                fabric.runtime_register_node(node_id, "reason")
            for scope in ("branch:a", "branch:b", "GLOBAL"):
                fabric.seed_scope(scope)
            for i, scope in enumerate(scopes):
                fabric.seed_task(
                    f"t{i:02d}",
                    scope,
                    100 - i,
                    "reason",
                    {"q": i},
                )

            # Lease creation is intentionally completed BEFORE the cohort snapshot so the
            # test isolates per-result fan-in, not lease-created staleness.
            lease_a, token_a = fabric.elect_coordinator("branch:a")
            lease_b, token_b = fabric.elect_coordinator("branch:b")

            source_script = Path(__file__).with_name("xeno_physical_grid10_acceptance_v2.py")
            packets, proof = concurrent_probe(
                source_script,
                db,
                ids,
                scopes,
                barrier,
            )
            cohort_snapshot = fabric.snapshot()
            cohort_identity = snapshot_identity(cohort_snapshot)
            packet_identities = {packet_identity(p) for p in packets}

            tests["F1_TRUE_CONCURRENT_COHORT"] = bool(
                proof["distinct_os_pids"] == N
                and proof["all_alive_at_barrier"]
                and proof["pid_binding_ok"]
                and proof["packet_pid_binding_ok"]
                and proof["interval_overlap_ok"]
            )
            tests["F2_ONE_EXACT_SHARED_SNAPSHOT"] = bool(
                proof["same_snapshot_identity"]
                and proof["writer_free_full_probe"]
                and len(packet_identities) == 1
                and next(iter(packet_identities)) == cohort_identity
            )

            first = next(p for p in packets if p["scope"] == "branch:a")
            second = next(p for p in packets if p["scope"] == "branch:b")
            second_before = cj(second)

            fabric.coordinator_commit(
                lease=lease_a,
                token=token_a,
                packet=first,
                expected_epoch=cohort_snapshot.epoch,
                expected_digest=cohort_snapshot.state_digest,
            )
            after_first = fabric.snapshot()
            tests["F3_FIRST_UNTOUCHED_COHORT_PACKET_ADMITS"] = (
                after_first.epoch == cohort_snapshot.epoch + 1
            )
            tests["F4_FIRST_COMMIT_ADVANCES_S1_IDENTITY"] = (
                snapshot_identity(after_first) != cohort_identity
            )

            tests["F5_SECOND_UNTOUCHED_COHORT_PACKET_REJECTS_STALE"] = expect_error(
                lambda: fabric.coordinator_commit(
                    lease=lease_b,
                    token=token_b,
                    packet=second,
                    expected_epoch=after_first.epoch,
                    expected_digest=after_first.state_digest,
                ),
                "RESULT_STALE_EPOCH",
            )
            tests["F6_SECOND_ORIGINAL_OBSERVATION_IDENTITY_PRESERVED"] = (
                cj(second) == second_before
                and packet_identity(second) == cohort_identity
            )

            passed = all(tests.values())
            return {
                "schema": SCHEMA,
                "pass": passed,
                "tests": tests,
                "observed": {
                    "cohort_identity": cohort_identity,
                    "after_first_identity": snapshot_identity(after_first),
                    "concurrent_distinct_os_pids": proof["distinct_os_pids"],
                    "second_rejection_expected": "RESULT_STALE_EPOCH",
                },
                "derived_scope": (
                    "CURRENT_EXACT_SNAPSHOT_ONLY_PER_PACKET_COMMIT_PROTOCOL_REQUIRES_"
                    "EXPLICIT_FANIN_CONTRACT_FOR_SAME_COHORT_N_GT_1"
                ),
                "candidate_resolutions_not_promoted": [
                    "ATOMIC_COHORT_BATCH_COMMIT",
                    "IMMUTABLE_OBSERVATION_SET_TO_CURRENT_DERIVED_SUMMARY",
                    "PROVEN_PROVENANCE_PRESERVING_REBASE",
                    "NARROW_SPLIT_COMPONENT_ACCEPTANCE_SCOPE",
                ],
                "credit_boundary": {
                    "physical_grid10_runtime_credit": 0,
                    "whole_hcu_runtime_credit": 0,
                    "whole_entityos_runtime_credit": 0,
                    "jspace_model_credit": 0,
                    "training_credit": 0,
                    "canonical_truth": False,
                    "effect_authority": False,
                },
            }
        finally:
            fabric.close()


def main() -> int:
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
