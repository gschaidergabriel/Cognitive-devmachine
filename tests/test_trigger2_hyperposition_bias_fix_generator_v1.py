"""Audit tests for tools/trigger2_hyperposition_bias_fix_generator_v1.py (run-4 prep, item 2).

Same discipline as every other generator this session: no duplicate prompts, no
duplicate ids, TRAIN/HOLDOUT disjoint at the prompt level, and labels independently
re-derived from the row's own recorded fields (domain/kind/n_branches) rather than
trusted blindly -- catches exactly the kind of label bug this file already had once
(strong_partial at n_branches==2 would have mislabeled a real collapse as PRESERVE).
"""
import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "trigger2_hyperposition_bias_fix_generator_v1.py"
spec = importlib.util.spec_from_file_location("bias_fix_gen", MODULE_PATH)
gen = importlib.util.module_from_spec(spec)
sys.modules["bias_fix_gen"] = gen
spec.loader.exec_module(gen)


@pytest.fixture(scope="module")
def rows():
    return gen.build()


def test_nonempty(rows):
    assert len(rows) > 0


def test_no_duplicate_prompts(rows):
    prompts = [r["prompt"] for r in rows]
    assert len(prompts) == len(set(prompts))


def test_no_duplicate_ids(rows):
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids))


def test_train_holdout_prompt_disjoint(rows):
    train = {r["prompt"] for r in rows if r["split"] == "TRAIN"}
    holdout = {r["prompt"] for r in rows if r["split"] == "HOLDOUT_FROZEN"}
    validation = {r["prompt"] for r in rows if r["split"] == "VALIDATION"}
    assert train.isdisjoint(holdout)
    assert train.isdisjoint(validation)
    assert holdout.isdisjoint(validation)


def test_all_five_domains_present(rows):
    domains = {r["domain"] for r in rows}
    assert domains == set(gen.DOMAINS.keys())


def test_strong_full_always_collapse_valid(rows):
    for r in rows:
        if r["kind"] == "strong_full":
            assert r["target"] == "COLLAPSE_VALID", r["id"]


def test_non_strong_full_kinds_always_preserve(rows):
    for r in rows:
        if r["kind"] in ("strong_partial", "weak", "social"):
            assert r["target"] == "PRESERVE_BRANCHES", r["id"]


def test_strong_partial_never_at_n_branches_2(rows):
    # excluding exactly 1 of 2 branches leaves exactly 1 survivor -> that would actually be
    # COLLAPSE_VALID by the family's real rule, so strong_partial must never be generated there.
    for r in rows:
        if r["kind"] == "strong_partial":
            assert r["n_branches"] > 2, r["id"]


def test_strong_full_survivor_count_is_really_one(rows):
    # Independently re-derive: parse the "names" list out of the prompt's intro sentence, then
    # confirm the excluded_list mentioned in the event sentence names exactly n_branches-1 of them
    # (i.e. exactly one name from the intro never appears as "excluded" -- the real survivor).
    for r in rows:
        if r["kind"] != "strong_full":
            continue
        pool = gen.NAME_POOLS[r["domain"]][: r["n_branches"]]
        # Isolate the text AFTER the intro sentence's own name-enumeration (which ends at the
        # first ". " following the colon) -- everything from there on is the event+question text,
        # where the survivor is never named again (only excluded names are).
        colon_idx = r["prompt"].index(":")
        period_after_names = r["prompt"].index(". ", colon_idx)
        after_intro = r["prompt"][period_after_names + 2:]
        absent_count = sum(1 for nm in pool if nm not in after_intro)
        assert absent_count == 1, (r["id"], pool, after_intro[:200])


def test_domain_name_pools_have_enough_variant_capacity(rows):
    # Sanity check on the combinatorics fix: every (kind, n_branches) combo actually used must have
    # n_branches * n_variants >= 8 (the number of distinct suffixes 1..8 the generator must fit
    # without collision) -- this is what the earlier duplicate-prompt bugs traced back to.
    for domain, cfg in gen.DOMAINS.items():
        for kind_key, variants in (("strong", cfg["strong"]), ("weak", cfg["weak"]), ("social", cfg["social"])):
            for n_branches in (2, 3, 4):
                assert n_branches * len(variants) >= 8, (domain, kind_key, n_branches, len(variants))


def test_generator_script_runs_clean(tmp_path):
    import subprocess
    result = subprocess.run([sys.executable, str(MODULE_PATH)], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr


def test_output_file_matches_build(rows):
    assert gen.OUT_PATH.exists()
    import json
    with open(gen.OUT_PATH) as f:
        file_rows = [json.loads(line) for line in f]
    assert len(file_rows) == len(rows)
    assert [r["id"] for r in file_rows] == [r["id"] for r in rows]
