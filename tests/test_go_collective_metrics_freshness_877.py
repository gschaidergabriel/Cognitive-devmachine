from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "free swarm/go_collective_freshness.py"
SPEC = importlib.util.spec_from_file_location("go_collective_freshness", MODULE_PATH)
assert SPEC and SPEC.loader
freshness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(freshness)


class GoCollectiveMetricsFreshness877Tests(unittest.TestCase):
    def _snapshot(self, snapshot_id: str, max_ts: str, epoch: str = "8.77"):
        return {
            "schema": freshness.SNAPSHOT_SCHEMA,
            "authority_epoch": epoch,
            "snapshot_id": snapshot_id,
            "min_input_generated_at": max_ts,
            "max_input_generated_at": max_ts,
            "inputs": {},
            "fields": {},
        }

    def _result(self, snapshot_id: str, max_ts: str, epoch: str = "8.77", value: int = 1):
        result = {
            "schema": "CLAY_GO_COLLECTIVE_METRICS/v1",
            "generated_at": "2026-08-25T02:50:00+00:00",
            "authority_epoch": epoch,
            "bounded_live_snapshot": self._snapshot(snapshot_id, max_ts, epoch),
            "aggregate": {"total_tokens": value},
            "workers": [],
            "freshness": {"schema": freshness.FRESHNESS_SCHEMA, "status": "FRESH"},
            "collector_sha256": "c" * 64,
            "config_sha256": "d" * 64,
        }
        result["result_digest_sha256"] = freshness.deterministic_result_digest(result)
        return result

    def _write_authority(self, repo: Path, epoch: str = "8.77"):
        auto = repo / "research_entity/claycode/autonomous"
        auto.mkdir(parents=True, exist_ok=True)
        steering_rel = f"research_entity/claycode/autonomous/SUPERVISOR_STEERING_{epoch.replace('.', '_')}.json"
        (auto / "SUPERVISOR_INBOX.json").write_text(
            json.dumps({"schema_version": epoch, "steering": steering_rel}), encoding="utf-8"
        )
        steering_path = repo / steering_rel
        steering_path.parent.mkdir(parents=True, exist_ok=True)
        steering_path.write_text(
            json.dumps({"schema_version": epoch, "program": "ENTITYOS_HCU"}), encoding="utf-8"
        )

    def _write_live(self, repo: Path, ts: str = "2026-08-25T02:30:00+00:00"):
        fs = repo / "free swarm"
        fs.mkdir(parents=True, exist_ok=True)
        (fs / "LIVE_METRICS.json").write_text(json.dumps({
            "schema": "CLAY_FREE_SWARM_METRICS/v1",
            "generated_at": ts,
            "workers": {"total_tokens": 10, "worker_records": 2},
        }), encoding="utf-8")
        (fs / "FORGE_LIVE.json").write_text(json.dumps({
            "schema": "CLAY_FREE_EVIDENCE_FORGE_STATUS/v1",
            "generated_at": "2026-08-25T02:30:01+00:00",
            "evaluations": 3,
            "accepted_deltas": 1,
        }), encoding="utf-8")
        (fs / "DISTILLERY_LIVE.json").write_text(json.dumps({
            "state": "LIVE",
            "generated_at": "2026-08-25T02:30:02+00:00",
            "accepted_packets": 0,
            "accepted_dataset_tokens": 0,
        }), encoding="utf-8")

    def test_newer_live_input_marks_existing_aggregate_stale(self):
        published = self._result("old", "2026-08-25T02:00:00+00:00")
        current = self._snapshot("new", "2026-08-25T02:30:00+00:00")
        status = freshness.assess_published_freshness(published, current, "8.77")
        self.assertEqual(status["status"], "STALE_NEWER_CANONICAL_INPUT")

    def test_authority_epoch_mismatch_is_historical(self):
        published = self._result("same", "2026-08-25T02:30:00+00:00", epoch="8.76")
        current = self._snapshot("same", "2026-08-25T02:30:00+00:00", epoch="8.77")
        status = freshness.assess_published_freshness(published, current, "8.77")
        self.assertEqual(status["status"], "HISTORICAL_AUTHORITY_EPOCH")

    def test_older_writer_finishing_after_newer_writer_is_rejected(self):
        newer = self._result("newer", "2026-08-25T02:40:00+00:00")
        older = self._result("older", "2026-08-25T02:20:00+00:00")
        self.assertEqual(
            freshness.publication_decision(newer, older),
            "REJECT_OUT_OF_ORDER_OLDER_SNAPSHOT",
        )

    def test_same_bounded_inputs_have_identical_result_digest(self):
        a = self._result("same", "2026-08-25T02:30:00+00:00", value=7)
        b = json.loads(json.dumps(a))
        b["generated_at"] = "2026-08-25T02:59:59+00:00"
        b["result_digest_sha256"] = freshness.deterministic_result_digest(b)
        self.assertEqual(a["result_digest_sha256"], b["result_digest_sha256"])

    def test_same_snapshot_semantic_divergence_fails_closed(self):
        old = self._result("same", "2026-08-25T02:30:00+00:00", value=7)
        changed = self._result("same", "2026-08-25T02:30:00+00:00", value=8)
        self.assertEqual(
            freshness.publication_decision(old, changed),
            "REJECT_SAME_SNAPSHOT_RESULT_DIVERGENCE",
        )

    def test_equal_time_different_snapshot_fails_closed(self):
        old = self._result("a", "2026-08-25T02:30:00+00:00")
        changed = self._result("b", "2026-08-25T02:30:00+00:00")
        self.assertEqual(
            freshness.publication_decision(old, changed),
            "REJECT_EQUAL_TIME_SNAPSHOT_CONFLICT",
        )

    def test_swarm_forge_distillery_fields_share_one_snapshot_identity(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._write_authority(repo)
            self._write_live(repo)
            snapshot = freshness.build_live_snapshot(repo)
            ids = {item["snapshot_id"] for item in snapshot["fields"].values()}
            self.assertEqual(ids, {snapshot["snapshot_id"]})
            self.assertEqual(snapshot["authority_epoch"], "8.77")
            self.assertEqual(snapshot["fields"]["free_swarm_total_tokens"]["value"], 10)
            self.assertEqual(snapshot["fields"]["forge_accepted_deltas"]["value"], 1)
            self.assertEqual(snapshot["fields"]["distillery_accepted_dataset_tokens"]["value"], 0)

    def test_locked_publish_receipt_is_idempotent_and_detects_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out_json = root / "GO_COLLECTIVE_METRICS.json"
            out_md = root / "GO_COLLECTIVE_METRICS.md"
            result = self._result("same", "2026-08-25T02:30:00+00:00", value=9)
            first = freshness.publish_bundle(
                out_json=out_json,
                out_md=out_md,
                result=result,
                markdown="first\n",
            )
            second = freshness.publish_bundle(
                out_json=out_json,
                out_md=out_md,
                result=result,
                markdown="second\n",
            )
            self.assertEqual(first, "PUBLISH_NO_EXISTING")
            self.assertEqual(second, "IDEMPOTENT_IDENTICAL_RESULT")
            self.assertEqual(out_md.read_text(), "first\n")
            receipt = freshness.validate_bundle(out_json, out_md)
            self.assertEqual(receipt["schema"], freshness.RECEIPT_SCHEMA)
            self.assertEqual(receipt["snapshot_id"], "same")
            out_md.write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "MD_RECEIPT_MISMATCH"):
                freshness.validate_bundle(out_json, out_md)


if __name__ == "__main__":
    unittest.main()
