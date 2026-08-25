#!/usr/bin/env python3
"""Bind raw one-token native-cvec observations to exact case prompts and runtime identity.

This tool is execution-free. It consumes JSONL emitted by
trigger1_native_llamacpp_single_token_cvec.cpp plus a frozen case manifest, verifies
that each observed prompt hex equals the exact manifest prompt, adds cryptographic
prompt/harness/runtime receipt identities, and emits the evidence object consumed by
trigger1_native_single_token_scope_gate_v1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from tools import trigger1_native_single_token_scope_gate_v1 as scope_gate

HEADER_SCHEMA = "CLAY_LLAMA_CPP_SINGLE_TOKEN_CVEC_HEADER/v1"
OBS_SCHEMA = "CLAY_LLAMA_CPP_SINGLE_TOKEN_CVEC_OBSERVATION/v1"
MANIFEST_SCHEMA = "CLAY_TRIGGER1_NATIVE_SINGLE_TOKEN_CASE_MANIFEST/v1"
EVIDENCE_SCHEMA = scope_gate.EVIDENCE_SCHEMA


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bind(raw_jsonl: Path, manifest_path: Path, harness_source: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema") != MANIFEST_SCHEMA:
        raise ValueError("CASE_MANIFEST_SCHEMA_INVALID")
    if manifest.get("llama_cpp_commit") != scope_gate.PINNED_LLAMA_CPP:
        raise ValueError("CASE_MANIFEST_LLAMA_CPP_COMMIT_MISMATCH")
    if manifest.get("gguf_sha256") != scope_gate.PINNED_GGUF_SHA256:
        raise ValueError("CASE_MANIFEST_GGUF_SHA256_MISMATCH")

    manifest_rows = manifest.get("rows")
    if not isinstance(manifest_rows, list) or not manifest_rows:
        raise ValueError("CASE_MANIFEST_ROWS_REQUIRED")
    expected: dict[tuple[str, str], dict[str, Any]] = {}
    for i, row in enumerate(manifest_rows):
        if not isinstance(row, dict):
            raise ValueError(f"CASE_MANIFEST_ROW_{i}_OBJECT_REQUIRED")
        case_id = str(row.get("case_id") or "")
        control = str(row.get("control") or "")
        prompt = row.get("prompt")
        if not case_id or control not in scope_gate.CONTROLS or not isinstance(prompt, str) or not prompt:
            raise ValueError(f"CASE_MANIFEST_ROW_{i}_IDENTITY_INVALID")
        key = (case_id, control)
        if key in expected:
            raise ValueError(f"CASE_MANIFEST_DUPLICATE:{case_id}:{control}")
        expected[key] = row

    parsed = [json.loads(line) for line in raw_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not parsed or parsed[0].get("schema") != HEADER_SCHEMA:
        raise ValueError("RAW_HEADER_INVALID")
    header = parsed[0]
    observed: dict[tuple[str, str], dict[str, Any]] = {}
    for i, row in enumerate(parsed[1:]):
        if not isinstance(row, dict) or row.get("schema") != OBS_SCHEMA:
            raise ValueError(f"RAW_ROW_{i}_SCHEMA_INVALID")
        key = (str(row.get("case_id") or ""), str(row.get("control") or ""))
        if key not in expected:
            raise ValueError(f"RAW_ROW_{i}_NOT_IN_MANIFEST:{key[0]}:{key[1]}")
        if key in observed:
            raise ValueError(f"RAW_DUPLICATE:{key[0]}:{key[1]}")
        prompt = expected[key]["prompt"]
        expected_hex = prompt.encode("utf-8").hex()
        if row.get("prompt_utf8_hex") != expected_hex:
            raise ValueError(f"RAW_PROMPT_MISMATCH:{key[0]}:{key[1]}")
        observed[key] = row
    if set(observed) != set(expected):
        missing = sorted(set(expected) - set(observed))
        raise ValueError(f"RAW_CASE_UNIVERSE_INCOMPLETE:{missing[:5]}")

    harness_sha = sha_file(harness_source)
    bound_rows: list[dict[str, Any]] = []
    for key in sorted(observed):
        row = dict(observed[key])
        prompt = expected[key]["prompt"]
        row["prompt_sha256"] = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        row["harness_source_sha256"] = harness_sha
        receipt_material = {
            "observation": row,
            "manifest_row": expected[key],
            "manifest_sha256": sha_file(manifest_path),
            "raw_jsonl_sha256": sha_file(raw_jsonl),
            "llama_cpp_commit": manifest["llama_cpp_commit"],
            "gguf_sha256": manifest["gguf_sha256"],
        }
        row["runtime_receipt_sha256"] = canonical_sha(receipt_material)
        bound_rows.append(row)

    evidence = {
        "schema": EVIDENCE_SCHEMA,
        "llama_cpp_commit": manifest["llama_cpp_commit"],
        "gguf_sha256": manifest["gguf_sha256"],
        "harness_source_sha256": harness_sha,
        "harness_header": header,
        "case_manifest_sha256": sha_file(manifest_path),
        "raw_jsonl_sha256": sha_file(raw_jsonl),
        "rows": bound_rows,
    }
    verdict = scope_gate.validate({"native_single_token_scope_evidence": evidence})
    if verdict.get("pass") is not True:
        raise ValueError("BOUND_SCOPE_GATE_FAILED:" + ",".join(verdict.get("failures", [])))
    evidence["binding_receipt_sha256"] = canonical_sha(evidence)
    return evidence


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-jsonl", required=True, type=Path)
    ap.add_argument("--manifest-json", required=True, type=Path)
    ap.add_argument("--harness-source", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    evidence = bind(args.raw_jsonl, args.manifest_json, args.harness_source)
    args.out.write_text(json.dumps(evidence, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": EVIDENCE_SCHEMA,
        "rows": len(evidence["rows"]),
        "binding_receipt_sha256": evidence["binding_receipt_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
