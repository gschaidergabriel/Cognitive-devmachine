from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

try:
    from .entry_canonicalization_v1 import (
        CANONICALIZATION_SCHEMA,
        CanonicalizationError,
        canonicalize,
    )
    from .global_jspace_gwt_v1 import (
        ABI_SCHEMA,
        TRACE_CANONICALIZATION_SCHEMA,
        TRACE_SCHEMA,
    )
    from .jspace_vector_control_v1 import (
        JSpaceVectorControlError,
        packet_bytes,
        parse_packet_text,
    )
except ImportError:
    from entry_canonicalization_v1 import (
        CANONICALIZATION_SCHEMA,
        CanonicalizationError,
        canonicalize,
    )
    from global_jspace_gwt_v1 import (
        ABI_SCHEMA,
        TRACE_CANONICALIZATION_SCHEMA,
        TRACE_SCHEMA,
    )
    from jspace_vector_control_v1 import (
        JSpaceVectorControlError,
        packet_bytes,
        parse_packet_text,
    )

DATASET_SCHEMA = "ENTITYOS_HCU_JSPACE_BOOTSTRAP_DATASET/v2"
SYSTEM = (
    "You are a narrow EntityOS/HCU cognitive coprocessor. "
    "Follow JSPACE_VECTOR_CONTROL_ABI/v1, GWT/Hyperposition, generation/basis/role fences, "
    "and output only the requested compact JSON decision. "
    "Model output is candidate/control behavior, never truth or EffectGate authority."
)


class DatasetError(ValueError):
    pass


def _canonical_json(value: Any) -> str:
    """Deterministic JSONL transport encoding, not trace identity authority."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _trace_sha(trace: dict[str, Any]) -> str:
    """Reuse the selected HCU RFC8785/JCS bytes for trace-family identity."""
    try:
        return hashlib.sha256(canonicalize(trace)).hexdigest()
    except CanonicalizationError as exc:
        raise DatasetError(f"TRACE_CANONICALIZATION_FAILED:{exc}") from exc


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
            {"role": "user", "content": _canonical_json({"task": kind, **user})},
            {"role": "assistant", "content": _canonical_json(assistant)},
        ],
        "metadata": {
            "dataset_schema": DATASET_SCHEMA,
            "trace_schema": TRACE_SCHEMA,
            "trace_canonicalization_schema": TRACE_CANONICALIZATION_SCHEMA,
            "trace_sha256": trace_sha256,
            "family": kind,
        },
    }


def _lower_sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value.lower() != value:
        raise DatasetError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if any(ch not in "0123456789abcdef" for ch in value):
        raise DatasetError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _validate_trace(trace: dict[str, Any]) -> str:
    if not isinstance(trace, dict) or trace.get("schema") != TRACE_SCHEMA:
        raise DatasetError("TRACE_SCHEMA_UNSUPPORTED")
    if TRACE_CANONICALIZATION_SCHEMA != CANONICALIZATION_SCHEMA:
        raise DatasetError("TRACE_CANONICALIZATION_AUTHORITY_MISMATCH")
    if trace.get("canonicalization_schema") != TRACE_CANONICALIZATION_SCHEMA:
        raise DatasetError("TRACE_CANONICALIZATION_SCHEMA_MISMATCH")

    required = (
        "generation",
        "basis_id",
        "basis_sha256",
        "winner_cell_id",
        "winner_role",
        "winner_gate_q",
        "hyperposition_cells",
        "control_condition",
        "control_packet_schema",
        "control_packet_text",
        "control_packet_identity_sha256",
        "control_packet_sha256",
        "control_packet_wire_sha256",
        "contributions",
        "authority",
    )
    for key in required:
        if key not in trace:
            raise DatasetError(f"TRACE_FIELD_MISSING:{key}")
    if trace["authority"] != "CANDIDATE_MEASUREMENT_ONLY_NOT_TRUTH_OR_EFFECT":
        raise DatasetError("TRACE_AUTHORITY_INVALID")
    if trace["control_packet_schema"] != ABI_SCHEMA:
        raise DatasetError("TRACE_CONTROL_PACKET_SCHEMA_MISMATCH")

    generation = trace["generation"]
    basis_id = trace["basis_id"]
    basis_sha256 = _lower_sha256(trace["basis_sha256"], "TRACE_BASIS_SHA256")
    winner_role = trace["winner_role"]
    winner_cell_id = trace["winner_cell_id"]
    winner_gate_q = trace["winner_gate_q"]
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise DatasetError("TRACE_GENERATION_INVALID")
    if not isinstance(basis_id, str) or not basis_id:
        raise DatasetError("TRACE_BASIS_ID_INVALID")
    if not isinstance(winner_role, str) or not winner_role:
        raise DatasetError("TRACE_WINNER_ROLE_INVALID")
    if not isinstance(winner_cell_id, str) or not winner_cell_id:
        raise DatasetError("TRACE_WINNER_CELL_ID_INVALID")
    if isinstance(winner_gate_q, bool) or not isinstance(winner_gate_q, int) or not 0 <= winner_gate_q <= 10000:
        raise DatasetError("TRACE_WINNER_GATE_Q_INVALID")

    try:
        packet = parse_packet_text(trace["control_packet_text"])
    except JSpaceVectorControlError as exc:
        raise DatasetError(f"TRACE_CONTROL_PACKET_INVALID:{exc}") from exc
    if packet.abi_schema != ABI_SCHEMA:
        raise DatasetError("TRACE_CONTROL_PACKET_ABI_MISMATCH")
    if packet.generation != generation:
        raise DatasetError("TRACE_CONTROL_PACKET_GENERATION_MISMATCH")
    if packet.basis_id != basis_id:
        raise DatasetError("TRACE_CONTROL_PACKET_BASIS_ID_MISMATCH")
    if packet.basis_sha256 != basis_sha256:
        raise DatasetError("TRACE_CONTROL_PACKET_BASIS_SHA256_MISMATCH")
    if packet.role != winner_role:
        raise DatasetError("TRACE_CONTROL_PACKET_ROLE_MISMATCH")
    if packet.control_condition != trace["control_condition"]:
        raise DatasetError("TRACE_CONTROL_PACKET_CONDITION_MISMATCH")

    identity_sha = _lower_sha256(
        trace["control_packet_identity_sha256"],
        "TRACE_CONTROL_PACKET_IDENTITY_SHA256",
    )
    if identity_sha != packet.packet_sha256:
        raise DatasetError("TRACE_CONTROL_PACKET_IDENTITY_MISMATCH")
    wire_sha = hashlib.sha256(packet_bytes(packet)).hexdigest()
    for field in ("control_packet_sha256", "control_packet_wire_sha256"):
        if _lower_sha256(trace[field], f"TRACE_{field.upper()}") != wire_sha:
            raise DatasetError("TRACE_CONTROL_PACKET_WIRE_SHA256_MISMATCH")

    contributions = trace["contributions"]
    if not isinstance(contributions, list) or not contributions:
        raise DatasetError("TRACE_CONTRIBUTIONS_REQUIRED")
    cell_ids: list[str] = []
    winner_rows: list[dict[str, Any]] = []
    for row in contributions:
        if not isinstance(row, dict):
            raise DatasetError("TRACE_CONTRIBUTION_OBJECT_REQUIRED")
        cell_id = row.get("cell_id")
        role = row.get("role")
        gate_q = row.get("gate_q")
        if not isinstance(cell_id, str) or not cell_id:
            raise DatasetError("TRACE_CONTRIBUTION_CELL_ID_INVALID")
        if not isinstance(role, str) or not role:
            raise DatasetError("TRACE_CONTRIBUTION_ROLE_INVALID")
        if isinstance(gate_q, bool) or not isinstance(gate_q, int) or not 0 <= gate_q <= 10000:
            raise DatasetError("TRACE_CONTRIBUTION_GATE_Q_INVALID")
        cell_ids.append(cell_id)
        if cell_id == winner_cell_id:
            winner_rows.append(row)
    if len(cell_ids) != len(set(cell_ids)):
        raise DatasetError("TRACE_CONTRIBUTION_CELL_ID_DUPLICATE")
    if len(winner_rows) != 1:
        raise DatasetError("TRACE_WINNER_CONTRIBUTION_MISSING")
    if winner_rows[0].get("role") != winner_role or winner_rows[0].get("gate_q") != winner_gate_q:
        raise DatasetError("TRACE_WINNER_CONTRIBUTION_MISMATCH")

    hyper = trace["hyperposition_cells"]
    if not isinstance(hyper, list) or any(not isinstance(cell_id, str) for cell_id in hyper):
        raise DatasetError("TRACE_HYPERPOSITION_INVALID")
    if len(hyper) != len(set(hyper)) or not set(hyper).issubset(set(cell_ids)):
        raise DatasetError("TRACE_HYPERPOSITION_BINDING_MISMATCH")

    return _trace_sha(trace)


def derive_bootstrap_examples(trace: dict[str, Any]) -> list[dict[str, Any]]:
    sha = _validate_trace(trace)
    common = {
        "control_packet": trace["control_packet_text"],
        "expected_basis_id": trace["basis_id"],
        "expected_basis_sha256": trace["basis_sha256"],
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
                "basis_sha256": trace["basis_sha256"],
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
        sha = _validate_trace(trace)
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
    receipt = {
        "schema": DATASET_SCHEMA,
        "trace_schema": TRACE_SCHEMA,
        "trace_canonicalization_schema": TRACE_CANONICALIZATION_SCHEMA,
        "input_trace_count": len(traces),
        "splits": {},
    }
    for split, rows in compiled.items():
        path = output_dir / f"{split}.jsonl"
        payload = "".join(_canonical_json(row) + "\n" for row in rows)
        path.write_text(payload, encoding="ascii")
        receipt["splits"][split] = {
            "row_count": len(rows),
            "sha256": hashlib.sha256(payload.encode("ascii")).hexdigest(),
            "path": path.name,
        }

    receipt_path = output_dir / "dataset_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt
