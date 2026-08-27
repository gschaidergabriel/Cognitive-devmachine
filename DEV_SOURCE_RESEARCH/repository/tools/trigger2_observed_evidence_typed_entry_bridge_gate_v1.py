#!/usr/bin/env python3
"""Repository-bound Trigger-2 OBSERVED -> Typed Entry bridge gate v1.

This gate authenticates *admission provenance*, not observation truth. It reuses the
retained EntityOS Typed Entry Fabric to recompute causal-event and concrete admission
identities from an independently repository-held witness. Candidate-row Entry/receipt
fields can never create or broaden that witness.

The historical state-history gate remains the semantic authority for event meaning/U/D/f.
This bridge only proves that an OBSERVED receipt is bound to one exact, independently
controlled admission witness and the authority-pinned Entry producer bytes/policy.

SOURCE/CANDIDATE PRE-ADMISSION ONLY. PASS mints no canonical truth, dataset, effect,
provider, runtime, J-Space, HCU, EntityOS, or training credit.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
from typing import Any

SCHEMA = "CLAY_TRIGGER2_OBSERVED_TYPED_ENTRY_BRIDGE_GATE/v1"
AUTHORITY_SCHEMA = "CLAY_TRIGGER2_OBSERVED_TYPED_ENTRY_BRIDGE_AUTHORITY/v1"
WITNESS_SCHEMA = "CLAY_TRIGGER2_OBSERVED_ADMISSION_WITNESS/v1"
ENVELOPE_SCHEMA = "CLAY_TRIGGER2_OBSERVATION_ADMISSION_ENVELOPE/v1"
SUBJECT_SCHEMA = "CLAY_TRIGGER2_OBSERVATION_AUTH_SUBJECT/v1"
OBSERVATION_RECEIPT_SCHEMA = "ENTITYOS_TYPED_OBSERVATION_EVIDENCE_RECEIPT/v1"
AUTHORITY_PATH = (
    "research_entity/global/j-space/research/"
    "TRIGGER2_OBSERVED_TYPED_ENTRY_BRIDGE_AUTHORITY_V1.json"
)
EXPECTED_REPOSITORY = "gschaidergabriel/clay-global-research-entity"
EXPECTED_BRANCH = "main"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON_OBJECT_REQUIRED")
    return value


def _load_authority() -> dict[str, Any]:
    return _load_json(_repo_root() / AUTHORITY_PATH)


def _canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _is_lower_hex(value: Any, width: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == width
        and all(ch in "0123456789abcdef" for ch in value)
    )


def _git_text(*args: str) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(_repo_root()), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        return 127, "", type(exc).__name__ + ":" + str(exc)
    return (
        proc.returncode,
        proc.stdout.decode("utf-8", "replace").strip(),
        proc.stderr.decode("utf-8", "replace").strip(),
    )


def _remote_repository_identity(url: str) -> str | None:
    value = url.strip()
    if value.endswith(".git"):
        value = value[:-4]
    for prefix in (
        "https://github.com/", "http://github.com/", "ssh://git@github.com/",
        "git://github.com/", "git@github.com:",
    ):
        if value.startswith(prefix):
            candidate = value[len(prefix):].strip("/")
            return candidate or None
    return None


def _verify_entry_fabric_source(producer: Any) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    details: dict[str, Any] = {
        "origin_repository": None,
        "executed_head_sha": None,
        "source_commit_blob_sha": None,
        "executed_head_blob_sha": None,
        "source_commit_is_ancestor_of_head": False,
    }
    if not isinstance(producer, dict):
        return ["OBS_ENTRY_PRODUCER_AUTHORITY_REQUIRED"], details
    repo_path = producer.get("repo_path")
    blob_sha = producer.get("source_git_blob_sha")
    lineage = producer.get("source_lineage")
    if not isinstance(repo_path, str) or not repo_path:
        failures.append("OBS_ENTRY_PRODUCER_PATH_REQUIRED")
    if not _is_lower_hex(blob_sha, 40):
        failures.append("OBS_ENTRY_PRODUCER_BLOB_SHA_REQUIRED")
    if not isinstance(lineage, dict):
        return sorted(set(failures + ["OBS_ENTRY_PRODUCER_LINEAGE_REQUIRED"])), details
    source_commit = lineage.get("source_commit_sha")
    source_path = lineage.get("source_path")
    if lineage.get("repository") != EXPECTED_REPOSITORY:
        failures.append("OBS_ENTRY_PRODUCER_REPOSITORY_MISMATCH")
    if lineage.get("branch") != EXPECTED_BRANCH:
        failures.append("OBS_ENTRY_PRODUCER_BRANCH_MISMATCH")
    if source_path != repo_path:
        failures.append("OBS_ENTRY_PRODUCER_LINEAGE_PATH_MISMATCH")
    if not _is_lower_hex(source_commit, 40):
        return sorted(set(failures + ["OBS_ENTRY_PRODUCER_SOURCE_COMMIT_REQUIRED"])), details

    code, origin_url, _ = _git_text("remote", "get-url", "origin")
    origin_repo = _remote_repository_identity(origin_url) if code == 0 else None
    details["origin_repository"] = origin_repo
    if origin_repo != EXPECTED_REPOSITORY:
        failures.append("OBS_ENTRY_REPOSITORY_ORIGIN_MISMATCH")

    code, head_sha, _ = _git_text("rev-parse", "HEAD")
    if code != 0 or not _is_lower_hex(head_sha, 40):
        failures.append("OBS_ENTRY_EXECUTED_HEAD_UNRESOLVED")
    else:
        details["executed_head_sha"] = head_sha

    code, _, _ = _git_text("cat-file", "-e", str(source_commit) + "^{commit}")
    if code != 0:
        return sorted(set(failures + ["OBS_ENTRY_SOURCE_COMMIT_UNRESOLVED"])), details

    code, source_blob, _ = _git_text("rev-parse", f"{source_commit}:{repo_path}")
    details["source_commit_blob_sha"] = source_blob if code == 0 else None
    if code != 0 or source_blob != blob_sha:
        failures.append("OBS_ENTRY_SOURCE_COMMIT_BLOB_MISMATCH")

    if isinstance(details.get("executed_head_sha"), str):
        code, _, _ = _git_text("merge-base", "--is-ancestor", str(source_commit), head_sha)
        details["source_commit_is_ancestor_of_head"] = code == 0
        if code != 0:
            failures.append("OBS_ENTRY_SOURCE_COMMIT_NOT_ANCESTOR")
        code, head_blob, _ = _git_text("rev-parse", f"HEAD:{repo_path}")
        details["executed_head_blob_sha"] = head_blob if code == 0 else None
        if code != 0 or head_blob != blob_sha:
            failures.append("OBS_ENTRY_EXECUTED_HEAD_BLOB_MISMATCH")
    return sorted(set(failures)), details


def _load_entry_fabric(producer: dict[str, Any]):
    path = (_repo_root() / str(producer["repo_path"])).resolve()
    try:
        path.relative_to(_repo_root().resolve())
    except ValueError as exc:
        raise ValueError("OBS_ENTRY_PRODUCER_PATH_ESCAPES_REPO") from exc
    spec = importlib.util.spec_from_file_location("trigger2_observed_bound_entry_fabric", path)
    if spec is None or spec.loader is None:
        raise ImportError("OBS_ENTRY_PRODUCER_SPEC_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _result(failures: list[str], **extra: Any) -> dict[str, Any]:
    failures = sorted(set(failures))
    result = {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "observation_truth_decided": False,
        "second_truth_or_admission_authority_created": False,
    }
    result.update(extra)
    return result


def _observed_events(row: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    failures: list[str] = []
    observed: dict[str, dict[str, Any]] = {}
    history = row.get("synthetic_event_history_evaluator_only", [])
    if not isinstance(history, list):
        failures.append("OBS_ENTRY_HISTORY_LIST_REQUIRED")
        history = []
    current = row.get("synthetic_test_event_evaluator_only")
    events = list(history)
    if isinstance(current, dict):
        events.append(current)
    for event in events:
        if not isinstance(event, dict) or event.get("epistemic_type") != "OBSERVED":
            continue
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            failures.append("OBS_ENTRY_EVENT_ID_REQUIRED")
            continue
        if event_id in observed and observed[event_id] != event:
            failures.append("OBS_ENTRY_EVENT_ID_REUSED_DIFFERENT_EVENT:" + event_id)
        observed.setdefault(event_id, event)
    return observed, sorted(set(failures))


def _index(items: Any, *, kind: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    if not isinstance(items, list):
        return {}, [kind + "_LIST_REQUIRED"]
    out: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            failures.append(kind + "_OBJECT_REQUIRED")
            continue
        event_id = item.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            failures.append(kind + "_EVENT_ID_REQUIRED")
            continue
        if event_id in out:
            failures.append("DUPLICATE_" + kind + "_EVENT_ID:" + event_id)
            continue
        out[event_id] = item
    return out, sorted(set(failures))


def _trusted_witness_subject(
    *, witness_id: str, witness: dict[str, Any], packet: Any,
    producer: dict[str, Any], policy_digest: str,
) -> dict[str, Any]:
    entry = witness.get("entry") if isinstance(witness.get("entry"), dict) else {}
    return {
        "schema": SUBJECT_SCHEMA,
        "witness_id": witness_id,
        "producer_id": producer.get("producer_id"),
        "producer_epoch": producer.get("producer_epoch"),
        "producer_source_git_blob_sha": producer.get("source_git_blob_sha"),
        "event_id": witness.get("event_id"),
        "event_semantic_sha256": witness.get("event_semantic_sha256"),
        "causal_id": entry.get("causal_id"),
        "ingress_id": entry.get("ingress_id"),
        "entity_generation": entry.get("entity_generation"),
        "source_kind": entry.get("source_kind"),
        "source_id": entry.get("source_id"),
        "observed_time": entry.get("observed_time"),
        "provenance_ref": entry.get("provenance_ref"),
        "provenance_sha256": entry.get("provenance_sha256"),
        "payload_ref": entry.get("payload_ref"),
        "payload_sha256": entry.get("payload_sha256"),
        "entry_event_sha256": getattr(packet, "event_sha256", None),
        "entry_admission_sha256": getattr(packet, "admission_sha256", None),
        "receipt_id": witness.get("receipt_id"),
        "replay_identity": witness.get("replay_identity"),
        "legacy_receipt_source": witness.get("legacy_receipt_source"),
        "legacy_receipt_provenance": witness.get("legacy_receipt_provenance"),
        "policy_digest": policy_digest,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }


def _validate_witness_structure(witness: Any, event_id: str) -> list[str]:
    if not isinstance(witness, dict):
        return ["OBS_ENTRY_WITNESS_NOT_ADMITTED:" + event_id]
    failures: list[str] = []
    if witness.get("schema") != WITNESS_SCHEMA:
        failures.append("OBS_ENTRY_WITNESS_SCHEMA_INVALID:" + event_id)
    if witness.get("status") != "CURRENT":
        failures.append("OBS_ENTRY_WITNESS_NOT_CURRENT:" + event_id)
    if witness.get("event_id") != event_id:
        failures.append("OBS_ENTRY_WITNESS_EVENT_ID_MISMATCH:" + event_id)
    if not _is_lower_hex(witness.get("event_semantic_sha256"), 64):
        failures.append("OBS_ENTRY_WITNESS_EVENT_SEMANTIC_SHA_INVALID:" + event_id)
    for field in ("receipt_id", "replay_identity", "legacy_receipt_source", "legacy_receipt_provenance"):
        if not isinstance(witness.get(field), str) or not witness.get(field):
            failures.append("OBS_ENTRY_WITNESS_FIELD_REQUIRED:" + field + ":" + event_id)
    if not isinstance(witness.get("entry"), dict):
        failures.append("OBS_ENTRY_WITNESS_ENTRY_REQUIRED:" + event_id)
    auth = witness.get("admission_authority")
    if not isinstance(auth, dict):
        failures.append("OBS_ENTRY_WITNESS_ADMISSION_AUTHORITY_REQUIRED:" + event_id)
    else:
        required = {
            "current_generation", "expected_capability_binding_sha256",
            "admitted_capabilities", "admitted_budget",
        }
        if set(auth) != required:
            failures.append("OBS_ENTRY_WITNESS_ADMISSION_AUTHORITY_FIELDS_EXACT_REQUIRED:" + event_id)
    return sorted(set(failures))


def _validate_one(
    *, event_id: str, event: dict[str, Any], receipt: Any, envelope: Any,
    authority: dict[str, Any], entry_fabric: Any, producer: dict[str, Any],
    policy_digest: str, replay_subjects: dict[str, str],
    receipt_subjects: dict[str, str],
) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    details: dict[str, Any] = {"event_id": event_id, "witness_id": None, "subject_sha256": None}
    policy = authority.get("policy")
    witnesses = authority.get("admission_witnesses")
    if not isinstance(policy, dict) or not isinstance(witnesses, dict):
        return ["OBS_ENTRY_AUTHORITY_STRUCTURE_INVALID"], details
    if not isinstance(receipt, dict):
        return ["OBS_ENTRY_RECEIPT_REQUIRED:" + event_id], details
    if not isinstance(envelope, dict):
        return ["OBS_ENTRY_ENVELOPE_REQUIRED:" + event_id], details
    if receipt.get("schema") != OBSERVATION_RECEIPT_SCHEMA:
        failures.append("OBS_ENTRY_RECEIPT_SCHEMA_INVALID:" + event_id)
    if envelope.get("schema") != ENVELOPE_SCHEMA:
        failures.append("OBS_ENTRY_ENVELOPE_SCHEMA_INVALID:" + event_id)

    witness_id = receipt.get("admission_witness_id")
    details["witness_id"] = witness_id
    if not isinstance(witness_id, str) or not witness_id or envelope.get("admission_witness_id") != witness_id:
        return failures + ["OBS_ENTRY_WITNESS_ID_REQUIRED_OR_MISMATCH:" + event_id], details
    witness = witnesses.get(witness_id)
    failures.extend(_validate_witness_structure(witness, event_id))
    if not isinstance(witness, dict):
        return sorted(set(failures)), details

    auth = witness.get("admission_authority")
    entry = witness.get("entry")
    packet = None
    if isinstance(auth, dict) and isinstance(entry, dict):
        try:
            packet = entry_fabric.admit_entry(
                entry,
                current_generation=auth.get("current_generation"),
                expected_capability_binding_sha256=auth.get("expected_capability_binding_sha256"),
                admitted_capabilities=auth.get("admitted_capabilities"),
                admitted_budget=auth.get("admitted_budget"),
            )
        except Exception as exc:
            failures.append("OBS_ENTRY_TRUSTED_WITNESS_RECOMPUTE_FAILED:" + type(exc).__name__ + ":" + event_id)
    if packet is None:
        return sorted(set(failures)), details

    if witness.get("producer_id") != producer.get("producer_id"):
        failures.append("OBS_ENTRY_WITNESS_PRODUCER_ID_MISMATCH:" + event_id)
    if witness.get("producer_epoch") != producer.get("producer_epoch"):
        failures.append("OBS_ENTRY_WITNESS_PRODUCER_EPOCH_MISMATCH:" + event_id)
    if witness.get("expected_entry_event_sha256") != getattr(packet, "event_sha256", None):
        failures.append("OBS_ENTRY_WITNESS_EVENT_IDENTITY_MISMATCH:" + event_id)
    if witness.get("expected_entry_admission_sha256") != getattr(packet, "admission_sha256", None):
        failures.append("OBS_ENTRY_WITNESS_ADMISSION_IDENTITY_MISMATCH:" + event_id)

    subject = _trusted_witness_subject(
        witness_id=witness_id, witness=witness, packet=packet,
        producer=producer, policy_digest=policy_digest,
    )
    try:
        subject_sha = sha256(entry_fabric.canonicalize(subject)).hexdigest()
    except Exception as exc:
        failures.append("OBS_ENTRY_SUBJECT_CANONICALIZATION_FAILED:" + type(exc).__name__ + ":" + event_id)
        subject_sha = None
    details["subject_sha256"] = subject_sha

    entry_fields = witness.get("entry") if isinstance(witness.get("entry"), dict) else {}
    exact = {
        "event_id": event_id,
        "event_semantic_sha256": witness.get("event_semantic_sha256"),
        "causal_id": entry_fields.get("causal_id"),
        "ingress_id": entry_fields.get("ingress_id"),
        "entity_generation": entry_fields.get("entity_generation"),
        "source_kind": entry_fields.get("source_kind"),
        "source_id": entry_fields.get("source_id"),
        "observed_time": entry_fields.get("observed_time"),
        "provenance_ref": entry_fields.get("provenance_ref"),
        "provenance_sha256": entry_fields.get("provenance_sha256"),
        "payload_ref": entry_fields.get("payload_ref"),
        "payload_sha256": entry_fields.get("payload_sha256"),
        "entry_event_sha256": getattr(packet, "event_sha256", None),
        "entry_admission_sha256": getattr(packet, "admission_sha256", None),
        "admission_witness_sha256": subject_sha,
        "policy_digest": policy_digest,
        "receipt_id": witness.get("receipt_id"),
        "replay_identity": witness.get("replay_identity"),
        "source": witness.get("legacy_receipt_source"),
        "provenance": witness.get("legacy_receipt_provenance"),
    }
    for field, expected in exact.items():
        if receipt.get(field) != expected:
            failures.append("OBS_ENTRY_RECEIPT_FIELD_MISMATCH:" + field + ":" + event_id)
        if envelope.get(field) != expected:
            failures.append("OBS_ENTRY_ENVELOPE_FIELD_MISMATCH:" + field + ":" + event_id)
    if event.get("event_id") != witness.get("event_id"):
        failures.append("OBS_ENTRY_EVENT_WITNESS_ID_MISMATCH:" + event_id)
    # Event-semantic digest itself is intentionally not recomputed here: that remains
    # the retained state-history gate's semantic responsibility.
    if receipt.get("canonical_truth_allowed") is not False or envelope.get("canonical_truth_allowed") is not False:
        failures.append("OBS_ENTRY_CANNOT_MINT_CANONICAL_TRUTH:" + event_id)
    if receipt.get("direct_effect_authority") is not False or envelope.get("direct_effect_authority") is not False:
        failures.append("OBS_ENTRY_CANNOT_MINT_DIRECT_EFFECT_AUTHORITY:" + event_id)
    if receipt.get("producer_id") != producer.get("producer_id") or envelope.get("producer_id") != producer.get("producer_id"):
        failures.append("OBS_ENTRY_PRODUCER_ID_MISMATCH:" + event_id)
    if receipt.get("producer_epoch") != producer.get("producer_epoch") or envelope.get("producer_epoch") != producer.get("producer_epoch"):
        failures.append("OBS_ENTRY_PRODUCER_EPOCH_MISMATCH:" + event_id)
    if receipt.get("producer_source_git_blob_sha") != producer.get("source_git_blob_sha") or envelope.get("producer_source_git_blob_sha") != producer.get("source_git_blob_sha"):
        failures.append("OBS_ENTRY_PRODUCER_SOURCE_MISMATCH:" + event_id)

    if isinstance(subject_sha, str):
        replay_id = witness.get("replay_identity")
        receipt_id = witness.get("receipt_id")
        if isinstance(replay_id, str):
            prior = replay_subjects.get(replay_id)
            if prior is not None and prior != subject_sha:
                failures.append("OBS_ENTRY_REPLAY_ID_REUSED_DIFFERENT_SUBJECT:" + event_id)
            replay_subjects.setdefault(replay_id, subject_sha)
        if isinstance(receipt_id, str):
            prior = receipt_subjects.get(receipt_id)
            if prior is not None and prior != subject_sha:
                failures.append("OBS_ENTRY_RECEIPT_ID_REUSED_DIFFERENT_SUBJECT:" + event_id)
            receipt_subjects.setdefault(receipt_id, subject_sha)
    return sorted(set(failures)), details


def adjudicate(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"])
    observed, failures = _observed_events(row)
    if not observed:
        return _result(
            failures,
            observed_event_count=0,
            authenticated_observed_event_count=0,
            independently_controlled_admission_witness_required=True,
            candidate_row_cannot_supply_admission_authority=True,
        )
    try:
        authority = _load_authority()
    except Exception as exc:
        return _result(failures + ["OBS_ENTRY_AUTHORITY_LOAD_FAILED:" + type(exc).__name__])
    if authority.get("schema") != AUTHORITY_SCHEMA:
        failures.append("OBS_ENTRY_AUTHORITY_SCHEMA_MISMATCH")
    expected_fences = {
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
    }
    if authority.get("authority_fences") != expected_fences:
        failures.append("OBS_ENTRY_AUTHORITY_FENCES_INVALID")
    policy = authority.get("policy")
    if not isinstance(policy, dict):
        return _result(failures + ["OBS_ENTRY_POLICY_REQUIRED"])
    policy_digest = _canonical_json_sha256(policy)
    if authority.get("policy_canonical_json_sha256") != policy_digest:
        failures.append("OBS_ENTRY_POLICY_DIGEST_MISMATCH")
    expected_policy_bindings = {
        "observation_receipt_schema": OBSERVATION_RECEIPT_SCHEMA,
        "instance_envelope_schema": ENVELOPE_SCHEMA,
        "subject_schema": SUBJECT_SCHEMA,
        "fail_closed_if_witness_unlisted": True,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }
    for key, expected in expected_policy_bindings.items():
        if policy.get(key) != expected:
            failures.append("OBS_ENTRY_POLICY_BINDING_MISMATCH:" + key)

    producer = authority.get("entry_fabric_producer")
    source_failures, source_details = _verify_entry_fabric_source(producer)
    failures.extend(source_failures)
    if not isinstance(producer, dict):
        return _result(failures + ["OBS_ENTRY_PRODUCER_AUTHORITY_REQUIRED"])
    try:
        entry_fabric = _load_entry_fabric(producer)
    except Exception as exc:
        return _result(failures + ["OBS_ENTRY_PRODUCER_LOAD_FAILED:" + type(exc).__name__])
    if getattr(entry_fabric, "ENTRY_SCHEMA", None) != producer.get("entry_schema"):
        failures.append("OBS_ENTRY_PRODUCER_ENTRY_SCHEMA_MISMATCH")
    if getattr(entry_fabric, "ENTRY_EVENT_IDENTITY_SCHEMA", None) != producer.get("entry_event_identity_schema"):
        failures.append("OBS_ENTRY_PRODUCER_EVENT_IDENTITY_SCHEMA_MISMATCH")
    if getattr(entry_fabric, "ENTRY_ADMISSION_IDENTITY_SCHEMA", None) != producer.get("entry_admission_identity_schema"):
        failures.append("OBS_ENTRY_PRODUCER_ADMISSION_IDENTITY_SCHEMA_MISMATCH")

    receipt_index, receipt_failures = _index(
        row.get("typed_observation_evidence_receipts_evaluator_only"), kind="OBS_ENTRY_RECEIPT",
    )
    envelope_index, envelope_failures = _index(
        row.get("typed_observation_admission_envelopes_evaluator_only"), kind="OBS_ENTRY_ENVELOPE",
    )
    failures.extend(receipt_failures)
    failures.extend(envelope_failures)

    replay_subjects: dict[str, str] = {}
    receipt_subjects: dict[str, str] = {}
    event_details: list[dict[str, Any]] = []
    authenticated = 0
    for event_id in sorted(observed):
        event_failures, details = _validate_one(
            event_id=event_id,
            event=observed[event_id],
            receipt=receipt_index.get(event_id),
            envelope=envelope_index.get(event_id),
            authority=authority,
            entry_fabric=entry_fabric,
            producer=producer,
            policy_digest=policy_digest,
            replay_subjects=replay_subjects,
            receipt_subjects=receipt_subjects,
        )
        failures.extend(event_failures)
        event_details.append(details)
        if not event_failures:
            authenticated += 1

    return _result(
        failures,
        observed_event_count=len(observed),
        authenticated_observed_event_count=authenticated,
        admission_witness_count=len(authority.get("admission_witnesses", {})) if isinstance(authority.get("admission_witnesses"), dict) else 0,
        independently_controlled_admission_witness_required=True,
        candidate_row_cannot_supply_admission_authority=True,
        trusted_entry_identity_recomputed=True,
        event_semantics_recomputed_here=False,
        event_semantics_delegated_to_retained_state_history_gate=True,
        entry_fabric_source_verification=source_details,
        policy_digest=policy_digest,
        event_authentication=event_details,
    )


if __name__ == "__main__":
    print({
        "schema": SCHEMA,
        "status": "SOURCE_ONLY_CANDIDATE_PRE_ADMISSION",
        "independently_controlled_admission_witness_required": True,
        "canonical_dataset_admission": False,
        "training_credit_minted": 0,
    })
