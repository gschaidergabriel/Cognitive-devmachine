from __future__ import annotations

from collections import Counter, defaultdict

from tools import trigger2_b5_variable_n_equivariance_generator_v1 as b5


def test_fail_closed_audit_passes_on_current_generator():
    rows = b5.build_rows()
    report = b5.audit(rows)
    assert report["overall_pass"] is True
    assert report["failures"] == []


def test_split_counts_match_design():
    rows = b5.build_rows()
    counts = Counter(r["split"] for r in rows)
    assert dict(counts) == {"TRAIN": 940, "VALIDATION": 564, "HOLDOUT_FROZEN": 324}


def test_every_row_training_ineligible_and_method_only():
    rows = b5.build_rows()
    for r in rows:
        assert r["training_eligible"] is False
        assert r["evidence_class"] == "METHOD_ONLY"
        assert r["canonical_truth_allowed"] is False


def test_core_equivariance_property_target_invariant_across_presentation_orders():
    """The whole point of B5: for a fixed episode and queried entity, the correct
    target must not change no matter which presentation-order permutation of the
    same codebook is shown."""
    rows = b5.build_rows()
    by_key: dict[tuple[str, str], set[str]] = defaultdict(set)
    for r in rows:
        by_key[(r["episode_id"], r["queried_entity"])].add(r["target"])
    for key, targets in by_key.items():
        assert len(targets) == 1, f"{key} had non-invariant targets: {targets}"


def test_presentation_orders_are_pairwise_distinct_per_episode():
    rows = b5.build_rows()
    by_episode: dict[str, set[tuple]] = defaultdict(set)
    for r in rows:
        by_episode[r["episode_id"]].add(tuple(r["entities_presentation_order"]))
    for episode_id, orders in by_episode.items():
        rows_for_ep = [r for r in rows if r["episode_id"] == episode_id]
        n = rows_for_ep[0]["n"]
        expected = 1
        for i in range(1, n + 1):
            expected *= i
        if n not in b5.EXACT_FULL_PERM_N:
            expected = b5.SAMPLED_PERM_COUNT
        assert len(orders) == expected, f"{episode_id}: {len(orders)} != {expected}"


def test_holdout_entity_namespace_and_atom_pool_disjoint():
    rows = b5.build_rows()
    train_val_entities = {
        e for r in rows if r["split"] in ("TRAIN", "VALIDATION") for e in r["entities_presentation_order"]
    }
    hold_entities = {e for r in rows if r["split"] == "HOLDOUT_FROZEN" for e in r["entities_presentation_order"]}
    assert hold_entities and hold_entities.isdisjoint(train_val_entities)

    train_val_atoms = {
        a for r in rows if r["split"] in ("TRAIN", "VALIDATION") for a in r["true_mapping"].values()
    }
    hold_atoms = {a for r in rows if r["split"] == "HOLDOUT_FROZEN" for a in r["true_mapping"].values()}
    assert hold_atoms and hold_atoms.isdisjoint(train_val_atoms)


def test_bag_of_words_probe_uses_deduplicated_episode_entity_pairs():
    """Regression test for the CV-fold-contamination bug found during development:
    naive row-level CV let near-duplicate (eq_text, target) rows from the same
    episode leak across folds and produced a spurious 86% shortcut accuracy. The
    probe must dedupe by (episode_id, queried_entity) before cross-validating."""
    rows = b5.build_rows()
    train_rows = [r for r in rows if r["split"] == "TRAIN"]
    deduped = b5.dedupe_by_episode_entity(train_rows)
    assert len(deduped) < len(train_rows)
    report = b5.bow_shortcut_probe(rows)
    assert report["n"] == len(deduped)
    assert report["pass"] is True


def test_no_duplicate_rendered_prompts():
    rows = b5.build_rows()
    prompts = [r["prompt"] for r in rows]
    assert len(prompts) == len(set(prompts))


def test_deterministic_across_process_reruns():
    import hashlib
    import json
    import os
    import subprocess
    import sys

    payload_a = "\n".join(
        json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in b5.build_rows()
    )
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "999"
    proc = subprocess.run(
        [sys.executable, "-c", (
            "import sys; sys.path.insert(0, 'tools'); "
            "import trigger2_b5_variable_n_equivariance_generator_v1 as b5; import json; "
            "print('\\n'.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) for r in b5.build_rows()))"
        )],
        cwd=str(b5.Path(__file__).resolve().parents[1]),
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    assert hashlib.sha256(payload_a.encode()).hexdigest() == hashlib.sha256(proc.stdout.strip().encode()).hexdigest()
