#!/usr/bin/env python3
"""Promote one passing exact-current Forge->Distillery runtime witness into live Distillery.

This is a deterministic, provider-independent successor to the disposable runtime gate.
It does not weaken Forge evidence admission and does not append a second Forge ledger.
Instead it re-validates the nested evidence-qualified Forge evaluation from a PASS witness
and feeds exactly that one row through the existing Distillery admission code against the
configured canonical Distillery SQLite database.

The live effect is additionally bound to the GitHub Actions execution context that owns the
canonical workflow: exact run id, event class, canonical-main source selection, source SHA
and source tree. The promoter records the SHA-256 of the exact pre-publication gate bytes;
the later repository publication must preserve and verify the same binding.

Idempotency is bound to the bridge's versioned replay-stable execution identity, not to byte
identity of the full evaluation envelope. Existing databases are schema-migrated through the
same bridge before replay-presence inspection, so historical ambiguous v1 hashes cannot make
a previously admitted execution look absent after the replay-identity ABI advances to v2.
A first promotion must add exactly one packet and nonzero accepted-dataset tokens. A
semantic envelope replay must add zero packets/tokens after SQLite reopen. Reusing the same
stable execution identity with changed measured evidence must fail closed as a replay-identity
conflict. Existing prior promotion is accepted only when the same v2 replay identity is
already present with nonzero packet tokens and all replay/conflict guards remain zero-delta.

No provider/network I/O occurs here. This tool grants no whole-product, HCU, J-Space,
canonical-semantics or training credit; it only closes the measured Forge->Distillery
execution-evidence path at its exact source and workflow identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
from typing import Any

import ingest_forge_accepts_into_distillery as bridge
from forge_evidence_credit_871 import evidence_reason

PASS_SCHEMA = "CLAY_FORGE_DISTILLERY_EXACT_CURRENT_RUNTIME_GATE/v2"
PASS_STATUS = "PASS_EXACT_CURRENT_1_TO_1_TO_NONZERO_REPLAY_ZERO"
CANONICAL_SOURCE_SELECTION = "CANONICAL_MAIN_AT_RUNNER_CHECKOUT_TIME"
ALLOWED_WORKFLOW_EVENTS = {"push", "pull_request", "workflow_dispatch"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
RUN_ID = re.compile(r"^[1-9][0-9]*$")


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


def validate_workflow_context(
    result: dict[str, Any],
    *,
    expected_source_sha: str,
    expected_source_tree: str,
    github_run_id: str,
    github_event_name: str,
    source_selection: str,
) -> dict[str, str]:
    expected_source_sha = expected_source_sha.strip().lower()
    expected_source_tree = expected_source_tree.strip().lower()
    github_run_id = str(github_run_id).strip()
    github_event_name = str(github_event_name).strip()
    source_selection = str(source_selection).strip()

    _require(bool(HEX40.fullmatch(expected_source_sha)), "EXPECTED_SOURCE_SHA_INVALID")
    _require(bool(HEX40.fullmatch(expected_source_tree)), "EXPECTED_SOURCE_TREE_INVALID")
    _require(bool(RUN_ID.fullmatch(github_run_id)), "GITHUB_RUN_ID_INVALID")
    _require(github_event_name in ALLOWED_WORKFLOW_EVENTS, "GITHUB_EVENT_NOT_ALLOWED")
    _require(source_selection == CANONICAL_SOURCE_SELECTION, "SOURCE_SELECTION_NOT_CANONICAL")
    _require(result.get("source_sha") == expected_source_sha, "WORKFLOW_SOURCE_SHA_MISMATCH")
    _require(result.get("source_tree") == expected_source_tree, "WORKFLOW_SOURCE_TREE_MISMATCH")
    return {
        "github_run_id": github_run_id,
        "github_event_name": github_event_name,
        "execution_source_sha": expected_source_sha,
        "execution_source_tree": expected_source_tree,
        "source_selection": source_selection,
    }


def validate_github_actions_environment(*, github_run_id: str, github_event_name: str) -> None:
    _require(os.environ.get("GITHUB_ACTIONS") == "true", "GITHUB_ACTIONS_CONTEXT_REQUIRED")
    _require(os.environ.get("GITHUB_RUN_ID") == str(github_run_id), "GITHUB_RUN_ID_ENV_MISMATCH")
    _require(os.environ.get("GITHUB_EVENT_NAME") == str(github_event_name), "GITHUB_EVENT_ENV_MISMATCH")


def inspect_db(
    db: Path,
    evaluation_sha256: str,
    replay_identity_sha256: str | None = None,
) -> dict[str, Any]:
    if not db.exists():
        return {
            "db_exists": False,
            "evaluation_present": False,
            "replay_identity_present": False,
            "replay_identity_column": None,
            "packet_id": None,
            "packet_tokens": 0,
            "accepted_dataset_tokens_counter": 0,
        }
    con = sqlite3.connect(db, timeout=30)
    try:
        # Schema migration/backfill is part of deterministic inspection. It changes no
        # packet/counter credit, but it prevents an old v1 hash from hiding an already
        # admitted semantic execution when current code computes the v2 hash.
        bridge.ensure_schema(con)
        tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        counter = 0
        if "counters" in tables:
            c = con.execute("SELECT value FROM counters WHERE key='accepted_dataset_tokens'").fetchone()
            counter = int(c[0]) if c else 0

        exact_row = None
        replay_row = None
        replay_column = None
        if "forge_execution_ingest" in tables:
            exact_row = con.execute(
                "SELECT packet_id, approx_tokens FROM forge_execution_ingest WHERE evaluation_sha256=?",
                (evaluation_sha256,),
            ).fetchone()
            columns = {str(row[1]) for row in con.execute("PRAGMA table_info(forge_execution_ingest)")}
            if replay_identity_sha256:
                if "execution_replay_identity_v2_sha256" in columns:
                    replay_column = "execution_replay_identity_v2_sha256"
                elif "execution_replay_identity_sha256" in columns:
                    replay_column = "execution_replay_identity_sha256"
                if replay_column:
                    replay_row = con.execute(
                        f"SELECT packet_id, approx_tokens FROM forge_execution_ingest WHERE {replay_column}=?",
                        (replay_identity_sha256,),
                    ).fetchone()
        selected = replay_row or exact_row
        return {
            "db_exists": True,
            "evaluation_present": exact_row is not None,
            "replay_identity_present": replay_row is not None if replay_identity_sha256 else exact_row is not None,
            "replay_identity_column": replay_column,
            "packet_id": selected[0] if selected else None,
            "packet_tokens": int(selected[1]) if selected else 0,
            "accepted_dataset_tokens_counter": counter,
        }
    finally:
        con.close()


def _semantic_replay(evaluation: dict[str, Any]) -> dict[str, Any]:
    replay = dict(evaluation)
    replay["evaluated_at"] = "2099-01-01T00:00:00+00:00"
    replay["delta_id"] = str(evaluation.get("delta_id") or "") + "-semantic-replay-envelope"
    replay["proposal_hypothesis"] = "semantic replay candidate narration mutation"
    replay["falsifier"] = "semantic replay candidate falsifier mutation"
    return replay


def _measured_conflict(evaluation: dict[str, Any]) -> dict[str, Any]:
    conflict = dict(evaluation)
    conflict["evaluated_at"] = "2099-01-01T00:00:01+00:00"
    conflict["delta_id"] = str(evaluation.get("delta_id") or "") + "-measured-conflict-envelope"
    conflict["relative_improvement_pct"] = float(evaluation["relative_improvement_pct"]) + 1.0
    conflict["proposal_hypothesis"] = "measured conflict negative control"
    return conflict


def promote(
    gate_result: Path,
    expected_source_sha: str,
    distillery_db: Path,
    *,
    expected_source_tree: str,
    github_run_id: str,
    github_event_name: str,
    source_selection: str,
) -> dict[str, Any]:
    raw = gate_result.read_bytes()
    result = json.loads(raw.decode("utf-8"))
    if not isinstance(result, dict):
        raise PromotionError("GATE_RESULT_NOT_OBJECT")
    evaluation = validate_gate_result(result, expected_source_sha)
    context = validate_workflow_context(
        result,
        expected_source_sha=expected_source_sha,
        expected_source_tree=expected_source_tree,
        github_run_id=github_run_id,
        github_event_name=github_event_name,
        source_selection=source_selection,
    )
    evaluation_sha = bridge.digest_json(evaluation)
    replay_identity_sha = bridge.digest_json(bridge.execution_replay_identity(evaluation))
    measured_evidence_sha = bridge.digest_json(bridge.measured_evidence_identity(evaluation))
    before = inspect_db(distillery_db, evaluation_sha, replay_identity_sha)

    semantic_replay_evaluation = _semantic_replay(evaluation)
    _require(
        bridge.digest_json(bridge.execution_replay_identity(semantic_replay_evaluation)) == replay_identity_sha,
        "SEMANTIC_REPLAY_IDENTITY_CHANGED",
    )
    _require(
        bridge.digest_json(bridge.measured_evidence_identity(semantic_replay_evaluation)) == measured_evidence_sha,
        "SEMANTIC_REPLAY_MEASURED_EVIDENCE_CHANGED",
    )

    measured_conflict_evaluation = _measured_conflict(evaluation)
    _require(
        bridge.digest_json(bridge.execution_replay_identity(measured_conflict_evaluation)) == replay_identity_sha,
        "MEASURED_CONFLICT_REPLAY_IDENTITY_CHANGED",
    )
    _require(
        bridge.digest_json(bridge.measured_evidence_identity(measured_conflict_evaluation)) != measured_evidence_sha,
        "MEASURED_CONFLICT_DID_NOT_CHANGE_EVIDENCE",
    )

    with tempfile.TemporaryDirectory(prefix="clay-forge-distillery-promote-") as td:
        one_row = Path(td) / "qualified.jsonl"
        semantic_row = Path(td) / "semantic-replay.jsonl"
        conflict_row = Path(td) / "measured-conflict.jsonl"
        one_row.write_text(json.dumps(evaluation, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        semantic_row.write_text(json.dumps(semantic_replay_evaluation, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        conflict_row.write_text(json.dumps(measured_conflict_evaluation, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

        # Each bridge call opens and closes SQLite independently. The semantic replay
        # therefore proves persistence across a DB reopen rather than one connection.
        first = bridge.ingest(one_row, distillery_db)
        replay = bridge.ingest(semantic_row, distillery_db)
        measured_conflict = bridge.ingest(conflict_row, distillery_db)

    after = inspect_db(distillery_db, evaluation_sha, replay_identity_sha)
    before_tokens = int(before.get("accepted_dataset_tokens_counter") or 0)
    first_tokens = int(first.get("accepted_dataset_tokens_counter") or 0)
    replay_tokens = int(replay.get("accepted_dataset_tokens_counter") or 0)
    conflict_tokens = int(measured_conflict.get("accepted_dataset_tokens_counter") or 0)
    was_present = bool(before.get("replay_identity_present"))

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

    _require(int(replay.get("admitted") or 0) == 0, "LIVE_SEMANTIC_REPLAY_ADDED_PACKET")
    _require(int(replay.get("duplicates") or 0) == 1, "LIVE_SEMANTIC_REPLAY_DUPLICATE_NOT_ONE")
    _require(replay_tokens == first_tokens, "LIVE_SEMANTIC_REPLAY_TOKEN_DELTA_NONZERO")
    _require(int(measured_conflict.get("admitted") or 0) == 0, "LIVE_MEASURED_CONFLICT_ADMITTED")
    _require(int(measured_conflict.get("duplicates") or 0) == 0, "LIVE_MEASURED_CONFLICT_CLASSIFIED_DUPLICATE")
    _require(
        int(measured_conflict.get("rejected", {}).get("REPLAY_IDENTITY_CONFLICT") or 0) == 1,
        "LIVE_MEASURED_CONFLICT_NOT_FAIL_CLOSED",
    )
    _require(conflict_tokens == replay_tokens, "LIVE_MEASURED_CONFLICT_TOKEN_DELTA_NONZERO")
    _require(bool(after.get("replay_identity_present")), "LIVE_REPLAY_IDENTITY_NOT_PERSISTED")
    _require(int(after.get("packet_tokens") or 0) > 0, "LIVE_PACKET_TOKENS_NOT_POSITIVE")
    _require(int(after.get("accepted_dataset_tokens_counter") or 0) == conflict_tokens, "LIVE_COUNTER_POSTCHECK_MISMATCH")

    return {
        "schema": "CLAY_FORGE_DISTILLERY_LIVE_PROMOTION/v1",
        "status": "PASS",
        "outcome": outcome,
        "source_sha": expected_source_sha,
        **context,
        "gate_result_sha256": hashlib.sha256(raw).hexdigest(),
        "evaluation_sha256": evaluation_sha,
        "execution_replay_identity_schema": bridge.REPLAY_IDENTITY_SCHEMA,
        "execution_replay_identity_sha256": replay_identity_sha,
        "measured_evidence_schema": bridge.MEASURED_EVIDENCE_SCHEMA,
        "measured_evidence_sha256": measured_evidence_sha,
        "distillery_db": str(distillery_db),
        "before": before,
        "first": first,
        "replay": replay,
        "semantic_replay": replay,
        "measured_conflict": measured_conflict,
        "after": after,
        "first_token_delta": first_tokens - before_tokens,
        "replay_token_delta": replay_tokens - first_tokens,
        "measured_conflict_token_delta": conflict_tokens - replay_tokens,
        "semantic_replay_db_reopen_proven": True,
        "replay_abi_v2_migration_checked": True,
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
    ap.add_argument("--expected-source-tree", required=True)
    ap.add_argument("--github-run-id", required=True)
    ap.add_argument("--github-event-name", required=True)
    ap.add_argument("--source-selection", required=True)
    ap.add_argument("--distillery-db", type=Path, default=bridge.DEFAULT_DISTILLERY_DB)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        validate_github_actions_environment(
            github_run_id=args.github_run_id,
            github_event_name=args.github_event_name,
        )
        out = promote(
            args.gate_result,
            args.expected_source_sha.strip().lower(),
            args.distillery_db,
            expected_source_tree=args.expected_source_tree.strip().lower(),
            github_run_id=args.github_run_id,
            github_event_name=args.github_event_name,
            source_selection=args.source_selection,
        )
        rc = 0
    except Exception as exc:
        out = {
            "schema": "CLAY_FORGE_DISTILLERY_LIVE_PROMOTION/v1",
            "status": "BLOCKED",
            "reason": f"{type(exc).__name__}:{str(exc)[:1000]}",
            "source_sha": args.expected_source_sha.strip().lower(),
            "github_run_id": str(args.github_run_id),
            "github_event_name": str(args.github_event_name),
            "execution_source_sha": args.expected_source_sha.strip().lower(),
            "execution_source_tree": args.expected_source_tree.strip().lower(),
            "source_selection": str(args.source_selection),
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
