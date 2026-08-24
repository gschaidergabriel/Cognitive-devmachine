#!/usr/bin/env python3
"""Fail-closed Forge candidate/execution boundary for Supervisor 8.71.

This module deliberately separates *candidate validity* from authority to execute
model-authored tests.  It may perform deterministic repository/source operations
with fixed argv (git identity, local clone, git apply --check), but it never runs a
command supplied by a worker.  Apply-clean candidates remain EXECUTION_BLOCKED
until a separately admitted isolated zero-cost executor consumes an exact policy-
and source-bound request.

It also materializes a bounded exact-source patch-context packet.  That packet is
noncanonical candidate evidence for the #1527 two-stage flow: choose targets first,
then synthesize a patch against exact HEAD/blob bytes instead of guessing a line-
sensitive diff from repository summaries.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from typing import Any

SCHEMA = "CLAY_FORGE_CANDIDATE_EXECUTION_BOUNDARY/v1"
PATCH_CONTEXT_SCHEMA = "CLAY_FORGE_PATCH_CONTEXT/v1"
EXECUTION_POLICY_SCHEMA = "CLAY_FORGE_EXECUTION_POLICY/v1"
MAX_PATCH_BYTES = 250_000
MAX_TARGETS = 8
MAX_TARGET_BYTES = 80_000
MAX_CONTEXT_BYTES = 250_000
MAX_COMMAND_TEXT = 2_000

# Candidate programs are preserved as evidence but are not host execution authority.
SHELL_META = (";", "|", "&&", "||", "`", "$(`", ">", "<", "\n", "\r")
SENSITIVE_SEGMENTS = {"private", "secrets", ".secrets"}
SENSITIVE_SUFFIXES = {".env", ".pem", ".p12", ".pfx", ".key"}

POLICY: dict[str, Any] = {
    "schema": EXECUTION_POLICY_SCHEMA,
    "candidate_is_execution_authority": False,
    "worker_commands_local_host": "FORBIDDEN",
    "shell_execution": "FORBIDDEN",
    "ambient_environment_inheritance": "FORBIDDEN",
    "static_source_operations": [
        "git rev-parse HEAD",
        "git rev-parse HEAD^{tree}",
        "git show HEAD:<validated-path>",
        "git clone --local --no-hardlinks <repo> <temp>",
        "git apply --check --whitespace=nowarn -",
    ],
    "post_apply_execution": "REQUIRES_SEPARATE_ISOLATED_ZERO_COST_EXECUTOR_ADMISSION",
}


def _canonical(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def policy_sha256() -> str:
    return sha256_text(_canonical(POLICY))


def _minimal_env(home: Path | None = None) -> dict[str, str]:
    # Construct from scratch.  In particular, provider/API credentials from the
    # Forge parent are not inherited by deterministic source operations.
    return {
        "PATH": os.defpath,
        "HOME": str(home or Path("/nonexistent")),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "GIT_CONFIG_NOSYSTEM": "1",
    }


def _run_argv(
    argv: list[str],
    *,
    cwd: Path,
    timeout: int = 60,
    input_text: str | None = None,
    home: Path | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    try:
        p = subprocess.run(
            argv,
            cwd=cwd,
            env=_minimal_env(home),
            text=True,
            input=input_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "rc": int(p.returncode),
            "elapsed_s": time.monotonic() - started,
            "stdout": p.stdout[-4000:],
            "stderr": p.stderr[-4000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "rc": 124,
            "elapsed_s": time.monotonic() - started,
            "stdout": str(exc.stdout or "")[-2000:],
            "stderr": "TIMEOUT",
        }
    except Exception as exc:  # source-operation failure, not candidate execution
        return {
            "rc": 125,
            "elapsed_s": time.monotonic() - started,
            "stdout": "",
            "stderr": f"{type(exc).__name__}:{str(exc)[:1000]}",
        }


def safe_target(value: str) -> bool:
    if not isinstance(value, str) or not value or len(value) > 500:
        return False
    if any(ord(ch) < 32 for ch in value):
        return False
    p = Path(value)
    if p.is_absolute() or ".." in p.parts or not p.parts:
        return False
    if p.parts[0] == ".git" or ".git" in p.parts:
        return False
    lower_parts = {part.lower() for part in p.parts}
    if lower_parts & SENSITIVE_SEGMENTS:
        return False
    if p.suffix.lower() in SENSITIVE_SUFFIXES:
        return False
    return True


def patch_paths_safe(patch: str, targets: list[str]) -> bool:
    if not isinstance(patch, str):
        return False
    if len(patch.encode("utf-8", errors="replace")) > MAX_PATCH_BYTES:
        return False
    if not targets or len(targets) > MAX_TARGETS or any(not safe_target(t) for t in targets):
        return False
    for line in patch.splitlines():
        if not line.startswith(("+++ ", "--- ")):
            continue
        raw = line[4:].split("\t", 1)[0]
        if raw == "/dev/null":
            continue
        raw = re.sub(r"^[ab]/", "", raw)
        if not safe_target(raw):
            return False
    return True


def command_evidence(commands: list[Any], benchmark: Any) -> dict[str, Any]:
    """Classify candidate command text without executing or normalizing it."""
    raw: list[str] = []
    malformed = False
    for item in commands:
        if not isinstance(item, str) or not item.strip() or len(item) > MAX_COMMAND_TEXT:
            malformed = True
            continue
        raw.append(item)
    if benchmark not in (None, ""):
        if isinstance(benchmark, str) and benchmark.strip() and len(benchmark) <= MAX_COMMAND_TEXT:
            raw.append(benchmark)
        else:
            malformed = True
    meta = [c for c in raw if any(token in c for token in SHELL_META)]
    interpreter_inline = [
        c for c in raw
        if re.search(r"(^|\s)(python(?:3)?|bash|sh)\s+(?:-c|-lc)(?:\s|$)", c)
    ]
    return {
        "schema": "CLAY_FORGE_MODEL_COMMAND_EVIDENCE/v1",
        "preserved_count": len(raw),
        "malformed": malformed,
        "shell_metacharacters_present": bool(meta),
        "inline_interpreter_present": bool(interpreter_inline),
        "execution_admitted": False,
        "reason": "MODEL_AUTHORED_COMMANDS_REQUIRE_ISOLATED_EXECUTOR_ADMISSION",
    }


def _git_identity(root: Path) -> dict[str, str] | None:
    head = _run_argv(["git", "rev-parse", "HEAD"], cwd=root, timeout=20)
    tree = _run_argv(["git", "rev-parse", "HEAD^{tree}"], cwd=root, timeout=20)
    if head["rc"] != 0 or tree["rc"] != 0:
        return None
    h = str(head["stdout"]).strip()
    t = str(tree["stdout"]).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", h) or not re.fullmatch(r"[0-9a-f]{40}", t):
        return None
    return {"commit": h, "tree": t}


def _target_blob(root: Path, head: str, target: str) -> tuple[dict[str, Any], bytes]:
    # `git show` reads the committed blob, never a possibly-mutated working-tree file.
    obj = _run_argv(["git", "rev-parse", f"{head}:{target}"], cwd=root, timeout=20)
    if obj["rc"] != 0:
        return ({"path": target, "exists_at_source": False, "blob_sha": None, "bytes": 0, "truncated": False}, b"")
    blob = str(obj["stdout"]).strip()
    if not re.fullmatch(r"[0-9a-f]{40,64}", blob):
        return ({"path": target, "exists_at_source": False, "blob_sha": None, "bytes": 0, "truncated": False}, b"")
    shown = subprocess.run(
        ["git", "show", f"{head}:{target}"],
        cwd=root,
        env=_minimal_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if shown.returncode != 0:
        return ({"path": target, "exists_at_source": True, "blob_sha": blob, "bytes": 0, "truncated": False, "read_error": "GIT_SHOW_FAILED"}, b"")
    data = bytes(shown.stdout)
    clipped = data[:MAX_TARGET_BYTES]
    return (
        {
            "path": target,
            "exists_at_source": True,
            "blob_sha": blob,
            "bytes": len(data),
            "truncated": len(data) > len(clipped),
        },
        clipped,
    )


def materialize_patch_context(
    *,
    root: Path,
    output_root: Path,
    candidate_hash: str,
    targets: list[str],
) -> dict[str, Any]:
    identity = _git_identity(root)
    if identity is None:
        return {"ok": False, "reason": "SOURCE_IDENTITY_UNRESOLVED"}
    if not targets or len(targets) > MAX_TARGETS or any(not safe_target(t) for t in targets):
        return {"ok": False, "reason": "TARGET_PATH_REJECTED"}

    entries: list[dict[str, Any]] = []
    used = 0
    for target in targets:
        meta, data = _target_blob(root, identity["commit"], target)
        allowance = max(0, MAX_CONTEXT_BYTES - used)
        payload = data[:allowance]
        used += len(payload)
        meta["context_truncated"] = len(payload) < len(data) or bool(meta.get("truncated"))
        meta["content_utf8"] = payload.decode("utf-8", errors="replace")
        entries.append(meta)

    packet = {
        "schema": PATCH_CONTEXT_SCHEMA,
        "canonical_truth": False,
        "effect_authority": False,
        "candidate_hash": candidate_hash,
        "source": identity,
        "targets": entries,
        "context_bytes": used,
        "context_budget_bytes": MAX_CONTEXT_BYTES,
        "purpose": "SECOND_STAGE_PATCH_SYNTHESIS_ONLY",
    }
    packet_sha = sha256_text(_canonical(packet))
    out_dir = output_root / "patch_context_packets"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{candidate_hash}.json"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return {
        "ok": True,
        "packet_sha256": packet_sha,
        "relative_path": str(path.relative_to(output_root)),
        "source": identity,
        "targets": [
            {k: v for k, v in entry.items() if k != "content_utf8"}
            for entry in entries
        ],
    }


def _apply_check(root: Path, patch: str) -> dict[str, Any]:
    parent = root.parent
    tmp = Path(tempfile.mkdtemp(prefix="clay-forge-static-", dir=parent))
    checkout = tmp / "repo"
    try:
        clone = _run_argv(
            ["git", "clone", "--quiet", "--no-hardlinks", "--local", str(root), str(checkout)],
            cwd=parent,
            timeout=90,
            home=tmp,
        )
        if clone["rc"] != 0:
            return {"ok": False, "reason": "LOCAL_CLONE_FAILED", "stderr": clone["stderr"][-1000:]}
        checked = _run_argv(
            ["git", "apply", "--check", "--whitespace=nowarn", "-"],
            cwd=checkout,
            timeout=30,
            input_text=patch,
            home=tmp,
        )
        return {
            "ok": checked["rc"] == 0,
            "reason": "APPLY_CHECK_PASS" if checked["rc"] == 0 else "PATCH_REJECTED",
            "stderr": checked["stderr"][-1000:],
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def validate_candidate_without_execution(forge: Any, con: Any, row: Any) -> dict[str, Any]:
    """Drop-in replacement for legacy Forge validation.

    `forge` is the imported legacy module; it supplies ROOT/FORGE_ROOT/now().  `con`
    is accepted for call compatibility but is intentionally not execution authority.
    """
    del con
    try:
        obj = json.loads(row["proposal_json"])
    except Exception:
        obj = None
    candidate_hash = str(row["candidate_hash"])
    base = {
        "schema": SCHEMA,
        "delta_id": str(row["delta_id"]),
        "candidate_hash": candidate_hash,
        "source_class": "free_swarm",
        "provider": str(row["provider"]),
        "model": str(row["model"]),
        "role": str(row["role"]),
        "worker_sha": str(row["worker_sha"]),
        "evaluated_at": forge.now(),
        "canonical_truth": False,
        "effect_authority": False,
        "execution_policy_sha256": policy_sha256(),
        "executor_identity": None,
        "execution_state": "EXECUTION_BLOCKED",
    }
    if not isinstance(obj, dict):
        return {**base, "status": "invalid_candidate", "reason": "PROPOSAL_JSON_INVALID"}

    targets_raw = obj.get("target_files", [])
    if not isinstance(targets_raw, list):
        return {**base, "status": "invalid_candidate", "reason": "TARGETS_NOT_LIST"}
    targets = [str(x) for x in targets_raw if isinstance(x, str)]
    if len(targets) != len(targets_raw) or not targets or len(targets) > MAX_TARGETS or any(not safe_target(t) for t in targets):
        return {**base, "status": "invalid_candidate", "reason": "TARGET_PATH_REJECTED"}

    command_info = command_evidence(
        list(obj.get("test_commands", [])) + list(obj.get("negative_test_commands", []))
        if isinstance(obj.get("test_commands", []), list) and isinstance(obj.get("negative_test_commands", []), list)
        else [],
        obj.get("benchmark_command", ""),
    )
    context = materialize_patch_context(
        root=Path(forge.ROOT),
        output_root=Path(forge.FORGE_ROOT),
        candidate_hash=candidate_hash,
        targets=targets,
    )
    common = {
        **base,
        "model_command_evidence": command_info,
        "patch_context": context,
    }
    if not context.get("ok"):
        return {**common, "status": "source_context_blocked", "reason": context.get("reason")}

    patch = obj.get("patch_unified_diff", "")
    if not isinstance(patch, str) or not patch.strip():
        return {
            **common,
            "status": "valid_candidate",
            "reason": "PATCH_SYNTHESIS_REQUIRED_FROM_EXACT_SOURCE_CONTEXT",
            "next_state": "SECOND_STAGE_PATCH_SYNTHESIS",
        }
    if not patch_paths_safe(patch, targets):
        return {**common, "status": "invalid_candidate", "reason": "PATCH_PATH_OR_SIZE_REJECTED"}

    patch_sha = hashlib.sha256(patch.encode("utf-8", errors="replace")).hexdigest()
    checked = _apply_check(Path(forge.ROOT), patch)
    with_patch = {**common, "patch_sha256": patch_sha, "apply_check": checked}
    if not checked.get("ok"):
        return {
            **with_patch,
            "status": "patch_rejected",
            "reason": "PATCH_REJECTED_AGAINST_BOUND_SOURCE",
            "next_state": "SECOND_STAGE_PATCH_SYNTHESIS",
        }

    return {
        **with_patch,
        "status": "apply_check_pass",
        "reason": "ISOLATED_EXECUTOR_ADMISSION_REQUIRED",
        "next_state": "EXECUTION_ADMISSION",
        "execution_state": "EXECUTION_BLOCKED",
        "execution_admitted": False,
    }
