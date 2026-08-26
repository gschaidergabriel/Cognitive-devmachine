from __future__ import annotations

from pathlib import Path

from tools import trigger2_canonical_atom_split_manifest_v1 as manifest_tool

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_manifest_has_exactly_46_atoms_split_disjoint():
    m = manifest_tool.build_manifest()
    tv = set(m["split"]["TRAIN_AND_VALIDATION"])
    hold = set(m["split"]["HOLDOUT_FROZEN"])
    assert len(tv) + len(hold) == 46
    assert tv.isdisjoint(hold)
    assert tv | hold == set(manifest_tool.ALL_ACCEPTED_ATOMS)


def test_rejected_atom_not_in_split():
    m = manifest_tool.build_manifest()
    all_atoms = set(m["split"]["TRAIN_AND_VALIDATION"]) | set(m["split"]["HOLDOUT_FROZEN"])
    assert manifest_tool.REJECTED_ATOM not in all_atoms


def test_both_strata_represented_in_both_split_roles():
    """Source delta H_T2_ABI_01 wants neutral-vs-language-bearing accuracy
    comparable on both sides of the split -- verify both strata actually have
    representatives in TRAIN_AND_VALIDATION and in HOLDOUT_FROZEN."""
    m = manifest_tool.build_manifest()
    neutral = set(manifest_tool.NEUTRAL_ATOMS)
    lang = set(manifest_tool.LANGUAGE_BEARING_ATOMS)
    tv = set(m["split"]["TRAIN_AND_VALIDATION"])
    hold = set(m["split"]["HOLDOUT_FROZEN"])
    assert neutral & tv and neutral & hold
    assert lang & tv and lang & hold


def test_remap_is_deterministic():
    m = manifest_tool.build_manifest()
    a = manifest_tool.remap_ordinal("B4", 25, "TRAIN_AND_VALIDATION", m)
    b = manifest_tool.remap_ordinal("B4", 25, "TRAIN_AND_VALIDATION", m)
    assert a == b


def test_remap_respects_split_role():
    m = manifest_tool.build_manifest()
    for family in ("B0", "B1", "B4", "B5"):
        for ordinal in range(0, 30):
            tv_atom = manifest_tool.remap_ordinal(family, ordinal, "TRAIN_AND_VALIDATION", m)
            assert tv_atom in m["split"]["TRAIN_AND_VALIDATION"]
            hold_atom = manifest_tool.remap_ordinal(family, ordinal, "HOLDOUT_FROZEN", m)
            assert hold_atom in m["split"]["HOLDOUT_FROZEN"]


def test_decoy_range_always_maps_into_train_and_validation():
    m = manifest_tool.build_manifest()
    for ordinal in manifest_tool.KNOWN_DECOY_ORDINAL_RANGE:
        atom = manifest_tool.remap_ordinal("B4", ordinal, "TRAIN_AND_VALIDATION", m)
        assert atom in m["split"]["TRAIN_AND_VALIDATION"]


def test_empirical_scan_finds_zero_real_split_crossings_in_committed_corpus():
    """The actual P1_BLOCKER check: across every currently-committed candidate
    JSONL file, no placeholder ordinal (other than the known B4 decoy range,
    which is intentionally split-agnostic noise, verified by direct source
    inspection) may appear in both a HOLDOUT_FROZEN row and a TRAIN/VALIDATION
    row anywhere in the corpus."""
    result = manifest_tool.verify_no_split_crossing(REPO_ROOT)
    assert result["pass"] is True
    assert result["crossings"] == []
    assert result["total_distinct_ordinals"] > 0


def test_full_run_against_real_repo_passes():
    report = manifest_tool.run(REPO_ROOT)
    assert report["overall_pass"] is True
    assert report["remap_integrity_check"]["pass"] is True
    assert report["remap_integrity_check"]["checked"] > 0
