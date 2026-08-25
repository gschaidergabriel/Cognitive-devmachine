import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "trigger2_binding_router_full_cross_generator_v1.py"
spec = importlib.util.spec_from_file_location("trigger2_binding_full_cross_v1", SRC)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def baseline():
    pools, render = mod.load_atom_manifest(None)
    rows = mod.generate(pools, render)
    return pools, render, rows


def test_full_cross_schedule_passes_and_stays_nonadmissible():
    pools, render, rows = baseline()
    report = mod.audit(rows, pools, render)
    assert report["pass"] is True
    assert report["rows"] == 2808
    assert report["nuisance_signatures"] == 864
    assert report["nuisance_signature_single_target_groups"] == 0
    assert report["conditional_mi_target_class_bits"] == 0.0
    assert report["nuisance_exact_lookup_accuracy"] == 1 / 3
    assert render["training_eligible"] is False
    assert all(row["training_eligible"] is False for row in rows)


def test_missing_display_order_fails_closed():
    pools, render, rows = baseline()
    victim = next(r for r in rows if r["curriculum_phase"] == "P1_SEMANTIC_TO_ROUTER")
    gid = victim["display_cross_group_id"]
    damaged = [
        r for r in rows
        if not (r.get("display_cross_group_id") == gid and r["display_order_id"] == "O5")
    ]
    report = mod.audit(damaged, pools, render)
    assert report["pass"] is False
    assert any(x.startswith("DISPLAY_ORDER_NOT_FULLY_CROSSED:") for x in report["failures"])


def test_collapsed_nuisance_signature_fails_closed():
    pools, render, rows = baseline()
    damaged = [dict(r) for r in rows]
    first = next(r for r in damaged if r["curriculum_phase"] == "P1_SEMANTIC_TO_ROUTER")
    for r in damaged:
        if (
            r.get("curriculum_phase") == "P1_SEMANTIC_TO_ROUTER"
            and r.get("split") == first["split"]
            and r.get("symbol_partition") == first["symbol_partition"]
            and r.get("template_partition") == first["template_partition"]
            and r.get("template_id") == first["template_id"]
            and r.get("query_polarity") == first["query_polarity"]
            and r.get("realized_mapping") == first["realized_mapping"]
            and r.get("codebook_entry_order") == first["codebook_entry_order"]
            and r.get("semantic_ablated_prompt") == first["semantic_ablated_prompt"]
        ):
            r["decision_class_metadata_only"] = first["decision_class_metadata_only"]
            r["semantic_slot_metadata_only"] = first["semantic_slot_metadata_only"]
            r["target"] = first["target"]
    report = mod.audit(damaged, pools, render)
    assert report["pass"] is False
    assert report["nuisance_signature_single_target_groups"] >= 1
    assert any(x.startswith("NUISANCE_SIGNATURE_NOT_TARGET_SLOT_COMPLETE:") for x in report["failures"])
