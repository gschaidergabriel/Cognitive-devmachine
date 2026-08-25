#!/usr/bin/env python3
"""Fail-closed trainer projection for materialized Trigger-2 rows.

This tool is a visibility boundary only. It cannot admit rows into the canonical
TrainingTrace/Forge/Distillery dataset and cannot mint dataset/model/runtime credit.
It emits a model-visible JSONL containing ONLY user prompt + assistant target and a
separate audit sidecar. Blueprint/placeholders and unverified materializations fail.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from tools import entityos_hcu_trainingtrace_candidate_gate_v1 as row_gate

SCHEMA = "TRIGGER2_SFT_PROJECTION_GATE/v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_HASHES = (
    "abi_manifest_sha256",
    "symbol_partition_manifest_sha256",
    "tokenizer_identity_sha256",
    "materialization_receipt_sha256",
)


def _sha(x: Any) -> bool:
    return isinstance(x, str) and bool(_SHA256.fullmatch(x.lower())) and x.lower() != ("0" * 64)


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_evidence_bytes(row: dict[str, Any], evidence_files: dict[str, Path]) -> list[str]:
    """Bind claimed materialization digests to the exact files supplied for export.

    This proves byte identity only. It does not prove that the contents semantically
    establish tokenizer quality, partition correctness, counterbalance, or admission.
    """
    failures: list[str] = []
    mat = row.get("abi_materialization") if isinstance(row, dict) else None
    if not isinstance(mat, dict):
        return ["ABI_MATERIALIZATION_REQUIRED"]
    for key in REQUIRED_HASHES:
        path = evidence_files.get(key)
        if not isinstance(path, Path) or not path.is_file():
            failures.append("EVIDENCE_FILE_REQUIRED:" + key)
            continue
        actual = _file_sha256(path)
        if mat.get(key) != actual:
            failures.append("EVIDENCE_BYTE_HASH_MISMATCH:" + key)
    return failures


def _canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def adjudicate(row: Any) -> dict[str, Any]:
    failures: list[str] = []
    base = row_gate.adjudicate(row)
    if not base["candidate_admission_pass"]:
        failures.extend("ROW_GATE:" + f for f in base["failures"])
    if not isinstance(row, dict):
        row = {}

    if row.get("training_eligible") is not True:
        failures.append("EXPLICIT_TRAINING_ELIGIBLE_TRUE_REQUIRED")
    if row.get("render_status") != "ABI_ATOM_RENDERED_AND_VERIFIED":
        failures.append("ABI_ATOM_RENDERED_AND_VERIFIED_REQUIRED")

    prompt = row.get("prompt")
    target = row.get("target")
    if not isinstance(prompt, str) or not prompt.strip():
        failures.append("PROMPT_REQUIRED")
    if not isinstance(target, str) or not target or "\n" in target or "\r" in target:
        failures.append("SINGLE_LINE_TARGET_REQUIRED")

    cfid = row.get("counterfactual_family_id")
    if not isinstance(cfid, str) or not cfid:
        failures.append("COUNTERFACTUAL_FAMILY_ID_REQUIRED")

    mat = row.get("abi_materialization")
    if not isinstance(mat, dict):
        failures.append("ABI_MATERIALIZATION_REQUIRED")
        mat = {}
    raw_triplet = mat.get("actual_atom_triplet")
    triplet = raw_triplet if isinstance(raw_triplet, list) else []
    if len(triplet) != 3 or len(set(map(str, triplet))) != 3:
        failures.append("INJECTIVE_ACTUAL_ATOM_TRIPLET_REQUIRED")
    if any(str(a) == "or" for a in triplet):
        failures.append("REJECTED_ATOM_OR_FORBIDDEN")
    if mat.get("target_atom") != target or target not in triplet:
        failures.append("TARGET_MUST_MATCH_REALIZED_ATOM_TRIPLET")
    for key in REQUIRED_HASHES:
        if not _sha(mat.get(key)):
            failures.append("MATERIALIZATION_HASH_REQUIRED:" + key)
    for key in (
        "tokenizer_single_token_verified",
        "symbol_partition_visibility_verified",
        "real_atom_counterbalance_verified",
        "rejected_atom_exclusion_verified",
    ):
        if mat.get(key) is not True:
            failures.append("MATERIALIZATION_GUARD_TRUE_REQUIRED:" + key)

    model_record = None
    audit_record = None
    if not failures:
        model_record = {
            "messages": [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": target},
            ]
        }
        model_sha = hashlib.sha256(_canonical_json(model_record)).hexdigest()
        audit_record = {
            "schema": "TRIGGER2_SFT_PROJECTION_AUDIT/v1",
            "family_id": row["family_id"],
            "provenance_ancestry_id": row["provenance_ancestry_id"],
            "counterfactual_family_id": cfid,
            "split": row["split"],
            "model_record_sha256": model_sha,
            "materialization_receipt_sha256": mat["materialization_receipt_sha256"],
            "canonical_dataset_admission": False,
            "accepted_dataset_tokens_minted": 0,
        }

    return {
        "schema": SCHEMA,
        "projection_pass": not failures,
        "failures": sorted(set(failures)),
        "model_record": model_record,
        "audit_record": audit_record,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": False,
        "evidence_boundary": "Visibility projection only; canonical evidence-qualified admission remains downstream.",
    }


def _load(path: Path) -> list[dict[str, Any]]:
    rows=[]
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, 1):
            if not raw.strip():
                continue
            obj=json.loads(raw)
            if not isinstance(obj, dict):
                raise ValueError(f"{path}:{line_no}: object required")
            rows.append(obj)
    return rows


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("--model-jsonl", required=True, type=Path)
    ap.add_argument("--audit-jsonl", required=True, type=Path)
    ap.add_argument("--abi-manifest", required=True, type=Path)
    ap.add_argument("--symbol-partition-manifest", required=True, type=Path)
    ap.add_argument("--tokenizer-identity", required=True, type=Path)
    ap.add_argument("--materialization-receipt", required=True, type=Path)
    args=ap.parse_args()
    evidence_files = {
        "abi_manifest_sha256": args.abi_manifest,
        "symbol_partition_manifest_sha256": args.symbol_partition_manifest,
        "tokenizer_identity_sha256": args.tokenizer_identity,
        "materialization_receipt_sha256": args.materialization_receipt,
    }
    rows=_load(args.input)
    results=[]
    for row in rows:
        result=adjudicate(row)
        byte_failures=verify_evidence_bytes(row, evidence_files) if result["projection_pass"] else []
        if byte_failures:
            result["failures"]=sorted(set(result["failures"] + byte_failures))
            result["projection_pass"]=False
            result["model_record"]=None
            result["audit_record"]=None
        results.append(result)
    bad=[{"index":i,"failures":r["failures"]} for i,r in enumerate(results) if not r["projection_pass"]]
    summary={"schema":SCHEMA,"rows_total":len(rows),"rows_pass":len(rows)-len(bad),"rows_fail":len(bad),"failures":bad,
             "outputs_written":False,"canonical_dataset_admission":False,"accepted_dataset_tokens_minted":0,
             "evidence_byte_identity_checked":True,
             "evidence_semantics_authenticated":False}
    if bad:
        print(json.dumps(summary, sort_keys=True))
        return 1
    model_text="\n".join(json.dumps(r["model_record"], ensure_ascii=False, sort_keys=True) for r in results)+("\n" if results else "")
    audit_text="\n".join(json.dumps(r["audit_record"], ensure_ascii=False, sort_keys=True) for r in results)+("\n" if results else "")
    args.model_jsonl.write_text(model_text, encoding="utf-8")
    args.audit_jsonl.write_text(audit_text, encoding="utf-8")
    summary["outputs_written"]=True
    summary["model_jsonl_sha256"]=hashlib.sha256(model_text.encode()).hexdigest()
    summary["audit_jsonl_sha256"]=hashlib.sha256(audit_text.encode()).hexdigest()
    print(json.dumps(summary, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
