#!/usr/bin/env python3
"""Fail-closed publisher for Clay GO collective metrics.

This is a compatibility wrapper around ``go_collective_metrics.py``. It does not
change the metric definitions. It closes the publication/metrology gap by binding
one publication to the inbox-selected supervisor authority plus one unchanged
shared input snapshot, serializing local writers, rejecting out-of-order writes,
and using atomic file replacement.

No provider call, credential lookup, model execution, canonical effect, or runtime/
model/training credit is introduced here.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Iterator

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "go_collective_metrics.py"
_SPEC = importlib.util.spec_from_file_location("clay_go_collective_metrics_v1", BASE_PATH)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - repository invariant
    raise RuntimeError("GO_COLLECTIVE_METRICS_BASE_IMPORT_FAILED")
base = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(base)

FRESHNESS_SCHEMA = "CLAY_COLLECTIVE_METRICS_FRESHNESS/v1"
PUBLICATION_SCHEMA = "CLAY_COLLECTIVE_METRICS_PUBLICATION/v1"


class FreshnessError(RuntimeError):
    pass


def read_json_strict(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise FreshnessError(f"JSON_REQUIRED:{path}") from exc
    if not isinstance(value, dict):
        raise FreshnessError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def epoch_key(value: Any) -> tuple[int, ...]:
    text = str(value or "").strip()
    if not text:
        raise FreshnessError("AUTHORITY_EPOCH_REQUIRED")
    try:
        return tuple(int(part) for part in text.split("."))
    except ValueError as exc:
        raise FreshnessError(f"AUTHORITY_EPOCH_INVALID:{text}") from exc


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def checkout_head(repo: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
    except Exception:
        return None
    value = proc.stdout.strip()
    return value if len(value) == 40 else None


def resolve_authority(repo: Path) -> dict[str, Any]:
    inbox_path = repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    inbox = read_json_strict(inbox_path)
    steering_rel = inbox.get("steering")
    if not isinstance(steering_rel, str) or not steering_rel.strip():
        raise FreshnessError("SUPERVISOR_INBOX_STEERING_REQUIRED")
    steering_path = repo / steering_rel
    steering = read_json_strict(steering_path)

    inbox_epoch = str(inbox.get("schema_version") or "")
    steering_epoch = str(steering.get("schema_version") or "")
    epoch_key(inbox_epoch)
    if steering_epoch != inbox_epoch:
        raise FreshnessError(
            f"SUPERVISOR_EPOCH_MISMATCH:inbox={inbox_epoch}:steering={steering_epoch}"
        )
    for key, expected in (
        ("program", "ENTITYOS_HCU"),
        ("product", "EntityOS"),
        ("integrated_cognition_compute_architecture", "HCU"),
    ):
        observed = steering.get(key)
        if observed != expected:
            raise FreshnessError(f"SUPERVISOR_{key.upper()}_MISMATCH:{observed}")
    authority = steering.get("authority")
    if not isinstance(authority, dict) or authority.get("free_only") is not True:
        raise FreshnessError("SUPERVISOR_FREE_ONLY_REQUIRED")

    return {
        "authority_epoch": inbox_epoch,
        "inbox_path": inbox_path,
        "steering_path": steering_path,
        "inbox_sha256": sha256_file(inbox_path),
        "steering_sha256": sha256_file(steering_path),
    }


def _input_files(repo: Path, artifacts: Path, authority: dict[str, Any]) -> list[tuple[str, Path]]:
    if not artifacts.exists() or not artifacts.is_dir():
        raise FreshnessError(f"FREE_SWARM_ARTIFACT_ROOT_REQUIRED:{artifacts}")

    paths: list[tuple[str, Path]] = []
    fixed = [
        ("repo:research_entity/continuity/go_metrics/GO_METRICS_CONFIG_V1.json",
         repo / "research_entity/continuity/go_metrics/GO_METRICS_CONFIG_V1.json"),
        ("repo:free swarm/architecture_delta_evaluations.jsonl",
         repo / "free swarm/architecture_delta_evaluations.jsonl"),
        ("repo:supervisor_inbox", Path(authority["inbox_path"])),
        ("repo:supervisor_steering", Path(authority["steering_path"])),
    ]
    for label, path in fixed:
        if not path.exists() or not path.is_file():
            raise FreshnessError(f"FRESHNESS_INPUT_REQUIRED:{label}:{path}")
        paths.append((label, path))

    worker_root = repo / "research_entity/continuity/go_metrics/worker_records"
    if worker_root.exists():
        for path in sorted(worker_root.rglob("*.json")):
            if path.is_file():
                rel = path.relative_to(repo).as_posix()
                paths.append((f"repo:{rel}", path))

    artifact_files = sorted(path for path in artifacts.rglob("workers.jsonl") if path.is_file())
    if not artifact_files:
        raise FreshnessError("FREE_SWARM_WORKERS_JSONL_REQUIRED")
    for path in artifact_files:
        rel = path.relative_to(artifacts).as_posix()
        paths.append((f"artifacts:{rel}", path))
    return paths


def snapshot_inputs(repo: Path, artifacts: Path, authority: dict[str, Any]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for label, path in _input_files(repo, artifacts, authority):
        stat = path.stat()
        entries.append({
            "label": label,
            "size": stat.st_size,
            "sha256": sha256_file(path),
        })
    canonical = json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return {
        "schema": "CLAY_COLLECTIVE_METRICS_SOURCE_SNAPSHOT/v1",
        "entry_count": len(entries),
        "entries": entries,
        "snapshot_sha256": sha256_bytes(canonical),
    }


def _parse_time(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def publication_decision(existing: dict[str, Any], candidate: dict[str, Any]) -> tuple[str, str]:
    """Return (decision, reason) for a serialized publication attempt."""
    if not existing:
        return "PUBLISH", "NO_EXISTING_PUBLICATION"

    current_epoch = str(candidate.get("authority_epoch") or "")
    existing_epoch = str(existing.get("authority_epoch") or "")
    try:
        current_key = epoch_key(current_epoch)
    except FreshnessError:
        return "REJECT", "CANDIDATE_AUTHORITY_EPOCH_INVALID"
    try:
        existing_key = epoch_key(existing_epoch)
    except FreshnessError:
        existing_key = ()

    if existing_key > current_key:
        return "REJECT", "EXISTING_NEWER_AUTHORITY_EPOCH"

    current_freshness = candidate.get("freshness") if isinstance(candidate.get("freshness"), dict) else {}
    existing_freshness = existing.get("freshness") if isinstance(existing.get("freshness"), dict) else {}
    current_snapshot = current_freshness.get("source_snapshot_sha256")
    existing_snapshot = existing_freshness.get("source_snapshot_sha256")
    if (
        existing_key == current_key
        and existing_freshness.get("status") == "FRESH_SHARED_SNAPSHOT"
        and existing_snapshot
        and existing_snapshot == current_snapshot
    ):
        return "IDEMPOTENT", "SAME_AUTHORITY_AND_SOURCE_SNAPSHOT"

    if existing_key == current_key:
        old_time = _parse_time(existing.get("generated_at"))
        new_time = _parse_time(candidate.get("generated_at"))
        if old_time is not None and new_time is not None and old_time > new_time:
            return "REJECT", "OUT_OF_ORDER_OLDER_WRITER"
        if old_time is not None and new_time is not None and old_time == new_time and existing_snapshot != current_snapshot:
            return "REJECT", "AMBIGUOUS_EQUAL_TIME_DIFFERENT_SNAPSHOT"

    return "PUBLISH", "NEWER_OR_DIFFERENT_ADMISSIBLE_SNAPSHOT"


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        try:
            dir_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass
    finally:
        if tmp.exists():
            tmp.unlink()


@contextlib.contextmanager
def publication_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def build_candidate(repo: Path, artifacts: Path, authority: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    config = base.load_config(repo)
    if config.get("schema") != "CLAY_GO_COLLECTIVE_METRICS_CONFIG/v1":
        raise FreshnessError("GO_METRICS_CONFIG_REQUIRED")
    workers = base.explicit_worker_rows(repo)
    workers.extend(base.free_swarm_rows(artifacts))
    deltas = base.delta_rows(repo)
    base.attach_delta_metrics(workers, deltas, config)
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()
    return {
        "schema": base.SCHEMA,
        "generated_at": generated_at,
        "generation_class": "EXECUTED_SHARED_SNAPSHOT_PUBLISHER",
        "authority_epoch": authority["authority_epoch"],
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "architecture": "HCU",
        "source_checkout_head": checkout_head(repo),
        "config_sha256": base.sha256_json(config),
        "worker_record_count": len(workers),
        "aggregate": base.aggregate(workers, config),
        "workers": workers,
        "anti_goodhart": config.get("anti_goodhart"),
        "selection_policy": config.get("selection_policy"),
        "freshness": {
            "schema": FRESHNESS_SCHEMA,
            "status": "FRESH_SHARED_SNAPSHOT",
            "authority_epoch": authority["authority_epoch"],
            "supervisor_inbox_sha256": authority["inbox_sha256"],
            "supervisor_steering_sha256": authority["steering_sha256"],
            "source_snapshot_sha256": snapshot["snapshot_sha256"],
            "source_snapshot_entry_count": snapshot["entry_count"],
            "shared_snapshot_verified_before_publish": True,
            "local_writer_serialization": "fcntl.flock/LOCK_EX",
            "atomic_replacement": "os.replace",
        },
        "publication": {
            "schema": PUBLICATION_SCHEMA,
            "decision": "PENDING",
            "reason": None,
        },
        "runtime_credit_added": 0,
        "note": "Derived measurement only. Freshness does not mint canonical truth or runtime/model/training credit.",
    }


def freshness_markdown(result: dict[str, Any]) -> str:
    body = base.markdown(result)
    freshness = result.get("freshness") or {}
    prefix = (
        "<!-- GO_COLLECTIVE_FRESHNESS:BEGIN -->\n"
        "### Publication freshness\n"
        f"- status: `{freshness.get('status')}`\n"
        f"- authority epoch: `{result.get('authority_epoch')}`\n"
        f"- source snapshot: `{freshness.get('source_snapshot_sha256')}`\n"
        f"- input entries: `{freshness.get('source_snapshot_entry_count')}`\n"
        "- writer admission: serialized + out-of-order fail-closed + atomic replace\n"
        "<!-- GO_COLLECTIVE_FRESHNESS:END -->\n\n"
    )
    return prefix + body


def publish(repo: Path, artifacts: Path, out_json: Path, out_md: Path, update_readme: bool = False) -> dict[str, Any]:
    lock_path = out_json.with_suffix(out_json.suffix + ".publish.lock")
    with publication_lock(lock_path):
        authority_before = resolve_authority(repo)
        snapshot_before = snapshot_inputs(repo, artifacts, authority_before)
        candidate = build_candidate(repo, artifacts, authority_before, snapshot_before)
        authority_after = resolve_authority(repo)
        if authority_after["authority_epoch"] != authority_before["authority_epoch"]:
            raise FreshnessError("AUTHORITY_CHANGED_DURING_PUBLICATION")
        if authority_after["inbox_sha256"] != authority_before["inbox_sha256"] or authority_after["steering_sha256"] != authority_before["steering_sha256"]:
            raise FreshnessError("AUTHORITY_BYTES_CHANGED_DURING_PUBLICATION")
        snapshot_after = snapshot_inputs(repo, artifacts, authority_after)
        if snapshot_after["snapshot_sha256"] != snapshot_before["snapshot_sha256"]:
            raise FreshnessError("SOURCE_CHANGED_DURING_SHARED_SNAPSHOT")

        existing = base.read_json(out_json) if out_json.exists() else {}
        decision, reason = publication_decision(existing, candidate)
        candidate["publication"] = {
            "schema": PUBLICATION_SCHEMA,
            "decision": decision,
            "reason": reason,
        }
        if decision == "REJECT":
            raise FreshnessError(f"PUBLICATION_REJECTED:{reason}")
        if decision == "IDEMPOTENT":
            return existing

        md = freshness_markdown(candidate)
        atomic_write(out_json, json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        atomic_write(out_md, md)
        if update_readme:
            readme = repo / "free swarm/README.md"
            current = readme.read_text(encoding="utf-8") if readme.exists() else "# Free Swarm\n"
            atomic_write(readme, base.replace_block(current, md))
        return candidate


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--artifacts", type=Path, default=Path("/artifacts/clay-entityos-swarm"))
    ap.add_argument("--output-json", type=Path, default=None)
    ap.add_argument("--output-md", type=Path, default=None)
    ap.add_argument("--update-readme", action="store_true")
    args = ap.parse_args()

    repo = args.repo.resolve()
    artifacts = args.artifacts.resolve()
    out_json = args.output_json or (repo / "free swarm/GO_COLLECTIVE_METRICS.json")
    out_md = args.output_md or (repo / "free swarm/GO_COLLECTIVE_METRICS.md")
    try:
        result = publish(repo, artifacts, out_json, out_md, args.update_readme)
    except FreshnessError as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)}, sort_keys=True))
        return 2
    print(out_json)
    print(out_md)
    print(json.dumps({
        "status": (result.get("freshness") or {}).get("status"),
        "authority_epoch": result.get("authority_epoch"),
        "source_snapshot_sha256": (result.get("freshness") or {}).get("source_snapshot_sha256"),
        "publication": result.get("publication"),
        "runtime_credit_added": result.get("runtime_credit_added", 0),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
