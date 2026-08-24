#!/usr/bin/env python3
"""Source-attested envelope for the two fixed local Trigger-1 Qwen runtimes.

The wrapper is intentionally not a generic command runner. It can execute only the
terminal positive-control or the non-terminal intermediate Qwen discriminator. It
requires the same clean Git identity before and after execution and, if a promotion
candidate is emitted, replaces its local runtime receipt with a receipt that binds
the original executor receipt to source, executor, Python and result identities.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from trigger1_source_attestation import require_clean_source

ROOT = Path(__file__).resolve().parents[1]
MODES = {
    "terminal": ROOT / "tools" / "trigger1_local_qwen06_activation_api_execute.py",
    "intermediate": ROOT / "tools" / "trigger1_local_qwen06_intermediate_api_execute.py",
}
BINDING_SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN_SOURCE_EXECUTION_BINDING/v1"


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return obj


def bind_candidate(
    candidate_path: Path,
    result_path: Path,
    mode: str,
    source: dict[str, Any],
    executor: Path,
) -> str:
    candidate = _load_object(candidate_path)
    result = _load_object(result_path)
    identity = candidate.get("source_identity")
    target = candidate.get("target")
    if not isinstance(identity, dict) or not isinstance(target, dict):
        raise RuntimeError("CANDIDATE_IDENTITY_OR_TARGET_MISSING")
    if identity.get("repo_head") != source["repo_head"]:
        raise RuntimeError("CANDIDATE_HEAD_SOURCE_ATTESTATION_MISMATCH")
    result_source = result.get("source")
    if not isinstance(result_source, dict) or result_source.get("repo_head") != source["repo_head"]:
        raise RuntimeError("RESULT_HEAD_SOURCE_ATTESTATION_MISMATCH")

    original_runtime_receipt = target.get("local_runtime_execution_receipt_sha256")
    if not isinstance(original_runtime_receipt, str) or len(original_runtime_receipt) != 64:
        raise RuntimeError("ORIGINAL_LOCAL_RUNTIME_RECEIPT_REQUIRED")
    try:
        int(original_runtime_receipt, 16)
    except ValueError as exc:
        raise RuntimeError("ORIGINAL_LOCAL_RUNTIME_RECEIPT_REQUIRED") from exc

    binding = {
        "schema": BINDING_SCHEMA,
        "mode": mode,
        "source_identity": source,
        "executor_path": str(executor.relative_to(ROOT)),
        "executor_sha256": sha256_file(executor),
        "python_executable": sys.executable,
        "python_executable_sha256": sha256_file(Path(sys.executable)),
        "candidate_pre_binding_sha256": sha256_file(candidate_path),
        "result_file_sha256": sha256_file(result_path),
        "original_local_runtime_execution_receipt_sha256": original_runtime_receipt,
        "endpoint": (candidate.get("transport") or {}).get("endpoint"),
    }
    binding_sha = canonical_sha(binding)
    binding["binding_sha256"] = binding_sha

    identity.update(source)
    target["executor_local_runtime_receipt_sha256"] = original_runtime_receipt
    target["source_execution_binding_sha256"] = binding_sha
    target["local_runtime_execution_receipt_sha256"] = binding_sha
    candidate_path.write_text(
        json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    binding_path = candidate_path.parent / "trigger1_source_execution_binding.json"
    binding_path.write_text(
        json.dumps(binding, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    result["source_attestation"] = source
    result["source_execution_binding_sha256"] = binding_sha
    result["promotion_candidate_sha256_after_binding"] = sha256_file(candidate_path)
    result["result_sha256"] = canonical_sha({k: v for k, v in result.items() if k != "result_sha256"})
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return binding_sha


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=sorted(MODES), required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--cache-dir", required=True)
    args = ap.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result_path = out / "trigger1_local_activation_api_result.json"
    candidate_path = out / "trigger1_direct_steering_candidate.json"
    executor = MODES[args.mode]

    pre = require_clean_source(ROOT)
    proc = subprocess.run(
        [sys.executable, str(executor), "--output-dir", str(out), "--cache-dir", str(args.cache_dir)],
        cwd=str(ROOT),
        check=False,
    )
    post = require_clean_source(ROOT)
    if pre != post:
        if candidate_path.exists():
            candidate_path.unlink()
        raise RuntimeError("SOURCE_CHANGED_DURING_LOCAL_QWEN_EXECUTION")

    if candidate_path.exists():
        if not result_path.is_file():
            candidate_path.unlink()
            raise RuntimeError("CANDIDATE_WITHOUT_RESULT_FAIL_CLOSED")
        bind_candidate(candidate_path, result_path, args.mode, pre, executor)
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
