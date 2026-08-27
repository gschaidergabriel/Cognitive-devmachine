from __future__ import annotations

from tools import trigger2_b0_read_write_baseline_generator_v1 as gen


def test_schema_and_counts():
    report = gen.run()
    assert report["schema"] == gen.SCHEMA
    assert report["training_eligible"] is False
    assert report["read"]["rows"] == 72
    assert report["write"]["rows"] == 540


def test_read_pass_clean():
    read_rows = gen.build_read_rows()
    report = gen.audit_read(read_rows)
    assert report["pass"] is True
    assert report["failures"] == []
    assert report["split_counts"] == {"TRAIN": 48, "VALIDATION": 12, "HOLDOUT_FROZEN": 12}


def test_read_rows_never_contain_symbol_atoms():
    """B0 READ must be pure semantic reading -- no codebook, no symbol atom should
    ever leak into a READ prompt (that would silently turn it into a WRITE task)."""
    for r in gen.build_read_rows():
        assert "ABI_ACCEPTED_ORDINAL" not in r["prompt"]
        assert r["target"] == r["class"]


def test_write_pass_clean():
    write_rows = gen.build_write_rows()
    report = gen.audit_write(write_rows)
    assert report["pass"] is True
    assert report["failures"] == []
    assert abs(report["order_target_mi_bits"]) < 1e-9


def test_write_symbol_partition_matches_blueprint_v2():
    """B0 WRITE must stay inside the same TRAIN/HOLDOUT symbol partition as the
    sibling B1 blueprint (tools/trigger2_dynamic_binding_blueprint_v2.py) so B0 and
    B1 remain part of one consistent ancestry rather than diverging pools."""
    import trigger2_dynamic_binding_blueprint_v2 as bp

    write_rows = gen.build_write_rows()
    train_targets = {r["target"] for r in write_rows if r["split"] == "TRAIN"}
    holdout_targets = {r["target"] for r in write_rows if r["split"] == "HOLDOUT_FROZEN"}
    expected_train = {bp.atom_ref(n) for triple in bp.TRAIN_TRIPLETS for n in triple}
    expected_holdout = {bp.atom_ref(n) for n in bp.HOLDOUT_TRIPLET}
    assert train_targets == expected_train
    assert holdout_targets == expected_holdout
    assert train_targets.isdisjoint(holdout_targets)


def test_overall_pass():
    report = gen.run()
    assert report["overall_pass"] is True
