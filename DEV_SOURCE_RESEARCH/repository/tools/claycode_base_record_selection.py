#!/usr/bin/env python3
"""Generic deterministic structured-record selection primitive for ClayCode BASE.

This module is deliberately domain-neutral. Field names, weighted score terms, epoch/
eligibility rule, grouping quota, conflict visibility fields, record cost, re-expansion
reference and output projection are supplied by a declarative policy. It can therefore
serve FRANK ActiveAssembly, schedulers, retrieval sets, queues and other bounded record
selection workloads without adding FRANK-specific language semantics.

The selector returns ordinary data only. It never creates runtime capability authority.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from copy import deepcopy
from typing import Any

VERSION = "claycode-base-record-selection/0.1"


class RecordSelectionError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RecordSelectionError("NON_CANONICAL_VALUE") from exc


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _field(record: dict[str, Any], name: str) -> Any:
    if name not in record:
        raise RecordSelectionError(f"MISSING_FIELD:{name}")
    return record[name]


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RecordSelectionError(f"BAD_{label}")
    return value


def _score(record: dict[str, Any], spec: dict[str, Any], record_id: str) -> float:
    terms = spec.get("terms")
    if not isinstance(terms, list) or not terms:
        raise RecordSelectionError("BAD_SCORE_TERMS")
    total = float(spec.get("bias", 0.0))
    for term in terms:
        field = str(term["field"])
        raw = _field(record, field)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise RecordSelectionError(f"BAD_SCORE:{record_id}:{field}")
        value = float(raw)
        if term.get("validate_unit_interval", False) and not 0.0 <= value <= 1.0:
            raise RecordSelectionError(f"BAD_SCORE:{record_id}:{field}")
        transform = term.get("transform", "identity")
        if transform == "one_minus":
            value = 1.0 - value
        elif transform != "identity":
            raise RecordSelectionError(f"BAD_SCORE_TRANSFORM:{transform}")
        total += float(term.get("weight", 1.0)) * value
    digits = int(spec.get("round", 12))
    if digits < 0 or digits > 15:
        raise RecordSelectionError("BAD_SCORE_ROUND")
    return round(total, digits)


def select_records(records: list[dict[str, Any]], policy: dict[str, Any]) -> dict[str, Any]:
    """Select records deterministically according to a declarative generic policy."""
    if not isinstance(records, list) or not all(isinstance(x, dict) for x in records):
        raise RecordSelectionError("RECORDS_NOT_OBJECT_LIST")
    if not isinstance(policy, dict):
        raise RecordSelectionError("POLICY_NOT_OBJECT")

    id_field = str(policy["id_field"])
    group_field = str(policy["group_field"])
    cost_field = str(policy["cost_field"])
    kind_field = policy.get("kind_field")
    authority_flag_field = policy.get("authority_flag_field")
    denied_authority_kinds = set(policy.get("deny_authority_kinds", []))
    required_nonempty = [str(x) for x in policy.get("required_nonempty_fields", [id_field, group_field])]
    max_items = _positive_int(policy.get("max_items"), "ITEM_BUDGET")
    max_per_group = _positive_int(policy.get("max_per_group"), "GROUP_BUDGET")
    max_cost = policy.get("max_cost")
    if max_cost is not None:
        max_cost = _positive_int(max_cost, "CONTEXT_BUDGET")

    eligibility = policy.get("eligibility") or {}
    eligibility_field = eligibility.get("field")
    eligibility_equals = eligibility.get("equals")
    eligibility_reason = str(eligibility.get("reason", "INELIGIBLE"))
    claim = policy.get("conflict") or {}
    claim_key_field = claim.get("key_field")
    claim_value_field = claim.get("value_field")
    reexpand_field = policy.get("reexpand_field")
    score_spec = policy.get("score") or {}
    output = policy.get("output") or {}

    unique: list[dict[str, Any]] = []
    identity_by_id: dict[str, str] = {}
    duplicate_count = 0
    score_by_id: dict[str, float] = {}
    cost_by_id: dict[str, int] = {}

    for record in records:
        for field in required_nonempty:
            value = _field(record, field)
            if not isinstance(value, str) or not value.strip():
                raise RecordSelectionError(f"BAD_IDENTITY:{field}")
        rid = str(_field(record, id_field))
        if authority_flag_field and bool(record.get(str(authority_flag_field), False)):
            kind = record.get(str(kind_field)) if kind_field else None
            if kind in denied_authority_kinds:
                raise RecordSelectionError(f"AUTHORITY_MINT_ATTEMPT:{rid}")
        score = _score(record, score_spec, rid)
        cost = _positive_int(_field(record, cost_field), f"RECORD_COST:{rid}")
        fingerprint = sha256_value(record)
        previous = identity_by_id.get(rid)
        if previous is not None:
            if previous != fingerprint:
                raise RecordSelectionError(f"RECORD_ID_COLLISION:{rid}")
            duplicate_count += 1
            continue
        identity_by_id[rid] = fingerprint
        score_by_id[rid] = score
        cost_by_id[rid] = cost
        unique.append(record)

    eligible: list[dict[str, Any]] = []
    omitted: list[tuple[dict[str, Any], str]] = []
    for record in unique:
        if eligibility_field is not None and record.get(str(eligibility_field)) != eligibility_equals:
            omitted.append((record, eligibility_reason))
            continue
        eligible.append(record)

    eligible.sort(key=lambda r: (-score_by_id[str(r[id_field])], str(r[id_field])))
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    group_counts: dict[str, int] = {}
    selection_roles: dict[str, str] = {}
    block_reason: dict[str, str] = {}
    used_cost = 0

    def add(record: dict[str, Any], *, conflict_visibility: bool = False) -> bool:
        nonlocal used_cost
        rid = str(record[id_field])
        group = str(_field(record, group_field))
        if rid in selected_ids:
            return False
        if len(selected) >= max_items:
            block_reason.setdefault(rid, "ITEM_BUDGET")
            return False
        if not conflict_visibility and group_counts.get(group, 0) >= max_per_group:
            block_reason.setdefault(rid, "ANCESTRY_CAP")
            return False
        cost = cost_by_id[rid]
        if max_cost is not None and used_cost + cost > max_cost:
            block_reason.setdefault(rid, "CONTEXT_COST_BUDGET")
            return False
        selected.append(record)
        selected_ids.add(rid)
        group_counts[group] = group_counts.get(group, 0) + 1
        selection_roles[rid] = "CONFLICT_VISIBILITY" if conflict_visibility else "ORDINARY"
        used_cost += cost
        return True

    # Preserve one best record for every conflicting value of a key before general fill.
    by_claim: dict[str, dict[str, dict[str, Any]]] = {}
    if claim_key_field is not None and claim_value_field is not None:
        for record in eligible:
            key = record.get(str(claim_key_field))
            value = record.get(str(claim_value_field))
            if key is None or value is None:
                continue
            by_claim.setdefault(str(key), {}).setdefault(str(value), record)
    conflict_representatives: list[dict[str, Any]] = []
    for values in by_claim.values():
        if len(values) > 1:
            conflict_representatives.extend(values.values())
    conflict_representatives.sort(key=lambda r: (-score_by_id[str(r[id_field])], str(r[id_field])))
    for record in conflict_representatives:
        add(record, conflict_visibility=True)

    # First-pass diversity, then remaining group quota.
    seen_groups: set[str] = set()
    for record in eligible:
        group = str(record[group_field])
        if group not in seen_groups:
            add(record)
            seen_groups.add(group)
    for record in eligible:
        add(record)

    for record in eligible:
        rid = str(record[id_field])
        if rid not in selected_ids:
            omitted.append((record, block_reason.get(rid, "BUDGET_OR_ANCESTRY_CAP")))

    selected_field = str(output.get("selected_field", "items"))
    identity_annotation = str(output.get("identity_annotation", "record_identity_sha256"))
    score_annotation = str(output.get("score_annotation", "score"))
    role_annotation = str(output.get("role_annotation", "selection_role"))
    replication_annotation = str(output.get("replication_annotation", "independent_replication_credit"))
    authority_annotation = str(output.get("authority_annotation", "execution_authority"))
    items: list[dict[str, Any]] = []
    for record in selected:
        rid = str(record[id_field])
        role = selection_roles[rid]
        item = deepcopy(record)
        item[identity_annotation] = identity_by_id[rid]
        item[score_annotation] = score_by_id[rid]
        item[role_annotation] = role
        item[replication_annotation] = False if role == "CONFLICT_VISIBILITY" else None
        # Data returned from selection is never an authority bearer.
        item[authority_annotation] = False
        items.append(item)

    reexpand_refs: set[str] = set()
    for record, _reason in omitted:
        rid = str(record[id_field])
        ref = record.get(str(reexpand_field)) if reexpand_field else None
        reexpand_refs.add(str(ref or rid))
    reason_counts = Counter(reason for _record, reason in omitted)

    result = deepcopy(output.get("fixed", {}))
    if not isinstance(result, dict):
        raise RecordSelectionError("OUTPUT_FIXED_NOT_OBJECT")
    result[selected_field] = items
    result[str(output.get("reexpand_refs_field", "reexpand_refs"))] = sorted(reexpand_refs)
    result[str(output.get("omitted_count_field", "omitted_count"))] = len(omitted)
    result[str(output.get("omitted_reasons_field", "omitted_reasons"))] = {k: reason_counts[k] for k in sorted(reason_counts)}
    result[str(output.get("cost_used_field", "context_cost_used"))] = used_cost
    result[str(output.get("cost_remaining_field", "context_cost_remaining"))] = None if max_cost is None else max_cost - used_cost

    hash_field = str(output.get("hash_field", "selection_sha256"))
    result[hash_field] = sha256_value(result)
    result[str(output.get("duplicate_count_field", "input_duplicate_count"))] = duplicate_count
    return result


def select_json(request_json: str) -> str:
    try:
        request = json.loads(request_json)
    except Exception as exc:
        raise RecordSelectionError("REQUEST_JSON_INVALID") from exc
    if not isinstance(request, dict):
        raise RecordSelectionError("REQUEST_NOT_OBJECT")
    result = select_records(request.get("records"), request.get("policy"))
    return canonical_bytes(result).decode("utf-8")


__all__ = ["select_records", "select_json", "RecordSelectionError", "canonical_bytes", "sha256_value", "VERSION"]
