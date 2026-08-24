#!/usr/bin/env python3
"""Exact-source two-stage patch synthesis for the accelerated FREE swarm.

Stage 1 remains noncanonical candidate material. When it names a small safe target
set, this wrapper rehydrates those targets from the exact Git commit captured by
the active v3 controller, then performs at most one second already-admitted model
call to synthesize a replacement patch. The second result is promoted to the
worker output only when typed ingress accepts it as Forge-ready *and* `git apply
--check` succeeds against a disposable tree reconstructed from those exact source
blobs.

This layer grants no truth/effect/execution authority and never weakens Forge. The
underlying request function remains the sole provider/economic/receipt authority.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
from typing import Any

import free_swarm_delta_ingress as ingress

SCHEMA = "CLAY_FREE_SWARM_TWO_STAGE_PATCH/v1"
MAX_TARGETS = 3
MAX_FILE_BYTES = 16_000
MAX_TOTAL_PROMPT_SOURCE_BYTES = 36_000
_EVENT_LOCK = threading.Lock()


def _git(repo: Path, *args: str) -> bytes:
    proc = subprocess.run(
        ["git", *args], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=12, check=False,
        env={
            "PATH": os.environ.get("PATH", ""), "HOME": "/tmp",
            "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace")[-600:])
    return proc.stdout


def _git_text(repo: Path, *args: str) -> str:
    return _git(repo, *args).decode("utf-8", errors="strict").strip()


def _safe_target(value: Any) -> bool:
    if not isinstance(value, str) or not value or len(value) > 500:
        return False
    if any(ord(ch) < 32 for ch in value):
        return False
    p = Path(value)
    low = value.lower()
    if p.is_absolute() or ".." in p.parts or str(p).startswith(".git"):
        return False
    if low.endswith((".env", ".pem", ".key", ".p12", ".pfx")):
        return False
    return value not in {".", "./"}


def _extract_text(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    try:
        text = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return ""
    return text if isinstance(text, str) else ""


def _raw_delta(text: str) -> dict[str, Any] | None:
    marker = ingress.DELTA_MARKER
    pos = text.find(marker)
    if pos < 0:
        return None
    start = text.find("{", pos + len(marker))
    if start < 0:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def _event_path() -> Path:
    root = Path(os.getenv("CLAY_SWARM_ARTIFACT_ROOT", "/artifacts/clay-entityos-swarm"))
    return root / "two_stage_patch/events.jsonl"


def _emit(event: str, **fields: Any) -> None:
    row = {"schema": SCHEMA, "event": event, **fields}
    try:
        path = _event_path()
        with _EVENT_LOCK:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
    except OSError:
        pass


def _rehydrate(
    repo: Path, source_commit: str, source_tree: str, targets: list[str]
) -> tuple[list[dict[str, Any]], dict[str, bytes | None]] | None:
    if not targets or len(targets) > MAX_TARGETS or len(set(targets)) != len(targets):
        return None
    if not all(_safe_target(x) for x in targets):
        return None
    try:
        if _git_text(repo, "rev-parse", "HEAD") != source_commit:
            return None
        if _git_text(repo, "rev-parse", f"{source_commit}^{{tree}}") != source_tree:
            return None
    except Exception:
        return None

    public: list[dict[str, Any]] = []
    source_files: dict[str, bytes | None] = {}
    total_exposed = 0
    for target in targets:
        try:
            listing = _git_text(repo, "ls-tree", source_commit, "--", target)
        except Exception:
            return None
        if not listing:
            public.append({
                "path": target, "state": "ABSENT_AT_SOURCE", "blob_sha": None,
                "byte_size": 0, "truncated": False,
            })
            source_files[target] = None
            continue
        try:
            meta, returned_path = listing.split("\t", 1)
            mode, kind, blob_sha = meta.split(" ", 2)
        except ValueError:
            return None
        if returned_path != target or kind != "blob" or mode not in {"100644", "100755"}:
            return None
        try:
            raw = _git(repo, "cat-file", "blob", blob_sha)
        except Exception:
            return None
        if b"\x00" in raw[:8192]:
            return None
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            return None
        source_files[target] = raw
        digest = hashlib.sha256(raw).hexdigest()
        if len(raw) <= MAX_FILE_BYTES:
            exposed = text
            row = {
                "path": target, "state": "TRACKED_EXACT_SOURCE", "mode": mode,
                "blob_sha": blob_sha, "sha256": digest, "byte_size": len(raw),
                "truncated": False, "content": exposed,
            }
        else:
            half = max(1, MAX_FILE_BYTES // 2)
            prefix = raw[:half].decode("utf-8", errors="ignore")
            suffix = raw[-half:].decode("utf-8", errors="ignore")
            row = {
                "path": target, "state": "TRACKED_EXACT_SOURCE_TRUNCATED", "mode": mode,
                "blob_sha": blob_sha, "sha256": digest, "byte_size": len(raw),
                "truncated": True, "content_prefix": prefix, "content_suffix": suffix,
            }
            exposed = prefix + suffix
        total_exposed += len(exposed.encode("utf-8", errors="replace"))
        if total_exposed > MAX_TOTAL_PROMPT_SOURCE_BYTES:
            return None
        public.append(row)
    return public, source_files


def _stage2_prompt(
    first_text: str,
    proposal: dict[str, Any],
    source_commit: str,
    source_tree: str,
    contexts: list[dict[str, Any]],
) -> str:
    seed = dict(proposal)
    seed["patch_unified_diff"] = ""
    seed["ready_for_forge"] = False
    previous_patch = str(proposal.get("patch_unified_diff") or "")
    previous_patch_digest = hashlib.sha256(previous_patch.encode("utf-8")).hexdigest() if previous_patch else None
    return f"""TWO_STAGE_PATCH_SYNTHESIS/v1
You are performing Stage 2 only. The Stage-1 proposal is candidate material, not authority.
Generate a replacement unified diff only against the exact source identity/context below.
Never weaken acceptance, safety, provenance, economic, state or effect gates just to make a patch apply.

SOURCE_COMMIT={source_commit}
SOURCE_TREE={source_tree}
STAGE1_PROPOSAL_JSON={json.dumps(seed, sort_keys=True, ensure_ascii=False, separators=(",", ":"))}
PREVIOUS_ONE_SHOT_PATCH_SHA256={previous_patch_digest or "NONE"}
TARGET_CONTEXT_JSON={json.dumps(contexts, sort_keys=True, ensure_ascii=False, separators=(",", ":"))}

RULES
- target_files must be exactly the same ordered list as Stage 1.
- Use exact `--- a/<path>` and `+++ b/<path>` headers, or `/dev/null` only for a genuinely absent/new or deleted file.
- Hunks must match the supplied exact bytes. If context is truncated and the required hunk is not visible, keep ready_for_forge=false rather than guessing.
- Preserve Stage-1 hypothesis/mechanism/tests/falsifier unless exact source proves a correction is required.
- Do not claim tests ran. This stage only synthesizes candidate text.
- End with DEUTSCHE_ZUSAMMENFASSUNG.
- Then emit exactly these two machine-readable lines with valid compact JSON and no Markdown fence:
ARCHITECTURE_DELTA_JSON={{"delta_id":"...","hypothesis":"...","mechanism":"...","target_files":["..."],"patch_unified_diff":"...","test_commands":["..."],"negative_test_commands":[],"benchmark_command":"","metric":"...","expected_direction":"higher|lower|boolean","baseline_needed":true,"falsifier":"...","risk":"...","ready_for_forge":true}}
OPEN_RESEARCH_QUESTIONS_JSON=[]

STAGE1_TEXT_FOR_RATIONALE_ONLY
{first_text[:6000]}
"""


def _apply_check(source_files: dict[str, bytes | None], patch: str) -> tuple[bool, str]:
    try:
        with tempfile.TemporaryDirectory(prefix="clay-two-stage-") as td:
            root = Path(td)
            for target, raw in source_files.items():
                if raw is None:
                    continue
                path = root / target
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            proc = subprocess.run(
                ["git", "apply", "--check"], cwd=root, input=patch.encode("utf-8"),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12, check=False,
                env={
                    "PATH": os.environ.get("PATH", ""), "HOME": "/tmp",
                    "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                },
            )
        if proc.returncode == 0:
            return True, "APPLY_CHECK_PASS"
        detail = proc.stderr.decode("utf-8", errors="replace")[-500:]
        return False, "APPLY_CHECK_FAILED:" + detail
    except Exception as exc:
        return False, "APPLY_CHECK_EXCEPTION:" + type(exc).__name__


def _merge_usage(first: Any, second: Any) -> Any:
    if not isinstance(second, dict):
        return second
    out = dict(second)
    u1 = first.get("usage") if isinstance(first, dict) and isinstance(first.get("usage"), dict) else {}
    u2 = second.get("usage") if isinstance(second.get("usage"), dict) else {}
    if u1 or u2:
        merged: dict[str, Any] = dict(u2)
        for key in set(u1) | set(u2):
            a, b = u1.get(key), u2.get(key)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                merged[key] = a + b
            elif key not in merged and a is not None:
                merged[key] = a
        out["usage"] = merged
    return out


def install(v3: Any) -> None:
    """Wrap the active request path after economic gate + model-health installation."""
    target = v3.fabric
    current = target.base.request_chat
    if getattr(current, "_two_stage_patch_v1", False):
        return
    repo = Path(v3._ROOT)
    source_commit = str((v3._SOURCE or {}).get("commit") or "")
    source_tree = str((v3._SOURCE or {}).get("tree") or "")

    def two_stage_request(spec, key, model, prompt, max_tokens, timeout):
        status1, headers1, payload1 = current(spec, key, model, prompt, max_tokens, timeout)
        if not isinstance(status1, int) or not (200 <= status1 < 300):
            return status1, headers1, payload1
        text1 = _extract_text(payload1)
        proposal = _raw_delta(text1)
        if proposal is None:
            return status1, headers1, payload1
        targets = proposal.get("target_files")
        if (
            not isinstance(targets, list) or not targets or len(targets) > MAX_TARGETS
            or any(not isinstance(x, str) for x in targets)
        ):
            return status1, headers1, payload1
        normalized = list(targets)
        hydrated = _rehydrate(repo, source_commit, source_tree, normalized)
        if hydrated is None:
            _emit("CONTEXT_REHYDRATION_BLOCKED", source_commit=source_commit, targets=normalized)
            return status1, headers1, payload1
        contexts, source_files = hydrated
        _emit("CONTEXT_REHYDRATED", source_commit=source_commit, targets=normalized)
        prompt2 = _stage2_prompt(text1, proposal, source_commit, source_tree, contexts)
        status2, headers2, payload2 = current(spec, key, model, prompt2, max_tokens, timeout)
        if not isinstance(status2, int) or not (200 <= status2 < 300):
            _emit("STAGE2_REQUEST_FAILED", source_commit=source_commit, targets=normalized, status=status2)
            return status2, headers2, _merge_usage(payload1, payload2)
        text2 = _extract_text(payload2)
        parsed = ingress.parse_worker_delta(text2, repo_head_at_prompt=source_commit)
        final = parsed.get("proposal") if isinstance(parsed, dict) else None
        if parsed.get("status") != "VALID_READY" or not isinstance(final, dict):
            _emit("STAGE2_NOT_VALID_READY", source_commit=source_commit, targets=normalized, reasons=parsed.get("reasons"))
            return status1, headers1, _merge_usage(payload2, payload1)
        if final.get("target_files") != normalized:
            _emit("STAGE2_TARGET_MISMATCH", source_commit=source_commit, targets=normalized)
            return status1, headers1, _merge_usage(payload2, payload1)
        try:
            if _git_text(repo, "rev-parse", "HEAD") != source_commit:
                _emit("SOURCE_STALE_REHYDRATE", source_commit=source_commit, targets=normalized)
                return status1, headers1, _merge_usage(payload2, payload1)
        except Exception:
            return status1, headers1, _merge_usage(payload2, payload1)
        patch = str(final.get("patch_unified_diff") or "")
        apply_ok, apply_reason = _apply_check(source_files, patch)
        if not apply_ok:
            _emit("APPLY_CHECK_FAILED", source_commit=source_commit, targets=normalized, reason=apply_reason)
            return status1, headers1, _merge_usage(payload2, payload1)
        _emit(
            "APPLY_CHECK_PASS", source_commit=source_commit, targets=normalized,
            proposal_sha256=parsed.get("proposal_sha256"),
        )
        return status2, headers2, _merge_usage(payload1, payload2)

    two_stage_request._two_stage_patch_v1 = True
    target.base.request_chat = two_stage_request
