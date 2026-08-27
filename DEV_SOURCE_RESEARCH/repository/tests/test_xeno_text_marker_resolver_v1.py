"""Tests for xeno_text_marker_resolver_v1 -- offline, no model. Every case here is a
real row (or a real class's exact wording) from the actual B6_DB_VS_SIM and
B6_CLAUDE_HANDOFF_REENTRY training files, and the resolvers are additionally verified
in this test to be 100% correct against the FULL real datasets (360 and 480 rows),
not just the handful of illustrative cases below."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from xeno_text_marker_resolver_v1 import resolve_db_vs_sim, resolve_claude_handoff  # noqa: E402

TRAINING_DIR = Path(__file__).resolve().parents[1] / "research_entity/claycode/training"


def test_db_vs_sim_canonical_db():
    prompt = (
        "CONTEXT: Claim under review: A direct SELECT against the canonical S0 ledger table for "
        "node_ash7 returned node_ash7.status=BLOCKED; the row was read at the current epoch and no "
        "simulation, generation or hypothesis step was involved.\nQUESTION: ..."
    )
    assert resolve_db_vs_sim(prompt) == "CANONICAL_DB"


def test_db_vs_sim_simulated_hypothesis():
    prompt = (
        "CONTEXT: Claim under review: No database query was issued for node_ash7; a model was asked "
        "to imagine what node_ash7.status might plausibly be and produced the unconfirmed guess "
        "node_ash7.status=BLOCKED, later described in prose as though it were settled.\nQUESTION: ..."
    )
    assert resolve_db_vs_sim(prompt) == "SIMULATED_HYPOTHESIS"


def test_db_vs_sim_stale_rebase_required():
    prompt = (
        "CONTEXT: Claim under review: node_ash7.status=READY was read from the ledger at epoch 41; "
        "the canonical epoch has since advanced to 44 (with 44 greater than 41) and no rebase or "
        "re-read has happened since that earlier read.\nQUESTION: ..."
    )
    assert resolve_db_vs_sim(prompt) == "STALE_REBASE_REQUIRED"


def test_db_vs_sim_unrecognized_returns_none():
    assert resolve_db_vs_sim("some unrelated free-form prompt with no markers at all") is None


def test_claude_handoff_claude_assertion():
    prompt = (
        "CONTEXT: Statement under review: Claude Code stated in natural language that the node_ash7 "
        "migration succeeded and that all checks passed; it phrased this confidently, but no external "
        "tool receipt and no ledger row is attached to the statement.\nQUESTION: ..."
    )
    assert resolve_claude_handoff(prompt) == "CLAUDE_ASSERTION"


def test_claude_handoff_external_tool_receipt():
    prompt = (
        "CONTEXT: Statement under review: A tool invocation against node_ash7 produced the receipt "
        "`test:0:5426`, an exit code and a description attached directly to the run, independent of "
        "any prose summary of it.\nQUESTION: ..."
    )
    assert resolve_claude_handoff(prompt) == "EXTERNAL_TOOL_RECEIPT"


def test_claude_handoff_canonical_ledger_evidence():
    prompt = (
        "CONTEXT: Statement under review: Ledger row `effect:6889` for node_ash7 is already committed "
        "and hash-verified in the canonical S0 store, independent of whatever was said about it "
        "afterward.\nQUESTION: ..."
    )
    assert resolve_claude_handoff(prompt) == "CANONICAL_LEDGER_EVIDENCE"


def test_claude_handoff_stale_mismatched_handoff():
    prompt = (
        "CONTEXT: Statement under review: The ZECP14 result for node_ash7 references handoff "
        "generation 12, but the current ZECP13 lease generation is 13 (with 12 not equal to 13); the "
        "handoff and the result do not bind to the same generation.\nQUESTION: ..."
    )
    assert resolve_claude_handoff(prompt) == "STALE_MISMATCHED_HANDOFF"


def test_claude_handoff_unrecognized_returns_none():
    assert resolve_claude_handoff("some unrelated free-form prompt with no markers at all") is None


def test_resolve_db_vs_sim_100pct_against_full_real_dataset():
    path = TRAINING_DIR / "TRIGGER2_B6_DB_VS_SIM_CANDIDATE_V1.jsonl"
    rows = [json.loads(line) for line in open(path)]
    assert len(rows) == 360
    wrong = [r["id"] for r in rows if resolve_db_vs_sim(r["prompt"]) != r["target"]]
    assert wrong == [], f"{len(wrong)}/{len(rows)} misclassified: {wrong[:5]}"


def test_resolve_claude_handoff_100pct_against_full_real_dataset():
    path = TRAINING_DIR / "TRIGGER2_B6_CLAUDE_HANDOFF_REENTRY_CANDIDATE_V1.jsonl"
    rows = [json.loads(line) for line in open(path)]
    assert len(rows) == 480
    wrong = [r["id"] for r in rows if resolve_claude_handoff(r["prompt"]) != r["target"]]
    assert wrong == [], f"{len(wrong)}/{len(rows)} misclassified: {wrong[:5]}"
