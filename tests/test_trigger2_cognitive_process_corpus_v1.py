from collections import Counter, defaultdict

from tools import entityos_hcu_trainingtrace_candidate_gate_v1 as gate
from tools import trigger2_cognitive_process_corpus_v1 as corpus


def _rows():
    return list(corpus.rows())


def test_exact_balanced_seed_shape():
    rows = _rows()
    report = corpus.audit(rows)
    assert report["pass"], report
    assert len(rows) == 64
    assert report["families"] == 16
    assert report["variant_counts"] == {
        "PROTOCOL": 16,
        "HARD_NEGATIVE": 16,
        "UNKNOWN": 16,
        "COUNTERFACTUAL": 16,
    }
    assert report["split_counts"] == {"TRAIN": 48, "VALIDATION": 8, "HOLDOUT": 8}


def test_every_row_passes_current_candidate_gate():
    failures = []
    for row in _rows():
        result = gate.adjudicate(row)
        if not result["candidate_admission_pass"]:
            failures.append((row["family_id"], row["variant"], result["failures"]))
    assert not failures, failures


def test_family_siblings_never_cross_split():
    splits = defaultdict(set)
    variants = defaultdict(set)
    for row in _rows():
        splits[row["family_id"]].add(row["split"])
        variants[row["family_id"]].add(row["variant"])
    assert all(len(v) == 1 for v in splits.values())
    assert all(v == {"PROTOCOL", "HARD_NEGATIVE", "UNKNOWN", "COUNTERFACTUAL"} for v in variants.values())


def test_no_row_mints_truth_effect_or_training_credit():
    rows = _rows()
    assert all(row["canonical_truth_allowed"] is False for row in rows)
    assert all(row["direct_effect_authority"] is False for row in rows)
    assert all("NO_ACCEPTED_DATASET_OR_RUNTIME_OR_TRAINING_CREDIT" in row["credit_boundary"] for row in rows)
    assert all(row["target_type"] not in gate.JSPACE_TARGET_TYPES for row in rows)


def test_not_a_trivial_always_reject_dataset():
    counts = Counter(row["variant"] for row in _rows())
    assert counts["HARD_NEGATIVE"] == 16
    assert counts["PROTOCOL"] == 16
    assert counts["UNKNOWN"] == 16
    assert counts["COUNTERFACTUAL"] == 16
