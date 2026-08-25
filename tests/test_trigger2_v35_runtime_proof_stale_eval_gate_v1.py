import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/trigger2_v35_runtime_proof_stale_eval_gate_v1.py"
SPEC = importlib.util.spec_from_file_location("trigger2_v35_gate", TOOL)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def rows():
    return mod.load_rows()


def test_current_seed_passes_and_mints_zero_credit():
    result = mod.audit_rows(rows())
    assert result["pass"] is True
    assert result["rows"] == 16
    assert result["training_eligible_rows"] == 0
    assert result["accepted_dataset_tokens"] == 0
    assert result["training_credit"] == 0
    assert result["model_runtime_credit"] == 0
    assert result["hcu_full_runtime_credit"] == 0
    assert result["whole_entityos_runtime_credit"] == 0


def test_training_eligibility_promotion_fails_closed():
    candidate = rows()
    candidate[0]["training_eligible"] = True
    with pytest.raises(mod.GateError, match="training_eligible"):
        mod.audit_rows(candidate)


def test_channel_promotion_fails_closed():
    candidate = rows()
    candidate[0]["channel"] = "TRAIN"
    with pytest.raises(mod.GateError, match="channel"):
        mod.audit_rows(candidate)


def test_duplicate_row_identity_fails_closed():
    candidate = rows()
    candidate[1]["row_id"] = candidate[0]["row_id"]
    with pytest.raises(mod.GateError, match="duplicate row_id"):
        mod.audit_rows(candidate)


def test_missing_typed_recovery_outcome_fails_closed():
    candidate = rows()
    candidate = [r for r in candidate if r.get("typed_runtime_outcome") != "SCOPE_CHANGED"]
    # Keep total row count fixed with a duplicate semantic row carrying a fresh id.
    replacement = copy.deepcopy(candidate[-1])
    replacement["row_id"] = "T2V35-STALE-999"
    candidate.append(replacement)
    with pytest.raises(mod.GateError, match="missing typed stale/recovery outcomes"):
        mod.audit_rows(candidate)


def test_model_minted_rebase_cannot_be_accepted():
    candidate = rows()
    target = next(r for r in candidate if r["row_id"] == "T2V35-STALE-004")
    target["verdict"] = "ACCEPT_RUNTIME_PROVEN_REBASE"
    with pytest.raises(mod.GateError, match="authority-creating action must be rejected"):
        mod.audit_rows(candidate)


def test_matched_family_must_retain_reject_and_bounded_accept():
    candidate = rows()
    target = next(r for r in candidate if r["row_id"] == "T2V35-PROOF-002")
    target["verdict"] = "REJECT_SCOPE_INFLATION"
    with pytest.raises(mod.GateError, match="pair lacks bounded accept control"):
        mod.audit_rows(candidate)


def test_axis_cardinality_drift_fails_closed():
    candidate = rows()
    candidate[0]["axis"] = "MODEL_COGNITION_VS_RUNTIME_PROOF"
    with pytest.raises(mod.GateError, match="physical proof axis"):
        mod.audit_rows(candidate)
