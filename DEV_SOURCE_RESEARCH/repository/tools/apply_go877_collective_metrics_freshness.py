#!/usr/bin/env python3
"""Apply the Supervisor 8.77 collective-metrics freshness repair.

This is a bounded source-hash-guarded patcher for the existing publisher path.  It is
intended to be executed inside the authorized clay-direct-dev sandbox.  It refuses to
patch if the observed collector/test blobs differ from the exact source inspected by the
creating organ.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import textwrap

EXPECTED_COLLECTOR_BLOB = "f1ed5cc154a0a51cb5b6c211174c4830352d58dc"
EXPECTED_TEST_BLOB = "d30cee02f1b4bd9322bc4cef8a21969e3dee059b"

HELPER = r'''#!/usr/bin/env python3
"""Fail-closed freshness/publication gate for GO collective metrics.

The module binds Swarm/Forge/Distillery fields to one bounded source snapshot, prevents
out-of-order writers from regressing the latest aggregate, exposes stale collector state
as STALE_UNMEASURED, and publishes JSON/Markdown with one shared snapshot identity.
"""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

SNAPSHOT_SCHEMA = "CLAY_GO_COLLECTIVE_INPUT_SNAPSHOT/v1"
RECEIPT_SCHEMA = "COLLECTIVE_METRICS_FRESHNESS_RECEIPT/v1"
PUBLICATION_SCHEMA = "CLAY_GO_COLLECTIVE_METRICS_PUBLICATION/v1"
MAX_SOURCE_SPAN_SECONDS = 120.0
COLLECTOR_TIME_SKEW_SECONDS = 30.0
SOURCE_PATHS = {
    "swarm": "free swarm/LIVE_METRICS.json",
    "forge": "free swarm/FORGE_LIVE.json",
    "distillery": "free swarm/DISTILLERY_LIVE.json",
}
DERIVED_AGGREGATE_KEYS = (
    "token_quality_efficiency",
    "code_quality_score",
    "verified_innovation_score",
    "performance_index_median",
    "p95_information_latency_seconds",
    "capability_information_latency_ratio",
)


class FreshnessError(RuntimeError):
    pass


class PublicationRejected(FreshnessError):
    def __init__(self, reason: str, receipt: dict[str, Any]):
        super().__init__(reason)
        self.reason = reason
        self.receipt = receipt


def _parse_ts(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        x = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return x if x.tzinfo else x.replace(tzinfo=dt.timezone.utc)
    except Exception:
        return None


def _iso(x: dt.datetime) -> str:
    return x.astimezone(dt.timezone.utc).isoformat()


def _epoch_tuple(value: Any) -> tuple[int, ...]:
    parts = str(value or "").strip().split(".")
    if not parts or any(not p.isdigit() for p in parts):
        raise FreshnessError(f"INVALID_AUTHORITY_EPOCH:{value!r}")
    return tuple(int(p) for p in parts)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _sha256_bytes(data)


def _read_json_bytes(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except Exception as exc:
        raise FreshnessError(f"REQUIRED_JSON_UNREADABLE:{path}:{exc}") from exc
    if not isinstance(value, dict):
        raise FreshnessError(f"REQUIRED_JSON_NOT_OBJECT:{path}")
    return value, raw


def resolve_authority_epoch(repo: Path) -> str:
    inbox_path = repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    inbox, _ = _read_json_bytes(inbox_path)
    steering_rel = inbox.get("steering")
    if not isinstance(steering_rel, str) or not steering_rel:
        raise FreshnessError("SUPERVISOR_INBOX_STEERING_REQUIRED")
    steering, _ = _read_json_bytes(repo / steering_rel)
    inbox_epoch = str(inbox.get("schema_version") or "")
    steering_epoch = str(steering.get("schema_version") or "")
    _epoch_tuple(inbox_epoch)
    _epoch_tuple(steering_epoch)
    if inbox_epoch != steering_epoch:
        raise FreshnessError(f"AUTHORITY_EPOCH_MISMATCH:inbox={inbox_epoch}:steering={steering_epoch}")
    return steering_epoch


def build_bounded_snapshot(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    authority_epoch = resolve_authority_epoch(repo)
    sources: dict[str, dict[str, Any]] = {}
    parsed: dict[str, dict[str, Any]] = {}
    times: list[dt.datetime] = []
    for name, rel in SOURCE_PATHS.items():
        value, raw = _read_json_bytes(repo / rel)
        generated = _parse_ts(value.get("generated_at"))
        if generated is None:
            raise FreshnessError(f"SOURCE_GENERATED_AT_REQUIRED:{name}")
        times.append(generated)
        parsed[name] = value
        sources[name] = {
            "path": rel,
            "sha256": _sha256_bytes(raw),
            "generated_at": _iso(generated),
        }
    span = (max(times) - min(times)).total_seconds()
    if span < 0 or span > MAX_SOURCE_SPAN_SECONDS:
        raise FreshnessError(f"UNBOUNDED_SOURCE_SNAPSHOT:span_seconds={span:.6f}")
    core = {
        "schema": SNAPSHOT_SCHEMA,
        "authority_epoch": authority_epoch,
        "sources": sources,
    }
    snapshot_id = _sha256_json(core)
    for item in sources.values():
        item["shared_snapshot_id"] = snapshot_id
    swarm = parsed["swarm"]
    forge = parsed["forge"]
    distillery = parsed["distillery"]
    workers = swarm.get("workers") if isinstance(swarm.get("workers"), dict) else {}
    deltas = swarm.get("deltas") if isinstance(swarm.get("deltas"), dict) else {}
    source_metrics = {
        "bounded_snapshot_id": snapshot_id,
        "swarm_total_tokens": workers.get("total_tokens"),
        "swarm_worker_records": workers.get("worker_records"),
        "swarm_evidence_qualified_accepted_deltas": deltas.get("accepted"),
        "swarm_nominal_accepted_deltas": deltas.get("nominal_accepted"),
        "forge_evaluations": forge.get("evaluations"),
        "forge_nominal_accepted_deltas": forge.get("accepted_deltas"),
        "distillery_accepted_packets": distillery.get("accepted_packets"),
        "distillery_accepted_dataset_tokens": distillery.get("accepted_dataset_tokens"),
    }
    return {
        "schema": SNAPSHOT_SCHEMA,
        "authority_epoch": authority_epoch,
        "snapshot_id": snapshot_id,
        "source_time_span_seconds": span,
        "min_generated_at": _iso(min(times)),
        "max_generated_at": _iso(max(times)),
        "sources": sources,
        "source_metrics": source_metrics,
    }


def stable_result_digest(result: dict[str, Any]) -> str:
    stable = copy.deepcopy(result)
    stable.pop("generated_at", None)
    stable.pop("publication", None)
    return _sha256_json(stable)


def _latest_worker_time(result: dict[str, Any]) -> dt.datetime | None:
    workers = result.get("workers")
    if not isinstance(workers, list):
        return None
    values = [_parse_ts(r.get("finished_at")) for r in workers if isinstance(r, dict)]
    known = [x for x in values if x is not None]
    return max(known) if known else None


def apply_freshness_to_result(result: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(result)
    if snapshot.get("schema") != SNAPSHOT_SCHEMA:
        raise FreshnessError("BOUNDED_SNAPSHOT_SCHEMA_REQUIRED")
    snapshot_id = snapshot.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise FreshnessError("BOUNDED_SNAPSHOT_ID_REQUIRED")
    authority_epoch = str(snapshot.get("authority_epoch") or "")
    _epoch_tuple(authority_epoch)
    source_metrics = copy.deepcopy(snapshot.get("source_metrics") or {})
    if source_metrics.get("bounded_snapshot_id") != snapshot_id:
        raise FreshnessError("SOURCE_METRICS_SNAPSHOT_ID_MISMATCH")
    out["authority_epoch"] = authority_epoch
    out["source_snapshot"] = copy.deepcopy(snapshot)
    out["source_metrics"] = source_metrics
    aggregate = out.get("aggregate")
    if not isinstance(aggregate, dict):
        raise FreshnessError("AGGREGATE_OBJECT_REQUIRED")
    collector_total = aggregate.get("total_tokens")
    live_total = source_metrics.get("swarm_total_tokens")
    collector_time = _latest_worker_time(out)
    live_time = _parse_ts(snapshot.get("max_generated_at"))
    reasons: list[str] = []
    if not isinstance(collector_total, (int, float)):
        reasons.append("COLLECTOR_TOTAL_TOKENS_UNKNOWN")
    if isinstance(live_total, (int, float)) and isinstance(collector_total, (int, float)) and live_total > collector_total:
        reasons.append("LIVE_SWARM_TOTAL_AHEAD")
    if live_time is not None:
        if collector_time is None:
            reasons.append("COLLECTOR_INPUT_TIME_UNKNOWN")
        elif (live_time - collector_time).total_seconds() > COLLECTOR_TIME_SKEW_SECONDS:
            reasons.append("LIVE_INPUT_TIMESTAMP_AHEAD")
    if reasons:
        aggregate["measurement_freshness"] = "STALE_UNMEASURED"
        aggregate["freshness_reasons"] = reasons
        aggregate["stale_raw_derived_metrics"] = {k: aggregate.get(k) for k in DERIVED_AGGREGATE_KEYS}
        for key in DERIVED_AGGREGATE_KEYS:
            aggregate[key] = None
        hcu = aggregate.get("hcu_confidence")
        if isinstance(hcu, dict):
            hcu["measurement_freshness"] = "STALE_UNMEASURED"
    else:
        aggregate["measurement_freshness"] = "MEASURED_CURRENT_BOUNDED_SNAPSHOT"
        aggregate["freshness_reasons"] = []
    return out


def _existing_latest_time(existing: dict[str, Any]) -> dt.datetime | None:
    snap = existing.get("source_snapshot")
    if isinstance(snap, dict):
        x = _parse_ts(snap.get("max_generated_at"))
        if x is not None:
            return x
    source = existing.get("source_metrics")
    if isinstance(source, dict):
        keys = (
            "free_swarm_live_metrics_generated_at",
            "forge_generated_at",
            "distillery_generated_at",
            "swarm_generated_at",
        )
        vals = [_parse_ts(source.get(k)) for k in keys]
        vals = [x for x in vals if x is not None]
        if vals:
            return max(vals)
    return _parse_ts(existing.get("generated_at"))


def publication_decision(candidate: dict[str, Any], existing: dict[str, Any] | None) -> str:
    snap = candidate.get("source_snapshot")
    if not isinstance(snap, dict):
        raise FreshnessError("CANDIDATE_SOURCE_SNAPSHOT_REQUIRED")
    candidate_epoch = str(candidate.get("authority_epoch") or "")
    snapshot_epoch = str(snap.get("authority_epoch") or "")
    if candidate_epoch != snapshot_epoch:
        return "BLOCK_CANDIDATE_AUTHORITY_SNAPSHOT_MISMATCH"
    c_epoch = _epoch_tuple(candidate_epoch)
    c_time = _parse_ts(snap.get("max_generated_at"))
    if c_time is None:
        raise FreshnessError("CANDIDATE_MAX_GENERATED_AT_REQUIRED")
    if not existing:
        return "PUBLISH_INITIAL"
    existing_epoch_raw = existing.get("authority_epoch") or "0"
    try:
        e_epoch = _epoch_tuple(existing_epoch_raw)
    except FreshnessError:
        e_epoch = (0,)
    if c_epoch < e_epoch:
        return "BLOCK_AUTHORITY_EPOCH_REGRESSION"
    e_time = _existing_latest_time(existing)
    if e_time is not None and c_time < e_time:
        return "BLOCK_OUT_OF_ORDER_WRITER"
    existing_snap = existing.get("source_snapshot") if isinstance(existing.get("source_snapshot"), dict) else None
    if e_time is not None and c_time == e_time and existing_snap:
        c_id = str(snap.get("snapshot_id") or "")
        e_id = str(existing_snap.get("snapshot_id") or "")
        if c_id == e_id:
            if stable_result_digest(candidate) == stable_result_digest(existing):
                return "IDEMPOTENT_NOOP"
            return "BLOCK_NONDETERMINISTIC_SAME_INPUT"
        return "BLOCK_AMBIGUOUS_SAME_TIME_DIFFERENT_SNAPSHOT"
    if c_epoch > e_epoch:
        return "PUBLISH_AUTHORITY_REFRESH"
    if existing_snap is None:
        return "PUBLISH_BOUND_SNAPSHOT_UPGRADE"
    return "PUBLISH_NEWER_SNAPSHOT"


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
        try:
            dir_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _receipt_base(candidate: dict[str, Any], decision: str) -> dict[str, Any]:
    snap = candidate["source_snapshot"]
    return {
        "schema": RECEIPT_SCHEMA,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "decision": decision,
        "authority_epoch": candidate.get("authority_epoch"),
        "snapshot_id": snap.get("snapshot_id"),
        "snapshot_max_generated_at": snap.get("max_generated_at"),
        "snapshot_source_time_span_seconds": snap.get("source_time_span_seconds"),
        "stable_result_digest_sha256": stable_result_digest(candidate),
        "runtime_credit_added": 0,
        "scope": "collective metrics freshness/publication component only",
    }


def publish_metrics_bundle(result: dict[str, Any], markdown_text: str, out_json: Path, out_md: Path) -> dict[str, Any]:
    import fcntl

    out_json = out_json.resolve()
    out_md = out_md.resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    receipt_path = out_json.parent / "COLLECTIVE_METRICS_FRESHNESS_RECEIPT.json"
    lock_path = out_json.parent / ".GO_COLLECTIVE_METRICS.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_fh:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
        existing: dict[str, Any] | None = None
        if out_json.exists():
            try:
                loaded = json.loads(out_json.read_text(encoding="utf-8"))
                existing = loaded if isinstance(loaded, dict) else None
            except Exception:
                existing = None
        decision = publication_decision(result, existing)
        receipt = _receipt_base(result, decision)
        if decision.startswith("BLOCK_"):
            _atomic_write_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
            raise PublicationRejected(decision, receipt)
        if decision == "IDEMPOTENT_NOOP":
            receipt["published"] = False
            receipt["idempotent"] = True
            _atomic_write_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
            return receipt
        published = copy.deepcopy(result)
        result_digest = stable_result_digest(published)
        published["publication"] = {
            "schema": PUBLICATION_SCHEMA,
            "decision": decision,
            "snapshot_id": published["source_snapshot"]["snapshot_id"],
            "stable_result_digest_sha256": result_digest,
        }
        json_text = json.dumps(published, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        marker = (
            "\n<!-- COLLECTIVE_METRICS_PUBLICATION "
            f"snapshot={published['source_snapshot']['snapshot_id']} result={result_digest} -->\n"
        )
        md_text = markdown_text.rstrip() + marker
        _atomic_write_text(out_json, json_text)
        _atomic_write_text(out_md, md_text)
        receipt.update({
            "published": True,
            "idempotent": False,
            "json_sha256": _sha256_bytes(out_json.read_bytes()),
            "markdown_sha256": _sha256_bytes(out_md.read_bytes()),
        })
        _atomic_write_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        return receipt
'''

TEST_METHODS = r'''
    def test_newer_live_input_marks_aggregate_stale_unmeasured(self):
        snapshot = {
            "schema": metrics.FRESHNESS_SNAPSHOT_SCHEMA,
            "authority_epoch": "8.77",
            "snapshot_id": "s1",
            "max_generated_at": "2026-08-25T02:00:30+00:00",
            "source_metrics": {"bounded_snapshot_id": "s1", "swarm_total_tokens": 20},
        }
        result = {
            "generated_at": "2026-08-25T02:01:00+00:00",
            "aggregate": {
                "total_tokens": 10,
                "token_quality_efficiency": 1.0,
                "code_quality_score": 1.0,
                "verified_innovation_score": 1.0,
                "performance_index_median": 1.0,
                "p95_information_latency_seconds": 1.0,
                "capability_information_latency_ratio": 1.0,
                "hcu_confidence": {},
            },
            "workers": [{"finished_at": "2026-08-25T02:00:00+00:00"}],
        }
        out = metrics.apply_freshness_to_result(result, snapshot)
        self.assertEqual(out["aggregate"]["measurement_freshness"], "STALE_UNMEASURED")
        self.assertIn("LIVE_SWARM_TOTAL_AHEAD", out["aggregate"]["freshness_reasons"])
        self.assertIsNone(out["aggregate"]["token_quality_efficiency"])

    def test_authority_epoch_regression_fails_closed(self):
        candidate = {
            "authority_epoch": "8.76",
            "source_snapshot": {"authority_epoch": "8.76", "snapshot_id": "new", "max_generated_at": "2026-08-25T02:02:00+00:00"},
        }
        existing = {
            "authority_epoch": "8.77",
            "generated_at": "2026-08-25T02:00:00+00:00",
        }
        self.assertEqual(metrics.publication_decision(candidate, existing), "BLOCK_AUTHORITY_EPOCH_REGRESSION")

    def test_older_writer_finishing_after_newer_writer_cannot_regress_latest(self):
        candidate = {
            "authority_epoch": "8.77",
            "source_snapshot": {"authority_epoch": "8.77", "snapshot_id": "old", "max_generated_at": "2026-08-25T02:00:00+00:00"},
        }
        existing = {
            "authority_epoch": "8.77",
            "source_snapshot": {"authority_epoch": "8.77", "snapshot_id": "new", "max_generated_at": "2026-08-25T02:01:00+00:00"},
        }
        self.assertEqual(metrics.publication_decision(candidate, existing), "BLOCK_OUT_OF_ORDER_WRITER")

    def test_same_bounded_inputs_rerun_has_identical_stable_result_digest(self):
        base = {
            "authority_epoch": "8.77",
            "source_snapshot": {"authority_epoch": "8.77", "snapshot_id": "same", "max_generated_at": "2026-08-25T02:00:00+00:00"},
            "aggregate": {"total_tokens": 5},
            "workers": [],
        }
        a = dict(base, generated_at="2026-08-25T02:01:00+00:00")
        b = dict(base, generated_at="2026-08-25T02:02:00+00:00")
        self.assertEqual(metrics.stable_result_digest(a), metrics.stable_result_digest(b))

    def test_swarm_forge_distillery_share_one_bounded_snapshot_identity(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "free swarm").mkdir(parents=True)
            (repo / "research_entity/claycode/autonomous").mkdir(parents=True)
            (repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json").write_text(json.dumps({
                "schema_version": "8.77",
                "steering": "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_77.json",
            }))
            (repo / "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_77.json").write_text(json.dumps({"schema_version": "8.77"}))
            (repo / "free swarm/LIVE_METRICS.json").write_text(json.dumps({
                "generated_at": "2026-08-25T02:00:00+00:00",
                "workers": {"total_tokens": 100, "worker_records": 2},
                "deltas": {"accepted": 0, "nominal_accepted": 1},
            }))
            (repo / "free swarm/FORGE_LIVE.json").write_text(json.dumps({
                "generated_at": "2026-08-25T02:00:01+00:00", "evaluations": 3, "accepted_deltas": 1,
            }))
            (repo / "free swarm/DISTILLERY_LIVE.json").write_text(json.dumps({
                "generated_at": "2026-08-25T02:00:02+00:00", "accepted_packets": 0, "accepted_dataset_tokens": 0,
            }))
            snap = metrics.build_bounded_snapshot(repo)
            ids = {row["shared_snapshot_id"] for row in snap["sources"].values()}
            self.assertEqual(ids, {snap["snapshot_id"]})
            self.assertLessEqual(snap["source_time_span_seconds"], 120.0)

    def test_identical_published_snapshot_is_idempotent_noop(self):
        candidate = {
            "generated_at": "2026-08-25T02:02:00+00:00",
            "authority_epoch": "8.77",
            "source_snapshot": {"authority_epoch": "8.77", "snapshot_id": "same", "max_generated_at": "2026-08-25T02:00:00+00:00"},
            "aggregate": {"total_tokens": 5},
        }
        existing = dict(candidate, generated_at="2026-08-25T02:01:00+00:00")
        self.assertEqual(metrics.publication_decision(candidate, existing), "IDEMPOTENT_NOOP")
'''


def git_blob(repo: Path, rel: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), "hash-object", rel], text=True).strip()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH_MARKER_{label}_COUNT_{count}")
    return text.replace(old, new, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()
    collector_rel = "free swarm/go_collective_metrics.py"
    tests_rel = "tests/test_go_collective_metrics_v1.py"
    collector_path = repo / collector_rel
    tests_path = repo / tests_rel
    if git_blob(repo, collector_rel) != EXPECTED_COLLECTOR_BLOB:
        raise SystemExit("COLLECTOR_SOURCE_BLOB_MOVED_FAIL_CLOSED")
    if git_blob(repo, tests_rel) != EXPECTED_TEST_BLOB:
        raise SystemExit("TEST_SOURCE_BLOB_MOVED_FAIL_CLOSED")

    helper_path = repo / "free swarm/collective_metrics_freshness.py"
    if helper_path.exists():
        raise SystemExit("FRESHNESS_HELPER_ALREADY_EXISTS_FAIL_CLOSED")
    helper_path.write_text(textwrap.dedent(HELPER).lstrip(), encoding="utf-8")

    collector = collector_path.read_text(encoding="utf-8")
    collector = replace_once(
        collector,
        "from typing import Any, Iterable\n",
        "from typing import Any, Iterable\nimport sys\n\nsys.path.insert(0, str(Path(__file__).resolve().parent))\nfrom collective_metrics_freshness import (\n    SNAPSHOT_SCHEMA as FRESHNESS_SNAPSHOT_SCHEMA,\n    apply_freshness_to_result,\n    build_bounded_snapshot,\n    publication_decision,\n    publish_metrics_bundle,\n    stable_result_digest,\n)\n",
        "IMPORTS",
    )
    collector = replace_once(
        collector,
        "    if config.get(\"schema\") != \"CLAY_GO_COLLECTIVE_METRICS_CONFIG/v1\":\n        raise SystemExit(\"GO_METRICS_CONFIG_REQUIRED\")\n\n    workers = explicit_worker_rows(repo)\n",
        "    if config.get(\"schema\") != \"CLAY_GO_COLLECTIVE_METRICS_CONFIG/v1\":\n        raise SystemExit(\"GO_METRICS_CONFIG_REQUIRED\")\n\n    bounded_snapshot = build_bounded_snapshot(repo)\n    workers = explicit_worker_rows(repo)\n",
        "SNAPSHOT",
    )
    collector = replace_once(
        collector,
        "    }\n    md = markdown(result)\n\n    out_json = args.output_json or (repo / \"free swarm/GO_COLLECTIVE_METRICS.json\")\n",
        "    }\n    result = apply_freshness_to_result(result, bounded_snapshot)\n    md = markdown(result)\n\n    out_json = args.output_json or (repo / \"free swarm/GO_COLLECTIVE_METRICS.json\")\n",
        "APPLY",
    )
    collector = replace_once(
        collector,
        "    out_json.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + \"\\n\", encoding=\"utf-8\")\n    out_md.write_text(md, encoding=\"utf-8\")\n\n    if args.update_readme:\n",
        "    receipt = publish_metrics_bundle(result, md, out_json, out_md)\n\n    if args.update_readme and receipt.get(\"published\") is True:\n",
        "PUBLISH",
    )
    collector = replace_once(
        collector,
        "        \"calibration_state\": h.get(\"calibration_state\"),\n    }, sort_keys=True))\n",
        "        \"calibration_state\": h.get(\"calibration_state\"),\n        \"measurement_freshness\": result[\"aggregate\"].get(\"measurement_freshness\"),\n        \"bounded_snapshot_id\": bounded_snapshot.get(\"snapshot_id\"),\n        \"publication_decision\": receipt.get(\"decision\"),\n    }, sort_keys=True))\n",
        "SUMMARY",
    )
    collector_path.write_text(collector, encoding="utf-8")

    tests = tests_path.read_text(encoding="utf-8")
    tests = replace_once(tests, "\n\nif __name__ == \"__main__\":\n", "\n" + textwrap.dedent(TEST_METHODS) + "\n\nif __name__ == \"__main__\":\n", "TESTS")
    tests_path.write_text(tests, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
