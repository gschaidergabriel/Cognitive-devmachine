#!/usr/bin/env python3
"""Fail-closed source-attested and loopback-guarded local Trigger-1 Qwen envelope."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any
from urllib.parse import urlsplit

from trigger1_source_attestation import require_clean_source

ROOT = Path(__file__).resolve().parents[1]
MODES = {
    "terminal": ROOT / "tools" / "trigger1_local_qwen06_activation_api_execute.py",
    "intermediate": ROOT / "tools" / "trigger1_local_qwen06_intermediate_api_execute.py",
}
BINDING_SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN_SOURCE_EXECUTION_BINDING/v2"
GUARD_RECEIPT_SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN_GUARDED_EXECUTION/v1"
MODEL_ID = "Qwen/Qwen3-0.6B"
MODEL_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"
PROVIDER_MARKERS = ("GROQ", "MISTRAL", "NVIDIA", "NGC", "OPENROUTER", "TOGETHER", "ANTHROPIC", "OPENAI")
SECRET_MARKERS = ("API_KEY", "TOKEN", "SECRET", "CREDENTIAL", "AUTH")
EXPLICIT_SENSITIVE_ENV = {"HF_TOKEN", "HUGGINGFACE_HUB_TOKEN", "HUGGING_FACE_HUB_TOKEN"}
SAFE_ENV_NAMES = {
    "PATH", "HOME", "USER", "LOGNAME", "SHELL", "LANG", "LC_ALL", "LC_CTYPE", "TZ",
    "TMPDIR", "TMP", "TEMP", "HF_HOME", "HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE",
    "TRANSFORMERS_CACHE", "XDG_CACHE_HOME", "CUDA_VISIBLE_DEVICES", "LD_LIBRARY_PATH",
    "VIRTUAL_ENV", "CONDA_PREFIX", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
}
KNOWN_OUTPUTS = (
    "trigger1_local_activation_api_result.json",
    "trigger1_direct_steering_candidate.json",
    "trigger1_source_execution_binding.json",
    "trigger1_guarded_execution_receipt.json",
)


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_hex(value: Any, size: int) -> bool:
    if not isinstance(value, str) or len(value) != size:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def sensitive_env_name(name: str) -> bool:
    upper = str(name).upper()
    return upper in EXPLICIT_SENSITIVE_ENV or (any(p in upper for p in PROVIDER_MARKERS) and any(s in upper for s in SECRET_MARKERS))


def guarded_env(audit_log: Path) -> tuple[dict[str, str], list[str]]:
    removed = sorted(k for k in os.environ if sensitive_env_name(k))
    env: dict[str, str] = {}
    for key, value in os.environ.items():
        if sensitive_env_name(key):
            continue
        if key in SAFE_ENV_NAMES or key.startswith(("LC_", "CUDA_", "ROCR_")):
            env[key] = value
    env.update({
        "CLAY_LOCAL_GUARD_AUDIT_LOG": str(audit_log),
        "CLAY_GUARD_REPO_ROOT": str(ROOT.resolve()),
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HF_DATASETS_OFFLINE": "1",
        "NO_PROXY": "127.0.0.1,localhost,::1",
        "no_proxy": "127.0.0.1,localhost,::1",
    })
    return env, removed


def guard_code() -> str:
    return r'''import datetime as _dt, ipaddress as _ip, json as _json, os as _os, socket as _socket, subprocess as _subprocess, threading as _threading
_A=_os.environ.get("CLAY_LOCAL_GUARD_AUDIT_LOG"); _L=_threading.Lock()
_P=("GROQ","MISTRAL","NVIDIA","NGC","OPENROUTER","TOGETHER","ANTHROPIC","OPENAI"); _S=("API_KEY","TOKEN","SECRET","CREDENTIAL","AUTH"); _X={"HF_TOKEN","HUGGINGFACE_HUB_TOKEN","HUGGING_FACE_HUB_TOKEN"}
def _sen(k):
 u=str(k).upper(); return u in _X or (any(p in u for p in _P) and any(s in u for s in _S))
def _log(e,**x):
 if not _A:return
 with _L:
  with open(_A,"a",encoding="utf-8") as f:f.write(_json.dumps({"event":e,"at":_dt.datetime.now(_dt.timezone.utc).isoformat(),**x},sort_keys=True,separators=(",",":"))+"\n")
def _loop(h):
 if h is None:return True
 h=h.decode() if isinstance(h,(bytes,bytearray)) else str(h)
 if h.lower()=="localhost":return True
 try:return _ip.ip_address(h.split("%",1)[0]).is_loopback
 except Exception:return False
_og=_os.getenv; _oi=_os._Environ.__getitem__; _oc=_os._Environ.__contains__; _ga=_socket.getaddrinfo; _co=_socket.socket.connect; _cx=_socket.socket.connect_ex
def _gg(k,z=None):
 if _sen(k):_log("blocked_provider_credential_lookup",key=str(k));raise RuntimeError("BLOCKED_PROVIDER_CREDENTIAL_LOOKUP:"+str(k))
 return _og(k,z)
def _gi(self,k):
 if _sen(k):_log("blocked_provider_credential_lookup",key=str(k));raise RuntimeError("BLOCKED_PROVIDER_CREDENTIAL_LOOKUP:"+str(k))
 return _oi(self,k)
def _gc(self,k):
 if _sen(k):_log("blocked_provider_credential_lookup",key=str(k));raise RuntimeError("BLOCKED_PROVIDER_CREDENTIAL_LOOKUP:"+str(k))
 return _oc(self,k)
def _gai(h,*a,**kw):
 if not _loop(h):_log("blocked_non_loopback_dns",host=str(h)[:300]);raise _socket.gaierror("BLOCKED_NON_LOOPBACK_DNS")
 return _ga(h,*a,**kw)
def _conn(self,a):
 h=a[0] if isinstance(a,tuple) and a else a
 if not _loop(h):_log("blocked_non_loopback_connect",host=str(h)[:300]);raise OSError("BLOCKED_NON_LOOPBACK_CONNECT")
 return _co(self,a)
def _cex(self,a):
 h=a[0] if isinstance(a,tuple) and a else a
 if not _loop(h):_log("blocked_non_loopback_connect_ex",host=str(h)[:300]);raise OSError("BLOCKED_NON_LOOPBACK_CONNECT_EX")
 return _cx(self,a)
_op=_subprocess.Popen
def _popen(args,*a,**kw):
 root=_os.environ.get("CLAY_GUARD_REPO_ROOT","")
 seq=list(args) if isinstance(args,(list,tuple)) else []
 allowed=(
  ["git","-C",root,"rev-parse","HEAD"],
  ["git","-C",root,"rev-parse","HEAD^{tree}"],
  ["git","-C",root,"status","--porcelain=v1"],
 )
 if seq in allowed:return _op(args,*a,**kw)
 _log("blocked_child_subprocess",argv0=(str(seq[0])[:120] if seq else type(args).__name__));raise RuntimeError("BLOCKED_CHILD_SUBPROCESS")
_os.getenv=_gg; _os._Environ.__getitem__=_gi; _os._Environ.__contains__=_gc; _socket.getaddrinfo=_gai; _socket.socket.connect=_conn; _socket.socket.connect_ex=_cex; _subprocess.Popen=_popen; _log("guard_installed")
'''


def audit_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


def _load_object(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return obj


def require_fresh_output(out: Path) -> None:
    resolved = out.expanduser().resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise RuntimeError("OUTPUT_DIR_MUST_BE_OUTSIDE_REPO")
    stale = [name for name in KNOWN_OUTPUTS if (resolved / name).exists()]
    if stale:
        raise RuntimeError("OUTPUT_DIR_CONTAINS_PRIOR_TRIGGER1_EVIDENCE:" + ",".join(sorted(stale)))


def verify_declared_result(result: dict[str, Any]) -> None:
    declared = result.get("result_sha256")
    expected = canonical_sha({k: v for k, v in result.items() if k != "result_sha256"})
    if not is_hex(declared, 64) or declared != expected:
        raise RuntimeError("RESULT_DECLARED_SHA256_MISMATCH")


def require_loopback_endpoint(endpoint: Any) -> str:
    if not isinstance(endpoint, str) or not endpoint:
        raise RuntimeError("LOOPBACK_ENDPOINT_REQUIRED")
    parts = urlsplit(endpoint)
    if parts.scheme != "http" or not parts.hostname:
        raise RuntimeError("LOOPBACK_ENDPOINT_INVALID")
    host = parts.hostname
    if host.lower() == "localhost":
        return endpoint
    try:
        if ipaddress.ip_address(host).is_loopback:
            return endpoint
    except ValueError:
        pass
    raise RuntimeError("NON_LOOPBACK_ENDPOINT_FAIL_CLOSED")


def recompute_original_runtime_receipt(result: dict[str, Any], candidate: dict[str, Any], mode: str) -> str:
    calibration_rows = result.get("calibration_rows")
    holdout_rows = result.get("holdout_rows")
    if not isinstance(calibration_rows, list) or not isinstance(holdout_rows, list):
        raise RuntimeError("RESULT_INVOCATION_ROWS_REQUIRED")
    endpoint = require_loopback_endpoint(result.get("api_endpoint"))
    material: dict[str, Any] = {
        "endpoint": endpoint,
        "runtime_build_sha256": result.get("runtime_build_sha256"),
        "checkpoint_sha256": result.get("checkpoint_sha256"),
        "tokenizer_sha256": result.get("tokenizer_sha256"),
        "source": result.get("source"),
        "api_invocations": len(calibration_rows) + len(holdout_rows),
    }
    if mode == "intermediate":
        material["selected_layer"] = result.get("selected_layer")
        material["selected_gain"] = result.get("selected_gain")
    expected = canonical_sha(material)
    target = candidate.get("target")
    if not isinstance(target, dict) or target.get("local_runtime_execution_receipt_sha256") != expected:
        raise RuntimeError("ORIGINAL_LOCAL_RUNTIME_RECEIPT_MISMATCH")
    return expected


def validate_common_result(result: dict[str, Any], source: dict[str, Any]) -> None:
    verify_declared_result(result)
    result_source = result.get("source")
    if not isinstance(result_source, dict):
        raise RuntimeError("RESULT_SOURCE_MISSING")
    if result_source.get("repo_head") != source["repo_head"] or result_source.get("repo_tree") != source["repo_tree"]:
        raise RuntimeError("RESULT_SOURCE_ATTESTATION_MISMATCH")
    if result.get("zero_provider_billing") is not True or result.get("external_provider_credentials_read") is not False:
        raise RuntimeError("RESULT_PROVIDER_FENCE_MISMATCH")


def validate_result_for_binding(result: dict[str, Any], source: dict[str, Any]) -> None:
    validate_common_result(result, source)
    if result.get("model") != MODEL_ID or result.get("model_revision") != MODEL_REVISION:
        raise RuntimeError("RESULT_MODEL_IDENTITY_MISMATCH")
    if result.get("api_loopback_only") is not True:
        raise RuntimeError("RESULT_LOOPBACK_FLAG_MISSING")
    require_loopback_endpoint(result.get("api_endpoint"))
    for name in ("runtime_build_sha256", "checkpoint_sha256", "tokenizer_sha256"):
        if not is_hex(result.get(name), 64):
            raise RuntimeError(f"RESULT_{name.upper()}_INVALID")
    runtime_manifest = result.get("runtime_manifest")
    if not isinstance(runtime_manifest, dict):
        raise RuntimeError("RESULT_RUNTIME_MANIFEST_MISSING")
    if result.get("runtime_build_sha256") != canonical_sha(runtime_manifest):
        raise RuntimeError("RUNTIME_BUILD_PREIMAGE_MISMATCH")
    for name in ("torch_version", "torch_module_sha256", "transformers_version", "transformers_module_sha256"):
        if runtime_manifest.get(name) in (None, ""):
            raise RuntimeError(f"RUNTIME_MANIFEST_FIELD_REQUIRED:{name}")
    for name in ("torch_module_sha256", "transformers_module_sha256"):
        if not is_hex(runtime_manifest.get(name), 64):
            raise RuntimeError(f"RUNTIME_MANIFEST_SHA256_INVALID:{name}")


def bind_candidate(candidate_path: Path, result_path: Path, mode: str, source: dict[str, Any], executor: Path, guard_context: dict[str, Any]) -> str:
    candidate = _load_object(candidate_path)
    result = _load_object(result_path)
    validate_result_for_binding(result, source)
    if result.get("status") != "PASS" or result.get("promotion_candidate_written") is not True:
        raise RuntimeError("CANDIDATE_PRESENT_WITHOUT_PASS_RESULT")
    identity = candidate.get("source_identity")
    target = candidate.get("target")
    if not isinstance(identity, dict) or not isinstance(target, dict):
        raise RuntimeError("CANDIDATE_IDENTITY_OR_TARGET_MISSING")
    if identity.get("repo_head") != source["repo_head"]:
        raise RuntimeError("CANDIDATE_HEAD_SOURCE_ATTESTATION_MISMATCH")
    for name in ("runtime_build_sha256", "checkpoint_sha256", "tokenizer_sha256"):
        if identity.get(name) != result.get(name):
            raise RuntimeError(f"CANDIDATE_RESULT_{name.upper()}_MISMATCH")
    original_runtime_receipt = recompute_original_runtime_receipt(result, candidate, mode)
    endpoint = require_loopback_endpoint((candidate.get("transport") or {}).get("endpoint"))
    transport = candidate.get("transport") or {}
    if transport.get("loopback_only") is not True or transport.get("api_served") is not True or endpoint != result.get("api_endpoint"):
        raise RuntimeError("CANDIDATE_TRANSPORT_FENCE_MISMATCH")
    if target.get("zero_provider_billing") is not True or target.get("provider") != "local":
        raise RuntimeError("CANDIDATE_PROVIDER_FENCE_MISMATCH")
    if target.get("model_or_route") != f"{MODEL_ID}@{MODEL_REVISION}":
        raise RuntimeError("CANDIDATE_MODEL_ROUTE_MISMATCH")
    binding = {
        "schema": BINDING_SCHEMA,
        "mode": mode,
        "source_identity": source,
        "envelope_sha256": sha256_file(Path(__file__)),
        "executor_path": str(executor.relative_to(ROOT)),
        "executor_sha256": sha256_file(executor),
        "python_executable": sys.executable,
        "python_executable_sha256": sha256_file(Path(sys.executable)),
        "candidate_pre_binding_sha256": sha256_file(candidate_path),
        "result_pre_binding_sha256": sha256_file(result_path),
        "original_local_runtime_execution_receipt_sha256": original_runtime_receipt,
        "endpoint": endpoint,
        "guard_context": guard_context,
    }
    binding_sha = canonical_sha(binding)
    binding["binding_sha256"] = binding_sha
    identity.update(source)
    target["executor_local_runtime_receipt_sha256"] = original_runtime_receipt
    target["source_execution_binding_sha256"] = binding_sha
    target["local_runtime_execution_receipt_sha256"] = binding_sha
    candidate_path.write_text(json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    (candidate_path.parent / "trigger1_source_execution_binding.json").write_text(json.dumps(binding, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    result["source_attestation"] = source
    result["source_execution_binding_sha256"] = binding_sha
    result["promotion_candidate_sha256_after_binding"] = sha256_file(candidate_path)
    result["result_sha256"] = canonical_sha({k: v for k, v in result.items() if k != "result_sha256"})
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return binding_sha


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=sorted(MODES), required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--cache-dir", required=True)
    ap.add_argument("--timeout-seconds", type=int, default=3600)
    args = ap.parse_args()

    out = Path(args.output_dir).expanduser().resolve()
    require_fresh_output(out)
    out.mkdir(parents=True, exist_ok=True)
    result_path = out / "trigger1_local_activation_api_result.json"
    candidate_path = out / "trigger1_direct_steering_candidate.json"
    guard_receipt_path = out / "trigger1_guarded_execution_receipt.json"
    executor = MODES[args.mode]

    pre = require_clean_source(ROOT)
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    with tempfile.TemporaryDirectory(prefix="clay-trigger1-guard-") as td:
        guard_path = Path(td) / "guard.py"
        audit_path = Path(td) / "audit.jsonl"
        guard_path.write_text(guard_code(), encoding="utf-8")
        env, removed = guarded_env(audit_path)
        boot = "import pathlib,runpy,sys;exec(pathlib.Path(sys.argv[1]).read_text(),{});t=sys.argv[2];sys.argv=[t]+sys.argv[3:];runpy.run_path(t,run_name='__main__')"
        proc = subprocess.run(
            [sys.executable, "-I", "-c", boot, str(guard_path), str(executor), "--output-dir", str(out), "--cache-dir", str(args.cache_dir)],
            cwd=str(ROOT), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=args.timeout_seconds, check=False,
        )
        audit = audit_rows(audit_path)
        guard_sha = sha256_file(guard_path)

    post = require_clean_source(ROOT)
    source_stable = pre == post
    events = [str(row.get("event")) for row in audit]
    blocked_credential_attempts = sum(e == "blocked_provider_credential_lookup" for e in events)
    blocked_nonloopback_attempts = sum(e.startswith("blocked_non_loopback") for e in events)
    blocked_child_subprocess_attempts = sum(e == "blocked_child_subprocess" for e in events)
    guard_ok = bool(
        source_stable
        and "guard_installed" in events
        and blocked_credential_attempts == 0
        and blocked_nonloopback_attempts == 0
        and blocked_child_subprocess_attempts == 0
        and not any(sensitive_env_name(k) for k in env)
    )
    result: dict[str, Any] | None = None
    result_error: str | None = None
    if result_path.is_file():
        try:
            result = _load_object(result_path)
            validate_common_result(result, pre)
        except Exception as exc:
            result_error = f"{type(exc).__name__}:{str(exc)[:400]}"
    else:
        result_error = "RESULT_FILE_MISSING"

    status = result.get("status") if result else None
    candidate_exists = candidate_path.is_file()
    relationship_ok = not candidate_exists or status == "PASS"
    if status in {"PASS", "SCIENTIFIC_NEGATIVE"} and result is not None:
        try:
            validate_result_for_binding(result, pre)
        except Exception as exc:
            result_error = f"{type(exc).__name__}:{str(exc)[:400]}"

    guard_context = {
        "guard_sha256": guard_sha,
        "audit_sha256": canonical_sha(audit),
        "guard_installed": "guard_installed" in events,
        "blocked_provider_credential_attempts": blocked_credential_attempts,
        "blocked_nonloopback_attempts": blocked_nonloopback_attempts,
        "blocked_child_subprocess_attempts": blocked_child_subprocess_attempts,
        "removed_sensitive_env_names": removed,
        "offline_model_cache_required": True,
        "network_policy": "PYTHON_SOCKET_LOOPBACK_ONLY_PLUS_CHILD_SUBPROCESS_DENY_EXCEPT_READONLY_GIT_IDENTITY",
        "child_stdout_sha256": hashlib.sha256(proc.stdout.encode("utf-8")).hexdigest(),
        "child_stderr_sha256": hashlib.sha256(proc.stderr.encode("utf-8")).hexdigest(),
        "child_exit_code": proc.returncode,
    }
    binding_sha = None
    if guard_ok and relationship_ok and result_error is None and status == "PASS" and candidate_exists and proc.returncode == 0:
        binding_sha = bind_candidate(candidate_path, result_path, args.mode, pre, executor, guard_context)
    elif candidate_exists and (status != "PASS" or result_error is not None or not guard_ok):
        relationship_ok = False

    if not source_stable:
        final_status = "SOURCE_CHANGED_FAIL_CLOSED"
        rc = 4
    elif result_error is not None:
        final_status = "RESULT_IDENTITY_FAIL_CLOSED"
        rc = 4
    elif not guard_ok:
        final_status = "GUARD_FAIL_CLOSED"
        rc = 4
    elif not relationship_ok:
        final_status = "CANDIDATE_RESULT_RELATION_FAIL_CLOSED"
        rc = 4
    elif status == "PASS" and binding_sha is not None and proc.returncode == 0:
        final_status = "BOUND_PROMOTION_CANDIDATE"
        rc = 0
    elif status == "SCIENTIFIC_NEGATIVE" and not candidate_exists:
        final_status = "BOUND_SCIENTIFIC_NEGATIVE"
        rc = 2
    elif status == "BLOCKED_LOCAL_FASTPATH" and not candidate_exists:
        final_status = "TARGET_BLOCKED_GUARD_INTACT"
        rc = 3
    else:
        final_status = "UNCLASSIFIED_FAIL_CLOSED"
        rc = 4

    receipt = {
        "schema": GUARD_RECEIPT_SCHEMA,
        "status": final_status,
        "started_at": started,
        "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "mode": args.mode,
        "source_before": pre,
        "source_after": post,
        "source_stable_clean": source_stable,
        "executor_path": str(executor.relative_to(ROOT)),
        "executor_sha256": sha256_file(executor),
        "envelope_sha256": sha256_file(Path(__file__)),
        "python_executable_sha256": sha256_file(Path(sys.executable)),
        "guard": guard_context,
        "target_status": status,
        "result_file_sha256": sha256_file(result_path) if result_path.is_file() else None,
        "candidate_file_sha256": sha256_file(candidate_path) if candidate_path.is_file() else None,
        "binding_sha256": binding_sha,
        "result_error": result_error,
        "evidence_scope": "LOCAL_QWEN_GUARD_SOURCE_AND_RUNTIME_BINDING_ONLY",
        "credit": {"whole_entityos_hcu": 0, "hcu_full": 0, "jspace_model": 0, "training": 0, "canonical_semantics": False},
    }
    receipt["receipt_sha256"] = canonical_sha(receipt)
    guard_receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
