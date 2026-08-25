from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.go_collective_metrics_freshness_v1 import (
    FreshnessError,
    bind_publication,
    capture_input_snapshot,
    publication_decision,
    publish_fresh_outputs,
    resolve_authority,
    validate_published_pair,
)


class GoCollectiveMetricsFreshnessV1Tests(unittest.TestCase):
    def make_repo(self, root: Path, epoch: str = "8.77") -> Path:
        repo = root / "repo"
        (repo / "research_entity/claycode/autonomous").mkdir(parents=True)
        (repo / "research_entity/continuity/go_metrics/worker_records/macro").mkdir(parents=True)
        (repo / "free swarm").mkdir(parents=True)
        (repo / "research_entity/continuity/go_metrics/GO_METRICS_CONFIG_V1.json").write_text(
            json.dumps({"schema": "CLAY_GO_COLLECTIVE_METRICS_CONFIG/v1"}), encoding="utf-8"
        )
        steering_rel = f"research_entity/claycode/autonomous/SUPERVISOR_STEERING_{epoch.replace('.', '_')}.json"
        (repo / steering_rel).write_text(
            json.dumps({"schema_version": epoch, "program": "ENTITYOS_HCU"}), encoding="utf-8"
        )
        (repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json").write_text(
            json.dumps({
                "schema_version": epoch,
                "active_program": "ENTITYOS_HCU",
                "steering": steering_rel,
            }),
            encoding="utf-8",
        )
        (repo / "research_entity/continuity/go_metrics/worker_records/macro/a.json").write_text(
            json.dumps({"worker_id": "a", "macrocycle_id": "macro", "total_tokens": 10}),
            encoding="utf-8",
        )
        (repo / "free swarm/architecture_delta_evaluations.jsonl").write_text("", encoding="utf-8")
        return repo

    def test_authority_requires_inbox_selected_steering_same_epoch(self):
        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(Path(td))
            steering = repo / "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_77.json"
            steering.write_text(json.dumps({"schema_version": "8.76", "program": "ENTITYOS_HCU"}), encoding="utf-8")
            with self.assertRaisesRegex(FreshnessError, "AUTHORITY_EPOCH_MISMATCH"):
                resolve_authority(repo)

    def test_snapshot_recheck_rejects_input_that_changes_during_compute(self):
        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(Path(td))
            artifacts = Path(td) / "artifacts"
            artifacts.mkdir()
            before = capture_input_snapshot(repo, artifacts)
            worker = repo / "research_entity/continuity/go_metrics/worker_records/macro/a.json"
            worker.write_text(json.dumps({"worker_id": "a", "total_tokens": 11}), encoding="utf-8")
            with self.assertRaisesRegex(FreshnessError, "INPUT_SNAPSHOT_CHANGED_DURING_COMPUTE"):
                publish_fresh_outputs(
                    repo=repo,
                    artifacts=artifacts,
                    result={"schema": "CLAY_GO_COLLECTIVE_METRICS/v1", "aggregate": {}},
                    markdown_text="# metrics\n",
                    out_json=repo / "free swarm/GO_COLLECTIVE_METRICS.json",
                    out_md=repo / "free swarm/GO_COLLECTIVE_METRICS.md",
                    expected_input_snapshot=before,
                )

    def test_out_of_order_writer_cannot_replace_newer_source_snapshot(self):
        existing = {
            "authority_epoch": "8.77",
            "source_snapshot": {
                "source_max_mtime_ns": 200,
                "source_snapshot_sha256": "newer",
            },
            "semantic_payload_sha256": "same",
        }
        candidate = {
            "authority_epoch": "8.77",
            "source_snapshot": {
                "source_max_mtime_ns": 100,
                "source_snapshot_sha256": "older",
            },
            "semantic_payload_sha256": "same",
        }
        with self.assertRaisesRegex(FreshnessError, "OUT_OF_ORDER_SOURCE_WRITER"):
            publication_decision(existing, candidate)

    def test_same_snapshot_is_idempotent_but_nondeterminism_fails(self):
        existing = {
            "authority_epoch": "8.77",
            "source_snapshot": {
                "source_max_mtime_ns": 200,
                "source_snapshot_sha256": "same-snapshot",
            },
            "semantic_payload_sha256": "semantic-a",
        }
        same = {
            "authority_epoch": "8.77",
            "source_snapshot": dict(existing["source_snapshot"]),
            "semantic_payload_sha256": "semantic-a",
        }
        self.assertEqual(publication_decision(existing, same), "NOOP_IDENTICAL_SNAPSHOT")
        divergent = dict(same, semantic_payload_sha256="semantic-b")
        with self.assertRaisesRegex(FreshnessError, "NONDETERMINISTIC_SAME_INPUT_RESULT"):
            publication_decision(existing, divergent)

    def test_newer_authority_can_replace_legacy_same_path(self):
        existing = {"authority_epoch": "8.71", "generation_class": "legacy"}
        candidate = {
            "authority_epoch": "8.77",
            "source_snapshot": {"source_max_mtime_ns": 100, "source_snapshot_sha256": "x"},
            "semantic_payload_sha256": "y",
        }
        self.assertEqual(publication_decision(existing, candidate), "PUBLISH")

    def test_publish_binds_one_shared_json_markdown_snapshot_and_replay_is_noop(self):
        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(Path(td))
            artifacts = Path(td) / "artifacts"
            artifacts.mkdir()
            (artifacts / "workers.jsonl").write_text(
                json.dumps({"worker_serial": 1, "total_tokens": 10}) + "\n", encoding="utf-8"
            )
            snapshot = capture_input_snapshot(repo, artifacts)
            result = {
                "schema": "CLAY_GO_COLLECTIVE_METRICS/v1",
                "generated_at": "2026-08-25T00:00:00+00:00",
                "aggregate": {"total_tokens": 10},
                "runtime_credit_added": 0,
            }
            out_json = repo / "free swarm/GO_COLLECTIVE_METRICS.json"
            out_md = repo / "free swarm/GO_COLLECTIVE_METRICS.md"
            first = publish_fresh_outputs(
                repo=repo,
                artifacts=artifacts,
                result=result,
                markdown_text="<!-- begin -->\n# metrics\n",
                out_json=out_json,
                out_md=out_md,
                expected_input_snapshot=snapshot,
            )
            self.assertEqual(first["status"], "PUBLISH")
            pair = validate_published_pair(out_json, out_md)
            self.assertEqual(first["publication_id"], pair["publication_id"])
            second = publish_fresh_outputs(
                repo=repo,
                artifacts=artifacts,
                result=result,
                markdown_text="<!-- begin -->\n# metrics\n",
                out_json=out_json,
                out_md=out_md,
                expected_input_snapshot=snapshot,
            )
            self.assertEqual(second["status"], "NOOP_IDENTICAL_SNAPSHOT")
            self.assertEqual(first["publication_id"], second["publication_id"])

    def test_authority_change_after_snapshot_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(Path(td))
            artifacts = Path(td) / "artifacts"
            artifacts.mkdir()
            snapshot = capture_input_snapshot(repo, artifacts)
            steering_rel = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_78.json"
            (repo / steering_rel).write_text(
                json.dumps({"schema_version": "8.78", "program": "ENTITYOS_HCU"}), encoding="utf-8"
            )
            (repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json").write_text(
                json.dumps({
                    "schema_version": "8.78",
                    "active_program": "ENTITYOS_HCU",
                    "steering": steering_rel,
                }),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(FreshnessError, "AUTHORITY_CHANGED_DURING_COMPUTE"):
                publish_fresh_outputs(
                    repo=repo,
                    artifacts=artifacts,
                    result={"schema": "CLAY_GO_COLLECTIVE_METRICS/v1", "aggregate": {}},
                    markdown_text="# metrics\n",
                    out_json=repo / "free swarm/GO_COLLECTIVE_METRICS.json",
                    out_md=repo / "free swarm/GO_COLLECTIVE_METRICS.md",
                    expected_input_snapshot=snapshot,
                )


if __name__ == "__main__":
    unittest.main()
