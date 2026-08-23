from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .jspace_dataset_family_split_v1 import (
        CAUSAL_FAMILY_SCHEMA,
        SPLIT_SCHEMA as FAMILY_SPLIT_SCHEMA,
        causal_family_id_from_event,
        split_for_family,
    )
    from .jspace_training_trace_v1 import TRACE_SCHEMA
    from .jspace_vector_control_v1 import ABI_SCHEMA, JSpaceVectorControlError, decode_vector, parse_packet_text
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from jspace_dataset_family_split_v1 import (
        CAUSAL_FAMILY_SCHEMA,
        SPLIT_SCHEMA as FAMILY_SPLIT_SCHEMA,
        causal_family_id_from_event,
        split_for_family,
    )
    from jspace_training_trace_v1 import TRACE_SCHEMA
    from jspace_vector_control_v1 import ABI_SCHEMA, JSpaceVectorControlError, decode_vector, parse_packet_text

DATASET_SCHEMA = "ENTITYOS_HCU_JSPACE_BOOTSTRAP_DATASET/v5"
SYSTEM = (
    "You are a narrow EntityOS/HCU cognitive coprocessor. "
    "Follow JSPACE_VECTOR_CONTROL_ABI/v1, GWT/Hyperposition, generation/basis/role fences, "
    "and output only the requested compact JSON decision. "
    "A basis is usable only when its id+digest is externally admitted; trace self-claims cannot grant basis authority. "
    "Model output is candidate/control behavior, never truth or EffectGate authority."
)


class DatasetError(ValueError):
    pass


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise DatasetError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _trace_material(trace: dict[str, Any]) -> dict[str, Any]:
    material = dict(trace)
    material.pop("trace_sha256", None)
    return material


def _row(
    kind: str,
    user: dict[str, Any],
    assistant: dict[str, Any],
    *,
    trace_sha256: str,
    trace_family_id: str,
    causal_family_id: str,
) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": _canonical_json({"task": kind, **user})},
            {"role": "assistant", "content": _canonical_json(assistant)},
        ],
        "metadata": {
            "dataset_schema": DATASET_SCHEMA,
            "trace_schema": TRACE_SCHEMA,
            "trace_canonicalization_schema": CANONICALIZATION_SCHEMA,
            "family_split_schema": FAMILY_SPLIT_SCHEMA,
            "causal_family_schema": CAUSAL_FAMILY_SCHEMA,
            "trace_sha256": trace_sha256,
            "trace_family_id": trace_family_id,
            "causal_family_id": causal_family_id,
            "family": kind,
        },
    }


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise DatasetError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _normalize_admitted_bases(value: Mapping[str, str] | None) -> dict[str, str]:
    """Normalize the deterministic external basis registry used by the dataset boundary.

    The registry is caller/control-plane authority. A trace or control packet may reference a
    basis, but neither may add to or broaden this registry.
    """
    if not isinstance(value, Mapping) or not value:
        raise DatasetError("JSPACE_BASIS_ADMISSION_REQUIRED")
    normalized: dict[str, str] = {}
    for basis_id, basis_sha256 in value.items():
        if not isinstance(basis_id, str) or not basis_id.strip():
            raise DatasetError("ADMITTED_JSPACE_BASIS_ID_INVALID")
        basis_id = basis_id.strip()
        if basis_id in normalized:
            raise DatasetError("ADMITTED_JSPACE_BASIS_ID_DUPLICATE")
        normalized[basis_id] = _sha256(basis_sha256, "ADMITTED_JSPACE_BASIS_SHA256")
    return normalized


def _require_admitted_basis(*, basis_id: str, basis_sha256: str, admitted_bases: Mapping[str, str] | None) -> dict[str, str]:
    normalized = _normalize_admitted_bases(admitted_bases)
    expected = normalized.get(basis_id)
    if expected is None:
        raise DatasetError("JSPACE_BASIS_NOT_ADMITTED")
    if expected != basis_sha256:
        raise DatasetError("JSPACE_BASIS_ADMISSION_DIGEST_MISMATCH")
    return normalized


def _validate_trace(
    trace: dict[str, Any],
    *,
    admitted_bases: Mapping[str, str] | None = None,
) -> tuple[str, str, str]:
    if not isinstance(trace, dict) or trace.get("schema_version") != TRACE_SCHEMA:
        raise DatasetError("TRACE_SCHEMA_UNSUPPORTED")
    if trace.get("canonicalization_schema") != CANONICALIZATION_SCHEMA:
        raise DatasetError("TRACE_CANONICALIZATION_SCHEMA_MISMATCH")

    required = (
        "trace_id", "trace_family_id", "generation", "entry_event_sha256", "entry_admission_sha256",
        "route_decision_sha256", "grid_plan_sha256", "cell_id", "role", "jspace_basis_id",
        "jspace_basis_sha256", "jspace_input_vector_ref", "jspace_input_codec_version",
        "vector_control_packet_sha256", "vector_control_packet_jcs_utf8", "vector_control_condition",
        "local_workspace_state_ref", "gwt_competition_set", "gwt_broadcast_gate",
        "global_jspace_slice_ref", "hyperposition_branch_ids", "provenance_evidence_class",
        "resource_budget", "requested_action_class", "expected_structured_model_output",
        "observed_downstream_outcome", "outcome_receipt_sha256", "falsifier_lesion_condition",
        "credit_label", "prototype_trace_sha256", "trace_sha256",
    )
    for key in required:
        if key not in trace:
            raise DatasetError(f"TRACE_FIELD_MISSING:{key}")

    generation = trace["generation"]
    if isinstance(generation, bool) or not isinstance(generation, int) or not 0 <= generation <= 9_007_199_254_740_991:
        raise DatasetError("TRACE_GENERATION_INVALID")

    for key in (
        "trace_id", "trace_family_id", "cell_id", "role", "jspace_basis_id", "jspace_input_vector_ref",
        "vector_control_condition", "local_workspace_state_ref", "global_jspace_slice_ref",
        "provenance_evidence_class", "requested_action_class", "expected_structured_model_output",
        "observed_downstream_outcome", "falsifier_lesion_condition", "credit_label",
    ):
        if not isinstance(trace[key], str) or not trace[key].strip():
            raise DatasetError(f"TRACE_TEXT_INVALID:{key}")

    for key in (
        "entry_event_sha256", "entry_admission_sha256", "route_decision_sha256", "grid_plan_sha256",
        "jspace_basis_sha256", "vector_control_packet_sha256", "prototype_trace_sha256", "trace_sha256",
    ):
        _sha256(trace[key], key)

    _require_admitted_basis(
        basis_id=trace["jspace_basis_id"],
        basis_sha256=trace["jspace_basis_sha256"],
        admitted_bases=admitted_bases,
    )

    trace_sha256 = trace["trace_sha256"]
    if trace_sha256 != _canonical_sha256(_trace_material(trace), "TRAINING_TRACE"):
        raise DatasetError("TRAINING_TRACE_DIGEST_MISMATCH")
    if trace["jspace_input_codec_version"] != ABI_SCHEMA:
        raise DatasetError("TRACE_VECTOR_CONTROL_ABI_MISMATCH")

    try:
        packet = parse_packet_text(trace["vector_control_packet_jcs_utf8"])
        decode_vector(
            packet,
            current_generation=generation,
            expected_basis_id=trace["jspace_basis_id"],
            expected_basis_sha256=trace["jspace_basis_sha256"],
            expected_role=trace["role"],
            expected_control_condition=trace["vector_control_condition"],
        )
    except JSpaceVectorControlError as exc:
        raise DatasetError(f"TRACE_CONTROL_PACKET_INVALID:{exc}") from exc
    if packet.packet_sha256 != trace["vector_control_packet_sha256"]:
        raise DatasetError("TRACE_CONTROL_PACKET_IDENTITY_MISMATCH")

    competition = trace["gwt_competition_set"]
    if not isinstance(competition, list) or not competition:
        raise DatasetError("TRACE_GWT_COMPETITION_REQUIRED")
    ids: list[str] = []
    winners: list[dict[str, Any]] = []
    for row in competition:
        if not isinstance(row, dict) or set(row) != {"cell_id", "role", "gate_q"}:
            raise DatasetError("TRACE_GWT_COMPETITION_ROW_SCHEMA_MISMATCH")
        cell_id, role, gate_q = row["cell_id"], row["role"], row["gate_q"]
        if not isinstance(cell_id, str) or not cell_id or not isinstance(role, str) or not role:
            raise DatasetError("TRACE_GWT_COMPETITION_IDENTITY_INVALID")
        if isinstance(gate_q, bool) or not isinstance(gate_q, int) or not 0 <= gate_q <= 10000:
            raise DatasetError("TRACE_GWT_GATE_INVALID")
        ids.append(cell_id)
        if cell_id == trace["cell_id"]:
            winners.append(row)
    if len(ids) != len(set(ids)):
        raise DatasetError("TRACE_GWT_CELL_ID_DUPLICATE")
    if len(winners) != 1 or winners[0]["role"] != trace["role"] or winners[0]["gate_q"] != trace["gwt_broadcast_gate"]:
        raise DatasetError("TRACE_GWT_WINNER_BINDING_MISMATCH")

    branches = trace["hyperposition_branch_ids"]
    if not isinstance(branches, list) or any(not isinstance(branch, str) or not branch for branch in branches) or len(branches) != len(set(branches)):
        raise DatasetError("TRACE_HYPERPOSITION_INVALID")

    budget = trace["resource_budget"]
    if not isinstance(budget, dict) or not budget:
        raise DatasetError("TRACE_RESOURCE_BUDGET_INVALID")
    if any(not isinstance(k, str) or not k or isinstance(v, bool) or not isinstance(v, int) or v < 0 for k, v in budget.items()):
        raise DatasetError("TRACE_RESOURCE_BUDGET_INVALID")

    credit = trace["credit_label"]
    receipt = trace["outcome_receipt_sha256"]
    if credit != "UNKNOWN":
        if receipt is None:
            raise DatasetError("NONUNKNOWN_CREDIT_REQUIRES_OUTCOME_RECEIPT")
        _sha256(receipt, "outcome_receipt_sha256")
        if trace["provenance_evidence_class"] != "EXACT_PROTOTYPE_TRACE_WITH_VERIFIED_OUTCOME":
            raise DatasetError("NONUNKNOWN_CREDIT_REQUIRES_VERIFIED_OUTCOME_PROVENANCE")
    elif receipt is not None:
        _sha256(receipt, "outcome_receipt_sha256")

    supplied_family_id = trace["trace_family_id"].strip()
    causal_family_id = causal_family_id_from_event(trace["entry_event_sha256"])
    return trace_sha256, supplied_family_id, causal_family_id


def derive_bootstrap_examples(
    trace: dict[str, Any],
    *,
    admitted_bases: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    trace_sha256, trace_family_id, causal_family_id = _validate_trace(
        trace,
        admitted_bases=admitted_bases,
    )
    common = {
        "control_packet": trace["vector_control_packet_jcs_utf8"],
        "expected_basis_id": trace["jspace_basis_id"],
        "expected_basis_sha256": trace["jspace_basis_sha256"],
        "expected_role": trace["role"],
        "expected_generation": trace["generation"],
        "expected_control_condition": trace["vector_control_condition"],
    }
    accept = {
        "decision": "ACCEPT_CONTROL",
        "cell_id": trace["cell_id"],
        "role": trace["role"],
        "gwt_broadcast_gate": trace["gwt_broadcast_gate"],
        "hyperposition_branch_ids": trace["hyperposition_branch_ids"],
        "authority": "CANDIDATE_CONTROL_ONLY",
    }

    def row(kind: str, user: dict[str, Any], assistant: dict[str, Any]) -> dict[str, Any]:
        return _row(
            kind,
            user,
            assistant,
            trace_sha256=trace_sha256,
            trace_family_id=trace_family_id,
            causal_family_id=causal_family_id,
        )

    wrong_basis_sha = "0" * 63 + ("1" if trace["jspace_basis_sha256"] != "0" * 63 + "1" else "2")
    return [
        row("VECTOR_CONTROL_VALIDATE", common, accept),
        row("VECTOR_CONTROL_VALIDATE", {**common, "expected_generation": trace["generation"] + 1}, {"decision": "REJECT", "reason": "STALE_VECTOR_CONTROL_GENERATION"}),
        row("VECTOR_CONTROL_VALIDATE", {**common, "expected_basis_id": trace["jspace_basis_id"] + "#WRONG"}, {"decision": "REJECT", "reason": "JSPACE_BASIS_ID_MISMATCH"}),
        row("VECTOR_CONTROL_VALIDATE", {**common, "expected_basis_sha256": wrong_basis_sha}, {"decision": "REJECT", "reason": "JSPACE_BASIS_SHA256_MISMATCH"}),
        row("VECTOR_CONTROL_VALIDATE", {**common, "expected_role": trace["role"] + "#SWAPPED"}, {"decision": "REJECT", "reason": "JSPACE_ROLE_MISMATCH"}),
        row(
            "GWT_BROADCAST_FROM_TRAINING_TRACE",
            {
                "generation": trace["generation"], "basis_id": trace["jspace_basis_id"],
                "basis_sha256": trace["jspace_basis_sha256"], "competition_set": trace["gwt_competition_set"],
                "resource_budget": trace["resource_budget"], "requested_action_class": trace["requested_action_class"],
            },
            {
                "decision": "GWT_BROADCAST", "cell_id": trace["cell_id"], "role": trace["role"],
                "gwt_broadcast_gate": trace["gwt_broadcast_gate"], "hyperposition_branch_ids": trace["hyperposition_branch_ids"],
                "control_packet": trace["vector_control_packet_jcs_utf8"], "authority": "CANDIDATE_CONTROL_ONLY",
            },
        ),
    ]


def compile_traces(
    traces: Iterable[dict[str, Any]],
    *,
    admitted_bases: Mapping[str, str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    normalized_bases = _normalize_admitted_bases(admitted_bases)
    out = {"train": [], "validation": [], "holdout": []}
    seen: set[str] = set()
    family_owner: dict[str, str] = {}
    for trace in traces:
        trace_sha256, _, causal_family_id = _validate_trace(
            trace,
            admitted_bases=normalized_bases,
        )
        if trace_sha256 in seen:
            continue
        seen.add(trace_sha256)
        split = split_for_family(causal_family_id)
        previous = family_owner.setdefault(causal_family_id, split)
        if previous != split:
            raise DatasetError("CAUSAL_FAMILY_SPLIT_INCONSISTENT")
        out[split].extend(derive_bootstrap_examples(trace, admitted_bases=normalized_bases))
    if not seen:
        raise DatasetError("NO_TRACES")
    return out


def compile_jsonl(
    input_path: Path,
    output_dir: Path,
    *,
    admitted_bases: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    if not isinstance(input_path, Path) or not isinstance(output_dir, Path):
        raise DatasetError("PATH_TYPE_REQUIRED")
    normalized_bases = _normalize_admitted_bases(admitted_bases)
    traces = []
    for lineno, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            traces.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise DatasetError(f"JSONL_INVALID_LINE:{lineno}") from exc

    compiled = compile_traces(traces, admitted_bases=normalized_bases)
    output_dir.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": DATASET_SCHEMA,
        "trace_schema": TRACE_SCHEMA,
        "trace_canonicalization_schema": CANONICALIZATION_SCHEMA,
        "split_unit": "replay_stable_entry_event_identity",
        "causal_family_schema": CAUSAL_FAMILY_SCHEMA,
        "family_split_schema": FAMILY_SPLIT_SCHEMA,
        "admitted_basis_registry_sha256": _canonical_sha256(normalized_bases, "ADMITTED_JSPACE_BASIS_REGISTRY"),
        "input_trace_count": len(traces),
        "splits": {},
    }
    for split, rows in compiled.items():
        path = output_dir / f"{split}.jsonl"
        payload = "".join(_canonical_json(row) + "\n" for row in rows)
        path.write_text(payload, encoding="ascii")
        receipt["splits"][split] = {
            "row_count": len(rows),
            "causal_family_count": len({row["metadata"]["causal_family_id"] for row in rows}),
            "supplied_trace_family_label_count": len({row["metadata"]["trace_family_id"] for row in rows}),
            "sha256": hashlib.sha256(payload.encode("ascii")).hexdigest(),
            "path": path.name,
        }
    (output_dir / "dataset_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt