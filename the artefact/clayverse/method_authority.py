from __future__ import annotations

import json
from typing import Any

METHOD_SCHEMA_VERSION = 1
PROMOTABLE_METHOD_KINDS = {"framework", "heuristic"}
CANDIDATE_FOR = {"framework": "framework_candidate", "heuristic": "heuristic_candidate"}
TERMINAL_EPISODE_STATES = {"COMPLETED", "ABORTED"}


class MethodAuthorityError(ValueError):
    pass


def _json_object(raw: Any, *, field: str) -> dict[str, Any]:
    if isinstance(raw, dict):
        value = raw
    else:
        try:
            value = json.loads(str(raw), parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise MethodAuthorityError(f"{field} must be finite JSON") from exc
    if not isinstance(value, dict):
        raise MethodAuthorityError(f"{field} must be an object")
    try:
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MethodAuthorityError(f"{field} must be canonical finite JSON") from exc
    return value


def _string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MethodAuthorityError(f"{field} must be a non-empty string")
    return value.strip()


def _string_list(value: Any, *, field: str, minimum: int = 0) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise MethodAuthorityError(f"{field} must be a string list")
    cleaned = [item.strip() for item in value]
    if len(cleaned) < minimum or len(set(cleaned)) != len(cleaned):
        raise MethodAuthorityError(f"{field} has invalid cardinality")
    return cleaned


def validate_promoted_row(db, row, record: dict[str, Any], provenance: dict[str, Any]) -> None:
    """Fail closed unless a served framework/heuristic is bound to a real promotion chain.

    This is the minimum promotion-authority fusion from the stricter method-memory lane:
    a self-declared PROMOTED flag is never sufficient. The promoted row must bind a
    candidate, a durable PROMOTE receipt and at least two terminal source episodes.
    """
    kind = str(row["kind"])
    if kind not in PROMOTABLE_METHOD_KINDS:
        return
    if provenance.get("method_schema_version") != METHOD_SCHEMA_VERSION:
        raise MethodAuthorityError("promoted method has unknown method schema version")

    source_id = _string(provenance.get("promotion_source_memory_id"), field="promotion_source_memory_id")
    receipt_id = _string(provenance.get("promotion_receipt_id"), field="promotion_receipt_id")
    expected_candidate_kind = CANDIDATE_FOR[kind]

    candidate = db.db.execute(
        "SELECT * FROM durable_memory WHERE memory_id=? AND kind=? LIMIT 1",
        (source_id, expected_candidate_kind),
    ).fetchone()
    if candidate is None:
        raise MethodAuthorityError("promotion source candidate is missing")
    if candidate["user_id"] != row["user_id"]:
        raise MethodAuthorityError("promotion source candidate user scope mismatch")
    candidate_provenance = _json_object(candidate["provenance"], field="candidate provenance")
    if candidate_provenance.get("method_schema_version") != METHOD_SCHEMA_VERSION:
        raise MethodAuthorityError("promotion source candidate has unknown schema version")

    receipt_row = db.db.execute(
        "SELECT * FROM durable_memory WHERE memory_id=? AND kind='method_receipt' LIMIT 1",
        (receipt_id,),
    ).fetchone()
    if receipt_row is None:
        raise MethodAuthorityError("promotion receipt is missing")
    if receipt_row["user_id"] != row["user_id"]:
        raise MethodAuthorityError("promotion receipt user scope mismatch")
    receipt_provenance = _json_object(receipt_row["provenance"], field="promotion receipt provenance")
    if receipt_provenance.get("method_schema_version") != METHOD_SCHEMA_VERSION:
        raise MethodAuthorityError("promotion receipt has unknown schema version")
    if receipt_provenance.get("promotion_source_memory_id") != source_id:
        raise MethodAuthorityError("promotion receipt source identity mismatch")

    receipt = _json_object(receipt_row["value"], field="promotion receipt")
    if receipt.get("action") != "PROMOTE" or receipt.get("method_memory_id") != source_id:
        raise MethodAuthorityError("promotion receipt action/source mismatch")
    receipt_episodes = _string_list(receipt.get("source_episode_ids"), field="promotion source episodes", minimum=2)

    record_episodes = record.get("source_episode_ids")
    if record_episodes is not None:
        normalized_record_episodes = _string_list(record_episodes, field="method source episodes", minimum=2)
        if normalized_record_episodes != receipt_episodes:
            raise MethodAuthorityError("promoted method/receipt episode identity mismatch")

    placeholders = ",".join("?" for _ in receipt_episodes)
    episodes = db.db.execute(
        f"SELECT episode_id,state FROM workspace_episodes WHERE episode_id IN ({placeholders})",
        tuple(receipt_episodes),
    ).fetchall()
    by_id = {str(item["episode_id"]): str(item["state"]) for item in episodes}
    if set(by_id) != set(receipt_episodes):
        raise MethodAuthorityError("promotion source episode evidence is incomplete")
    if any(by_id[episode_id] not in TERMINAL_EPISODE_STATES for episode_id in receipt_episodes):
        raise MethodAuthorityError("promotion source episode is not terminal")
