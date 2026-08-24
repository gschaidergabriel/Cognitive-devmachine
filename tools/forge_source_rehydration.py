#!/usr/bin/env python3
"""Exact-source rehydration boundary for Free-Swarm Forge candidates.

This module deliberately stops before patch synthesis and execution. Model output is
candidate evidence only. Target paths are validated, exact Git object identities are
bound, and bounded source context is read from the committed blob rather than the
mutable working tree. No model-authored command is executed here.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any

SCHEMA = "CLAY_FORGE_SOURCE_REHYDRATION/v1"
MAX_TARGETS = 12
MAX_FILE_BYTES = 96_000
MAX_TOTAL_BYTES = 384_000
SAFE_ENV = {
    "PATH": os.environ.get("PATH", ""),
    "HOME": "/tmp",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "PYTHONDONTWRITEBYTECODE": "1",
}


class RehydrationError(RuntimeError):
    pass


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _safe_target(value: str) -> bool:
    if not value or len(value) > 500 or any(ord(ch) < 32 for ch in value):
        return False
    path = Path(value)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and not str(path).startswith(".git")
        and not str(path).startswith("/")
    )


def _git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=SAFE_ENV,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", errors="replace")[-800:]
        raise RehydrationError(f"git {' '.join(args)} failed: {detail}")
    return proc.stdout


def _git_text(repo: Path, *args: str) -> str:
    return _git(repo, *args).decode("utf-8", errors="strict").strip()


def source_identity(repo: Path) -> dict[str, str]:
    repo = repo.resolve()
    return {
        "commit": _git_text(repo, "rev-parse", "HEAD"),
        "tree": _git_text(repo, "rev-parse", "HEAD^{tree}"),
    }


def _blob(repo: Path, commit: str, target: str) -> tuple[str, bytes]:
    blob_sha = _git_text(repo, "rev-parse", f"{commit}:{target}")
    kind = _git_text(repo, "cat-file", "-t", blob_sha)
    if kind != "blob":
        raise RehydrationError(f"target is not a blob: {target}")
    return blob_sha, _git(repo, "cat-file", "blob", blob_sha)


def rehydrate_candidate(repo: Path, proposal: dict[str, Any]) -> dict[str, Any]:
    """Bind a candidate to exact committed target bytes without executing it.

    Large files are represented with a bounded UTF-8 prefix plus explicit
    truncation metadata. A truncated/binary context is never patch-synthesis-ready.
    """
    if not isinstance(proposal, dict):
        raise RehydrationError("proposal must be an object")
    raw_targets = proposal.get("target_files")
    if not isinstance(raw_targets, list) or not raw_targets or len(raw_targets) > MAX_TARGETS:
        raise RehydrationError("target_files must contain 1..MAX_TARGETS entries")
    if any(not isinstance(x, str) or not _safe_target(x) for x in raw_targets):
        raise RehydrationError("unsafe target path")
    targets = list(dict.fromkeys(raw_targets))
    if len(targets) != len(raw_targets):
        raise RehydrationError("duplicate target path")

    repo = repo.resolve()
    src = source_identity(repo)
    files: list[dict[str, Any]] = []
    total_context = 0
    all_full_text = True

    for target in targets:
        blob_sha, data = _blob(repo, src["commit"], target)
        full_size = len(data)
        remaining = max(0, MAX_TOTAL_BYTES - total_context)
        take = min(full_size, MAX_FILE_BYTES, remaining)
        prefix = data[:take]
        truncated = take < full_size
        try:
            text = prefix.decode("utf-8", errors="strict")
            utf8 = True
        except UnicodeDecodeError:
            text = ""
            utf8 = False
        if not utf8 or truncated:
            all_full_text = False
        total_context += take
        files.append(
            {
                "path": target,
                "blob_sha": blob_sha,
                "sha256": _sha_bytes(data),
                "size_bytes": full_size,
                "context_bytes": take,
                "truncated": truncated,
                "utf8": utf8,
                "content": text if utf8 else None,
            }
        )

    binding_material = {
        "schema": SCHEMA,
        "candidate_sha256": _canonical_sha(proposal),
        "source": src,
        "files": [
            {
                "path": f["path"],
                "blob_sha": f["blob_sha"],
                "sha256": f["sha256"],
                "size_bytes": f["size_bytes"],
                "context_bytes": f["context_bytes"],
                "truncated": f["truncated"],
                "utf8": f["utf8"],
            }
            for f in files
        ],
    }
    binding_sha = _canonical_sha(binding_material)
    return {
        **binding_material,
        "binding_sha256": binding_sha,
        "files": files,
        "context_state": "CONTEXT_READY" if all_full_text else "CONTEXT_BOUNDED_NOT_PATCH_READY",
        "execution_state": "EXECUTION_BLOCKED",
        "execution_reason": "NO_ADMITTED_ISOLATED_CANDIDATE_EXECUTOR_BOUND",
        "model_commands_executed": 0,
    }


def build_patch_synthesis_packet(rehydrated: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    """Create the second-stage input packet only when complete exact text exists."""
    if rehydrated.get("schema") != SCHEMA:
        raise RehydrationError("wrong rehydration schema")
    if rehydrated.get("candidate_sha256") != _canonical_sha(proposal):
        raise RehydrationError("candidate identity changed")
    if rehydrated.get("context_state") != "CONTEXT_READY":
        raise RehydrationError("exact complete text context required")
    files = rehydrated.get("files")
    if not isinstance(files, list) or not files:
        raise RehydrationError("missing files")
    packet = {
        "schema": "CLAY_FORGE_PATCH_SYNTHESIS_PACKET/v1",
        "candidate_sha256": rehydrated["candidate_sha256"],
        "source_commit": rehydrated["source"]["commit"],
        "source_tree": rehydrated["source"]["tree"],
        "source_binding_sha256": rehydrated["binding_sha256"],
        "proposal": proposal,
        "targets": [
            {
                "path": f["path"],
                "blob_sha": f["blob_sha"],
                "sha256": f["sha256"],
                "content": f["content"],
            }
            for f in files
        ],
        "required_next_gate": "PATCH_SYNTHESIS_THEN_GIT_APPLY_CHECK_SAME_SOURCE",
        "execution_authority": "NONE",
    }
    packet["packet_sha256"] = _canonical_sha(packet)
    return packet
