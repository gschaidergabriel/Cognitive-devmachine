from __future__ import annotations

"""Leak-resistant family splitter for admitted EntityOS/HCU J-Space training traces.

This module is dataset plumbing only. It mints no truth, reward, model authority, effect
capability, or runtime credit. Its sole job is to keep correlated traces from the same
explicit ``trace_family_id`` together when forming train/validation/holdout partitions.

Inputs are expected to have already passed ``jspace_dataset_admission_gate_v1``. The exact
training-trace object is nevertheless re-bound to the admitted-training-trace registry here
so a caller cannot relabel ``trace_family_id`` after admission and silently move a correlated
trace into another split. The accepted admission schema is imported from the selected
admission gate, and v2 packet/control-condition bindings are rechecked rather than copied as
an independent schema authority.
"""

import hashlib
import unicodedata
from typing import Any, Iterable, Mapping

try:
    from .jspace_dataset_admission_gate_v1 import ADMISSION_SCHEMA as DATASET_ADMISSION_SCHEMA
except ImportError:
    from jspace_dataset_admission_gate_v1 import ADMISSION_SCHEMA as DATASET_ADMISSION_SCHEMA

SPLIT_SCHEMA = "ENTITYOS_HCU_JSPACE_DATASET_FAMILY_SPLIT/v1"
TRAINING_TRACE_SCHEMA = "ENTITYOS_HCU_JSPACE_TRAINING_TRACE/v1"
SPLIT_NAMES = ("train", "validation", "holdout")


class JSpaceDatasetFamilySplitError(ValueError):
    pass


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise JSpaceDatasetFamilySplitError(f"{field}:MAPPING_REQUIRED")
    return value


def _text(value: Any, field: str, *, max_len: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JSpaceDatasetFamilySplitError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value.encode("utf-8", "strict")) > max_len:
        raise JSpaceDatasetFamilySplitError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, max_len=64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise JSpaceDatasetFamilySplitError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise JSpaceDatasetFamilySplitError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _generation(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JSpaceDatasetFamilySplitError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise JSpaceDatasetFamilySplitError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def split_for_family(trace_family_id: str) -> str:
    """Return a deterministic ~80/10/10 split from one explicit family identity.

    Domain-separated UTF-8 hashing is only partition plumbing. It is deliberately not reused
    as EntityOS causal/state identity and therefore creates no competing canonicalizer.

    JCS preserves Unicode strings as-is, so this boundary must not silently normalize a
    family identifier after the training trace has already been hashed/admitted. Non-NFC
    family identifiers therefore fail closed before partition hashing. This prevents two
    canonically equivalent spellings from becoming distinct split keys without rewriting
    any existing trace identity.
    """
    family = _text(trace_family_id, "trace_family_id")
    if unicodedata.normalize("NFC", family) != family:
        raise JSpaceDatasetFamilySplitError("trace_family_id:NFC_REQUIRED")
    digest = hashlib.sha256((SPLIT_SCHEMA + "\0" + family).encode("utf-8", "strict")).digest()
    bucket = digest[0]
    if bucket < 205:
        return "train"
    if bucket < 230:
        return "validation"
    return "holdout"


def _exact_registry_trace(
    training_trace: Mapping[str, Any],
    admitted_training_traces: Mapping[str, Mapping[str, Any]],
) -> str:
    trace_sha = _sha256(training_trace.get("trace_sha256"), "training_trace.trace_sha256")
    registry = _mapping(admitted_training_traces, "admitted_training_traces")
    admitted = registry.get(trace_sha)
    if not isinstance(admitted, Mapping):
        raise JSpaceDatasetFamilySplitError("TRAINING_TRACE_NOT_ADMITTED")
    if dict(admitted) != dict(training_trace):
        raise JSpaceDatasetFamilySplitError("TRAINING_TRACE_REGISTRY_MISMATCH")
    return trace_sha


def _bind_admission(training_trace: Mapping[str, Any], admission: Mapping[str, Any]) -> tuple[str, str, str]:
    if training_trace.get("schema_version") != TRAINING_TRACE_SCHEMA:
        raise JSpaceDatasetFamilySplitError("TRAINING_TRACE_SCHEMA_UNSUPPORTED")
    if admission.get("schema") != DATASET_ADMISSION_SCHEMA:
        raise JSpaceDatasetFamilySplitError("DATASET_ADMISSION_SCHEMA_UNSUPPORTED")

    trace_sha = _sha256(training_trace.get("trace_sha256"), "training_trace.trace_sha256")
    admitted_sha = _sha256(admission.get("training_trace_sha256"), "admission.training_trace_sha256")
    if trace_sha != admitted_sha:
        raise JSpaceDatasetFamilySplitError("TRAINING_TRACE_ADMISSION_SHA_MISMATCH")

    for field in (
        "entry_event_sha256",
        "entry_admission_sha256",
        "route_decision_sha256",
        "grid_plan_sha256",
        "jspace_basis_sha256",
        "vector_control_packet_sha256",
    ):
        left = _sha256(training_trace.get(field), f"training_trace.{field}")
        right = _sha256(admission.get(field), f"admission.{field}")
        if left != right:
            raise JSpaceDatasetFamilySplitError(f"TRAINING_TRACE_ADMISSION_BINDING_MISMATCH:{field}")

    generation = _generation(training_trace.get("generation"), "training_trace.generation")
    if generation != _generation(admission.get("generation"), "admission.generation"):
        raise JSpaceDatasetFamilySplitError("TRAINING_TRACE_ADMISSION_BINDING_MISMATCH:generation")

    for field in ("cell_id", "role", "jspace_basis_id", "vector_control_condition"):
        left = _text(training_trace.get(field), f"training_trace.{field}")
        right = _text(admission.get(field), f"admission.{field}")
        if left != right:
            raise JSpaceDatasetFamilySplitError(f"TRAINING_TRACE_ADMISSION_BINDING_MISMATCH:{field}")

    credit = _text(training_trace.get("credit_label"), "training_trace.credit_label", max_len=32).upper()
    admitted_credit = _text(admission.get("credit_label"), "admission.credit_label", max_len=32).upper()
    if credit != admitted_credit:
        raise JSpaceDatasetFamilySplitError("TRAINING_TRACE_ADMISSION_BINDING_MISMATCH:credit_label")

    outcome = training_trace.get("outcome_receipt_sha256")
    admitted_outcome = admission.get("outcome_receipt_sha256")
    if outcome is None:
        if admitted_outcome is not None:
            raise JSpaceDatasetFamilySplitError("TRAINING_TRACE_ADMISSION_BINDING_MISMATCH:outcome_receipt_sha256")
    else:
        if _sha256(outcome, "training_trace.outcome_receipt_sha256") != _sha256(
            admitted_outcome,
            "admission.outcome_receipt_sha256",
        ):
            raise JSpaceDatasetFamilySplitError("TRAINING_TRACE_ADMISSION_BINDING_MISMATCH:outcome_receipt_sha256")

    trace_id = _text(training_trace.get("trace_id"), "training_trace.trace_id")
    family_id = _text(training_trace.get("trace_family_id"), "training_trace.trace_family_id")
    return trace_sha, trace_id, family_id


def partition_admitted_training_traces(
    records: Iterable[tuple[Mapping[str, Any], Mapping[str, Any]]],
    *,
    admitted_training_traces: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Partition exact admitted traces without allowing family leakage across splits.

    Each record is ``(training_trace, dataset_admission)``. Duplicate identical traces are
    idempotent. Reusing a ``trace_id`` for different trace identities fails closed.
    """
    partitions: dict[str, list[dict[str, Any]]] = {name: [] for name in SPLIT_NAMES}
    families: dict[str, str] = {}
    seen_sha: set[str] = set()
    trace_ids: dict[str, str] = {}

    for ordinal, pair in enumerate(records):
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise JSpaceDatasetFamilySplitError(f"records[{ordinal}]:TRACE_ADMISSION_PAIR_REQUIRED")
        training_trace = _mapping(pair[0], f"records[{ordinal}].training_trace")
        admission = _mapping(pair[1], f"records[{ordinal}].admission")

        registry_sha = _exact_registry_trace(training_trace, admitted_training_traces)
        trace_sha, trace_id, family_id = _bind_admission(training_trace, admission)
        if registry_sha != trace_sha:
            raise JSpaceDatasetFamilySplitError("INTERNAL_TRACE_SHA_BINDING_MISMATCH")

        prior_sha = trace_ids.get(trace_id)
        if prior_sha is not None and prior_sha != trace_sha:
            raise JSpaceDatasetFamilySplitError("TRACE_ID_COLLISION")
        trace_ids[trace_id] = trace_sha
        if trace_sha in seen_sha:
            continue
        seen_sha.add(trace_sha)

        split = split_for_family(family_id)
        prior_split = families.get(family_id)
        if prior_split is not None and prior_split != split:
            raise JSpaceDatasetFamilySplitError("FAMILY_SPLIT_DIVERGENCE")
        families[family_id] = split
        partitions[split].append(dict(training_trace))

    if not seen_sha:
        raise JSpaceDatasetFamilySplitError("NO_ADMITTED_TRAINING_TRACES")

    for rows in partitions.values():
        rows.sort(key=lambda row: (row["trace_family_id"], row["trace_id"], row["trace_sha256"]))

    family_counts = {name: sum(1 for value in families.values() if value == name) for name in SPLIT_NAMES}
    return {
        "schema": SPLIT_SCHEMA,
        "trace_count": len(seen_sha),
        "family_count": len(families),
        "family_counts": family_counts,
        "family_assignments": dict(sorted(families.items())),
        "splits": partitions,
        "authority": "DATASET_PARTITION_ONLY_NOT_TRUTH_REWARD_EFFECT_OR_RUNTIME_AUTHORITY",
    }
