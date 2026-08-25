import collections

from tools import trigger1_cross_task_factorial_cases_v3 as g


def test_cross_task_factorial_bundle_v3():
    b = g.build_bundle()
    assert b["schema"] == g.SCHEMA
    assert b["lexical_disjointness"]["pass"] is True
    assert b["lexical_disjointness"]["content_overlap"] == []
    assert b["model_executed"] is False
    assert b["runtime_credit_minted"] is False
    assert [x["task_family"] for x in b["calibration"]] == list(g.CAL_FAMILIES)
    assert [x["task_family"] for x in b["holdout"]] == list(g.HOLD_FAMILIES)

    prompt_hashes = []
    for split in ("calibration", "holdout"):
        for fam in b[split]:
            assert fam["case_count"] == 36
            cells = collections.Counter(
                (x["semantic_target"], x["output_code_identity"], x["probe_query_negated"])
                for x in fam["cases"]
            )
            assert len(cells) == 18
            assert set(cells.values()) == {2}

            pairs = collections.defaultdict(set)
            for x in fam["cases"]:
                assert x["codebook"][x["semantic_target"]] == x["output_code_identity"]
                assert x["model_facing_explicit_semantic_labels"] is False
                pairs[x["polarity_pair_id"]].add(x["probe_query_negated"])
                low = set(g.re.findall(r"[a-z_]+", x["prompt"].lower()))
                assert not [w for w in g.BANNED_MODEL_FACING if w in low]
                prompt_hashes.append(x["prompt_sha256"])

            assert set(map(frozenset, pairs.values())) == {frozenset({False, True})}

    assert len(prompt_hashes) == len(set(prompt_hashes)) == 216
