"""Full-dataset verification for xeno_hyperposition_resolver_v1 -- both real
Hyperposition training files checked in full (1496 rows combined), not a sample.
Offline, no model, no network."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from xeno_hyperposition_resolver_v1 import resolve_hyperposition  # noqa: E402

TRAINING_DIR = Path(__file__).resolve().parents[1] / "research_entity/claycode/training"


def test_original_family_100pct():
    path = TRAINING_DIR / "TRIGGER2_B6_HYPERPOSITION_EVIDENCE_AUTHORITY_CANDIDATE_V1.jsonl"
    rows = [json.loads(line) for line in open(path)]
    assert len(rows) == 600
    wrong = [r["id"] for r in rows if resolve_hyperposition(r["prompt"]) != r["target"]]
    assert wrong == [], f"{len(wrong)}/{len(rows)} misclassified: {wrong[:5]}"


def test_expansion_family_100pct():
    path = TRAINING_DIR / "TRIGGER2_B6_HYPERPOSITION_EXPANSION_CANDIDATE_V1.jsonl"
    rows = [json.loads(line) for line in open(path)]
    assert len(rows) == 896
    wrong = [r["id"] for r in rows if resolve_hyperposition(r["prompt"]) != r["target"]]
    assert wrong == [], f"{len(wrong)}/{len(rows)} misclassified: {wrong[:5]}"


def test_the_exact_run3_residual_failure_case_now_resolves_correctly():
    """The concrete miss reported in RUN3_TEST_RESULTS_20260827.json: a 4-branch
    case where the discriminator only excludes ONE branch (3 survivors remain) --
    the model said COLLAPSE_VALID, wrong; correct answer is PRESERVE_BRANCHES."""
    prompt = (
        "CONTEXT: 4 Hyperposition branches for node_hazel9 remain open: branch A, "
        "branch B, branch C, branch D, each still holding supporting evidence with "
        "none formally falsified. A new discriminator test was run against "
        "node_hazel9 and its result FORMALLY EXCLUDES branch A -- this is real "
        "falsifying evidence, not a preference.\n"
        "QUESTION: Should the open branches be preserved or may they be validly "
        "collapsed: PRESERVE_BRANCHES or COLLAPSE_VALID?\n"
        "Respond with exactly one label: PRESERVE_BRANCHES or COLLAPSE_VALID."
    )
    assert resolve_hyperposition(prompt) == "PRESERVE_BRANCHES"


def test_full_exclusion_to_one_survivor_collapses():
    prompt = (
        "CONTEXT: 4 Hyperposition branches for node_test1 remain open: branch A, "
        "branch B, branch C, branch D, each still holding supporting evidence with "
        "none formally falsified. A new discriminator test was run against "
        "node_test1 and its result FORMALLY EXCLUDES branch A, branch B, branch C "
        "-- this is real falsifying evidence, not a preference.\n"
        "QUESTION: ..."
    )
    assert resolve_hyperposition(prompt) == "COLLAPSE_VALID"


def test_unrecognized_prompt_returns_none():
    assert resolve_hyperposition("no branch structure here at all") is None
