#!/usr/bin/env python3
"""Fail-closed freshness publisher for Clay GO collective metrics.

This wrapper preserves the existing metric collector as the measurement engine, but
prevents a stale/out-of-order writer from publishing GO_COLLECTIVE_METRICS.json.
It binds every publication to one exact snapshot of LIVE_METRICS.json,
FORGE_LIVE.json, DISTILLERY_LIVE.json, and the selected supervisor authority.

No provider call is performed and no runtime/model/training credit is granted.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

SCHEMA = "CLAY_GO_COLLECTIVE_FRESHNESS_GATE/v1"
SNAPSHOT_SCHEMA = "CLAY_GO_LIVE_SNAPSHOT/v1"
PROJECTION_SCHEMA = "CLAY_GO_LIVE_PROJECTION/v1"

LIVE_SOURCES = {
    "free_swarm": Path("free swarm/LIVE_METRICS.json"),
    "forge": Path("free swarm/FORGE_LIVE.json"),
    "distillery": Path("free swarm/DISTILLERY_LIVE.json"),
}
AUTHORITY_SOURCE = Path("research_entity/claycode/autonomous/SUPERVISOR_INBOX.json")
COLLECTOR = Path("free swarm/go_collective_metrics.py")
DEFAULT_JSON = Path("free swarm/GO_COLLECTIVE_METRICS.json")
DEFAULT_MD = Path("free swarm/GO_COLLECTIVE_METRICS.md")


class FreshnessError(RuntimeError):
    """Publication would violate the freshness/provenance gate."""


def read_json_required(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FreshnessError(f"SOURCE_MISSING:{path}") from exc
    except Exception as exc:
        raise FreshnessError(f"SOURCE_JSON_INVALID:{path}") from exc
    if not isinstance(value, dict):
        raise FreshnessError(f"SOURCE_OBJECT_REQUIRED:{path}")
    return value


def sha256_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def parse_ts_required(value: Any, *, source: str) -> dt.datetime:
    if not isinstance(value, str) or not value.strip():
        raise FreshnessError(f"SOURCE_GENERATED_AT_REQUIRED:{source}")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FreshnessError(f"SOURCE_GENERATED_AT_INVALID:{source}") from exc
    if parsed.tzinfo is None:
        raise FreshnessError(f"SOURCE_GENERATED_AT_TZ_REQUIRED:{source}")
    return parsed.astimezone(dt.timezone.utc)


def canonical_ts(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def authority_epoch(repo: Path) -> str:
    inbox = read_json_required(repo / AUTHORITY_SOURCE)
    selected = inbox.get("selected")
    if not isinstance(selected, dict):
        raise FreshnessError("SUPERVISOR_SELECTED_REQUIRED")
    epoch = selected.get("schema_version")
    if epoch is None or str(epoch).strip() == "":
        raise FreshnessError("SUPERVISOR_EPOCH_REQUIRED")
    return str(epoch)


def _epoch_tuple(value: Any) -> tuple[int, ...]:
    text = str(value or "").strip()
    if not text:
        raise FreshnessError("AUTHORITY_EPOCH_INVALID")
    try:
        return tuple(int(part) for part in text.split("."))
    except ValueError as exc:
        raise FreshnessError(f"AUTHORITY_EPOCH_INVALID:{text}") from exc


def build_live_snapshot(repo: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    source_rows: dict[str, dict[str, Any]] = {}
    source_docs: dict[str, dict[str, Any]] = {}
    source_times: list[dt.datetime] = []

    for name, relative in LIVE_SOURCES.items():
        doc = read_json_required(repo / relative)
        parsed = parse_ts_required(doc.get("generated_at"), source=name)
        source_times.append(parsed)
        source_docs[name] = doc
        source_rows[name] = {
            "path": relative.as_posix(),
            "generated_at": canonical_ts(parsed),
            "sha256": sha256_json(doc),
        }

    epoch = authority_epoch(repo)
    authority_doc = read_json_required(repo / AUTHORITY_SOURCE)
    authority_row = {
        "path": AUTHORITY_SOURCE.as_posix(),
        "schema_version": epoch,
        "sha256": sha256_json(authority_doc),
    }

    stable_identity = {
        "schema": SNAPSHOT_SCHEMA,
        "authority": authority_row,
        "sources": source_rows,
    }
    snapshot_id = sha256_json(stable_identity)
    snapshot = {
        **stable_identity,
        "snapshot_id": snapshot_id,
        "source_min_generated_at": canonical_ts(min(source_times)),
        "source_max_generated_at": canonical_ts(max(source_times)),
    }
    return snapshot, source_docs


def _required_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FreshnessError(f"LIVE_FIELD_REQUIRED:{field}")
    as_int = int(value)
    if float(value) != float(as_int) or as_int < 0:
        raise FreshnessError(f"LIVE_FIELD_INVALID:{field}")
    return as_int


def build_live_projection(snapshot: dict[str, Any], docs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    swarm = docs["free_swarm"]
    forge = docs["forge"]
    distillery = docs["distillery"]
    projection = {
        "schema": PROJECTION_SCHEMA,
        "source_snapshot_id": snapshot["snapshot_id"],
        "free_swarm_tokens": _required_int(swarm.get("total_tokens"), field="free_swarm.total_tokens"),
        "forge_evaluations": _required_int(forge.get("evaluated"), field="forge.evaluated"),
        "forge_accepted_deltas": _required_int(forge.get("accepted"), field="forge.accepted"),
        "distillery_accepted_dataset_tokens": _required_int(
            distillery.get("accepted_dataset_tokens"), field="distillery.accepted_dataset_tokens"
        ),
    }
    return projection


def stable_result_digest(result: dict[str, Any]) -> str:
    """Digest the semantic publication while excluding wall-clock-only fields."""
    stable = copy.deepcopy(result)
    stable.pop("generated_at", None)
    gate = stable.get("freshness_gate")
    if isinstance(gate, dict):
        gate.pop("published_at", None)
        gate.pop("result_digest", None)
    return sha256_json(stable)


def bind_freshness(result: dict[str, Any], repo: Path, *, published_at: str | None = None) -> dict[str, Any]:
    snapshot, docs = build_live_snapshot(repo)
    projection = build_live_projection(snapshot, docs)
    bound = copy.deepcopy(result)
    bound["live_projection"] = projection

    # Compatibility fields make the live facts directly consumable by existing readers.
    bound["free_swarm_tokens"] = projection["free_swarm_tokens"]
    bound["forge_evaluations"] = projection["forge_evaluations"]
    bound["forge_accepted_deltas"] = projection["forge_accepted_deltas"]
    bound["distillery_accepted_dataset_tokens"] = projection["distillery_accepted_dataset_tokens"]
    bound["free_swarm_live_metrics_generated_at"] = snapshot["sources"]["free_swarm"]["generated_at"]

    gate = {
        "schema": SCHEMA,
        "authority_epoch": snapshot["authority"]["schema_version"],
        "source_snapshot": snapshot,
        "source_snapshot_id": snapshot["snapshot_id"],
        "source_min_generated_at": snapshot["source_min_generated_at"],
        "source_max_generated_at": snapshot["source_max_generated_at"],
        "published_at": published_at or dt.datetime.now(dt.timezone.utc).isoformat(),
        "result_digest": None,
        "runtime_credit_added": 0,
        "training_credit_added": 0,
    }
    bound["freshness_gate"] = gate
    gate["result_digest"] = stable_result_digest(bound)
    return bound


def _source_vector(gate: dict[str, Any], *, label: str) -> dict[str, tuple[dt.datetime, str]]:
    snapshot = gate.get("source_snapshot")
    if not isinstance(snapshot, dict):
        raise FreshnessError(f"SOURCE_SNAPSHOT_REQUIRED:{label}")
    sources = snapshot.get("sources")
    if not isinstance(sources, dict):
        raise FreshnessError(f"SOURCE_VECTOR_REQUIRED:{label}")
    vector: dict[str, tuple[dt.datetime, str]] = {}
    for name in LIVE_SOURCES:
        row = sources.get(name)
        if not isinstance(row, dict):
            raise FreshnessError(f"SOURCE_VECTOR_ROW_REQUIRED:{label}:{name}")
        timestamp = parse_ts_required(row.get("generated_at"), source=f"{label}:{name}")
        digest = str(row.get("sha256") or "")
        if not digest:
            raise FreshnessError(f"SOURCE_VECTOR_DIGEST_REQUIRED:{label}:{name}")
        vector[name] = (timestamp, digest)
    return vector


def assert_not_older(existing: dict[str, Any], candidate: dict[str, Any]) -> None:
    if not existing:
        return
    next_gate = candidate.get("freshness_gate")
    if not isinstance(next_gate, dict) or next_gate.get("schema") != SCHEMA:
        raise FreshnessError("CANDIDATE_FRESHNESS_GATE_REQUIRED")

    prev_gate = existing.get("freshness_gate")
    next_epoch = _epoch_tuple(next_gate.get("authority_epoch"))
    if isinstance(prev_gate, dict) and prev_gate.get("schema") == SCHEMA:
        prev_epoch = _epoch_tuple(prev_gate.get("authority_epoch"))
        if next_epoch < prev_epoch:
            raise FreshnessError("OUT_OF_ORDER_AUTHORITY_EPOCH")

        prev_vector = _source_vector(prev_gate, label="existing_output")
        next_vector = _source_vector(next_gate, label="candidate_output")
        for name in LIVE_SOURCES:
            prev_ts, prev_digest = prev_vector[name]
            next_ts, next_digest = next_vector[name]
            if next_ts < prev_ts:
                raise FreshnessError(f"OUT_OF_ORDER_SOURCE_SNAPSHOT:{name}")
            if next_ts == prev_ts and next_digest != prev_digest:
                raise FreshnessError(f"AMBIGUOUS_SAME_TIME_DIFFERENT_SNAPSHOT:{name}")
        return

    # One-time migration from a legacy aggregate: its only explicit live timestamp is
    # a lower-bound fence. Once v1 freshness metadata exists, ordering becomes per-source.
    legacy = existing.get("free_swarm_live_metrics_generated_at")
    if legacy:
        prev_ts = parse_ts_required(legacy, source="existing_legacy_output")
        next_ts = parse_ts_required(next_gate.get("source_max_generated_at"), source="candidate_output")
        if next_ts < prev_ts:
            raise FreshnessError("OUT_OF_ORDER_LEGACY_SOURCE_SNAPSHOT")


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def publish_fail_closed(out_json: Path, out_md: Path, candidate: dict[str, Any], markdown: str) -> None:
    """Serialize writer ordering under a filesystem lock and publish atomically per file."""
    out_json.parent.mkdir(parents=True, exist_ok=True)
    lock_path = out_json.with_name(f".{out_json.name}.publish.lock")
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        existing: dict[str, Any] = {}
        if out_json.exists():
            existing = read_json_required(out_json)
        assert_not_older(existing, candidate)
        _atomic_text(out_json, json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        _atomic_text(out_md, markdown)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def run_collector(repo: Path, artifacts: Path, temp_json: Path, temp_md: Path) -> None:
    collector = repo / COLLECTOR
    if not collector.exists():
        raise FreshnessError(f"COLLECTOR_MISSING:{collector}")
    cmd = [
        sys.executable,
        str(collector),
        "--repo",
        str(repo),
        "--artifacts",
        str(artifacts),
        "--output-json",
        str(temp_json),
        "--output-md",
        str(temp_md),
    ]
    completed = subprocess.run(cmd, check=False, text=True, capture_output=True)
    if completed.returncode != 0:
        raise FreshnessError(
            "COLLECTOR_FAILED:" + str(completed.returncode) + ":" + completed.stderr.strip()[-1000:]
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--artifacts", type=Path, default=Path("/artifacts/clay-entityos-swarm"))
    ap.add_argument("--output-json", type=Path, default=None)
    ap.add_argument("--output-md", type=Path, default=None)
    args = ap.parse_args()

    repo = args.repo.resolve()
    out_json = (args.output_json or (repo / DEFAULT_JSON)).resolve()
    out_md = (args.output_md or (repo / DEFAULT_MD)).resolve()

    with tempfile.TemporaryDirectory(prefix="clay-go-metrics-") as tmp_name:
        tmp = Path(tmp_name)
        raw_json = tmp / "GO_COLLECTIVE_METRICS.raw.json"
        raw_md = tmp / "GO_COLLECTIVE_METRICS.raw.md"
        run_collector(repo, args.artifacts, raw_json, raw_md)
        result = read_json_required(raw_json)
        markdown = raw_md.read_text(encoding="utf-8")
        candidate = bind_freshness(result, repo)
        publish_fail_closed(out_json, out_md, candidate, markdown)

    print(out_json)
    print(json.dumps({
        "freshness_gate": "PASS",
        "source_snapshot_id": candidate["freshness_gate"]["source_snapshot_id"],
        "result_digest": candidate["freshness_gate"]["result_digest"],
        "source_max_generated_at": candidate["freshness_gate"]["source_max_generated_at"],
        "authority_epoch": candidate["freshness_gate"]["authority_epoch"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
