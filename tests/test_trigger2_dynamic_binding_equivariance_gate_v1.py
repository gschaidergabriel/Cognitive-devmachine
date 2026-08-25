from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _modules():
    bp = _load("trigger2_dynamic_binding_blueprint_v2", ROOT / "tools" / "trigger2_dynamic_binding_blueprint_v2.py")
    gate = _load("trigger2_dynamic_binding_equivariance_gate_v1", ROOT / "tools" / "trigger2_dynamic_binding_equivariance_gate_v1.py")
    return bp, gate


def test_current_blueprint_passes_exact_equivariance_gate():
    bp, gate = _modules()
    report = gate.audit_rows(list(bp.build_rows()), bp)
    assert report["pass"] is True
    assert report["rows"] == 9072
    assert report["ablation_groups"] == 3024
    assert report["nuisance_lookup_accuracy"] == 1 / 3
    assert report["order_groups"] == 1512
    assert report["mapping_equivariance_groups"] == 252
    assert report["layout_groups"] == 4536
    assert report["training_eligible"] is False
    assert report["accepted_dataset_tokens"] == 0
    assert report["training_credit"] == 0


def test_target_tamper_fails_closed():
    bp, gate = _modules()
    rows = list(bp.build_rows())
    rows[0] = copy.deepcopy(rows[0])
    original = rows[0]["target"]
    rows[0]["target"] = next(s for s in rows[0]["sym"] if s != original)
    report = gate.audit_rows(rows, bp)
    assert report["pass"] is False
    assert any(x.startswith("TARGET_DERIVATION_MISMATCH:") for x in report["failures"])


def test_model_visible_query_hint_breaks_semantic_ablation_balance():
    bp, gate = _modules()
    rows = list(bp.build_rows())
    rows[0] = copy.deepcopy(rows[0])
    rows[0]["q"] = rows[0]["q"] + " TARGET_HINT=" + rows[0]["target"]
    report = gate.audit_rows(rows, bp)
    assert report["pass"] is False
    assert any(x.startswith("ABLATION_GROUP_SIZE:") for x in report["failures"])


def test_hidden_audit_metadata_does_not_change_gate():
    bp, gate = _modules()
    rows = [dict(r, hidden_audit_note="must_not_enter_projection") for r in bp.build_rows()]
    report = gate.audit_rows(rows, bp)
    assert report["pass"] is True
    assert report["nuisance_lookup_accuracy"] == 1 / 3


def test_missing_crossing_row_fails_multiple_invariants():
    bp, gate = _modules()
    rows = list(bp.build_rows())[:-1]
    report = gate.audit_rows(rows, bp)
    assert report["pass"] is False
    assert any(x.startswith("ORDER_CROSSING_INCOMPLETE:") for x in report["failures"])
    assert any(x.startswith("MAPPING_ORDER_CELL_SIZE:") for x in report["failures"])
    assert any(x.startswith("LAYOUT_CROSSING_INCOMPLETE:") for x in report["failures"])
