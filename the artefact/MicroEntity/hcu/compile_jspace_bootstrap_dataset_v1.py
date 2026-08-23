from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

TRACE_SCHEMA = "ENTITYOS_HCU_GLOBAL_JSPACE_GWT_TRACE/v1"
DATASET_SCHEMA = "ENTITYOS_HCU_JSPACE_BOOTSTRAP_DATASET/v1"
SYSTEM = (
    "You are a narrow EntityOS/HCU cognitive coprocessor. "
    "Follow JSPACE_VECTOR_CONTROL_ABI/v1, GWT/Hyperposition, generation/basis/role fences, "
    "and output only the requested compact JSON decision. "
    "Model output is candidate/control behavior, never truth or EffectGate authority."
)


class DatasetError(ValueError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _trace_sha(trace: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(trace).encode("ascii")).hexdigest()


def _split(trace_sha256: str) -> str:
    # Deterministic whole-trace-family split: ~80 / 10 / 10.
    bucket = int(trace_sha256[:2], 16)
    if bucket < 205:
        return "train"
    if bucket < 230:
        return "validation"
    return "holdout"


def _row(kind: str, user: dict[str, Any], assistant: dict[str, Any], trace_sha256: str) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": _canonical({"task": kind, **user})},
            {"role": "assistant", "content": _canonical(assistant)},
        ],
        "metadata": {
            "dataset_schema": DATASET_SCHEMA,
            "trace_sha256": trace_sha256,
            "family": kind,
        },
    }


def derive_bootstrap_examples(trace: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(trace, dict) or trace.get("schema") != TRACE_SCHEMA:
        raise DatasetError("TRACE_SCHEMA_UNSUPPORTED")
    required = (
        "generation",
        "basis_id",
        "winner_cell_id",
        "winner_role",
        "winner_gate_q",
        "hyperposition_cells",
        "control_packet_text",
        "contributions",
        "authority",
    )
    for key in required:
        if key not in trace:
            raise DatasetError(f"TRACE_FIELD_MISSING:{key}")
    if trace["authority"] != "CANDIDATE_MEASUREMENT_ONLY_NOT_TRUTH_OR_EFFECT":
        raise DatasetError("TRACE_AUTHORITY_INVALID")

    sha = _trace_sha(trace)
    common = {
        "control_packet": trace["control_packet_text"],
        "expected_basis_id": trace["basis_id"],
        "expected_role": trace["winner_role"],
        "expected_generation": trace["generation"],
    }
    accept = {
        "decision": "ACCEPT_CONTROL",
        "winner_cell_id": trace["winner_cell_id"],
        "winner_role": trace["winner_role"],
        "winner_gate_q": trace["winner_gate_q"],
        "hyperposition_cells": trace["hyperposition_cells"],
        "authority": "CANDIDATE_CONTROL_ONLY",
    }

    rows = [_row("VECTOR_CONTROL_VALIDATE", common, accept, sha)]
    rows.append(
        _row(
            "VECTOR_CONTROL_VALIDATE",
            {**common, "expected_generation": trace["generation"] + 1},
            {"decision": "REJECT", "reason": "JCTL_GENERATION_MISMATCH"},
            sha,
        )
    )
    rows.append(
        _row(
            "VECTOR_CONTROL_VALIDATE",
            {**common, "expected_basis_id": trace["basis_id"] + "#WRONG"},
            {"decision": "REJECT", "reason": "JCTL_BASIS_MISMATCH"},
            sha,
        )
    )
    rows.append(
        _row(
            "GWT_BROADCAST_FROM_TRACE",
            {
                "generation": trace["generation"],
                "basis_id": trace["basis_id"],
                "contributions": trace["contributions"],
            },
            {
                "decision": "GWT_BROADCAST",
                "winner_cell_id": trace["winner_cell_id"],
                "winner_role": trace["winner_role"],
                "winner_gate_q": trace["winner_gate_q"],
                "hyperposition_cells": trace["hyperposition_cells"],
                "control_packet": trace["control_packet_text"],
                "authority": "CANDIDATE_CONTROL_ONLY",
            },
            sha,
        )
    )
    return rows


def compile_traces(traces: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out = {"train": [], "validation": [], "holdout": []}
    seen: set[str] = set()
    for trace in traces:
        sha = _trace_sha(trace)
        if sha in seen:
            continue
        seen.add(sha)
        out[_split(sha)].extend(derive_bootstrap_examples(trace))
    if not seen:
        raise DatasetError("NO_TRACES")
    return out


def compile_jsonl(input_path: Path, output_dir: Path) -> dict[str, Any]:
    if not isinstance(input_path, Path) or not isinstance(output_dir, Path):
        raise DatasetError("PATH_TYPE_REQUIRED")
    traces = []
    for lineno, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            traces.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise DatasetError(f"JSONL_INVALID_LINE:{lineno}") from exc

    compiled = compile_traces(traces)
    output_dir.mkdir(parents=True, exist_ok=True)
    receipt = {"schema": DATASET_SCHEMA, "input_trace_count": len(traces), "splits": {}}
    for split, rows in compiled.items():
        path = output_dir / f"{split}.jsonl"
        payload = "".join(_canonical(row) + "\n" for row in rows)
        path.write_text(payload, encoding="ascii")
        receipt["splits"][split] = {
            "row_count": len(rows),
            "sha256": hashlib.sha256(payload.encode("ascii")).hexdigest(),
            "path": path.name,
        }

    receipt_path = output_dir / "dataset_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt
