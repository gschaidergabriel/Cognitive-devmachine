#!/usr/bin/env python3
"""Deterministic execution admission for model-authored Evidence Forge commands.

This module is intentionally not an authority for canonical truth.  It narrows the
local disposable-clone execution surface used by run_free_evidence_forge.py.
Worker-authored command strings are treated as untrusted data and are admitted only
as a small argv grammar, executed without a shell, without inherited credentials,
and inside a bubblewrap network/filesystem namespace with bounded POSIX resources.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shlex
import shutil
import subprocess
import time
from typing import Any

POLICY_SCHEMA = "CLAY_FORGE_EXECUTION_ADMISSION/v1"
FORBIDDEN_META = frozenset(";&|><`$\n\r\x00")
SECRET_NAME_RE = re.compile(r"(?i)(api[_-]?key|token|secret|credential|password|passwd|auth)")
SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_./:+,=@%~-]+$")
MAX_COMMAND_BYTES = 4096
MAX_ARGC = 64
MAX_ARG_BYTES = 768
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class Admission:
    admitted: bool
    reason: str
    argv: tuple[str, ...] = ()
    execution_class: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="strict")).hexdigest()


def _path_token_safe(token: str) -> bool:
    if token.startswith("/") or token.startswith("~"):
        return False
    values = [token]
    if "=" in token:
        values.append(token.split("=", 1)[1])
    for value in values:
        if value.startswith("/") or value.startswith("~"):
            return False
        pathish = value.split("::", 1)[0]
        if "/" in pathish and ".." in Path(pathish).parts:
            return False
    return True


def _tokens_safe(argv: list[str]) -> bool:
    if not argv or len(argv) > MAX_ARGC:
        return False
    for token in argv:
        if len(token.encode("utf-8")) > MAX_ARG_BYTES:
            return False
        if any(ch in token for ch in FORBIDDEN_META):
            return False
        if not SAFE_TOKEN_RE.fullmatch(token):
            return False
        if not _path_token_safe(token):
            return False
    return True


def admit_command(command: str) -> Admission:
    if not isinstance(command, str) or not command.strip():
        return Admission(False, "EMPTY")
    if len(command.encode("utf-8", errors="ignore")) > MAX_COMMAND_BYTES:
        return Admission(False, "TOO_LARGE")
    if any(ch in command for ch in FORBIDDEN_META):
        return Admission(False, "SHELL_METACHARACTER")
    try:
        argv = shlex.split(command, posix=True)
    except ValueError:
        return Admission(False, "SHLEX_PARSE_ERROR")
    if not _tokens_safe(argv):
        return Admission(False, "TOKEN_OR_PATH_POLICY")

    exe = argv[0]
    rest = argv[1:]

    if exe in {"python", "python3"}:
        if "-c" in rest:
            return Admission(False, "PYTHON_INLINE_CODE_FORBIDDEN")
        if len(rest) >= 2 and rest[0] == "-m":
            module = rest[1]
            if module not in {"unittest", "pytest", "py_compile"}:
                return Admission(False, "PYTHON_MODULE_NOT_ALLOWLISTED")
            return Admission(True, "ALLOWLISTED_PYTHON_MODULE", tuple(argv), "TEST_OR_STATIC")
        if rest and rest[0].startswith("tests/") and rest[0].endswith(".py"):
            return Admission(True, "ALLOWLISTED_TEST_SCRIPT", tuple(argv), "TEST")
        return Admission(False, "PYTHON_FORM_NOT_ALLOWLISTED")

    if exe in {"pytest", "py.test"}:
        return Admission(True, "ALLOWLISTED_PYTEST", tuple(argv), "TEST")

    if exe == "bash":
        if len(rest) == 2 and rest[0] == "-n" and rest[1].endswith(".sh"):
            return Admission(True, "ALLOWLISTED_BASH_SYNTAX_ONLY", tuple(argv), "STATIC")
        return Admission(False, "BASH_EXECUTION_FORBIDDEN")

    if exe == "git":
        if rest in (["diff", "--check"], ["status", "--porcelain"]):
            return Admission(True, "ALLOWLISTED_GIT_READONLY_CHECK", tuple(argv), "STATIC")
        return Admission(False, "GIT_FORM_NOT_ALLOWLISTED")

    if exe == "cargo":
        if rest and rest[0] in {"check", "test"} and "--offline" in rest:
            return Admission(True, "ALLOWLISTED_CARGO_OFFLINE", tuple(argv), "TEST_OR_STATIC")
        return Admission(False, "CARGO_REQUIRES_OFFLINE_CHECK_OR_TEST")

    if exe == "go":
        if rest and rest[0] == "test":
            return Admission(True, "ALLOWLISTED_GO_TEST", tuple(argv), "TEST")
        return Admission(False, "GO_FORM_NOT_ALLOWLISTED")

    return Admission(False, "EXECUTABLE_NOT_ALLOWLISTED")


def safe_command(command: str) -> bool:
    return admit_command(command).admitted


def _minimal_env() -> dict[str, str]:
    return {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": "/tmp",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "NO_PROXY": "*",
        "TMPDIR": "/tmp",
        "CARGO_TARGET_DIR": "/tmp/cargo-target",
        "GOCACHE": "/tmp/go-cache",
        "GOTMPDIR": "/tmp/go-tmp",
    }


def _bubblewrap_prefix(cwd: Path) -> list[str] | None:
    bwrap = shutil.which("bwrap")
    if not bwrap:
        return None
    cwd = cwd.resolve()
    prefix = [
        bwrap,
        "--unshare-all",
        "--die-with-parent",
        "--new-session",
        "--proc", "/proc",
        "--dev", "/dev",
        "--tmpfs", "/tmp",
    ]
    for host in ("/usr", "/bin", "/lib", "/lib64", "/usr/local"):
        if Path(host).exists():
            prefix += ["--ro-bind", host, host]
    prefix += ["--ro-bind", str(cwd), "/work", "--chdir", "/work"]
    for key, value in _minimal_env().items():
        prefix += ["--setenv", key, value]
    return prefix + ["--"]


def execution_backend_status(cwd: Path) -> dict[str, Any]:
    prefix = _bubblewrap_prefix(cwd)
    if prefix is None:
        return {
            "schema": POLICY_SCHEMA,
            "admitted": False,
            "backend": None,
            "reason": "BUBBLEWRAP_NOT_FOUND",
            "network_namespace": "UNAVAILABLE",
            "secret_environment_inherited": False,
            "host_secret_paths_exposed": False,
        }
    try:
        probe = subprocess.run(
            prefix + ["/usr/bin/true"],
            cwd=str(cwd),
            env=_minimal_env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
        functional = probe.returncode == 0
        reason = "OK" if functional else f"BUBBLEWRAP_PROBE_RC_{probe.returncode}"
    except Exception as exc:
        functional = False
        reason = f"BUBBLEWRAP_PROBE_{type(exc).__name__}"
    return {
        "schema": POLICY_SCHEMA,
        "admitted": functional,
        "backend": "bubblewrap_unshare_all",
        "reason": reason,
        "network_namespace": "ISOLATED" if functional else "UNAVAILABLE",
        "secret_environment_inherited": False,
        "host_secret_paths_exposed": False,
    }


def _limit_child(timeout: int) -> None:
    cpu = max(2, min(int(timeout) + 2, 180))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
    mem = 2 * 1024**3
    resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
    resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024**2, 128 * 1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))
    try:
        resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
    except (ValueError, OSError):
        pass


def run_cmd(cwd: Path, command: str, timeout: int = 120) -> dict[str, Any]:
    decision = admit_command(command)
    started = time.monotonic()
    if not decision.admitted:
        return {
            "rc": 126,
            "elapsed_s": 0.0,
            "stdout": "",
            "stderr": f"FORGE_EXECUTION_NOT_ADMITTED:{decision.reason}",
            "execution_admission": decision.to_dict(),
        }
    prefix = _bubblewrap_prefix(cwd)
    if prefix is None:
        return {
            "rc": 126,
            "elapsed_s": 0.0,
            "stdout": "",
            "stderr": "FORGE_EXECUTION_BLOCKED:NO_ISOLATED_EXECUTOR",
            "execution_admission": decision.to_dict(),
        }
    argv = prefix + list(decision.argv)
    try:
        proc = subprocess.run(
            argv,
            cwd=str(cwd),
            env=_minimal_env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            preexec_fn=lambda: _limit_child(timeout),
        )
        return {
            "rc": int(proc.returncode),
            "elapsed_s": time.monotonic() - started,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
            "execution_admission": decision.to_dict(),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "rc": 124,
            "elapsed_s": time.monotonic() - started,
            "stdout": str(exc.stdout or "")[-2000:],
            "stderr": "TIMEOUT",
            "execution_admission": decision.to_dict(),
        }
    except Exception as exc:
        return {
            "rc": 125,
            "elapsed_s": time.monotonic() - started,
            "stdout": "",
            "stderr": f"EXECUTOR_ERROR:{type(exc).__name__}:{str(exc)[:500]}",
            "execution_admission": decision.to_dict(),
        }


def candidate_execution_manifest(row: Any, proposal: dict[str, Any], cwd: Path) -> dict[str, Any]:
    patch = str(proposal.get("patch_unified_diff") or "")
    commands: list[str] = []
    for key in ("test_commands", "negative_test_commands"):
        commands.extend(str(x) for x in proposal.get(key, []) if isinstance(x, str))
    bench = proposal.get("benchmark_command")
    if isinstance(bench, str) and bench.strip():
        commands.append(bench)
    decisions = [admit_command(cmd).to_dict() for cmd in commands]
    worker_source_head = str(row["repo_head"] or "").strip().lower() if "repo_head" in row.keys() else ""
    source_identity_bound = bool(COMMIT_RE.fullmatch(worker_source_head))
    evaluation_head = "UNKNOWN"
    worker_source_tree = "UNKNOWN"
    try:
        evaluation_head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(cwd), env=_minimal_env(), text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10, check=True,
        ).stdout.strip()
        if source_identity_bound:
            worker_source_tree = subprocess.run(
                ["git", "rev-parse", f"{worker_source_head}^{{tree}}"], cwd=str(cwd), env=_minimal_env(), text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10, check=True,
            ).stdout.strip()
    except Exception:
        pass
    proposal_raw = json.dumps(proposal, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return {
        "schema": POLICY_SCHEMA,
        "candidate_hash": str(row["candidate_hash"]),
        "proposal_sha256": sha256_text(proposal_raw),
        "patch_sha256": sha256_text(patch),
        "commands_sha256": sha256_text(json.dumps(commands, ensure_ascii=False, separators=(",", ":"))),
        "worker_source_head": worker_source_head or None,
        "worker_source_tree": worker_source_tree if worker_source_tree != "UNKNOWN" else None,
        "evaluation_head": evaluation_head if evaluation_head != "UNKNOWN" else None,
        "source_identity_bound": source_identity_bound,
        "decisions": decisions,
        "all_commands_admitted": bool(decisions) and all(bool(d["admitted"]) for d in decisions),
        "backend": execution_backend_status(cwd),
        "candidate_is_canonical_truth": False,
    }


def validate_candidate_with_admission(base: Any, original_validate: Any, con: Any, row: Any) -> dict[str, Any]:
    proposal = json.loads(row["proposal_json"])
    manifest = candidate_execution_manifest(row, proposal, Path(base.ROOT))
    base_record = {
        "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
        "delta_id": row["delta_id"],
        "source_class": "free_swarm",
        "provider": row["provider"],
        "model": row["model"],
        "role": row["role"],
        "worker_sha": row["worker_sha"],
        "evaluated_at": base.now(),
        "execution_admission": manifest,
    }
    if not manifest["source_identity_bound"]:
        return {**base_record, "status": "source_identity_unbound", "reason": "valid repo_head_at_prompt required before execution admission"}
    if not manifest["all_commands_admitted"]:
        return {**base_record, "status": "execution_not_admitted", "reason": "MODEL_COMMAND_POLICY_REJECTED"}
    if not manifest["backend"]["admitted"]:
        return {**base_record, "status": "execution_blocked_no_isolated_executor", "reason": "BUBBLEWRAP_REQUIRED"}
    result = original_validate(con, row)
    result["execution_admission"] = manifest
    return result


def assert_no_secret_names(env: dict[str, str]) -> None:
    bad = [name for name in env if SECRET_NAME_RE.search(name)]
    if bad:
        raise AssertionError(f"secret-like environment keys present: {bad}")
