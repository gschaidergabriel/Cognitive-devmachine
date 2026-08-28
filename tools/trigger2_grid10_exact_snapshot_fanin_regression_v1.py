#!/usr/bin/env python3
"""Trigger-2 deterministic regression for exact-snapshot GRID10 fan-in semantics.

This is a local/source regression only. It proves no physical GRID10 runtime,
whole-HCU, EntityOS, J-Space, training, canonical-truth, or effect-authority credit.

Property under test:
Two immutable NODE_RESULT packets observed from the same exact S1 snapshot cannot
both be admitted by repeated per-packet ExactSnapshotFabric.coordinator_commit()
when every successful commit advances S1 and implicit rebase is forbidden.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

from xeno_physical_grid10_acceptance_v2 import ExactSnapshotFabric
from xeno_self_organizing_fabric_acceptance_v1 import FabricError, Xeno


SCHEMA = "TRIGGER2_GRID10_EXACT_SNAPSHOT_FANIN_REGRESSION/v1"


def run() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="trigger2-grid10-fanin-") as td:
        db = Path(td) / "fanin.sqlite"
        fabric = ExactSnapshotFabric(db)
        try:
            fabric.runtime_register_node("x01", "reason")
            fabric.runtime_register_node("x02", "reason")
            fabric.seed_scope("branch:a")
            fabric.seed_task("t01", "branch:a", 100, "reason", {"q": 1})
            fabric.seed_task("t02", "branch:a", 99, "reason", {"q": 2})

            # Lease creation itself advances S1, so establish deterministic coordinator
            # authority before taking the cohort snapshot used by both packets.
            lease, token = fabric.elect_coordinator("branch:a")
            cohort_snapshot = fabric.snapshot()
            p1 = Xeno("x01", "reason").result(
                cohort_snapshot, "branch:a", {"probe": "same_snapshot_p1"}
            )
            p2 = Xeno("x02", "reason").result(
                cohort_snapshot, "branch:a", {"probe": "same_snapshot_p2"}
            )

            before_first = fabric.snapshot()
            first_receipt = fabric.coordinator_commit(
                lease=lease,
                token=token,
                packet=p1,
                expected_epoch=before_first.epoch,
                expected_digest=before_first.state_digest,
            )

            after_first = fabric.snapshot()
            second_error = None
            try:
                fabric.coordinator_commit(
                    lease=lease,
                    token=token,
                    packet=p2,
                    expected_epoch=after_first.epoch,
                    expected_digest=after_first.state_digest,
                )
            except FabricError as exc:
                second_error = str(exc)

            passed = (
                first_receipt["prior_epoch"] == cohort_snapshot.epoch
                and first_receipt["new_epoch"] == cohort_snapshot.epoch + 1
                and after_first.epoch == cohort_snapshot.epoch + 1
                and second_error in {"RESULT_STALE_EPOCH", "RESULT_STALE_DIGEST"}
                and p2["state_epoch"] == cohort_snapshot.epoch
                and p2["state_digest"] == cohort_snapshot.state_digest
            )

            return {
                "schema": SCHEMA,
                "pass": passed,
                "claim_scope": "CURRENT_EXACT_SNAPSHOT_ONLY_PER_PACKET_COMMIT_PROTOCOL",
                "cohort_identity": {
                    "generation": cohort_snapshot.generation,
                    "epoch": cohort_snapshot.epoch,
                    "state_digest": cohort_snapshot.state_digest,
                    "packet_digests": [p1["packet_digest"], p2["packet_digest"]],
                },
                "first_commit": first_receipt,
                "state_after_first": {
                    "generation": after_first.generation,
                    "epoch": after_first.epoch,
                    "state_digest": after_first.state_digest,
                },
                "second_untouched_cohort_packet_error": second_error,
                "interpretation": (
                    "A same-snapshot cohort with N>1 cannot be directly fanned in by "
                    "repeated exact-current per-packet commits after the first commit "
                    "advances S1. Same-cohort integrated semantics therefore require an "
                    "explicit batch/rebase/derived-summary protocol, or acceptance must "
                    "remain deliberately split into narrower component claims."
                ),
                "credit_boundary": {
                    "local_regression_only": True,
                    "physical_grid10_runtime_credit": 0,
                    "whole_hcu_runtime_credit": 0,
                    "whole_entityos_runtime_credit": 0,
                    "jspace_model_credit": 0,
                    "training_credit": 0,
                    "canonical_truth_credit": 0,
                    "effect_authority_credit": 0,
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
