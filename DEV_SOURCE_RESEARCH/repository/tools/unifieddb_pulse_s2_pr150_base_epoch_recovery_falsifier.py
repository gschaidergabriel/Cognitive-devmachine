#!/usr/bin/env python3
"""Adversarial recovery/base-binding test for UnifiedDB Pulse S2 PR150.

This is a research falsifier, not a production patch.  It imports the candidate runtime
selected by --runtime-dir and asks whether an effectivized batch whose declared *from*
epochs do not match the current SPM-S1 head can nevertheless publish incrementally.

Why this matters: EffectivizedPulsePlan preserves from_source_epoch/from_graph_epoch, but the
current to_spm_s1_plan adapter lowers only target epochs into PulsePlan.  SPM-S1 then rejects
regression/equality but cannot reject a skipped base.  A read-free preprocessor must be bound
to the projection basis it was computed against, otherwise crash/restart/replay or delivery
gaps can advance the head while silently reusing segments invalidated by omitted events.

A successful reproduction is NEGATIVE evidence: exit 0 means the bug was demonstrated.
It does not authorize a fix, merge PR150, or promote UnifiedDB.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-dir", type=Path, required=True)
    args = ap.parse_args()
    runtime = args.runtime_dir.resolve()
    sys.path.insert(0, str(runtime))

    import semantic_access_pulse_v12 as spm  # type: ignore
    import semantic_pulse_effectivizer_s2 as s2  # type: ignore

    versions = {seed: 0 for seed in ("A", "B", "C", "D", "E")}

    def paths_for(seed: str):
        v = versions[seed]
        logical = f"logical:{seed}"
        return [spm.AccessPath(
            target_record_id=f"rec:{seed}:v{v}",
            target_logical_id=logical,
            path_rank=1,
            hop_count=0,
            path_weight=1.0 + v / 1000,
            dependencies=(seed, logical),
        )]

    with tempfile.TemporaryDirectory(prefix="pulse-s2-base-epoch-") as td:
        db = str(Path(td) / "pulse.sqlite")
        p = spm.SegmentedPulseProjection(db)
        boot = p.bootstrap(
            event_id="boot",
            source_epoch=1,
            graph_epoch=1,
            seeds=tuple(versions),
            recompute_seed=paths_for,
        )
        initial_snapshot = p.snapshot()
        initial_head = p.head_basis()
        p.close()

        # Simulate an omitted authoritative change in the gap head(1)->batch-base(3):
        # B should now be v1 in final source state, but it is absent from the supplied S2 batch.
        versions["B"] = 1
        # The supplied batch itself changes only A from source/graph epoch 3 -> 4.
        versions["A"] = 1
        event = s2.PulseDeltaEvent(
            event_id="e-A-3-4",
            change_class="VALUE_UPDATE",
            from_source_epoch=3,
            to_source_epoch=4,
            from_graph_epoch=3,
            to_graph_epoch=4,
            changed_logical_id="logical:A",
            before_fingerprint="A@v0",
            after_fingerprint="A@v1",
            impact_seed_ids=("A",),
            impact_complete=True,
            final_state_projection_safe=True,
            intermediate_observation_required=False,
        )
        effect = s2.effectivize_pulse_batch("batch-from-3", (event,))
        lowered = s2.to_spm_s1_plan(effect)

        # Reopen at head epoch 1 to exercise restart delivery. Correct behavior should reject
        # because effect.from_* == 3 does not match current head == 1. Current lowering has no
        # from-epoch fields, so the test predicts an incremental publication to epoch 4.
        p = spm.SegmentedPulseProjection(db)
        head_before_apply = p.head_basis()
        apply_error = None
        receipt = None
        try:
            receipt = p.apply_pulse(
                lowered,
                recompute_seed=paths_for,
                recompute_all_seeds=lambda: tuple(versions),
                incremental_fraction_limit=0.25,
            )
        except Exception as exc:
            apply_error = f"{type(exc).__name__}: {exc}"
        snapshot_after_apply = p.snapshot()
        head_after_apply = p.head_basis()
        p.close()

        # Persistence matters: if the unsafe head survives close/reopen, this is not merely
        # an in-memory transient.
        p = spm.SegmentedPulseProjection(db)
        restart_head = p.head_basis()
        restart_snapshot = p.snapshot()
        query_a = p.query("A")
        query_b = p.query("B")

        # The full final-state projection is the reference oracle for the skipped-gap case.
        oracle_db = str(Path(td) / "oracle.sqlite")
        oracle = spm.SegmentedPulseProjection(oracle_db)
        oracle.bootstrap(
            event_id="oracle-final",
            source_epoch=4,
            graph_epoch=4,
            seeds=tuple(versions),
            recompute_seed=paths_for,
        )
        oracle_snapshot = oracle.snapshot()
        oracle_b = oracle.query("B")
        oracle.close()

        replay_error = None
        try:
            p.apply_pulse(
                lowered,
                recompute_seed=paths_for,
                recompute_all_seeds=lambda: tuple(versions),
                incremental_fraction_limit=0.25,
            )
        except Exception as exc:
            replay_error = f"{type(exc).__name__}: {exc}"
        head_after_replay = p.head_basis()
        p.close()

    unsafe_publish = (
        receipt is not None
        and effect.from_source_epoch == 3
        and effect.from_graph_epoch == 3
        and head_before_apply is not None
        and head_before_apply[:2] == (1, 1)
        and receipt.mode == "SEGMENTED_INCREMENTAL_PULSE"
        and head_after_apply is not None
        and head_after_apply[:2] == (4, 4)
    )
    persisted = restart_head == head_after_apply and restart_snapshot == snapshot_after_apply
    stale_segment_survived = query_b == ("rec:B:v0",) and oracle_b == ("rec:B:v1",)
    diverges_from_full_final_state = restart_snapshot != oracle_snapshot
    replay_fail_closed = replay_error is not None and head_after_replay == restart_head

    refuted = bool(
        unsafe_publish
        and persisted
        and stale_segment_survived
        and diverges_from_full_final_state
        and replay_fail_closed
    )

    out = {
        "schema_version": "1.0",
        "experiment": "UnifiedDB Pulse S2 PR150 base-epoch binding / restart falsifier",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "EXECUTABLE_NEGATIVE_RECOVERY_DIFFERENTIAL",
        "runtime": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "runner_name": os.environ.get("RUNNER_NAME"),
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        },
        "inputs": {
            "runtime_dir": str(runtime),
            "s2_sha256": digest_file(runtime / "semantic_pulse_effectivizer_s2.py"),
            "spm_s1_sha256": digest_file(runtime / "semantic_access_pulse_v12.py"),
            "effect_from_source_epoch": effect.from_source_epoch,
            "effect_from_graph_epoch": effect.from_graph_epoch,
            "lowered_pulseplan_has_from_source_epoch": hasattr(lowered, "from_source_epoch"),
            "lowered_pulseplan_has_from_graph_epoch": hasattr(lowered, "from_graph_epoch"),
        },
        "observations": {
            "bootstrap_generation": boot.generation_id,
            "initial_head": initial_head,
            "initial_snapshot_rows": len(initial_snapshot),
            "head_before_apply": head_before_apply,
            "apply_error": apply_error,
            "receipt": None if receipt is None else receipt.__dict__,
            "head_after_apply": head_after_apply,
            "restart_head": restart_head,
            "query_A_after_restart": query_a,
            "query_B_after_restart": query_b,
            "oracle_query_B": oracle_b,
            "restart_snapshot_equals_full_final_state": restart_snapshot == oracle_snapshot,
            "replay_error": replay_error,
            "head_after_replay": head_after_replay,
        },
        "checks": {
            "mismatched_batch_base_was_published_incrementally": unsafe_publish,
            "unsafe_publication_persisted_across_restart": persisted,
            "omitted_gap_change_left_stale_B_segment": stale_segment_survived,
            "published_snapshot_diverges_from_full_final_state": diverges_from_full_final_state,
            "exact_replay_after_publication_fails_closed": replay_fail_closed,
        },
        "result": "REFUTED_CURRENT_PR150_SELECTION" if refuted else "COUNTEREXAMPLE_NOT_ESTABLISHED",
        "interpretation": (
            "PR150 repairs content-ABA invalidation identity, but the S2->SPM-S1 adapter still discards the batch base epochs. A mismatched-base batch can therefore advance the projection head incrementally across an unrepresented epoch gap and persist a stale segment after restart. Exact replay is rejected only after the unsafe publication has already committed."
            if refuted else
            "The predicted base-epoch/restart divergence was not established on these exact bytes."
        ),
        "candidate_fix_obligation": (
            "Bind every effectivized batch to the exact current projection basis before incremental publication. Prefer a versioned PulsePlan/base contract carrying from_source_epoch/from_graph_epoch (and ideally previous_generation_id/head_hash) into apply_pulse so mismatch fails closed before recompute/publication; then test crash/restart/replay and sequential/full-rebuild equivalence."
        ),
        "promotion": "NONE",
        "authority": "NON_AUTHORITATIVE_RESEARCH_FALSIFIER",
        "scope_guard": "REFUTED applies only to selecting current PR150/S2 without an enforced base-binding gate. It does not refute the ABA identity-preservation change itself, SPM-S1 generally, UnifiedDB truth, or authorize Frank Harness changes."
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if refuted else 1


if __name__ == "__main__":
    raise SystemExit(main())
