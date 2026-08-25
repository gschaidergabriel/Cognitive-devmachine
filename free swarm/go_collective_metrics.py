#!/usr/bin/env python3
"""Freshness-fenced publisher for Clay GO collective metrics.

Supervisor 8.76/8.77 requires the existing GO collective metrics path to stop
publishing a stale aggregate as current. The prior v1 implementation is kept
byte-for-byte as ``go_collective_metrics_core_v1.py`` and this module reuses its
measurement functions. The only new authority here is a fail-closed publication
fence over one stable bounded snapshot of the already-canonical live Swarm, Forge,
Distillery and supervisor-inbox inputs.

No provider call, credential read, model execution, canonical-truth promotion or
runtime/model/training credit is introduced by this publisher.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Any

HERE = Path(__file__).resolve().parent
CORE_PATH = HERE / "go_collective_metrics_core_v1.py"
_CORE_SPEC = importlib.util.spec_from_file_location("clay_go_collective_metrics_core_v1", CORE_PATH)
if _CORE_SPEC is None or _CORE_SPEC.loader is None:
    raise RuntimeError("GO_COLLECTIVE_METRICS_CORE_V1_REQUIRED")
_core = importlib.util.module_from_spec(_CORE_SPEC)
_CORE_SPEC.loader.exec_module(_core)

# Preserve the existing import surface so current tests/consumers do not need a
# second metrics implementation.
for _name in (
    "SCHEMA", "WORKER_SCHEMA", "AUTO_BEGIN", "AUTO_END", "read_json", "iter_jsonl",
    "parse_ts", "fnum", "inum", "usage", "sha256_json", "load_config", "accepted_delta",
    "test_ratio", "code_quality", "innovation_score", "information_latency",
    "performance_index", "explicit_worker_rows", "free_swarm_rows", "delta_rows",
    "worker_key", "worker_lineage", "attach_delta_metrics", "robust_median", "hcu_forecast",
    "aggregate", "fmt", "worker_table_rows", "replace_block",
):
    if hasattr(_core, _name):
        globals()[_name] = getattr(_core, _name)

FRESHNESS_SCHEMA = "CLAY_GO_COLLECTIVE_METRICS_FRESHNESS/v1"
SNAPSHOT_SCHEMA = "CLAY_GO_COLLECTIVE_METRICS_INPUT_SNAPSHOT/v1"
RECEIPT_SCHEMA = "COLLECTIVE_METRICS_FRESHNESS_RECEIPT/v1"
MAX_INPUT_BYTES = 2_000_000
DEFAULT_MAX_INPUT_SKEW_SECONDS = 300.0
INPUT_PATHS = {
    "authority": "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
    "swarm": "free swarm/LIVE_METRICS.json",
    "forge": "free swarm/FORGE_LIVE.json",
    "distillery": "free swarm/DISTILLERY_LIVE.json",
}


class FreshnessError(RuntimeError):
    pass


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical_json_bytes(value))


def _exact_dict(value: Any, code: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise FreshnessError(code)
    return value


def _exact_str(value: Any, code: str) -> str:
    if type(value) is not str or not value:
        raise FreshnessError(code)
    return value


def _nonnegative_int(value: Any, code: str) -> int:
    if type(value) is not int or value < 0:
        raise FreshnessError(code)
    return value


def _parse_timestamp(value: Any, code: str) -> dt.datetime:
    text = _exact_str(value, code)
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FreshnessError(code) from exc
    if parsed.tzinfo is None:
        raise FreshnessError(code)
    return parsed.astimezone(dt.timezone.utc)


def _epoch_tuple(value: Any) -> tuple[int, ...] | None:
    if type(value) is not str or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)+", value):
        return None
    return tuple(int(part) for part in value.split("."))


def _read_bounded(path: Path) -> bytes:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise FreshnessError(f"INPUT_UNREADABLE:{path.as_posix()}") from exc
    if len(data) > MAX_INPUT_BYTES:
        raise FreshnessError(f"INPUT_TOO_LARGE:{path.as_posix()}")
    return data


def _decode_document(data: bytes, logical_name: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FreshnessError(f"INVALID_JSON:{logical_name}") from exc
    return _exact_dict(value, f"OBJECT_REQUIRED:{logical_name}")


def _validate_documents(documents: dict[str, dict[str, Any]], max_skew_seconds: float) -> tuple[str, dict[str, str], float]:
    inbox = documents["authority"]
    swarm = documents["swarm"]
    forge = documents["forge"]
    distillery = documents["distillery"]

    authority_epoch = _exact_str(inbox.get("schema_version"), "AUTHORITY_EPOCH_REQUIRED")
    if _epoch_tuple(authority_epoch) is None:
        raise FreshnessError("AUTHORITY_EPOCH_NONCANONICAL")
    if inbox.get("product") not in (None, "EntityOS") or inbox.get("integrated_cognition_compute_architecture") not in (None, "HCU"):
        raise FreshnessError("AUTHORITY_PRODUCT_ARCHITECTURE_MISMATCH")
    if swarm.get("schema") != "CLAY_FREE_SWARM_METRICS/v1":
        raise FreshnessError("SWARM_SCHEMA_MISMATCH")
    if forge.get("schema") != "CLAY_FREE_EVIDENCE_FORGE_STATUS/v1":
        raise FreshnessError("FORGE_SCHEMA_MISMATCH")
    if distillery.get("state") != "LIVE":
        raise FreshnessError("DISTILLERY_NOT_LIVE")

    for name, doc in (("swarm", swarm), ("forge", forge), ("distillery", distillery)):
        embedded_epoch = doc.get("authority_epoch")
        if embedded_epoch is not None and embedded_epoch != authority_epoch:
            raise FreshnessError(f"INPUT_AUTHORITY_EPOCH_MISMATCH:{name}")

    timestamps = {
        "swarm": _exact_str(swarm.get("generated_at"), "SWARM_GENERATED_AT_REQUIRED"),
        "forge": _exact_str(forge.get("generated_at"), "FORGE_GENERATED_AT_REQUIRED"),
        "distillery": _exact_str(distillery.get("generated_at"), "DISTILLERY_GENERATED_AT_REQUIRED"),
    }
    parsed = {name: _parse_timestamp(value, f"INPUT_TIMESTAMP_INVALID:{name}") for name, value in timestamps.items()}
    oldest = min(parsed.values())
    newest = max(parsed.values())
    skew = (newest - oldest).total_seconds()
    if not math.isfinite(skew) or skew < 0 or skew > max_skew_seconds:
        raise FreshnessError("INPUT_SNAPSHOT_SKEW_EXCEEDED")
    return authority_epoch, timestamps, skew


def read_stable_input_snapshot(repo: Path, max_skew_seconds: float = DEFAULT_MAX_INPUT_SKEW_SECONDS, attempts: int = 4) -> dict[str, Any]:
    """Read one double-observed stable snapshot of all current metric inputs."""
    if type(attempts) is not int or attempts < 1 or attempts > 16:
        raise FreshnessError("SNAPSHOT_ATTEMPTS_INVALID")
    if not isinstance(max_skew_seconds, (int, float)) or isinstance(max_skew_seconds, bool) or not math.isfinite(float(max_skew_seconds)) or max_skew_seconds < 0:
        raise FreshnessError("MAX_INPUT_SKEW_INVALID")

    paths = {name: repo / relative for name, relative in INPUT_PATHS.items()}
    for _ in range(attempts):
        first = {name: _read_bounded(path) for name, path in paths.items()}
        second = {name: _read_bounded(path) for name, path in paths.items()}
        first_hashes = {name: _sha256_bytes(data) for name, data in first.items()}
        second_hashes = {name: _sha256_bytes(data) for name, data in second.items()}
        if first_hashes != second_hashes:
            continue
        documents = {name: _decode_document(data, name) for name, data in second.items()}
        authority_epoch, timestamps, skew = _validate_documents(documents, float(max_skew_seconds))
        input_meta = {
            name: {
                "path": INPUT_PATHS[name],
                "sha256": second_hashes[name],
                "bytes": len(second[name]),
                "generated_at": timestamps.get(name),
            }
            for name in INPUT_PATHS
        }
        input_meta["authority"]["authority_epoch"] = authority_epoch
        preimage = {
            "schema": SNAPSHOT_SCHEMA,
            "authority_epoch": authority_epoch,
            "inputs": input_meta,
        }
        snapshot_id = _sha256_json(preimage)
        return {
            "schema": SNAPSHOT_SCHEMA,
            "snapshot_id": snapshot_id,
            "authority_epoch": authority_epoch,
            "input_generated_at": timestamps,
            "input_sha256": {name: second_hashes[name] for name in INPUT_PATHS},
            "input_bytes": {name: len(second[name]) for name in INPUT_PATHS},
            "input_skew_seconds": skew,
            "inputs": input_meta,
            "documents": documents,
        }
    raise FreshnessError("INPUT_SNAPSHOT_UNSTABLE")


def build_bounded_source_metrics(snapshot: dict[str, Any]) -> dict[str, Any]:
    docs = _exact_dict(snapshot.get("documents"), "SNAPSHOT_DOCUMENTS_REQUIRED")
    swarm = _exact_dict(docs.get("swarm"), "SWARM_DOCUMENT_REQUIRED")
    forge = _exact_dict(docs.get("forge"), "FORGE_DOCUMENT_REQUIRED")
    distillery = _exact_dict(docs.get("distillery"), "DISTILLERY_DOCUMENT_REQUIRED")
    workers = _exact_dict(swarm.get("workers"), "SWARM_WORKERS_REQUIRED")
    snapshot_id = _exact_str(snapshot.get("snapshot_id"), "SNAPSHOT_ID_REQUIRED")
    epoch = _exact_str(snapshot.get("authority_epoch"), "AUTHORITY_EPOCH_REQUIRED")

    common = {"snapshot_id": snapshot_id, "authority_epoch": epoch}
    return {
        "snapshot_id": snapshot_id,
        "authority_epoch": epoch,
        "swarm": {
            **common,
            "generated_at": swarm["generated_at"],
            "worker_records": _nonnegative_int(workers.get("worker_records"), "SWARM_WORKER_RECORDS_INVALID"),
            "exact_usage_rows": _nonnegative_int(workers.get("exact_usage_rows"), "SWARM_EXACT_USAGE_ROWS_INVALID"),
            "input_tokens": _nonnegative_int(workers.get("input_tokens"), "SWARM_INPUT_TOKENS_INVALID"),
            "output_tokens": _nonnegative_int(workers.get("output_tokens"), "SWARM_OUTPUT_TOKENS_INVALID"),
            "total_tokens": _nonnegative_int(workers.get("total_tokens"), "SWARM_TOTAL_TOKENS_INVALID"),
        },
        "forge": {
            **common,
            "generated_at": forge["generated_at"],
            "discovery_hits": _nonnegative_int(forge.get("discovery_hits"), "FORGE_DISCOVERY_HITS_INVALID"),
            "evaluations": _nonnegative_int(forge.get("evaluations"), "FORGE_EVALUATIONS_INVALID"),
            "accepted_deltas": _nonnegative_int(forge.get("accepted_deltas"), "FORGE_ACCEPTED_DELTAS_INVALID"),
        },
        "distillery": {
            **common,
            "generated_at": distillery["generated_at"],
            "collected_source_tokens": _nonnegative_int(distillery.get("collected_source_tokens"), "DISTILLERY_SOURCE_TOKENS_INVALID"),
            "collected_chunks": _nonnegative_int(distillery.get("collected_chunks"), "DISTILLERY_CHUNKS_INVALID"),
            "accepted_packets": _nonnegative_int(distillery.get("accepted_packets"), "DISTILLERY_ACCEPTED_PACKETS_INVALID"),
            "accepted_dataset_tokens": _nonnegative_int(distillery.get("accepted_dataset_tokens"), "DISTILLERY_ACCEPTED_DATASET_TOKENS_INVALID"),
        },
    }


def bounded_result_sha256(snapshot: dict[str, Any]) -> str:
    source = build_bounded_source_metrics(snapshot)
    return _sha256_json({
        "schema": SCHEMA,
        "freshness_schema": FRESHNESS_SCHEMA,
        "authority_epoch": snapshot["authority_epoch"],
        "snapshot_id": snapshot["snapshot_id"],
        "source_metrics": source,
    })


def _existing_vector(existing: dict[str, Any]) -> tuple[str | None, dict[str, str | None], str | None]:
    epoch = existing.get("authority_epoch") if type(existing.get("authority_epoch")) is str else None
    freshness = existing.get("freshness")
    if type(freshness) is dict:
        times = freshness.get("input_generated_at")
        if type(times) is dict:
            return epoch, {name: times.get(name) if type(times.get(name)) is str else None for name in ("swarm", "forge", "distillery")}, freshness.get("snapshot_id") if type(freshness.get("snapshot_id")) is str else None
    source = existing.get("source_metrics")
    if type(source) is dict:
        legacy = {
            "swarm": source.get("free_swarm_live_metrics_generated_at"),
            "forge": source.get("forge_generated_at"),
            "distillery": source.get("distillery_generated_at"),
        }
        for name in ("swarm", "forge", "distillery"):
            section = source.get(name)
            if type(section) is dict and type(section.get("generated_at")) is str:
                legacy[name] = section["generated_at"]
        return epoch, {name: value if type(value) is str else None for name, value in legacy.items()}, source.get("snapshot_id") if type(source.get("snapshot_id")) is str else None
    return epoch, {name: None for name in ("swarm", "forge", "distillery")}, None


def classify_existing_aggregate(existing: dict[str, Any], snapshot: dict[str, Any]) -> str:
    if not existing:
        return "ABSENT"
    existing_epoch, existing_times, existing_snapshot = _existing_vector(existing)
    candidate_times = snapshot["input_generated_at"]

    parsed_existing: dict[str, dt.datetime] = {}
    parsed_candidate: dict[str, dt.datetime] = {}
    for name in ("swarm", "forge", "distillery"):
        candidate = candidate_times.get(name)
        if type(candidate) is not str:
            return "CANDIDATE_FRESHNESS_INVALID_FAIL_CLOSED"
        parsed_candidate[name] = _parse_timestamp(candidate, f"CANDIDATE_TIMESTAMP_INVALID:{name}")
        current = existing_times.get(name)
        if type(current) is str:
            try:
                parsed_existing[name] = _parse_timestamp(current, f"EXISTING_TIMESTAMP_INVALID:{name}")
            except FreshnessError:
                return "EXISTING_FRESHNESS_INVALID_FAIL_CLOSED"

    if any(parsed_existing[name] > parsed_candidate[name] for name in parsed_existing):
        return "EXISTING_NEWER_OUT_OF_ORDER_FAIL_CLOSED"

    candidate_epoch = snapshot["authority_epoch"]
    if existing_epoch is not None and existing_epoch != candidate_epoch:
        old_tuple = _epoch_tuple(existing_epoch)
        new_tuple = _epoch_tuple(candidate_epoch)
        if old_tuple is None or new_tuple is None:
            return "AUTHORITY_EPOCH_UNORDERED_FAIL_CLOSED"
        if old_tuple > new_tuple:
            return "FUTURE_AUTHORITY_EPOCH_FAIL_CLOSED"
        if old_tuple < new_tuple:
            return "HISTORICAL_AUTHORITY_EPOCH"

    if len(parsed_existing) < 3:
        return "EXISTING_FRESHNESS_INCOMPLETE_FAIL_CLOSED"
    if any(parsed_existing[name] < parsed_candidate[name] for name in parsed_existing):
        return "STALE_SUPERSEDED"
    if existing_snapshot == snapshot["snapshot_id"]:
        return "CURRENT_IDENTICAL"
    return "SAME_TIMESTAMPS_DIFFERENT_SNAPSHOT_FAIL_CLOSED"


def publication_decision(existing: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    classification = classify_existing_aggregate(existing, snapshot)
    if classification in {"ABSENT", "STALE_SUPERSEDED", "HISTORICAL_AUTHORITY_EPOCH"}:
        action = "PUBLISH"
    elif classification == "CURRENT_IDENTICAL":
        action = "NOOP_IDENTICAL_SNAPSHOT"
    else:
        action = "REJECT_FAIL_CLOSED"
    return {"classification": classification, "action": action}


def build_result(snapshot: dict[str, Any], workers: list[dict[str, Any]], config: dict[str, Any], decision: dict[str, Any], generated_at: str | None = None) -> dict[str, Any]:
    source_metrics = build_bounded_source_metrics(snapshot)
    bounded_digest = bounded_result_sha256(snapshot)
    core_aggregate = aggregate(workers, config)
    return {
        "schema": SCHEMA,
        "generated_at": generated_at or dt.datetime.now(dt.timezone.utc).isoformat(),
        "generation_class": "FRESHNESS_FENCED_CANONICAL_INPUT_SNAPSHOT",
        "authority_epoch": snapshot["authority_epoch"],
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "architecture": "HCU",
        "config_sha256": _core.sha256_json(config),
        "worker_record_count": len(workers),
        "aggregate": core_aggregate,
        "source_metrics": source_metrics,
        "freshness": {
            "schema": FRESHNESS_SCHEMA,
            "status": "CURRENT_BOUNDED_SNAPSHOT",
            "snapshot_id": snapshot["snapshot_id"],
            "authority_epoch": snapshot["authority_epoch"],
            "input_generated_at": snapshot["input_generated_at"],
            "input_sha256": snapshot["input_sha256"],
            "input_skew_seconds": snapshot["input_skew_seconds"],
            "bounded_result_sha256": bounded_digest,
            "previous_aggregate_classification": decision["classification"],
            "publication_action": decision["action"],
        },
        "workers": workers,
        "anti_goodhart": config.get("anti_goodhart"),
        "selection_policy": config.get("selection_policy"),
        "runtime_credit_added": 0,
        "note": "Derived measurement only. Freshness publication cannot mint canonical truth or runtime/model/training credit.",
    }


def build_freshness_receipt(snapshot: dict[str, Any], decision: dict[str, Any], result: dict[str, Any] | None, status: str, error: str | None = None) -> dict[str, Any]:
    return {
        "schema": RECEIPT_SCHEMA,
        "status": status,
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "architecture": "HCU",
        "authority_epoch": snapshot.get("authority_epoch"),
        "snapshot_id": snapshot.get("snapshot_id"),
        "input_generated_at": snapshot.get("input_generated_at"),
        "input_sha256": snapshot.get("input_sha256"),
        "input_skew_seconds": snapshot.get("input_skew_seconds"),
        "bounded_result_sha256": result.get("freshness", {}).get("bounded_result_sha256") if result else None,
        "previous_aggregate_classification": decision.get("classification"),
        "publication_action": decision.get("action"),
        "error": error,
        "runtime_credit_added": 0,
        "whole_entityos_hcu_credit_added": 0,
        "jspace_model_credit_added": 0,
        "training_credit_added": 0,
    }


def markdown(result: dict[str, Any]) -> str:
    base = _core.markdown(result)
    freshness = result["freshness"]
    source = result["source_metrics"]
    block = "\n".join([
        "### Freshness / shared snapshot gate",
        f"- status: `{freshness['status']}`",
        f"- authority epoch: `{freshness['authority_epoch']}`",
        f"- snapshot: `{freshness['snapshot_id']}`",
        f"- bounded result: `{freshness['bounded_result_sha256']}`",
        f"- input skew: `{freshness['input_skew_seconds']:.6f}s`",
        f"- Swarm tokens: `{source['swarm']['total_tokens']}`",
        f"- Forge evaluations / accepted: `{source['forge']['evaluations']}` / `{source['forge']['accepted_deltas']}`",
        f"- Distillery packets / dataset tokens: `{source['distillery']['accepted_packets']}` / `{source['distillery']['accepted_dataset_tokens']}`",
        "- all three live metric families above are bound to the same snapshot id; stale or mixed publication fails closed.",
        "",
    ])
    marker = _core.AUTO_BEGIN + "\n"
    return base.replace(marker, marker + block, 1) if marker in base else block + base


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def _write_receipt_create_or_verify(path: Path, receipt: dict[str, Any]) -> None:
    data = json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n"
    if path.exists():
        existing = path.read_bytes()
        if existing != data:
            raise FreshnessError("RECEIPT_CREATE_ONCE_CONFLICT")
        return
    _atomic_write(path, data)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--artifacts", type=Path, default=Path("/artifacts/clay-entityos-swarm"))
    ap.add_argument("--output-json", type=Path, default=None)
    ap.add_argument("--output-md", type=Path, default=None)
    ap.add_argument("--freshness-receipt", type=Path, default=None)
    ap.add_argument("--max-input-skew-seconds", type=float, default=DEFAULT_MAX_INPUT_SKEW_SECONDS)
    ap.add_argument("--update-readme", action="store_true")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()

    repo = args.repo.resolve()
    out_json = args.output_json or (repo / "free swarm/GO_COLLECTIVE_METRICS.json")
    out_md = args.output_md or (repo / "free swarm/GO_COLLECTIVE_METRICS.md")
    config = load_config(repo)
    if config.get("schema") != "CLAY_GO_COLLECTIVE_METRICS_CONFIG/v1":
        raise SystemExit("GO_METRICS_CONFIG_REQUIRED")

    try:
        snapshot = read_stable_input_snapshot(repo, args.max_input_skew_seconds)
        existing = read_json(out_json) if out_json.exists() else {}
        decision = publication_decision(existing, snapshot)
        if decision["action"] == "REJECT_FAIL_CLOSED":
            raise FreshnessError(decision["classification"])

        workers = explicit_worker_rows(repo)
        workers.extend(free_swarm_rows(args.artifacts))
        deltas = delta_rows(repo)
        attach_delta_metrics(workers, deltas, config)
        result = build_result(snapshot, workers, config, decision)
        md = markdown(result)

        verify_snapshot = read_stable_input_snapshot(repo, args.max_input_skew_seconds)
        if verify_snapshot["snapshot_id"] != snapshot["snapshot_id"]:
            raise FreshnessError("INPUTS_CHANGED_BEFORE_PUBLICATION")
        latest_existing = read_json(out_json) if out_json.exists() else {}
        final_decision = publication_decision(latest_existing, snapshot)
        if final_decision["action"] == "REJECT_FAIL_CLOSED":
            raise FreshnessError(final_decision["classification"])
        result["freshness"]["previous_aggregate_classification"] = final_decision["classification"]
        result["freshness"]["publication_action"] = final_decision["action"]

        receipt_path = args.freshness_receipt or (
            repo / "research_entity/continuity/receipts/collective_metrics_freshness" / f"{snapshot['snapshot_id']}.json"
        )
        status = "PASS_NOOP_IDENTICAL_SNAPSHOT" if final_decision["action"] == "NOOP_IDENTICAL_SNAPSHOT" else "PASS_CURRENT_BOUNDED_SNAPSHOT"
        receipt = build_freshness_receipt(snapshot, final_decision, result, status)

        if not args.check_only and final_decision["action"] == "PUBLISH":
            _atomic_write(out_json, json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n")
            _atomic_write(out_md, md.encode("utf-8"))
            if args.update_readme:
                readme = repo / "free swarm/README.md"
                current = readme.read_text(encoding="utf-8") if readme.exists() else "# Free Swarm\n"
                _atomic_write(readme, replace_block(current, md).encode("utf-8"))
        _write_receipt_create_or_verify(receipt_path, receipt)

        print(json.dumps({
            "status": status,
            "authority_epoch": snapshot["authority_epoch"],
            "snapshot_id": snapshot["snapshot_id"],
            "bounded_result_sha256": result["freshness"]["bounded_result_sha256"],
            "publication_action": final_decision["action"],
            "previous_aggregate_classification": final_decision["classification"],
            "receipt": str(receipt_path),
        }, sort_keys=True))
        return 0
    except FreshnessError as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
