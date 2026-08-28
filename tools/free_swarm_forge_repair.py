#!/usr/bin/env python3
"""Source-bound repair feed for the Free-Swarm -> Evidence-Forge funnel.

This module is deliberately read-only with respect to repository source and Forge
state. It converts recent PATCH_REJECTED / NEEDS_IMPLEMENTATION candidate records
into bounded repair packets for future workers. Source context is read from exact
Git objects at the current checkout HEAD, never from mutable worktree bytes.

The previous candidate remains noncanonical. A repair packet grants no execution,
truth, effect, provider, or acceptance authority; it only supplies better evidence
for synthesizing a replacement candidate that Forge must independently validate.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import threading
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = Path(os.getenv("CLAY_SWARM_ARTIFACT_ROOT", "/artifacts/clay-entityos-swarm"))
FORGE_DB = ARTIFACT_ROOT / "forge/forge.sqlite3"
SCHEMA = "CLAY_FORGE_REPAIR_PACKET/v2"
MAX_REPAIRS = 128
MAX_TARGETS = 2
MAX_SOURCE_BYTES_PER_TARGET = 12_000
MAX_OLD_PATCH_CHARS = 8_000
CACHE_SECONDS = 20.0

_SAFE_ENV = {
    "PATH": os.environ.get("PATH", ""),
    "HOME": "/tmp",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "PYTHONDONTWRITEBYTECODE": "1",
}
_CACHE_LOCK = threading.Lock()
_CACHE_AT = 0.0
_CACHE_KEY: tuple[str, str] | None = None
_CACHE_ROWS: list[dict[str, Any]] = []


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(repo: Path, *args: str) -> bytes:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=_SAFE_ENV,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=15,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace")[-800:])
    return proc.stdout


def _git_text(repo: Path, *args: str) -> str:
    return _git(repo, *args).decode("utf-8", errors="strict").strip()


def _safe_target(value: str) -> bool:
    if not value or len(value) > 500 or any(ord(ch) < 32 for ch in value):
        return False
    path = Path(value)
    low = value.lower()
    if path.is_absolute() or ".." in path.parts or str(path).startswith(".git"):
        return False
    if low.endswith((".env", ".pem", ".key", ".p12", ".pfx")):
        return False
    return value not in {".", "./"}


def _source_identity(repo: Path) -> dict[str, str]:
    return {
        "commit": _git_text(repo, "rev-parse", "HEAD"),
        "tree": _git_text(repo, "rev-parse", "HEAD^{tree}"),
    }


def _patch_anchor_lines(patch: str, target: str) -> list[str]:
    current_target = False
    anchors: list[str] = []
    for line in patch.splitlines():
        if line.startswith("--- "):
            candidate = line[4:].split("\t", 1)[0].strip()
            if candidate.startswith("a/"):
                candidate = candidate[2:]
            current_target = candidate == target
            continue
        if line.startswith("+++ "):
            candidate = line[4:].split("\t", 1)[0].strip()
            if candidate.startswith("b/"):
                candidate = candidate[2:]
            current_target = current_target or candidate == target
            continue
        if not current_target or len(line) < 2 or line[0] not in {" ", "-"}:
            continue
        value = line[1:].strip()
        if len(value) >= 12 and value not in anchors:
            anchors.append(value)
        if len(anchors) >= 12:
            break
    return anchors


def _bounded_excerpt(text: str, anchors: list[str]) -> tuple[str, bool, str, list[int]]:
    limit = MAX_SOURCE_BYTES_PER_TARGET
    encoded = text.encode("utf-8")
    if len(encoded) <= limit:
        return text, False, "FULL_FILE", [0, len(text)]

    # Bound by characters after locating an exact old/context anchor. The final
    # UTF-8 byte cap is enforced after slicing to avoid oversized prompt payloads.
    for anchor in anchors:
        idx = text.find(anchor)
        if idx < 0:
            continue
        half = max(1, limit // 4)
        start = max(0, idx - half)
        end = min(len(text), idx + len(anchor) + half)
        excerpt = text[start:end]
        while len(excerpt.encode("utf-8")) > limit and len(excerpt) > 1:
            excerpt = excerpt[: max(1, len(excerpt) * 3 // 4)]
            end = start + len(excerpt)
        return excerpt, True, "PATCH_CONTEXT_ANCHOR", [start, end]

    # No trustworthy anchor: expose bounded head/tail evidence but explicitly
    # mark the packet truncated so workers cannot call it complete patch context.
    head = text[: max(1, limit // 8)]
    tail = text[-max(1, limit // 8) :]
    excerpt = head + "\n...[SOURCE_EXCERPT_GAP]...\n" + tail
    while len(excerpt.encode("utf-8")) > limit and len(head) > 1 and len(tail) > 1:
        head = head[: len(head) * 3 // 4]
        tail = tail[-len(tail) * 3 // 4 :]
        excerpt = head + "\n...[SOURCE_EXCERPT_GAP]...\n" + tail
    return excerpt, True, "HEAD_TAIL_FALLBACK", [0, len(text)]


def _committed_source(repo: Path, commit: str, target: str, old_patch: str) -> dict[str, Any]:
    if not _safe_target(target):
        return {"path": target, "state": "REJECTED_UNSAFE_PATH"}
    try:
        blob_sha = _git_text(repo, "rev-parse", f"{commit}:{target}")
        kind = _git_text(repo, "cat-file", "-t", blob_sha)
        if kind != "blob":
            return {"path": target, "state": "NOT_A_BLOB"}
        raw = _git(repo, "cat-file", "blob", blob_sha)
    except Exception:
        return {"path": target, "state": "NEW_OR_MISSING_AT_REPAIR_HEAD"}
    if b"\x00" in raw[:8192]:
        return {"path": target, "state": "BINARY_NOT_EXPOSED", "blob_sha": blob_sha}
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return {"path": target, "state": "NON_UTF8_NOT_EXPOSED", "blob_sha": blob_sha}
    anchors = _patch_anchor_lines(old_patch, target)
    excerpt, truncated, strategy, char_range = _bounded_excerpt(text, anchors)
    return {
        "path": target,
        "state": "TRACKED_COMMITTED_SOURCE",
        "blob_sha": blob_sha,
        "sha256": _sha_bytes(raw),
        "size_bytes": len(raw),
        "truncated": truncated,
        "excerpt_strategy": strategy,
        "excerpt_char_range": char_range,
        "patch_anchor_candidates": anchors[:4],
        "content": excerpt,
    }


def load_repair_packets(
    db_path: Path = FORGE_DB,
    repo_root: Path = ROOT,
    limit: int = MAX_REPAIRS,
) -> list[dict[str, Any]]:
    """Return bounded failed candidates rebound to exact current committed source."""
    if not db_path.exists():
        return []
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=0.5)
        con.row_factory = sqlite3.Row
        columns = {str(row[1]) for row in con.execute("PRAGMA table_info(candidates)")}
        repo_head_expr = "repo_head" if "repo_head" in columns else "NULL AS repo_head"
        rows = con.execute(
            "SELECT candidate_hash,delta_id,proposal_json,state,last_reason,ingested_at,evaluated_at,"
            + repo_head_expr
            + " FROM candidates WHERE state IN ('PATCH_REJECTED','NEEDS_IMPLEMENTATION') "
            "ORDER BY COALESCE(evaluated_at,ingested_at) DESC LIMIT ?",
            (max(1, min(int(limit), MAX_REPAIRS)),),
        ).fetchall()
        con.close()
    except Exception:
        return []

    try:
        source = _source_identity(repo_root)
    except Exception:
        return []

    out: list[dict[str, Any]] = []
    for row in rows:
        try:
            proposal = json.loads(row["proposal_json"])
        except Exception:
            continue
        if not isinstance(proposal, dict):
            continue
        raw_targets = proposal.get("target_files")
        if not isinstance(raw_targets, list):
            continue
        targets = [x for x in raw_targets if isinstance(x, str) and _safe_target(x)][:MAX_TARGETS]
        if not targets:
            continue
        old_patch = str(proposal.get("patch_unified_diff") or "")[:MAX_OLD_PATCH_CHARS]
        sources = [_committed_source(repo_root, source["commit"], target, old_patch) for target in targets]
        if not any(item.get("state") == "TRACKED_COMMITTED_SOURCE" for item in sources):
            continue
        out.append(
            {
                "schema": SCHEMA,
                "repair_of_candidate_hash": str(row["candidate_hash"]),
                "repair_of_delta_id": str(row["delta_id"] or ""),
                "previous_candidate_source_head": str(row["repo_head"] or "") or None,
                "previous_state": str(row["state"]),
                "previous_reason": str(row["last_reason"] or "")[:1200],
                "previous_hypothesis": str(proposal.get("hypothesis") or "")[:2000],
                "previous_mechanism": str(proposal.get("mechanism") or "")[:2000],
                "previous_patch_unified_diff": old_patch,
                "repair_source_commit": source["commit"],
                "repair_source_tree": source["tree"],
                "target_sources": sources,
                "execution_authority": "NONE",
                "canonical_truth": False,
            }
        )
    return out


def current_repair_packets(db_path: Path = FORGE_DB, repo_root: Path = ROOT) -> list[dict[str, Any]]:
    global _CACHE_AT, _CACHE_KEY, _CACHE_ROWS
    key = (str(db_path), str(repo_root))
    now = time.monotonic()
    with _CACHE_LOCK:
        if _CACHE_KEY == key and now - _CACHE_AT < CACHE_SECONDS:
            return list(_CACHE_ROWS)
    rows = load_repair_packets(db_path=db_path, repo_root=repo_root)
    with _CACHE_LOCK:
        _CACHE_KEY = key
        _CACHE_AT = now
        _CACHE_ROWS = rows
    return list(rows)


def repair_suffix(serial: int, rows: list[dict[str, Any]]) -> str:
    """Route roughly half of logical calls through backlog repair while it exists."""
    if not rows or serial % 2:
        return ""
    index = max(0, serial // 2 - 1) % len(rows)
    payload = json.dumps(rows[index], ensure_ascii=False, separators=(",", ":"))
    return f"""

FORGE SOURCE-BOUND REPAIR PACKET
{payload}

REPAIR LAW
- The previous candidate failed Forge. Replace or falsify it; never defend it by weakening Forge.
- Synthesize against repair_source_commit and TRACKED_COMMITTED_SOURCE bytes above, not remembered or guessed source.
- Preserve repair_of_candidate_hash and repair_of_delta_id in the replacement ARCHITECTURE_DELTA_JSON for lineage.
- If a required edit is outside a truncated excerpt, set ready_for_forge=false rather than inventing hunk context.
- ready_for_forge=true requires a real unified diff, exact declared target paths, and bounded repo-root tests.
- Do not use shell/network/effect tricks to make acceptance pass. The candidate remains noncanonical and Forge must independently validate it.
"""
