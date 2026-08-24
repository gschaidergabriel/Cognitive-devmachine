#!/usr/bin/env python3
"""Purpose-specific bridge for the strongest local Trigger-1 Qwen discriminator.

This wrapper executes only the existing counterbalanced intermediate Qwen3-0.6B
protocol, requires a stable clean Git source before/after execution, verifies the
intermediate result/candidate self-digests, translates a scientific PASS through the
existing promotion bridge, and exposes the filenames consumed by the lease-gated V2
self-hosted publisher. It is not a generic command runner and does not mint canonical,
whole-EntityOS/HCU, J-Space-model, or training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from trigger1_intermediate_promotion_bridge import build_direct_candidate
from trigger1_source_attestation import require_clean_source

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / "tools" / "trigger1_local_qwen06_intermediate_execute.py"
SCHEMA = "CLAY_TRIGGER1_STRONGEST_INTERMEDIATE_EXECUTION_BRIDGE/v1"


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


def load_object(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return obj


def verify_self_digest(obj: dict[str, Any], field: str) -> None:
    observed = obj.get(field)
    if not isinstance(observed, str) or len(observed) != 64:
        raise RuntimeError(f"SELF_DIGEST_REQUIRED:{field}")
    material = {k: v for k, v in obj.items() if k != field}
    if canonical_sha(material) != observed:
        raise RuntimeError(f"SELF_DIGEST_MISMATCH:{field}")


def write_alias(
    path: Path,
    result: dict[str, Any],
    *,
    source: dict[str, Any],
    process_rc: int,
    bridge: dict[str, Any],
) -> None:
    alias = json.loads(json.dumps(result))
    alias["strongest_intermediate_execution_bridge"] = {
        "schema": SCHEMA,
        "source_attestation": source,
        "executor_path": str(EXECUTOR.relative_to(ROOT)),
        "executor_sha256": sha256_file(EXECUTOR),
        "python_executable_sha256": sha256_file(Path(sys.executable)),
        "process_exit_code": process_rc,
        **bridge,
        "credit_boundary": {
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
        },
    }
    alias["result_sha256"] = canonical_sha({k: v for k, v in alias.items() if k != "result_sha256"})
    path.write_text(json.dumps(alias, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--cache-dir", required=True)
    args = ap.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    intermediate_result_path = out / "trigger1_intermediate_result.json"
    intermediate_candidate_path = out / "trigger1_intermediate_candidate.json"
    direct_candidate_path = out / "trigger1_direct_steering_candidate.json"
    compatibility_result_path = out / "trigger1_local_activation_api_result.json"

    pre = require_clean_source(ROOT)
    proc = subprocess.run(
        [
            sys.executable,
            str(EXECUTOR),
            "--output-dir",
            str(out),
            "--cache-dir",
            str(args.cache_dir),
        ],
        cwd=str(ROOT),
        check=False,
    )
    post = require_clean_source(ROOT)
    if pre != post:
        direct_candidate_path.unlink(missing_ok=True)
        if intermediate_result_path.is_file():
            result = load_object(intermediate_result_path)
            write_alias(
                compatibility_result_path,
                result,
                source=pre,
                process_rc=int(proc.returncode),
                bridge={"status": "BLOCKED", "reason": "SOURCE_CHANGED_DURING_INTERMEDIATE_EXECUTION"},
            )
        raise RuntimeError("SOURCE_CHANGED_DURING_INTERMEDIATE_EXECUTION")

    if not intermediate_result_path.is_file():
        raise RuntimeError("INTERMEDIATE_RESULT_MISSING")
    result = load_object(intermediate_result_path)
    verify_self_digest(result, "result_sha256")
    result_source = result.get("source")
    if not isinstance(result_source, dict):
        raise RuntimeError("INTERMEDIATE_RESULT_SOURCE_REQUIRED")
    if result_source.get("repo_head") != pre["repo_head"] or result_source.get("repo_tree") != pre["repo_tree"]:
        raise RuntimeError("INTERMEDIATE_RESULT_SOURCE_ATTESTATION_MISMATCH")

    if proc.returncode != 0:
        direct_candidate_path.unlink(missing_ok=True)
        write_alias(
            compatibility_result_path,
            result,
            source=pre,
            process_rc=int(proc.returncode),
            bridge={"status": "NOT_PROMOTED", "reason": "INTERMEDIATE_PROTOCOL_NONZERO"},
        )
        return int(proc.returncode)

    if result.get("status") != "PASS" or not intermediate_candidate_path.is_file():
        direct_candidate_path.unlink(missing_ok=True)
        write_alias(
            compatibility_result_path,
            result,
            source=pre,
            process_rc=int(proc.returncode),
            bridge={"status": "BLOCKED", "reason": "PASS_WITHOUT_INTERMEDIATE_CANDIDATE"},
        )
        return 4

    intermediate = load_object(intermediate_candidate_path)
    verify_self_digest(intermediate, "candidate_sha256")
    direct = build_direct_candidate(result, intermediate)
    direct_candidate_path.write_text(
        json.dumps(direct, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    bridge_record = {
        "status": "PASS",
        "intermediate_result_file_sha256": sha256_file(intermediate_result_path),
        "intermediate_candidate_file_sha256": sha256_file(intermediate_candidate_path),
        "direct_candidate_sha256": canonical_sha(direct),
    }
    write_alias(
        compatibility_result_path,
        result,
        source=pre,
        process_rc=int(proc.returncode),
        bridge=bridge_record,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
