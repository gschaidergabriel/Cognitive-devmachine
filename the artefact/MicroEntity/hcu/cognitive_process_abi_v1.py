#!/usr/bin/env python3
"""Fail-closed cognitive-process packet ABI for EntityOS/HCU.

Source/component scope only. This module serializes request-scoped cognitive work and
results; it cannot grant canonical truth, coordinator, security, capability or real-effect
authority. Durable data remains externally stored and content/provenance referenced.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence

HCU_DIR = Path(__file__).resolve().parent
if str(HCU_DIR) not in sys.path:
    sys.path.insert(0, str(HCU_DIR))


def _import_exact_repo_module(name: str, expected_path: Path):
    module = importlib.import_module(name)
    raw_path = getattr(module, "__file__", None)
    if not raw_path:
        raise RuntimeError(f"COGNITIVE_ABI_AUTHORITY_MODULE_PATH_MISSING:{name}")
    loaded = Path(raw_path).resolve()
    expected = expected_path.resolve()
    if loaded != expected:
        raise RuntimeError(f"COGNITIVE_ABI_AUTHORITY_MODULE_SHADOWED:{name}:{loaded}:{expected}")
    return module


_canonicalization = _import_exact_repo_module(
    "entry_canonicalization_v1", HCU_DIR / "entry_canonicalization_v1.py"
)
canonicalize = _canonicalization.canonicalize
CanonicalizationError = _canonicalization.CanonicalizationError

ABI_SCHEMA = "COGNITIVE_PROCESS_ABI/v1"
INVOCATION_SCHEMA = "COGNITIVE_PROCESS_INVOCATION/v1"
RESULT_SCHEMA = "COGNITIVE_PROCESS_RESULT/v1"
OWNER_TARGET = "VARIABLE_COGNITIVE_GRID_DB_CLAUDE_CODE_GLOBAL_JSPACE"

# Registry semantics are externally digest-bound. Both candidate census spellings are
# accepted at this transport layer so this ABI does not create a second process registry.
PROCESS_ID_RE = re.compile(r"^AZP-?[0-9]{2}$")
EXECUTION_TARGETS = frozenset(
    {"GRID_SMALL_MODEL", "CLAUDE_CODE", "DETERMINISTIC", "TOOL_ADAPTER", "NONE"}
)
STATE_REQUIREMENTS = frozenset(
    {"DB_REQUIRED", "SIMULATION_ALLOWED", "EPHEMERAL_ONLY", "MIXED"}
)
RESULT_CLASSES = frozenset(
    {
        "OBSERVATION",
        "CANDIDATE",
        "SELECTION",
        "RESULT",
        "EFFECT_REQUEST",
        "EFFECT_RECEIPT_REF",
        "MEASUREMENT",
        "UNKNOWN",
    }
)

FORBIDDEN_NESTED_KEYS = frozenset(
    {
        "canonical",
        "canonicaltruth",
        "canonicaltruthauthority",
        "truthauthority",
        "effectauthority",
        "effectgate",
        "effectjournal",
        "securityauthority",
        "coordinatorauthority",
        "capabilityauthority",
        "permission",
        "permissions",
        "credential",
        "credentials",
        "secret",
        "secrets",
        "sudo",
        "root",
    }
)


class CognitiveProcessABIError(ValueError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    try:
        return canonicalize(value)
    except CanonicalizationError as exc:
        raise CognitiveProcessABIError(f"NONCANONICAL:{exc}") from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CognitiveProcessABIError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def _sha(value: Any, field: str) -> str:
    text = _text(value, field)
    if len(text) != 64 or any(c not in "0123456789abcdef" for c in text):
        raise CognitiveProcessABIError(f"{field}:SHA256_HEX_REQUIRED")
    return text


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CognitiveProcessABIError(f"{field}:NONNEGATIVE_INT_REQUIRED")
    return value


def _unique_texts(values: Sequence[str], field: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise CognitiveProcessABIError(f"{field}:SEQUENCE_REQUIRED")
    rows = tuple(_text(v, field) for v in values)
    if len(set(rows)) != len(rows):
        raise CognitiveProcessABIError(f"{field}:DUPLICATE_FORBIDDEN")
    return rows


def _normalized_key(value: Any) -> str:
    return str(value).lower().replace("_", "").replace("-", "")


def _find_forbidden(value: Any, path: str = "$") -> str | None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _normalized_key(key) in FORBIDDEN_NESTED_KEYS:
                return f"{path}.{key}"
            nested = _find_forbidden(item, f"{path}.{key}")
            if nested:
                return nested
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested = _find_forbidden(item, f"{path}[{index}]")
            if nested:
                return nested
    return None


def _passive_mapping(value: Any, field: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise CognitiveProcessABIError(f"{field}:EXACT_DICT_REQUIRED")
    forbidden = _find_forbidden(value)
    if forbidden:
        raise CognitiveProcessABIError(f"{field}:FORBIDDEN_AUTHORITY_FIELD:{forbidden}")
    copied = dict(value)
    _canonical_bytes(copied)
    return copied


def _process_id(value: Any) -> str:
    text = _text(value, "process_id")
    if not PROCESS_ID_RE.fullmatch(text):
        raise CognitiveProcessABIError("process_id:AZP_REGISTRY_ID_REQUIRED")
    return text


def _enum(value: Any, field: str, allowed: frozenset[str]) -> str:
    text = _text(value, field)
    if text not in allowed:
        raise CognitiveProcessABIError(f"{field}:UNSUPPORTED:{text}")
    return text


@dataclass(frozen=True)
class CognitiveProcessInvocation:
    packet: Mapping[str, Any]
    invocation_id: str


@dataclass(frozen=True)
class CognitiveProcessResult:
    packet: Mapping[str, Any]
    result_id: str


def build_invocation(
    *,
    process_id: str,
    causal_event_id: str,
    admission_id: str,
    work_id: str,
    state_generation: int,
    state_epoch: int,
    state_digest: str,
    process_registry_digest: str,
    capability_authority_digest: str,
    source_provenance_digest: str,
    execution_target: str,
    state_requirement: str,
    input_payload_ref: str,
    input_payload_sha256: str,
    required_capabilities: Sequence[str] = (),
    dependency_work_ids: Sequence[str] = (),
    parent_work_id: str | None = None,
    workspace_id: str | None = None,
    durable_data_refs: Sequence[str] = (),
    resource_budget: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> CognitiveProcessInvocation:
    process_id = _process_id(process_id)
    causal_event_id = _text(causal_event_id, "causal_event_id")
    admission_id = _text(admission_id, "admission_id")
    work_id = _text(work_id, "work_id")
    if causal_event_id == admission_id:
        raise CognitiveProcessABIError("CAUSAL_EVENT_AND_ADMISSION_ID_MUST_DIFFER")
    state_generation = _nonnegative_int(state_generation, "state_generation")
    state_epoch = _nonnegative_int(state_epoch, "state_epoch")
    state_digest = _sha(state_digest, "state_digest")
    process_registry_digest = _sha(process_registry_digest, "process_registry_digest")
    capability_authority_digest = _sha(capability_authority_digest, "capability_authority_digest")
    source_provenance_digest = _sha(source_provenance_digest, "source_provenance_digest")
    execution_target = _enum(execution_target, "execution_target", EXECUTION_TARGETS)
    state_requirement = _enum(state_requirement, "state_requirement", STATE_REQUIREMENTS)
    input_payload_ref = _text(input_payload_ref, "input_payload_ref")
    input_payload_sha256 = _sha(input_payload_sha256, "input_payload_sha256")
    required_capabilities = _unique_texts(required_capabilities, "required_capabilities")
    dependency_work_ids = _unique_texts(dependency_work_ids, "dependency_work_ids")
    durable_data_refs = _unique_texts(durable_data_refs, "durable_data_refs")
    if parent_work_id is not None:
        parent_work_id = _text(parent_work_id, "parent_work_id")
    if workspace_id is not None:
        workspace_id = _text(workspace_id, "workspace_id")
    budget = _passive_mapping(dict(resource_budget or {}), "resource_budget")
    meta = _passive_mapping(dict(metadata or {}), "metadata")

    packet = {
        "schema": INVOCATION_SCHEMA,
        "abi": ABI_SCHEMA,
        "owner_target": OWNER_TARGET,
        "process_id": process_id,
        "causal_event_id": causal_event_id,
        "admission_id": admission_id,
        "work_id": work_id,
        "parent_work_id": parent_work_id,
        "dependency_work_ids": list(dependency_work_ids),
        "workspace_id": workspace_id,
        "state": {
            "generation": state_generation,
            "epoch": state_epoch,
            "digest": state_digest,
            "requirement": state_requirement,
            "durable_data_refs": list(durable_data_refs),
        },
        "authority_bindings": {
            "process_registry_digest": process_registry_digest,
            "capability_authority_digest": capability_authority_digest,
            "source_provenance_digest": source_provenance_digest,
        },
        "execution_target": execution_target,
        "required_capabilities": list(required_capabilities),
        "input_payload": {"ref": input_payload_ref, "sha256": input_payload_sha256},
        "resource_budget": budget,
        "metadata": meta,
        "authority_claims": {
            "canonical_truth": False,
            "effect_authority": False,
            "security_authority": False,
            "coordinator_authority": False,
            "capability_self_grant": False,
        },
    }
    invocation_id = _sha256(packet)
    packet = {**packet, "invocation_id": invocation_id}
    _canonical_bytes(packet)
    return CognitiveProcessInvocation(packet=packet, invocation_id=invocation_id)


def validate_invocation(packet: Mapping[str, Any]) -> CognitiveProcessInvocation:
    if type(packet) is not dict:
        raise CognitiveProcessABIError("invocation:EXACT_DICT_REQUIRED")
    required = {
        "schema", "abi", "owner_target", "process_id", "causal_event_id", "admission_id",
        "work_id", "parent_work_id", "dependency_work_ids", "workspace_id", "state",
        "authority_bindings", "execution_target", "required_capabilities", "input_payload",
        "resource_budget", "metadata", "authority_claims", "invocation_id",
    }
    if set(packet) != required:
        raise CognitiveProcessABIError("invocation:CLOSED_SCHEMA_REQUIRED")
    if packet["schema"] != INVOCATION_SCHEMA or packet["abi"] != ABI_SCHEMA:
        raise CognitiveProcessABIError("invocation:SCHEMA_MISMATCH")
    if packet["owner_target"] != OWNER_TARGET:
        raise CognitiveProcessABIError("invocation:OWNER_TARGET_MISMATCH")
    if packet["authority_claims"] != {
        "canonical_truth": False,
        "effect_authority": False,
        "security_authority": False,
        "coordinator_authority": False,
        "capability_self_grant": False,
    }:
        raise CognitiveProcessABIError("invocation:AUTHORITY_CLAIMS_MUST_ALL_BE_FALSE")
    body = dict(packet)
    invocation_id = _sha(body.pop("invocation_id"), "invocation_id")
    if _sha256(body) != invocation_id:
        raise CognitiveProcessABIError("invocation:IDENTITY_MISMATCH")
    _process_id(packet["process_id"])
    _text(packet["causal_event_id"], "causal_event_id")
    _text(packet["admission_id"], "admission_id")
    _text(packet["work_id"], "work_id")
    if packet["causal_event_id"] == packet["admission_id"]:
        raise CognitiveProcessABIError("CAUSAL_EVENT_AND_ADMISSION_ID_MUST_DIFFER")
    if packet["parent_work_id"] is not None:
        _text(packet["parent_work_id"], "parent_work_id")
    if packet["workspace_id"] is not None:
        _text(packet["workspace_id"], "workspace_id")
    _enum(packet["execution_target"], "execution_target", EXECUTION_TARGETS)
    state = packet["state"]
    if type(state) is not dict or set(state) != {"generation", "epoch", "digest", "requirement", "durable_data_refs"}:
        raise CognitiveProcessABIError("invocation:STATE_SCHEMA_MISMATCH")
    _nonnegative_int(state["generation"], "state.generation")
    _nonnegative_int(state["epoch"], "state.epoch")
    _sha(state["digest"], "state.digest")
    _enum(state["requirement"], "state.requirement", STATE_REQUIREMENTS)
    _unique_texts(state["durable_data_refs"], "state.durable_data_refs")
    bindings = packet["authority_bindings"]
    if type(bindings) is not dict or set(bindings) != {
        "process_registry_digest", "capability_authority_digest", "source_provenance_digest"
    }:
        raise CognitiveProcessABIError("invocation:AUTHORITY_BINDINGS_SCHEMA_MISMATCH")
    for key, value in bindings.items():
        _sha(value, f"authority_bindings.{key}")
    input_payload = packet["input_payload"]
    if type(input_payload) is not dict or set(input_payload) != {"ref", "sha256"}:
        raise CognitiveProcessABIError("invocation:INPUT_PAYLOAD_SCHEMA_MISMATCH")
    _text(input_payload["ref"], "input_payload.ref")
    _sha(input_payload["sha256"], "input_payload.sha256")
    _unique_texts(packet["required_capabilities"], "required_capabilities")
    _unique_texts(packet["dependency_work_ids"], "dependency_work_ids")
    _passive_mapping(packet["resource_budget"], "resource_budget")
    _passive_mapping(packet["metadata"], "metadata")
    _canonical_bytes(packet)
    return CognitiveProcessInvocation(packet=dict(packet), invocation_id=invocation_id)


def build_result(
    invocation: CognitiveProcessInvocation,
    *,
    executor_identity: str,
    runtime_identity_digest: str,
    result_class: str,
    output_payload_ref: str,
    output_payload_sha256: str,
    writes_s1_candidate: bool = False,
    coordinator_lease_ref: str | None = None,
    coordinator_lease_digest: str | None = None,
    trace_ref: str | None = None,
    trace_digest: str | None = None,
    unknown_reason: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> CognitiveProcessResult:
    if not isinstance(invocation, CognitiveProcessInvocation):
        raise CognitiveProcessABIError("invocation:COGNITIVE_PROCESS_INVOCATION_REQUIRED")
    validated = validate_invocation(invocation.packet)
    executor_identity = _text(executor_identity, "executor_identity")
    runtime_identity_digest = _sha(runtime_identity_digest, "runtime_identity_digest")
    result_class = _enum(result_class, "result_class", RESULT_CLASSES)
    output_payload_ref = _text(output_payload_ref, "output_payload_ref")
    output_payload_sha256 = _sha(output_payload_sha256, "output_payload_sha256")
    if type(writes_s1_candidate) is not bool:
        raise CognitiveProcessABIError("writes_s1_candidate:BOOL_REQUIRED")
    if writes_s1_candidate:
        coordinator_lease_ref = _text(coordinator_lease_ref, "coordinator_lease_ref")
        coordinator_lease_digest = _sha(coordinator_lease_digest, "coordinator_lease_digest")
    elif coordinator_lease_ref is not None or coordinator_lease_digest is not None:
        raise CognitiveProcessABIError("COORDINATOR_LEASE_ONLY_WITH_S1_WRITE_CANDIDATE")
    if (trace_ref is None) != (trace_digest is None):
        raise CognitiveProcessABIError("TRACE_REF_AND_DIGEST_MUST_PAIR")
    if trace_ref is not None:
        trace_ref = _text(trace_ref, "trace_ref")
        trace_digest = _sha(trace_digest, "trace_digest")
    if result_class == "UNKNOWN":
        unknown_reason = _text(unknown_reason, "unknown_reason")
    elif unknown_reason is not None:
        raise CognitiveProcessABIError("unknown_reason:ONLY_ALLOWED_FOR_UNKNOWN")
    meta = _passive_mapping(dict(metadata or {}), "metadata")
    inv = validated.packet
    packet = {
        "schema": RESULT_SCHEMA,
        "abi": ABI_SCHEMA,
        "owner_target": OWNER_TARGET,
        "invocation_id": validated.invocation_id,
        "process_id": inv["process_id"],
        "causal_event_id": inv["causal_event_id"],
        "admission_id": inv["admission_id"],
        "work_id": inv["work_id"],
        "state": dict(inv["state"]),
        "executor_identity": executor_identity,
        "runtime_identity_digest": runtime_identity_digest,
        "result_class": result_class,
        "output_payload": {"ref": output_payload_ref, "sha256": output_payload_sha256},
        "s1_write_candidate": {
            "requested": writes_s1_candidate,
            "coordinator_lease_ref": coordinator_lease_ref,
            "coordinator_lease_digest": coordinator_lease_digest,
            "direct_write_authority": False,
        },
        "trace": {"ref": trace_ref, "sha256": trace_digest},
        "unknown_reason": unknown_reason,
        "metadata": meta,
        "authority_claims": {
            "canonical_truth": False,
            "effect_authority": False,
            "security_authority": False,
            "coordinator_authority": False,
        },
    }
    result_id = _sha256(packet)
    packet = {**packet, "result_id": result_id}
    _canonical_bytes(packet)
    return CognitiveProcessResult(packet=packet, result_id=result_id)


def validate_result(packet: Mapping[str, Any], invocation: CognitiveProcessInvocation) -> CognitiveProcessResult:
    if type(packet) is not dict:
        raise CognitiveProcessABIError("result:EXACT_DICT_REQUIRED")
    validated_inv = validate_invocation(invocation.packet)
    required = {
        "schema", "abi", "owner_target", "invocation_id", "process_id", "causal_event_id",
        "admission_id", "work_id", "state", "executor_identity", "runtime_identity_digest",
        "result_class", "output_payload", "s1_write_candidate", "trace", "unknown_reason",
        "metadata", "authority_claims", "result_id",
    }
    if set(packet) != required:
        raise CognitiveProcessABIError("result:CLOSED_SCHEMA_REQUIRED")
    if packet["schema"] != RESULT_SCHEMA or packet["abi"] != ABI_SCHEMA or packet["owner_target"] != OWNER_TARGET:
        raise CognitiveProcessABIError("result:SCHEMA_OR_OWNER_MISMATCH")
    for field in ("invocation_id", "process_id", "causal_event_id", "admission_id", "work_id"):
        expected = validated_inv.invocation_id if field == "invocation_id" else validated_inv.packet[field]
        if packet[field] != expected:
            raise CognitiveProcessABIError(f"result:{field}:INVOCATION_BINDING_MISMATCH")
    if packet["state"] != validated_inv.packet["state"]:
        raise CognitiveProcessABIError("result:STATE_BINDING_MISMATCH")
    if packet["authority_claims"] != {
        "canonical_truth": False,
        "effect_authority": False,
        "security_authority": False,
        "coordinator_authority": False,
    }:
        raise CognitiveProcessABIError("result:AUTHORITY_CLAIMS_MUST_ALL_BE_FALSE")
    _text(packet["executor_identity"], "executor_identity")
    _sha(packet["runtime_identity_digest"], "runtime_identity_digest")
    output_payload = packet["output_payload"]
    if type(output_payload) is not dict or set(output_payload) != {"ref", "sha256"}:
        raise CognitiveProcessABIError("result:OUTPUT_PAYLOAD_SCHEMA_MISMATCH")
    _text(output_payload["ref"], "output_payload.ref")
    _sha(output_payload["sha256"], "output_payload.sha256")
    result_class = _enum(packet["result_class"], "result_class", RESULT_CLASSES)
    if result_class == "UNKNOWN":
        _text(packet["unknown_reason"], "unknown_reason")
    elif packet["unknown_reason"] is not None:
        raise CognitiveProcessABIError("unknown_reason:ONLY_ALLOWED_FOR_UNKNOWN")
    s1 = packet["s1_write_candidate"]
    if type(s1) is not dict or set(s1) != {"requested", "coordinator_lease_ref", "coordinator_lease_digest", "direct_write_authority"}:
        raise CognitiveProcessABIError("result:S1_WRITE_SCHEMA_MISMATCH")
    if s1["direct_write_authority"] is not False:
        raise CognitiveProcessABIError("result:DIRECT_S1_WRITE_AUTHORITY_FORBIDDEN")
    if s1["requested"] is True:
        _text(s1["coordinator_lease_ref"], "coordinator_lease_ref")
        _sha(s1["coordinator_lease_digest"], "coordinator_lease_digest")
    elif s1["requested"] is False:
        if s1["coordinator_lease_ref"] is not None or s1["coordinator_lease_digest"] is not None:
            raise CognitiveProcessABIError("result:UNREQUESTED_COORDINATOR_LEASE")
    else:
        raise CognitiveProcessABIError("result:s1_write_candidate.requested:BOOL_REQUIRED")
    trace = packet["trace"]
    if type(trace) is not dict or set(trace) != {"ref", "sha256"}:
        raise CognitiveProcessABIError("result:TRACE_SCHEMA_MISMATCH")
    if (trace["ref"] is None) != (trace["sha256"] is None):
        raise CognitiveProcessABIError("result:TRACE_REF_AND_DIGEST_MUST_PAIR")
    if trace["ref"] is not None:
        _text(trace["ref"], "trace.ref")
        _sha(trace["sha256"], "trace.sha256")
    _passive_mapping(packet["metadata"], "metadata")
    body = dict(packet)
    result_id = _sha(body.pop("result_id"), "result_id")
    if _sha256(body) != result_id:
        raise CognitiveProcessABIError("result:IDENTITY_MISMATCH")
    _canonical_bytes(packet)
    return CognitiveProcessResult(packet=dict(packet), result_id=result_id)
