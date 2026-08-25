from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "free swarm/go_collective_metrics.py"
SPEC = importlib.util.spec_from_file_location("go_collective_metrics_freshness", MODULE_PATH)
assert SPEC and SPEC.loader
metrics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(metrics)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


class GoCollectiveMetricsFreshnessV1Tests(unittest.TestCase):
    def make_repo(self, root: Path, *, epoch: str = "8.77", base_second: int = 0) -> Path:
        write_json(
            root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
            {
                "schema_version": epoch,
                "steering": f"research_entity/claycode/autonomous/SUPERVISOR_STEERING_{epoch.replace('.', '_')}.json",
            },
        )
        write_json(
            root / "free swarm/LIVE_METRICS.json",
            {
                "generated_at": f"2026-08-25T02:33:{base_second:02d}+00:00",
                "workers": {"worker_records": 10, "total_tokens": 1000 + base_second},
                "deltas": {"nominal_accepted": 1, "accepted": 0},
            },
        )
        write_json(
            root / "free swarm/FORGE_LIVE.json",
            {
                "generated_at": f"2026-08-25T02:33:{base_second + 1:02d}+00:00",
                "evaluations": 144,
                "accepted_deltas": 1,
                "state": "LIVE",
            },
        )
        write_json(
            root / "free swarm/DISTILLERY_LIVE.json",
            {
                "generated_at": f"2026-08-25T02:33:{base_second + 2:02d}+00:00",
                "accepted_packets": 0,
                "accepted_dataset_tokens": 0,
                "state": "LIVE",
            },
        )
        return root

    def candidate(self, snapshot: dict) -> dict:
        result = {
            "schema": metrics.SCHEMA,
            "generated_at": snapshot["latest_input_at"],
            "authority_epoch": snapshot["authority_epoch"],
            "bounded_snapshot": snapshot,
            "live_observations": snapshot["observations"],
            "aggregate": {"total_tokens": 10},
            "workers": [],
            "runtime_credit_added": 0,
        }
        result["measurement_digest_sha256"] = metrics.measurement_digest(result)
        return result

    def test_newer_live_input_marks_older_aggregate_stale(self):
        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(Path(td), base_second=0)
            old_snapshot = metrics.build_bounded_snapshot(repo)
            old = self.candidate(old_snapshot)
            self.make_repo(repo, base_second=10)
            new_snapshot = metrics.build_bounded_snapshot(repo)
            self.assertEqual(
                metrics.classify_publication(old, new_snapshot),
                "STALE_LIVE_INPUT",
            )

    def test_authority_epoch_mismatch_is_historical(self):
        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(Path(td), epoch="8.76")
            old = self.candidate(metrics.build_bounded_snapshot(repo))
            self.make_repo(repo, epoch="8.77")
            current = metrics.build_bounded_snapshot(repo)
            self.assertEqual(
                metrics.classify_publication(old, current),
                "HISTORICAL_AUTHORITY_EPOCH",
            )

    def test_older_writer_finishing_after_newer_cannot_regress_latest(self):
        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(Path(td), base_second=0)
            older = self.candidate(metrics.build_bounded_snapshot(repo))
            self.make_repo(repo, base_second=10)
            newer = self.candidate(metrics.build_bounded_snapshot(repo))
            allowed, reason = metrics.publication_guard(newer, older)
            self.assertFalse(allowed)
            self.assertEqual(reason, "STALE_WRITER_SUPERSEDED")

    def test_same_bounded_inputs_rerun_has_identical_result_digest(self):
        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(Path(td), base_second=4)
            first = self.candidate(metrics.build_bounded_snapshot(repo))
            second = self.candidate(metrics.build_bounded_snapshot(repo))
            self.assertEqual(
                first["bounded_snapshot"]["snapshot_id"],
                second["bounded_snapshot"]["snapshot_id"],
            )
            self.assertEqual(
                first["measurement_digest_sha256"],
                second["measurement_digest_sha256"],
            )

    def test_forge_distillery_swarm_share_one_snapshot_identity(self):
        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(Path(td), base_second=2)
            snapshot = metrics.build_bounded_snapshot(repo)
            self.assertEqual(snapshot["state"], "CURRENT")
            ids = {
                observation["snapshot_id"]
                for observation in snapshot["observations"].values()
            }
            self.assertEqual(ids, {snapshot["snapshot_id"]})

    def test_missing_live_input_fails_closed_unmeasured(self):
        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(Path(td))
            (repo / "free swarm/FORGE_LIVE.json").unlink()
            snapshot = metrics.build_bounded_snapshot(repo)
            self.assertEqual(snapshot["state"], "UNMEASURED")
            self.assertIsNone(snapshot["snapshot_id"])


if __name__ == "__main__":
    unittest.main()
