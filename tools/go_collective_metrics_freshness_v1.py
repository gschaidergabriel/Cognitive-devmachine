#!/usr/bin/env python3
"""Fail-closed freshness/atomicity substrate for GO collective metrics.

This module does not calculate Clay metrics.  It binds an already-calculated metrics
snapshot to the exact admitted supervisor epoch and the exact input bytes that were
observed before calculation, then refuses stale/out-of-order publication.

Evidence boundary: deterministic local publisher/control-plane mechanism only.  It
cannot mint EntityOS/HCU/model/training/runtime credit.
"""
from __future__ import annotations

import copy
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any, Iterable

SCHEMA = "COLLECTIVE_METRICS_FRESHNESS_RECEIPT/v1"
GENERATION_CLASS = "EXECUTABLE_FRESHNESS_GUARDED_PUBLISHER"
MARKER_PREFIX = "COLLECTIVE_METRICS_PUBLICATION_ID"


class FreshnessError(RuntimeError):
    """A fail-closed publication invariant was violated."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _json_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _epoch_key(value: Any) -> tuple[int, ...]:
    text = str(value or "").strip()
    if not re.fullmatch(r"\d+(?:\.\d+)*", text):
        raise FreshnessError(f"INVALID_AUTHORITY_EPOCH:{text or 'EMPTY'}")
    return tuple(int(part) for part in text.split("."))


def _git_head(repo: Path) -> str | None:
    try:
        p = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    out = p.stdout.strip()
    return out if p.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", out) else None


def resolve_authority(repo: Path) -> dict[str, Any]:
    """Resolve the inbox-selected steering epoch; self-consistent stale islands fail."""
    inbox_path = repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    inbox = _read_json(inbox_path)
    epoch = str(inbox.get("schema_version") or "")
    _epoch_key(epoch)
    steering_rel = inbox.get("steering")
    if not isinstance(steering_rel, str) or not steering_rel.strip():
        raise FreshnessError("SUPERVISOR_INBOX_STEERING_REQUIRED")
    steering_path = (repo / steering_rel).resolve()
    try:
        steering_path.relative_to(repo.resolve())
    except ValueError as exc:
        raise FreshnessError("STEERING_PATH_ESCAPES_REPO") from exc
    steering = _read_json(steering_path)
    steering_epoch = str(steering.get("schema_version") or "")
    _epoch_key(steering_epoch)
    if steering_epoch != epoch:
        raise FreshnessError(f"AUTHORITY_EPOCH_MISMATCH:INBOX={epoch}:STEERING={steering_epoch}")
    if str(inbox.get("active_program") or "") != "ENTITYOS_HCU":
        raise FreshnessError("ACTIVE_PROGRAM_NOT_ENTITYOS_HCU")
    if str(steering.get("program") or "") != "ENTITYOS_HCU":
        raise FreshnessError("STEERING_PROGRAM_NOT_ENTITYOS_HCU")
    return {
        "authority_epoch": epoch,
        "steering": steering_rel,
        "inbox_sha256": _file_sha(inbox_path),
        "steering_sha256": _file_sha(steering_path),
    }


def _input_paths(repo: Path, artifacts: Path | None) -> list[tuple[str, Path]]:
    """Return only source families actually consumed by go_collective_metrics.py."""
    paths: list[tuple[str, Path]] = []
    fixed = [
        repo / "research_entity/continuity/go_metrics/GO_METRICS_CONFIG_V1.json",
        repo / "free swarm/architecture_delta_evaluations.jsonl",
        repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
    ]
    for path in fixed:
        if path.is_file():
            paths.append((path.relative_to(repo).as_posix(), path))

    worker_root = repo / "research_entity/continuity/go_metrics/worker_records"
    if worker_root.exists():
        for path in sorted(worker_root.rglob("*.json")):
            if path.is_file():
                paths.append((path.relative_to(repo).as_posix(), path))

    if artifacts is not None and artifacts.exists():
        for path in sorted(artifacts.rglob("workers.jsonl")):
            if path.is_file():
                try:
                    rel = path.relative_to(artifacts).as_posix()
                except ValueError:
                    rel = path.as_posix()
                paths.append((f"ARTIFACTS/{rel}", path))
    return paths


def capture_input_snapshot(repo: Path, artifacts: Path | None) -> dict[str, Any]:
    """Hash the exact input families once, before metric calculation."""
    repo = repo.resolve()
    artifacts = artifacts.resolve() if artifacts is not None else None
    authority = resolve_authority(repo)
    entries: list[dict[str, Any]] = []
    max_mtime_ns = 0
    for logical, path in _input_paths(repo, artifacts):
        stat = path.stat()
        max_mtime_ns = max(max_mtime_ns, int(stat.st_mtime_ns))
        entries.append({
            "path": logical,
            "size": int(stat.st_size),
            "mtime_ns": int(stat.st_mtime_ns),
            "sha256": _file_sha(path),
        })
    root_state = {
        "artifact_root": str(artifacts) if artifacts is not None else None,
        "artifact_root_exists": bool(artifacts is not None and artifacts.exists()),
        "entry_count": len(entries),
        "entries": entries,
        "authority": authority,
    }
    return {
        "schema": "COLLECTIVE_METRICS_INPUT_SNAPSHOT/v1",
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_snapshot_sha256": _json_sha(root_state),
        "source_max_mtime_ns": max_mtime_ns,
        "entry_count": len(entries),
        "authority": authority,
        "canonical_source_sha": _git_head(repo),
        "artifact_root_exists": root_state["artifact_root_exists"],
    }


def assert_snapshot_unchanged(repo: Path, artifacts: Path | None, expected: dict[str, Any]) -> dict[str, Any]:
    """Re-read inputs just before publish; stale calculations cannot overwrite live state."""
    observed = capture_input_snapshot(repo, artifacts)
    fields = ("source_snapshot_sha256", "source_max_mtime_ns", "entry_count")
    changed = [key for key in fields if observed.get(key) != expected.get(key)]
    if observed.get("authority") != expected.get("authority"):
        changed.append("authority")
    if changed:
        raise FreshnessError("INPUT_SNAPSHOT_CHANGED_DURING_COMPUTE:" + ",".join(changed))
    return observed


def _semantic_result(result: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(result)
    for key in (
        "generated_at",
        "generation_class",
        "authority_epoch",
        "canonical_main_observed_before_write",
        "source_snapshot",
        "semantic_payload_sha256",
        "publication_id",
    ):
        value.pop(key, None)
    return value


def bind_publication(
    result: dict[str, Any],
    snapshot: dict[str, Any],
    authority: dict[str, Any],
    repo: Path,
) -> dict[str, Any]:
    bound = copy.deepcopy(result)
    semantic_sha = _json_sha(_semantic_result(bound))
    pub_material = {
        "authority_epoch": authority["authority_epoch"],
        "source_snapshot_sha256": snapshot["source_snapshot_sha256"],
        "source_max_mtime_ns": snapshot["source_max_mtime_ns"],
        "semantic_payload_sha256": semantic_sha,
    }
    publication_id = _json_sha(pub_material)
    bound.update({
        "generation_class": GENERATION_CLASS,
        "authority_epoch": authority["authority_epoch"],
        "canonical_main_observed_before_write": _git_head(repo),
        "source_snapshot": {
            "schema": snapshot.get("schema"),
            "captured_at": snapshot.get("captured_at"),
            "source_snapshot_sha256": snapshot.get("source_snapshot_sha256"),
            "source_max_mtime_ns": snapshot.get("source_max_mtime_ns"),
            "entry_count": snapshot.get("entry_count"),
            "artifact_root_exists": snapshot.get("artifact_root_exists"),
            "canonical_source_sha": snapshot.get("canonical_source_sha"),
        },
        "semantic_payload_sha256": semantic_sha,
        "publication_id": publication_id,
    })
    return bound


def _existing_order(existing: dict[str, Any]) -> tuple[tuple[int, ...], int | None, str | None, str | None]:
    epoch = _epoch_key(existing.get("authority_epoch"))
    snap = existing.get("source_snapshot")
    if not isinstance(snap, dict):
        return epoch, None, None, existing.get("semantic_payload_sha256")
    mtime = snap.get("source_max_mtime_ns")
    return (
        epoch,
        int(mtime) if isinstance(mtime, int) else None,
        snap.get("source_snapshot_sha256") if isinstance(snap.get("source_snapshot_sha256"), str) else None,
        existing.get("semantic_payload_sha256") if isinstance(existing.get("semantic_payload_sha256"), str) else None,
    )


def publication_decision(existing: dict[str, Any], candidate: dict[str, Any]) -> str:
    """Return PUBLISH/NOOP or reject a stale/ambiguous writer."""
    if not existing:
        return "PUBLISH"
    try:
        old_epoch, old_mtime, old_snapshot, old_semantic = _existing_order(existing)
    except FreshnessError:
        # Legacy/current file without a parseable authority cannot outrank admitted current authority.
        old_epoch, old_mtime, old_snapshot, old_semantic = (0,), None, None, None
    new_epoch = _epoch_key(candidate.get("authority_epoch"))
    if old_epoch > new_epoch:
        raise FreshnessError("OUT_OF_ORDER_AUTHORITY_WRITER")
    if old_epoch < new_epoch:
        return "PUBLISH"

    snap = candidate.get("source_snapshot")
    if not isinstance(snap, dict):
        raise FreshnessError("CANDIDATE_SOURCE_SNAPSHOT_REQUIRED")
    new_mtime_raw = snap.get("source_max_mtime_ns")
    if not isinstance(new_mtime_raw, int):
        raise FreshnessError("CANDIDATE_SOURCE_MTIME_REQUIRED")
    new_mtime = int(new_mtime_raw)
    new_snapshot = snap.get("source_snapshot_sha256")
    new_semantic = candidate.get("semantic_payload_sha256")

    if old_mtime is None:
        # Same admitted authority but legacy/non-fresh output: successor publisher may replace it.
        return "PUBLISH"
    if old_mtime > new_mtime:
        raise FreshnessError("OUT_OF_ORDER_SOURCE_WRITER")
    if old_mtime < new_mtime:
        return "PUBLISH"
    if old_snapshot == new_snapshot and old_semantic == new_semantic:
        return "NOOP_IDENTICAL_SNAPSHOT"
    if old_snapshot == new_snapshot and old_semantic != new_semantic:
        raise FreshnessError("NONDETERMINISTIC_SAME_INPUT_RESULT")
    raise FreshnessError("AMBIGUOUS_EQUAL_MTIME_DIFFERENT_SNAPSHOT")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
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


def _bind_markdown(markdown_text: str, candidate: dict[str, Any]) -> str:
    marker = (
        f"<!-- {MARKER_PREFIX}:{candidate['publication_id']} "
        f"authority_epoch={candidate['authority_epoch']} "
        f"source_snapshot={candidate['source_snapshot']['source_snapshot_sha256']} -->"
    )
    if marker in markdown_text:
        return markdown_text
    lines = markdown_text.splitlines()
    if lines:
        lines.insert(1, marker)
        return "\n".join(lines) + ("\n" if markdown_text.endswith("\n") else "")
    return marker + "\n"


def validate_published_pair(out_json: Path, out_md: Path) -> dict[str, Any]:
    result = _read_json(out_json)
    publication_id = result.get("publication_id")
    if not isinstance(publication_id, str) or not publication_id:
        raise FreshnessError("JSON_PUBLICATION_ID_REQUIRED")
    try:
        markdown_text = out_md.read_text(encoding="utf-8")
    except OSError as exc:
        raise FreshnessError("MARKDOWN_PUBLICATION_REQUIRED") from exc
    marker = f"<!-- {MARKER_PREFIX}:{publication_id} "
    if marker not in markdown_text:
        raise FreshnessError("JSON_MARKDOWN_PUBLICATION_MISMATCH")
    return {
        "publication_id": publication_id,
        "authority_epoch": result.get("authority_epoch"),
        "source_snapshot_sha256": (result.get("source_snapshot") or {}).get("source_snapshot_sha256"),
    }


def publish_fresh_outputs(
    *,
    repo: Path,
    artifacts: Path | None,
    result: dict[str, Any],
    markdown_text: str,
    out_json: Path,
    out_md: Path,
    expected_input_snapshot: dict[str, Any],
    receipt_path: Path | None = None,
) -> dict[str, Any]:
    """Publish one self-consistent pair or fail closed before replacing current state."""
    repo = repo.resolve()
    artifacts = artifacts.resolve() if artifacts is not None else None
    out_json = out_json.resolve()
    out_md = out_md.resolve()
    authority = resolve_authority(repo)
    if authority != expected_input_snapshot.get("authority"):
        raise FreshnessError("AUTHORITY_CHANGED_DURING_COMPUTE")
    observed = assert_snapshot_unchanged(repo, artifacts, expected_input_snapshot)
    candidate = bind_publication(result, observed, authority, repo)
    bound_md = _bind_markdown(markdown_text, candidate)

    lock_path = out_json.with_name(out_json.name + ".publish.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_fh:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
        # The input may move while waiting for another publisher.
        assert_snapshot_unchanged(repo, artifacts, expected_input_snapshot)
        existing = _read_json(out_json)
        decision = publication_decision(existing, candidate)
        if decision == "PUBLISH":
            # Markdown first, JSON last. Consumers must validate the shared publication id;
            # a crash between replaces therefore fails closed instead of accepting a mixed pair.
            _atomic_write(out_md, bound_md.encode("utf-8"))
            _atomic_write(
                out_json,
                (json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"),
            )
        validated = validate_published_pair(out_json, out_md)

    receipt = {
        "schema": SCHEMA,
        "status": decision,
        "authority_epoch": authority["authority_epoch"],
        "publication_id": validated["publication_id"],
        "source_snapshot_sha256": validated["source_snapshot_sha256"],
        "source_max_mtime_ns": expected_input_snapshot.get("source_max_mtime_ns"),
        "canonical_source_sha": _git_head(repo),
        "freshness_fail_closed": True,
        "shared_json_markdown_snapshot_verified": True,
        "provider_calls": 0,
        "paid_fallback_attempt_count": 0,
        "whole_entityos_hcu_runtime_credit": 0,
        "hcu_full_runtime_credit": 0,
        "jspace_model_runtime_credit": 0,
        "training_credit": 0,
    }
    if receipt_path is not None:
        _atomic_write(
            receipt_path.resolve(),
            (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
    return receipt
