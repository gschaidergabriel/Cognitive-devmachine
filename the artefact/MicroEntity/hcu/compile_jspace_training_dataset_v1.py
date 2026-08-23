#!/usr/bin/env python3
"""Compile causal EntityOS/HCU J-Space training traces into leak-resistant JSONL.

This is the first training-eligible compiler boundary. It consumes only
ENTITYOS_HCU_JSPACE_TRAINING_TRACE/v1 records that already bind observable J-Space/GWT
state to Entry -> route -> GRID10 causal identities. Raw prototype traces remain a separate
bootstrap source and are not silently promoted into serious training evidence.
"""
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
    from .jspace_dataset_family_split_v1 import SPLIT_SCHEMA as FAMILY_SPLIT_SCHEMA, split_for_family
    from .jspace_training_trace_v1 import TRACE_SCHEMA as TRAINING_TRACE_SCHEMA
    from .jspace_vector_control_v1 import (
        ABI_SCHEMA,
        JSpaceVectorControlError,
        parse_packet_text,
    )
except ImportError:
    from entry_canonicalization_v1 import (
        CANONICALIZATION_SCHEMA,
        CanonicalizationError,
        canonicalize,
    )
    from jspace_dataset_family_split_v1 import SPLIT_SCHEMA as FAMILY_SPLIT_SCHEMA, split_for_family
    from jspace_training_trace_v1 import TRACE_SCHEMA as TRAINING_TRACE_SCHEMA
    from jspace_vector_control_v1 import (
        ABI_SCHEMA,
        JSpaceVectorControlError,
        parse_packet_text,
    )

DATASET_SCHEMA = "ENTITYOS_HCU_JSPACE_TRAINING_DATASET/v1"
SYSTEM = (
    "You are a narrow EntityOS/HCU cognitive coprocessor. "
    "Obey JSPACE_VECTOR_CONTROL_ABI/v1, causal Entry/route/GRID10 bindings, GWT and "
    "Hyperposition fences. Output only the requested compact JSON decision. "
    "Model output is candidate/control behavior, never canonical truth or EffectGate authority."
)
CREDIT_LABELS = frozenset({"UNKNOWN", "POSITIVE", "NEGATIVE", "NEUTRAL"})


class TrainingDatasetError(ValueError):
    pass


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise TrainingDatasetError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _text(value: Any, field: str, *, max_len: int = 8192) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TrainingDatasetError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise TrainingDatasetError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, max_len=64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise TrainingDatasetError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise TrainingDatasetError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _generation(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TrainingDatasetError("generation:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise TrainingDatasetError("generation:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _poison_sha(value: str) -> str:
    value = _sha256(value, "poison_source_sha256")
    replacement = "1" if value[0] == "0" else "0"
    poisoned = replacement + value[1:]
    if poisoned == value:
        raise TrainingDatasetError("POISON_SHA_IDENTITY_FAILURE")
    return poisoned


def _row(
    kind: str,
    user: dict[str, Any],
    assistant: dict[str, Any],
    *,
    trace_sha256: str,
    trace_family_id: str,
) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": _canonical_json({"task": kind, **user})},
            {"role": "assistant", "content": _canonical_json(assistant)},
        ],
        "metadata": {
            "dataset_schema": DATASET_SCHEMA,
            "trace_schema": TRAINING_TRACE_SCHEMA,
            "trace_canonicalization_schema": CANONICALIZATION_SCHEMA,
            "family_split_schema": FAMILY_SPLIT_SCHEMA,
            "trace_sha256": trace_sha256,
            "trace_family_id": trace_family_id,
            "family": kind,
        },
    }


def _validate_trace(trace: dict[str, Any]) -> tuple[str, str]:
    if not isinstance(trace, dict) or trace.get("schema_version") != TRAINING_TRACE_SCHEMA:
        raise TrainingDatasetError("TRACE_SCHEMA_UNSUPPORTED")
    if trace.get("canonicalization_schema") != CANONICALIZATION_SCHEMA:
        raise TrainingDatasetError("TRACE_CANONICALIZATION_SCHEMA_MISMATCH")

    required = (
        "trace_id",
        "trace_family_id",
        "generation",
        "entry_event_sha256",
        "entry_admission_sha256",
        "route_decision_sha256",
        "grid_plan_sha256",
        "cell_id",
        "role",
        "jspace_basis_id",
        "jspace_basis_sha256",
        "jspace_input_vector_ref",
        "jspace_input_codec_version",
        "vector_control_packet_sha256",
        "vector_control_packet_jcs_utf8",
        "vector_control_condition",
        "local_workspace_state_ref",
        "gwt_competition_set",
        "gwt_broadcast_gate",
        "global_jspace_slice_ref",
        "hyperposition_branch_ids",
        "provenance_evidence_class",
        "resource_budget",
        "requested_action_class",
        "expected_structured_model_output",
        "observed_downstream_outcome",
        "outcome_receipt_sha256",
        "falsifier_lesion_condition",
        "credit_label",
        "prototype_trace_sha256",
        "trace_sha256",
    )
    for key in required:
        if key not in trace:
            raise TrainingDatasetError(f"TRACE_FIELD_MISSING:{key}")

    trace_id = _text(trace["trace_id"], "trace_id", max_len=256)
    family = _text(trace["trace_family_id"], "trace_family_id", max_len=256)
    generation = _generation(trace["generation"])
    role = _text(trace["role"], "role", max_len=256)
    cell_id = _text(trace["cell_id"], "cell_id", max_len=256)
    basis_id = _text(trace["jspace_basis_id"], "jspace_basis_id", max_len=256)
    basis_sha = _sha256(trace["jspace_basis_sha256"], "jspace_basis_sha256")

    for field in (
        "entry_event_sha256",
        "entry_admission_sha256",
        "route_decision_sha256",
        "grid_plan_sha256",
        "prototype_trace_sha256",
        "vector_control_packet_sha256",
    ):
        _sha256(trace[field], field)

    observed_trace_sha = _sha256(trace["trace_sha256"], "trace_sha256")
    material = dict(trace)
    material.pop("trace_sha256", None)
    expected_trace_sha = _canonical_sha256(material, "TRAINING_TRACE")
    if observed_trace_sha != expected_trace_sha:
        raise TrainingDatasetError("TRAINING_TRACE_DIGEST_MISMATCH")

    if trace["jspace_input_codec_version"] != ABI_SCHEMA:
        raise TrainingDatasetError("TRACE_VECTOR_CONTROL_ABI_MISMATCH")
    try:
        packet = parse_packet_text(trace["vector_control_packet_jcs_utf8"])
    except JSpaceVectorControlError as exc:
        raise TrainingDatasetError(f"TRACE_VECTOR_CONTROL_PACKET_INVALID:{exc}") from exc
    if packet.packet_sha256 != trace["vector_control_packet_sha256"]:
        raise TrainingDatasetError("TRACE_VECTOR_CONTROL_PACKET_IDENTITY_MISMATCH")
    if packet.generation != generation:
        raise TrainingDatasetError("TRACE_VECTOR_CONTROL_GENERATION_MISMATCH")
    if packet.basis_id != basis_id:
        raise TrainingDatasetError("TRACE_VECTOR_CONTROL_BASIS_ID_MISMATCH")
    if packet.basis_sha256 != basis_sha:
        raise TrainingDatasetError("TRACE_VECTOR_CONTROL_BASIS_SHA256_MISMATCH")
    if packet.role != role:
        raise TrainingDatasetError("TRACE_VECTOR_CONTROL_ROLE_MISMATCH")
    if packet.control_condition != trace["vector_control_condition"]:
        raise TrainingDatasetError("TRACE_VECTOR_CONTROL_CONDITION_MISMATCH")

    gate = trace["gwt_broadcast_gate"]
    if isinstance(gate, bool) or not isinstance(gate, int) or not 0 <= gate <= 10000:
        raise TrainingDatasetError("TRACE_GWT_BROADCAST_GATE_INVALID")
    competition = trace["gwt_competition_set"]
    if not isinstance(competition, list) or not competition:
        raise TrainingDatasetError("TRACE_GWT_COMPETITION_REQUIRED")
    seen_cells: set[str] = set()
    winners: list[dict[str, Any]] = []
    for item in competition:
        if not isinstance(item, dict):
            raise TrainingDatasetError("TRACE_GWT_COMPETITION_ITEM_INVALID")
        item_cell = _text(item.get("cell_id"), "competition.cell_id", max_len=256)
        item_role = _text(item.get("role"), "competition.role", max_len=256)
        item_gate = item.get("gate_q")
        if isinstance(item_gate, bool) or not isinstance(item_gate, int) or not 0 <= item_gate <= 10000:
            raise TrainingDatasetError("TRACE_GWT_COMPETITION_GATE_INVALID")
        if item_cell in seen_cells:
            raise TrainingDatasetError("TRACE_GWT_COMPETITION_DUPLICATE_CELL")
        seen_cells.add(item_cell)
        if item_cell == cell_id:
            winners.append({"role": item_role, "gate_q": item_gate})
    if len(winners) != 1 or winners[0]["role"] != role or winners[0]["gate_q"] != gate:
        raise TrainingDatasetError("TRACE_GWT_WINNER_BINDING_MISMATCH")

    branches = trace["hyperposition_branch_ids"]
    if not isinstance(branches, list) or any(not isinstance(value, str) or not value for value in branches):
        raise TrainingDatasetError("TRACE_HYPERPOSITION_BRANCHES_INVALID")
    if len(branches) != len(set(branches)):
        raise TrainingDatasetError("TRACE_HYPERPOSITION_BRANCH_DUPLICATE")

    budget = trace["resource_budget"]
    if not isinstance(budget, dict) or not budget:
        raise TrainingDatasetError("TRACE_RESOURCE_BUDGET_INVALID")
    for key, amount in budget.items():
        _text(key, "resource_budget.key", max_len=128)
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            raise TrainingDatasetError("TRACE_RESOURCE_BUDGET_AMOUNT_INVALID")

    credit = _text(trace["credit_label"], "credit_label", max_len=32).upper()
    if credit not in CREDIT_LABELS:
        raise TrainingDatasetError("TRACE_CREDIT_LABEL_UNSUPPORTED")
    outcome = trace["outcome_receipt_sha256"]
    if outcome is not None:
        _sha256(outcome, "outcome_receipt_sha256")
    if credit != "UNKNOWN" and outcome is None:
        raise TrainingDatasetError("TRACE_NONUNKNOWN_CREDIT_REQUIRES_OUTCOME_RECEIPT")
    if credit != "UNKNOWN" and trace["provenance_evidence_class"] != "EXACT_PROTOTYPE_TRACE_WITH_VERIFIED_OUTCOME":
        raise TrainingDatasetError("TRACE_NONUNKNOWN_CREDIT_REQUIRES_VERIFIED_OUTCOME_PROVENANCE")

    for field in (
        "jspace_input_vector_ref",
        "local_workspace_state_ref",
        "global_jspace_slice_ref",
        "provenance_evidence_class",
        "requested_action_class",
        "expected_structured_model_output",
        "observed_downstream_outcome",
        "falsifier_lesion_condition",
    ):
        _text(trace[field], field)

    _text(trace_id, "trace_id", max_len=256)
    return observed_trace_sha, family


def derive_training_examples(trace: dict[str, Any]) -> list[dict[str, Any]]:
    trace_sha, family = _validate_trace(trace)
    common = {
        "control_packet": trace["vector_control_packet_jcs_utf8"],
        "expected_generation": trace["generation"],
        "expected_basis_id": trace["jspace_basis_id"],
        "expected_basis_sha256": trace["jspace_basis_sha256"],
        "expected_role": trace["role"],
        "expected_control_condition": trace["vector_control_condition"],
    }
    accept = {
        "decision": "ACCEPT_CONTROL",
        "cell_id": trace["cell_id"],
        "role": trace["role"],
        "authority": "CANDIDATE_CONTROL_ONLY",
    }
    rows = [
        _row("VECTOR_CONTROL_VALIDATE", common, accept, trace_sha256=trace_sha, trace_family_id=family),
        _row(
            "VECTOR_CONTROL_VALIDATE",
            {**common, "expected_generation": trace["generation"] + 1},
            {"decision": "REJECT", "reason": "STALE_VECTOR_CONTROL_GENERATION"},
            trace_sha256=trace_sha,
            trace_family_id=family,
        ),
        _row(
            "VECTOR_CONTROL_VALIDATE",
            {**common, "expected_basis_sha256": _poison_sha(trace["jspace_basis_sha256"])},
            {"decision": "REJECT", "reason": "JSPACE_BASIS_SHA256_MISMATCH"},
            trace_sha256=trace_sha,
            trace_family_id=family,
        ),
        _row(
            "VECTOR_CONTROL_VALIDATE",
            {**common, "expected_role": trace["role"] + "#SWAP"},
            {"decision": "REJECT", "reason": "JSPACE_ROLE_MISMATCH"},
            trace_sha256=trace_sha,
            trace_family_id=family,
        ),
    ]

    causal = {
        "entry_event_sha256": trace["entry_event_sha256"],
        "entry_admission_sha256": trace["entry_admission_sha256"],
        "route_decision_sha256": trace["route_decision_sha256"],
        "grid_plan_sha256": trace["grid_plan_sha256"],
    }
    rows.append(
        _row(
            "GWT_BROADCAST_FROM_CAUSAL_TRACE",
            {
                "generation": trace["generation"],
                "causal_binding": causal,
                "competition": trace["gwt_competition_set"],
                "hyperposition_branch_ids": trace["hyperposition_branch_ids"],
                "resource_budget": trace["resource_budget"],
            },
            {
                "decision": "GWT_BROADCAST",
                "cell_id": trace["cell_id"],
                "role": trace["role"],
                "gwt_broadcast_gate": trace["gwt_broadcast_gate"],
                "control_packet": trace["vector_control_packet_jcs_utf8"],
                "authority": "CANDIDATE_CONTROL_ONLY",
            },
            trace_sha256=trace_sha,
            trace_family_id=family,
        )
    )
    rows.append(
        _row(
            "CAUSAL_TRACE_BINDING_VALIDATE",
            {"observed": causal, "expected": causal},
            {"decision": "ACCEPT_CAUSAL_BINDING"},
            trace_sha256=trace_sha,
            trace_family_id=family,
        )
    )
    rows.append(
        _row(
            "CAUSAL_TRACE_BINDING_VALIDATE",
            {"observed": {**causal, "entry_event_sha256": _poison_sha(causal["entry_event_sha256"])}, "expected": causal},
            {"decision": "REJECT", "reason": "ENTRY_EVENT_MISMATCH"},
            trace_sha256=trace_sha,
            trace_family_id=family,
        )
    )
    rows.append(
        _row(
            "CAUSAL_TRACE_BINDING_VALIDATE",
            {"observed": {**causal, "route_decision_sha256": _poison_sha(causal["route_decision_sha256"])}, "expected": causal},
            {"decision": "REJECT", "reason": "ROUTE_DECISION_MISMATCH"},
            trace_sha256=trace_sha,
            trace_family_id=family,
        )
    )
    return rows


def compile_traces(traces: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out = {"train": [], "validation": [], "holdout": []}
    seen_trace_sha: set[str] = set()
    for trace in traces:
        trace_sha, family = _validate_trace(trace)
        if trace_sha in seen_trace_sha:
            continue
        seen_trace_sha.add(trace_sha)
        out[split_for_family(family)].extend(derive_training_examples(trace))
    if not seen_trace_sha:
        raise TrainingDatasetError("NO_TRAINING_TRACES")
    return out


def compile_jsonl(input_path: Path, output_dir: Path) -> dict[str, Any]:
    if not isinstance(input_path, Path) or not isinstance(output_dir, Path):
        raise TrainingDatasetError("PATH_TYPE_REQUIRED")
    traces: list[dict[str, Any]] = []
    for lineno, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TrainingDatasetError(f"JSONL_INVALID_LINE:{lineno}") from exc
        traces.append(value)

    compiled = compile_traces(traces)
    output_dir.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": DATASET_SCHEMA,
        "trace_schema": TRAINING_TRACE_SCHEMA,
        "trace_canonicalization_schema": CANONICALIZATION_SCHEMA,
        "input_trace_count": len(traces),
        "split_policy": FAMILY_SPLIT_SCHEMA,
        "splits": {},
    }
    for split, rows in compiled.items():
        path = output_dir / f"{split}.jsonl"
        payload = "".join(_canonical_json(row) + "\n" for row in rows)
        path.write_text(payload, encoding="ascii")
        receipt["splits"][split] = {
            "row_count": len(rows),
            "trace_family_count": len({row["metadata"]["trace_family_id"] for row in rows}),
            "sha256": hashlib.sha256(payload.encode("ascii")).hexdigest(),
            "path": path.name,
        }

    receipt_path = output_dir / "dataset_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt
