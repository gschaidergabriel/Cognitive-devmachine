import copy
import hashlib
import importlib.util
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "tools" / "trigger2_factorized_challenge_guard_v1.py"
spec = importlib.util.spec_from_file_location("guard", P)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def _h(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _row(split, family, prov, template, lexicon, atoms, surface, axis=None):
    return {
        "split": split,
        "family_id": family,
        "provenance_ancestry_id": prov,
        "challenge_axis": axis,
        "curriculum": {
            "template_family": template,
            "lexical_family": lexicon,
            "atom_token_ids": atoms,
            "semantic_surface_sha256": _h(surface),
        },
    }


def _valid_rows():
    return [
        _row("TRAIN", "ftr1", "ptr1", "T1", "L1", [1, 2, 3], "train1"),
        _row("TRAIN", "ftr2", "ptr2", "T2", "L2", [4, 5, 6], "train2"),
        _row("VALIDATION", "fv", "pv", "TV", "LV", [7, 8, 9], "val1"),
        _row("HOLDOUT", "hs", "ps", "T1", "L1", [10, 11, 12], "hs", "SYMBOL_ONLY"),
        _row("HOLDOUT", "ht", "pt", "T3", "L1", [1, 2, 3], "ht", "TEMPLATE_ONLY"),
        _row("HOLDOUT", "hl", "pl", "T2", "L3", [4, 5, 6], "hl", "LEXICON_ONLY"),
        _row("HOLDOUT", "hj", "pj", "T4", "L4", [13, 14, 15], "hj", "JOINT_OOD"),
    ]


def test_factorized_axes_pass_when_only_intended_factor_changes():
    result = guard.adjudicate(_valid_rows())
    assert result["pass"], result
    assert result["challenge_axes_present"] == ["JOINT_OOD", "LEXICON_ONLY", "SYMBOL_ONLY", "TEMPLATE_ONLY"]


def test_symbol_only_requires_unseen_atoms_but_familiar_template_and_lexicon():
    rows = _valid_rows()
    rows[3]["curriculum"]["atom_token_ids"] = [1, 10, 11]
    result = guard.adjudicate(rows)
    assert not result["pass"]
    assert any("SYMBOL_ONLY:ATOM_MUST_BE_UNSEEN" in x for x in result["failures"])

    rows = _valid_rows()
    rows[3]["curriculum"]["template_family"] = "UNSEEN_TEMPLATE"
    result = guard.adjudicate(rows)
    assert any("SYMBOL_ONLY:TEMPLATE_MUST_BE_FAMILIAR" in x for x in result["failures"])


def test_template_and_lexicon_axes_reject_confounded_reuse():
    rows = _valid_rows()
    rows[4]["curriculum"]["template_family"] = "T1"
    result = guard.adjudicate(rows)
    assert any("TEMPLATE_ONLY:TEMPLATE_MUST_BE_UNSEEN" in x for x in result["failures"])

    rows = _valid_rows()
    rows[5]["curriculum"]["lexical_family"] = "L1"
    result = guard.adjudicate(rows)
    assert any("LEXICON_ONLY:LEXICON_MUST_BE_UNSEEN" in x for x in result["failures"])


def test_exact_semantic_episode_never_crosses_splits():
    rows = _valid_rows()
    rows[3]["curriculum"]["semantic_surface_sha256"] = rows[0]["curriculum"]["semantic_surface_sha256"]
    result = guard.adjudicate(rows)
    assert not result["pass"]
    assert "EXACT_SEMANTIC_SURFACE_OVERLAP:TRAIN:HOLDOUT" in result["failures"]


def test_joint_ood_requires_all_three_high_level_factors_unseen():
    rows = _valid_rows()
    rows[6]["curriculum"]["atom_token_ids"] = [1, 13, 14]
    result = guard.adjudicate(rows)
    assert not result["pass"]
    assert any("JOINT_OOD:ATOM_MUST_BE_UNSEEN" in x for x in result["failures"])
