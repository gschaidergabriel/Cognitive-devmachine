import importlib.util
from pathlib import Path
import collections

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "tools" / "trigger2_c1_hyperposition_pilot_generator_v1.py"
spec = importlib.util.spec_from_file_location("trigger2_c1_v1", P)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def test_c1_blueprint_audit_passes_and_is_nonpromoting():
    rows = gen.generate_rows()
    audit = gen.validate_rows(rows)
    assert audit["pass"], audit
    assert audit["rows_total"] == 960
    assert audit["split_counts"] == {"TRAIN": 576, "VALIDATION": 192, "HOLDOUT": 192}
    assert audit["training_eligible"] is False
    assert audit["accepted_dataset_tokens"] == 0
    assert audit["training_credit"] == 0


def test_fixed_class_labels_are_mechanically_derived_not_rotating_codebook():
    rows = gen.generate_rows()
    assert {r["target"] for r in rows} == set(gen.CLASSES)
    assert all("CODEBOOK" not in r["prompt"].upper() for r in rows)
    assert all(r["prompt"].count("ENTAILED_BY_FACT") == 1 for r in rows)
    assert all(r["prompt"].count("CONTRADICTED_BY_FACT") == 1 for r in rows)
    assert all(r["prompt"].count("UNDETERMINED_BY_FACT") == 1 for r in rows)
    assert all(r["semantic_hyperposition_carrier"]["full_D_optimization_present"] is False for r in rows)


def test_every_fixed_nuisance_signature_retains_all_three_classes():
    rows = gen.generate_rows()
    by_sig = collections.defaultdict(set)
    for r in rows:
        f = r["c1_factors_evaluator_only"]
        sig = (r["split"], r["family_id"], f["atom_role"], f["fact_polarity"], f["template_id"], f["order"])
        by_sig[sig].add(r["target"])
    assert by_sig
    assert all(v == set(gen.CLASSES) for v in by_sig.values())


def test_family_and_lexeme_splits_are_disjoint():
    manifest = gen.split_manifest()
    seen_family = {}
    seen_lexeme = {}
    for split, families in manifest["families"].items():
        for fam in families:
            fid = fam["family_id"]
            assert fid not in seen_family
            seen_family[fid] = split
            for lex in fam["predicate_lexemes"] + fam["entity_lexemes"]:
                assert lex not in seen_lexeme, (lex, split, seen_lexeme.get(lex))
                seen_lexeme[lex] = split


def test_polarity_and_surface_factors_are_class_balanced_per_split():
    rows = gen.generate_rows()
    for split in ("TRAIN", "VALIDATION", "HOLDOUT"):
        sr = [r for r in rows if r["split"] == split]
        for cls in gen.CLASSES:
            cr = [r for r in sr if r["target"] == cls]
            assert collections.Counter(r["c1_factors_evaluator_only"]["fact_polarity"] for r in cr) == {
                "POSITIVE": len(cr) // 2,
                "NEGATIVE": len(cr) // 2,
            }
            assert collections.Counter(r["c1_factors_evaluator_only"]["query_polarity"] for r in cr) == {
                "POSITIVE": len(cr) // 2,
                "NEGATIVE": len(cr) // 2,
            }
            assert set(r["c1_factors_evaluator_only"]["template_id"] for r in cr) == set(gen.TEMPLATES)
            assert set(r["c1_factors_evaluator_only"]["order"] for r in cr) == set(gen.ORDERS)
