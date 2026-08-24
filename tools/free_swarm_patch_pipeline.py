#!/usr/bin/env python3
"""Deterministic stage-2 patch synthesis/preflight support for the Free Swarm.

Exact source rehydration is delegated to ``forge_source_rehydration``. This module
owns worker-text parsing, stage-2 prompt construction and deterministic patch
preflight. It contains no provider/network code.

A patch may be normalized only for incorrect unified-diff hunk counts. Repair is
accepted only when ``git apply --recount`` succeeds against the exact source and
the regenerated diff then passes ordinary ``git apply --check`` in a fresh
exact-source clone. No fuzzy/3-way application is used.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any

import forge_source_rehydration as fsr

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
MAX_TARGET_FILES = 3
MAX_PATCH_BYTES = 250_000
DEFAULT_PER_FILE_CHARS = 18_000
DEFAULT_TOTAL_CHARS = 36_000


def balanced_json_span_after(text: str, marker: str) -> tuple[int, int, dict[str, Any]] | None:
    pos = text.find(marker)
    if pos < 0:
        return None
    start = text.find("{", pos + len(marker))
    if start < 0:
        return None
    depth = 0
    in_str = False
    escaped = False
    for index in range(start, len(text)):
        ch = text[index]
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(text[start:index + 1])
                except Exception:
                    return None
                return (start, index + 1, obj) if isinstance(obj, dict) else None
    return None


def architecture_delta(text: str) -> dict[str, Any] | None:
    found = balanced_json_span_after(text, "ARCHITECTURE_DELTA_JSON=")
    return found[2] if found else None


def canonicalize_architecture_delta(text: str, obj: dict[str, Any]) -> str:
    found = balanced_json_span_after(text, "ARCHITECTURE_DELTA_JSON=")
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if found is None:
        suffix = "" if text.endswith("\n") or not text else "\n"
        return text + suffix + "ARCHITECTURE_DELTA_JSON=" + raw + "\n"
    start, end, _ = found
    return text[:start] + raw + text[end:]


def safe_target(raw: str) -> str | None:
    value = str(raw or "").strip()
    if not value or len(value) > 300 or not fsr.safe_target(value):
        return None
    normalized = Path(value).as_posix()
    return None if normalized.startswith("./") else normalized


def target_files(obj: dict[str, Any], limit: int = MAX_TARGET_FILES) -> list[str]:
    out: list[str] = []
    values = obj.get("target_files")
    if not isinstance(values, list):
        return out
    for raw in values:
        if not isinstance(raw, str):
            continue
        normalized = safe_target(raw)
        if normalized and normalized not in out:
            out.append(normalized)
        if len(out) >= limit:
            break
    return out


def proposal_complete(obj: dict[str, Any]) -> bool:
    tests = obj.get("test_commands")
    return bool(
        target_files(obj)
        and isinstance(tests, list)
        and any(isinstance(x, str) and x.strip() for x in tests)
        and isinstance(obj.get("falsifier"), str)
        and obj["falsifier"].strip()
    )


def _git(cwd: Path, *args: str, input_text: str | None = None, timeout: int = 45) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=cwd, input=input_text, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as exc:
        return 125, "", f"{type(exc).__name__}:{exc}"


def _source_exists(repo: Path, source_head: str) -> tuple[bool, str]:
    if not COMMIT_RE.fullmatch(source_head):
        return False, "SOURCE_HEAD_INVALID"
    rc, _, err = _git(repo, "cat-file", "-e", source_head + "^{commit}")
    return rc == 0, "" if rc == 0 else "SOURCE_COMMIT_UNAVAILABLE:" + err[-500:]


def rehydrate_targets(
    repo: Path,
    source_head: str,
    targets: list[str],
    *,
    per_file_chars: int = DEFAULT_PER_FILE_CHARS,
    total_chars: int = DEFAULT_TOTAL_CHARS,
) -> dict[str, Any]:
    proposal = {"target_files": targets}
    try:
        got = fsr.rehydrate_candidate(
            repo,
            proposal,
            source_commit=source_head,
            max_targets=MAX_TARGET_FILES,
            max_file_bytes=max(1, int(per_file_chars)),
            max_total_bytes=max(1, int(total_chars)),
        )
    except fsr.RehydrationError as exc:
        message = str(exc)
        if "unsafe target path" in message:
            reason = "UNSAFE_TARGET_PATH"
        elif "source commit" in message or "rev-parse" in message:
            reason = "SOURCE_COMMIT_UNAVAILABLE"
        else:
            reason = "SOURCE_REHYDRATION_FAILED:" + message[-500:]
        return {"ok": False, "reason": reason, "source_head": source_head, "files": []}

    records = [{
        "path": row["path"],
        "state": "BOUND_TEXT_SOURCE" if row.get("utf8") else "BINARY_TARGET_NOT_SUPPORTED",
        "git_blob": row.get("blob_sha"),
        "sha256": row.get("sha256"),
        "bytes_total": row.get("size_bytes"),
        "bytes_supplied": row.get("context_bytes"),
        "truncated": bool(row.get("truncated")),
        "content": row.get("content") or "",
    } for row in got.get("files") or []]
    ready = got.get("context_state") == "CONTEXT_READY"
    return {
        "ok": ready,
        "reason": None if ready else got.get("context_state"),
        "source_head": got["source"]["commit"],
        "source_tree": got["source"]["tree"],
        "source_binding_sha256": got.get("binding_sha256"),
        "candidate_sha256": got.get("candidate_sha256"),
        "files": records,
        "context_complete": ready,
        "execution_state": got.get("execution_state"),
    }


def source_capsule_text(binding: dict[str, Any]) -> str:
    chunks = [
        "CLAY_FORGE_PATCH_SYNTHESIS_PACKET/v1",
        f"source_head={binding.get('source_head')}",
        f"source_tree={binding.get('source_tree')}",
        f"source_binding_sha256={binding.get('source_binding_sha256')}",
        "execution_authority=NONE",
        "authority=CANDIDATE_INPUT_ONLY",
    ]
    for row in binding.get("files") or []:
        chunks.extend([
            f"\nTARGET path={row.get('path')}",
            f"state={row.get('state')}",
            f"git_blob={row.get('git_blob')}",
            f"sha256={row.get('sha256')}",
            f"bytes_total={row.get('bytes_total')}",
            f"bytes_supplied={row.get('bytes_supplied')}",
            f"truncated={str(bool(row.get('truncated'))).lower()}",
            "--- BEGIN EXACT TARGET CONTENT ---",
            str(row.get("content") or ""),
            "--- END EXACT TARGET CONTENT ---",
        ])
    return "\n".join(chunks)


def stage2_prompt(protocol: str, proposal: dict[str, Any], binding: dict[str, Any]) -> str:
    stable = dict(proposal)
    stable["patch_unified_diff"] = ""
    stable["ready_for_forge"] = False
    proposal_json = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"""{protocol}

ENTITYOS/HCU TWO-STAGE PATCH SYNTHESIS — STAGE 2
The stage-1 proposal below is noncanonical candidate input. Produce only the
source-bound implementation delta. Do not change target_files, test_commands,
hypothesis or falsifier. The exact source head/tree/blob binding is fixed.

Fail-closed rules:
- Modify only the declared target_files.
- Use only exact visible source bytes below for removals/context; never invent old lines.
- Emit a normal unified diff with exact ---/+++ paths and valid @@ hunk counts.
- No Markdown fence, ellipsis, prose placeholder, rename/copy metadata or binary patch.
- If supplied exact context is insufficient, keep patch_unified_diff empty and ready_for_forge=false.
- ready_for_forge is only a request for deterministic local preflight; the controller forces it false unless ordinary git apply --check succeeds on this exact source.
- End with DEUTSCHE_ZUSAMMENFASSUNG and one compact ARCHITECTURE_DELTA_JSON line.

STAGE1_PROPOSAL_JSON={proposal_json}

{source_capsule_text(binding)}
"""


def _patch_declared_paths(patch: str) -> tuple[bool, set[str], str]:
    if not patch or len(patch.encode("utf-8", errors="replace")) > MAX_PATCH_BYTES:
        return False, set(), "PATCH_EMPTY_OR_TOO_LARGE"
    paths: set[str] = set()
    forbidden_meta = ("rename from ", "rename to ", "copy from ", "copy to ", "GIT binary patch")
    for line in patch.splitlines():
        if line.startswith(forbidden_meta):
            return False, set(), "PATCH_RENAME_COPY_BINARY_NOT_ALLOWED"
        if line.startswith(("--- ", "+++ ")):
            value = line[4:].split("\t", 1)[0].strip()
            if value == "/dev/null":
                continue
            normalized = safe_target(re.sub(r"^[ab]/", "", value))
            if normalized is None:
                return False, set(), "PATCH_UNSAFE_HEADER_PATH"
            paths.add(normalized)
        elif line.startswith("diff --git "):
            parts = line.split()
            if len(parts) != 4:
                return False, set(), "PATCH_BAD_DIFF_HEADER"
            for value in parts[2:4]:
                normalized = safe_target(re.sub(r"^[ab]/", "", value))
                if normalized is None:
                    return False, set(), "PATCH_UNSAFE_DIFF_PATH"
                paths.add(normalized)
    return bool(paths), paths, "" if paths else "PATCH_HAS_NO_PATHS"


def _clone_exact(repo: Path, source_head: str, dest: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        ["git", "clone", "--quiet", "--no-hardlinks", "--local", str(repo), str(dest)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=90,
    )
    if proc.returncode != 0:
        return False, "LOCAL_CLONE_FAILED:" + proc.stderr[-500:]
    rc, _, err = _git(dest, "checkout", "--quiet", "--detach", source_head)
    if rc != 0:
        return False, "SOURCE_CHECKOUT_FAILED:" + err[-500:]
    rc, got, err = _git(dest, "rev-parse", "HEAD")
    if rc != 0 or got.strip() != source_head:
        return False, "SOURCE_CHECKOUT_IDENTITY_MISMATCH:" + (got or err)[-500:]
    return True, ""


def _standard_apply_check(repo: Path, source_head: str, patch: str, temp_root: Path) -> tuple[bool, str]:
    dest = temp_root / "check"
    ok, reason = _clone_exact(repo, source_head, dest)
    if not ok:
        return False, reason
    rc, _, err = _git(dest, "apply", "--check", "--whitespace=nowarn", "-", input_text=patch)
    return rc == 0, err[-1200:]


def normalize_patch_against_source(repo: Path, source_head: str, patch: str, targets: list[str]) -> dict[str, Any]:
    ok, reason = _source_exists(repo, source_head)
    if not ok:
        return {"ok": False, "reason": reason, "repair_mode": "NONE", "patch": patch}
    declared_ok, paths, path_reason = _patch_declared_paths(patch)
    expected = set(targets)
    if not declared_ok:
        return {"ok": False, "reason": path_reason, "repair_mode": "NONE", "patch": patch}
    if paths != expected:
        return {
            "ok": False, "reason": "PATCH_TARGET_SET_MISMATCH",
            "declared_paths": sorted(paths), "expected_paths": sorted(expected),
            "repair_mode": "NONE", "patch": patch,
        }

    root = Path(tempfile.mkdtemp(prefix="clay-patch-preflight-"))
    try:
        clean, err = _standard_apply_check(repo, source_head, patch, root)
        if clean:
            return {"ok": True, "reason": None, "repair_mode": "NONE", "patch": patch, "original_apply_error": None}

        recount_repo = root / "recount"
        cloned, clone_reason = _clone_exact(repo, source_head, recount_repo)
        if not cloned:
            return {"ok": False, "reason": clone_reason, "repair_mode": "NONE", "patch": patch, "original_apply_error": err}
        rc, _, recount_err = _git(recount_repo, "apply", "--recount", "--whitespace=nowarn", "-", input_text=patch)
        if rc != 0:
            return {
                "ok": False, "reason": "PATCH_APPLY_REJECTED", "repair_mode": "NONE",
                "patch": patch, "original_apply_error": err,
                "recount_apply_error": recount_err[-1200:],
            }

        rc, normalized, diff_err = _git(recount_repo, "diff", "--no-ext-diff", "--binary", "--", *targets)
        if rc != 0 or not normalized.strip():
            return {
                "ok": False, "reason": "RECOUNT_NORMALIZATION_EMPTY_OR_FAILED:" + diff_err[-500:],
                "repair_mode": "NONE", "patch": patch, "original_apply_error": err,
            }

        verify_root = root / "verify"
        verify_root.mkdir()
        clean2, err2 = _standard_apply_check(repo, source_head, normalized, verify_root)
        if not clean2:
            return {
                "ok": False, "reason": "RECOUNT_NORMALIZED_PATCH_FAILED_STANDARD_CHECK",
                "repair_mode": "NONE", "patch": patch, "original_apply_error": err,
                "normalized_apply_error": err2,
            }
        return {
            "ok": True, "reason": None, "repair_mode": "RECOUNT_NORMALIZED",
            "patch": normalized, "original_apply_error": err,
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)
