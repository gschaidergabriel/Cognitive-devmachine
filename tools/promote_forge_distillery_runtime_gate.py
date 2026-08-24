#!/usr/bin/env python3
"""Promote one passing exact-current Forge->Distillery runtime witness into live Distillery.

This is a deterministic, provider-independent successor to the disposable runtime gate.
It does not weaken Forge evidence admission and does not append a second Forge ledger.
Instead it re-validates the nested evidence-qualified Forge evaluation from a PASS receipt
and feeds exactly that one row through the existing Distillery admission code against the
configured canonical Distillery SQLite database.

The operation is idempotent by the existing evaluation digest. A first promotion must add
exactly one packet and nonzero accepted-dataset tokens. An identical retry must add zero
packets/tokens and report one duplicate. Existing prior promotion is accepted only when the
same digest is already present with nonzero packet tokens and the retry remains +0.

No provider/network I/O occurs here. This tool grants no whole-product, HCU, J-Space,
canonical-semantics or training credit; it only closes the measured Forge->Distillery
execution-evidence path at its exact source identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import tempfile
from typing import Any

import ingest_forge_accepts_into_distillery as bridge
from forge_evidence_credit_871 import evidence_reason

PASS_SCHEMA = "CLAY_FORGE_DISTILLERY_EXACT_CURRENT_RUNTIME_GATE/v2"
PASS_STATUS = "PASS_EXACT_CURRENT_1_TO_1_TO_NONZERO_REPLAY_ZERO"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


class PromotionError(RuntimeError):
    pass


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise PromotionError(reason)


def load_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise PromotionError("GATE_RESULT_NOT_OBJECT")
    return obj


def validate_gate_result(result: dict[str, Any], expected_source_sha: str) -> dict[str, Any]:
    expected_source_sha = expected_source_sha.strip().lower()
    _require(bool(HEX40.fullmatch(expected_source_sha)), "EXPECTED_SOURCE_SHA_INVALID")
    _require(result.get("schema") == PASS_SCHEMA, "WRONG_GATE_SCHEMA")
    _require(result.get("pass") is True, "GATE_NOT_PASS")
    _require(result.get("status") == PASS_STATUS, "WRONG_GATE_PASS_STATUS")
    _require(result.get("source_sha") == expected_source_sha, "GATE_SOURCE_SHA_MISMATCH")
    if result.get("execution_source_sha") is not None:
        _require(result.get("execution_source_sha") == expected_source_sha, "EXECUTION_SOURCE_SHA_MISMATCH")
    _require(result.get("network_used") is False, "GATE_NETWORK_FENCE_MISSING")
    _require(int(result.get("provider_calls") or 0) == 0, "GATE_PROVIDER_CALLS_NONZERO")
    _require(int(result.get("paid_fallback_attempt_count") or 0) == 0, "GATE_PAID_FALLBACK_NONZERO")

    witness = result.get("acceptance_witness")
    _require(isinstance(witness, dict), "ACCEPTANCE_WITNESS_MISSING")
    _require(witness.get("nominal_without_execution_admission_rejected") is True, "NOMINAL_NEGATIVE_CONTROL_NOT_REJECTED")
    _require(int(witness.get("exact_evidence_qualified_accept") or 0) == 1, "QUALIFIED_ACCEPT_NOT_EXACTLY_ONE")
    _require(int(witness.get("first_new_distillery_packets") or 0) == 1, "DISPOSABLE_FIRST_PACKET_NOT_ONE")
    first_tokens = int(witness.get("accepted_dataset_tokens_after_first") or 0)
    replay_tokens = int(witness.get("accepted_dataset_tokens_after_replay") or 0)
    _require(first_tokens > 0, "DISPOSABLE_DATASET_TOKENS_NOT_POSITIVE")
    _require(int(witness.get("replay_new_packets") or 0) == 0, "DISPOSABLE_REPLAY_ADDED_PACKET")
    _require(int(witness.get("replay_duplicates") or 0) == 1, "DISPOSABLE_REPLAY_DUPLICATE_NOT_ONE")
    _require(int(witness.get("token_delta_on_replay") or 0) == 0, "DISPOSABLE_REPLAY_TOKEN_DELTA_NONZERO")
    _require(replay_tokens == first_tokens, "DISPOSABLE_REPLAY_TOKEN_COUNTER_CHANGED")

    first = result.get("distillery_first")
    replay = result.get("distillery_replay")
    _require(isinstance(first, dict) and isinstance(replay, dict), "DISPOSABLE_DISTILLERY_SUMMARIES_MISSING")
    _require(int(first.get("admitted") or 0) == 1, "DISPOSABLE_FIRST_SUMMARY_NOT_ONE")
    _require(int(first.get("accepted_dataset_tokens_counter") or 0) == first_tokens, "DISPOSABLE_FIRST_TOKEN_SUMMARY_MISMATCH")
    _require(int(replay.get("admitted") or 0) == 0, "DISPOSABLE_REPLAY_SUMMARY_ADMITTED")
    _require(int(replay.get("duplicates") or 0) == 1, "DISPOSABLE_REPLAY_SUMMARY_DUPLICATE_MISMATCH")
    _require(int(replay.get("accepted_dataset_tokens_counter") or 0) == replay_tokens, "DISPOSABLE_REPLAY_TOKEN_SUMMARY_MISMATCH")

    evaluation = result.get("forge_evaluation")
    _require(isinstance(evaluation, dict), "FORGE_EVALUATION_MISSING")
    _require(evaluation.get("source_repo_head") == expected_source_sha, "FORGE_SOURCE_HEAD_MISMATCH")
    _require(evaluation.get("evaluation_repo_head") == expected_source_sha, "FORGE_EVALUATION_HEAD_MISMATCH")
    _require(str(evaluation.get("status", "")).lower() == "accepted", "FORGE_EVALUATION_NOT_ACCEPTED")
    qualified, reason = evidence_reason(evaluation)
    _require(qualified and reason == "EVIDENCE_QUALIFIED_ACCEPT", "FORGE_EVIDENCE_NOT_QUALIFIED:" + reason)
    return evaluation


def inspect_db(db: Path, evaluation_sha256: str) -> dict[str, Any]:
    if not db.exists():
        return {
            "db_exists": False,
            "evaluation_present": False,
            "packet_id": None,
            "packet_tokens": 0,
            "accepted_dataset_tokens_counter": 0,
        }
    con = sqlite3.connect(db, timeout=30)
    try:
        tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "forge_execution_ingest" not in tables:
            return {
                "db_exists": True,
                "evaluation_present": False,
                "packet_id": None,
                "packet_tokens": 0,
                "accepted_dataset_tokens_counter": 0,
            }
        row = con.execute(
            "SELECT packet_id, approx_tokens FROM forge_execution_ingest WHERE evaluation_sha256=?",
            (evaluation_sha256,),
        ).fetchone()
        counter = 0
        if "counters" in tables:
            c = con.execute("SELECT value FROM counters WHERE key='accepted_dataset_tokens'").fetchone()
            counter = int(c[0]) if c else 0
        return {
            "db_exists": True,
            "evaluation_present": row is not None,
            "packet_id": row[0] if row else None,
            "packet_tokens": int(row[1]) if row else 0,
            "accepted_dataset_tokens_counter": counter,
        }
    finally:
        con.close()


def promote(gate_result: Path, expected_source_sha: str, distillery_db: Path) -> dict[str, Any]:
    raw = gate_result.read_bytes()
    result = json.loads(raw.decode("utf-8"))
    if not isinstance(result, dict):
        raise PromotionError("GATE_RESULT_NOT_OBJECT")
    evaluation = validate_gate_result(result, expected_source_sha)
    evaluation_sha = bridge.digest_json(evaluation)
    before = inspect_db(distillery_db, evaluation_sha)

    with tempfile.TemporaryDirectory(prefix="clay-forge-distillery-promote-") as td:
        one_row = Path(td) / "qualified.jsonl"
        one_row.write_text(json.dumps(evaluation, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        first = bridge.ingest(one_row, distillery_db)
        replay = bridge.ingest(one_row, distillery_db)

    after = inspect_db(distillery_db, evaluation_sha)
    before_tokens = int(before.get("accepted_dataset_tokens_counter") or 0)
    first_tokens = int(first.get("accepted_dataset_tokens_counter") or 0)
    replay_tokens = int(replay.get("accepted_dataset_tokens_counter") or 0)
    was_present = bool(before.get("evaluation_present"))

    if was_present:
        _require(int(first.get("admitted") or 0) == 0, "EXISTING_PROMOTION_REINGEST_ADMITTED")
        _require(int(first.get("duplicates") or 0) == 1, "EXISTING_PROMOTION_NOT_DUPLICATE")
        _require(first_tokens == before_tokens, "EXISTING_PROMOTION_CHANGED_TOKEN_COUNTER")
        outcome = "ALREADY_PROMOTED_IDEMPOTENT"
    else:
        _require(int(first.get("admitted") or 0) == 1, "LIVE_FIRST_PROMOTION_NOT_ONE")
        _require(int(first.get("duplicates") or 0) == 0, "LIVE_FIRST_PROMOTION_UNEXPECTED_DUPLICATE")
        _require(first_tokens > before_tokens, "LIVE_FIRST_PROMOTION_TOKEN_DELTA_NOT_POSITIVE")
        outcome = "PROMOTED_NEW_PACKET"

    _require(int(replay.get("admitted") or 0) == 0, "LIVE_REPLAY_ADDED_PACKET")
    _require(int(replay.get("duplicates") or 0) == 1, "LIVE_REPLAY_DUPLICATE_NOT_ONE")
    _require(replay_tokens == first_tokens, "LIVE_REPLAY_TOKEN_DELTA_NONZERO")
    _require(bool(after.get("evaluation_present")), "LIVE_EVALUATION_NOT_PERSISTED")
    _require(int(after.get("packet_tokens") or 0) > 0, "LIVE_PACKET_TOKENS_NOT_POSITIVE")
    _require(int(after.get("accepted_dataset_tokens_counter") or 0) == replay_tokens, "LIVE_COUNTER_POSTCHECK_MISMATCH")

    return {
        "schema": "CLAY_FORGE_DISTILLERY_LIVE_PROMOTION/v1",
        "status": "PASS",
        "outcome": outcome,
        "source_sha": expected_source_sha,
        "gate_result_sha256": hashlib.sha256(raw).hexdigest(),
        "evaluation_sha256": evaluation_sha,
        "distillery_db": str(distillery_db),
        "before": before,
        "first": first,
        "replay": replay,
        "after": after,
        "first_token_delta": first_tokens - before_tokens,
        "replay_token_delta": replay_tokens - first_tokens,
        "network_used": False,
        "provider_calls": 0,
        "paid_fallback_attempt_count": 0,
        "canonical_truth_credit": 0,
        "whole_product_credit": 0,
        "hcu_full_credit": 0,
        "jspace_credit": 0,
        "training_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-result", type=Path, required=True)
    ap.add_argument("--expected-source-sha", required=True)
    ap.add_argument("--distillery-db", type=Path, default=bridge.DEFAULT_DISTILLERY_DB)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        out = promote(args.gate_result, args.expected_source_sha.strip().lower(), args.distillery_db)
        rc = 0
    except Exception as exc:
        out = {
            "schema": "CLAY_FORGE_DISTILLERY_LIVE_PROMOTION/v1",
            "status": "BLOCKED",
            "reason": f"{type(exc).__name__}:{str(exc)[:1000]}",
            "source_sha": args.expected_source_sha.strip().lower(),
            "distillery_db": str(args.distillery_db),
            "network_used": False,
            "provider_calls": 0,
            "paid_fallback_attempt_count": 0,
            "canonical_truth_credit": 0,
            "whole_product_credit": 0,
            "hcu_full_credit": 0,
            "jspace_credit": 0,
            "training_credit": 0,
        }
        rc = 1
    args.output.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
