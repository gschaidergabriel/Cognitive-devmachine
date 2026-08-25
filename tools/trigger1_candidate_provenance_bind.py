#!/usr/bin/env python3
"""Bind a Trigger-1 promotion candidate to the exact executor/source identity in its runtime result.

This is a deterministic post-processing gate. It does not execute a model. It fails closed
when the candidate and runtime result disagree, then copies the already-observed exact source
identity into the candidate so later promotion cannot silently lose executor or dirty-tree
provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

RESULT_SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_MIDLAYER_CAUSAL_EXPERIMENT/v1"
CANDIDATE_SCHEMA = "CLAY_TRIGGER1_JSPACE_DIRECT_STEERING_CANDIDATE/v1"


def _sha256_text(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_text(path.read_bytes())


def _is_hex(value: Any, length: int) -> bool:
    if not isinstance(value, str) or len(value) != length:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _require_hex(obj: dict[str, Any], key: str, length: int) -> str:
    value = obj.get(key)
    if not _is_hex(value, length):
        raise ValueError(f"INVALID_OR_MISSING_IDENTITY:{key}")
    return str(value)


def bind_candidate(result: dict[str, Any], candidate: dict[str, Any], *, binder_sha256: str) -> dict[str, Any]:
    if result.get("schema") != RESULT_SCHEMA:
        raise ValueError("RESULT_SCHEMA_INVALID")
    if result.get("status") != "PASS":
        raise ValueError("RESULT_PASS_REQUIRED")
    if candidate.get("schema") != CANDIDATE_SCHEMA:
        raise ValueError("CANDIDATE_SCHEMA_INVALID")

    source = result.get("source")
    identity = candidate.get("source_identity")
    if not isinstance(source, dict):
        raise ValueError("RESULT_SOURCE_IDENTITY_REQUIRED")
    if not isinstance(identity, dict):
        raise ValueError("CANDIDATE_SOURCE_IDENTITY_REQUIRED")

    repo_head = _require_hex(source, "repo_head", 40)
    repo_tree = _require_hex(source, "repo_tree", 40)
    dirty_sha = _require_hex(source, "repo_dirty_porcelain_sha256", 64)
    executor_sha = _require_hex(source, "executor_sha256", 64)
    runtime_build_sha = _require_hex(result, "runtime_build_sha256", 64)
    checkpoint_sha = _require_hex(result, "checkpoint_sha256", 64)
    tokenizer_sha = _require_hex(result, "tokenizer_sha256", 64)
    if not _is_hex(binder_sha256, 64):
        raise ValueError("BINDER_SHA256_INVALID")

    expected = {
        "repo_head": repo_head,
        "runtime_build_sha256": runtime_build_sha,
        "checkpoint_sha256": checkpoint_sha,
        "tokenizer_sha256": tokenizer_sha,
    }
    for key, value in expected.items():
        if identity.get(key) != value:
            raise ValueError(f"CANDIDATE_RESULT_IDENTITY_MISMATCH:{key}")

    bound = dict(candidate)
    bound_identity = dict(identity)
    bound_identity.update(
        {
            "repo_tree": repo_tree,
            "repo_dirty_porcelain_sha256": dirty_sha,
            "executor_sha256": executor_sha,
            "provenance_binder_sha256": binder_sha256,
        }
    )
    binding_material = {
        "repo_head": repo_head,
        "repo_tree": repo_tree,
        "repo_dirty_porcelain_sha256": dirty_sha,
        "executor_sha256": executor_sha,
        "runtime_build_sha256": runtime_build_sha,
        "checkpoint_sha256": checkpoint_sha,
        "tokenizer_sha256": tokenizer_sha,
        "provenance_binder_sha256": binder_sha256,
    }
    bound_identity["provenance_binding_sha256"] = _sha256_text(
        json.dumps(binding_material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    bound["source_identity"] = bound_identity
    return bound


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()

    result_path = Path(args.result)
    candidate_path = Path(args.candidate)
    result = json.loads(result_path.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    if not isinstance(result, dict) or not isinstance(candidate, dict):
        raise ValueError("RESULT_AND_CANDIDATE_OBJECTS_REQUIRED")

    bound = bind_candidate(result, candidate, binder_sha256=_sha256_file(Path(__file__)))
    tmp = candidate_path.with_suffix(candidate_path.suffix + ".tmp")
    tmp.write_text(json.dumps(bound, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(candidate_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
