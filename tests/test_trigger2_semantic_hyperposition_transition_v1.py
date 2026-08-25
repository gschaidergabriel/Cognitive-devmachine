from copy import deepcopy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, TOOLS / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


B = load("trigger2_shp_blueprint_v1", "trigger2_semantic_hyperposition_transition_blueprint_v1.py")
G = load("trigger2_shp_transition_gate_v1_test", "trigger2_semantic_hyperposition_transition_gate_v1.py")


def one_row(klass="QUERY_TRUE"):
    return B.build_row(
        B.TRAIN_TEMPLATES[0],
        "TRAIN",
        klass,
        B.BRANCH_ORDERS[0],
        B.CODEBOOK_PERMS[0],
        B.LAYOUTS[0],
    )


def failure_set(row):
    return set(G.adjudicate(row)["failures"])


def test_blueprint_selftest_passes_and_renders_no_holdout():
    result = B.selftest()
    assert result["pass"] is True
    assert result["rows"] == 648
    assert result["train"] == 432
    assert result["validation"] == 216
    assert result["holdout_rendered"] == 0
    assert result["training_eligible"] is False
    assert result["accepted_dataset_tokens_minted"] == 0
    assert all(abs(v) < 1e-12 for v in result["shortcut_mi_bits"].values())


def test_reference_derived_row_passes_transition_gate():
    verdict = G.adjudicate(one_row())
    assert verdict["semantic_hyperposition_transition_pass"] is True
    assert verdict["metrics"]["branch_permutations_checked"] == 6
    assert verdict["training_credit_minted"] is False


def test_mutated_state_after_fails_derivability():
    row = one_row()
    row["semantic_hyperposition_transition"]["state_after"]["branches"][0]["validity"] = "FALSIFIED"
    assert "STATE_AFTER_NOT_REFERENCE_LABELER_DERIVABLE" in failure_set(row)


def test_silent_branch_drop_fails_closed():
    row = one_row()
    row["semantic_hyperposition_transition"]["state_after"]["branches"].pop()
    failures = failure_set(row)
    assert "BRANCH_SET_CHANGED_OR_SILENTLY_DROPPED" in failures


def test_mutated_resolution_fails_derivability():
    row = one_row()
    row["semantic_hyperposition_transition"]["resolution"] = {
        "status": "UNRESOLVED",
        "resolved_branch": None,
        "basis": "NO_UNIQUE_EXPLICIT_PROOF_OR_DISCRIMINATOR",
    }
    assert "RESOLUTION_NOT_REFERENCE_LABELER_DERIVABLE" in failure_set(row)


def test_unknown_episode_stays_unresolved_without_deleting_branches():
    row = one_row("QUERY_UNKNOWN")
    tr = row["semantic_hyperposition_transition"]
    assert tr["resolution"]["status"] == "UNRESOLVED"
    assert len(tr["state_before"]["branches"]) == len(tr["state_after"]["branches"]) == 3
    assert G.adjudicate(row)["semantic_hyperposition_transition_pass"] is True


def test_wrong_discriminator_order_is_rejected():
    row = one_row()
    order = row["semantic_hyperposition_transition"]["discriminator_order"]
    row["semantic_hyperposition_transition"]["discriminator_order"] = list(reversed(order))
    assert "DISCRIMINATOR_ORDER_NOT_REFERENCE_LABELER_DERIVABLE" in failure_set(row)


def test_salience_never_substitutes_for_truth_and_wrong_order_is_rejected():
    row = one_row("QUERY_UNKNOWN")
    tr = row["semantic_hyperposition_transition"]
    assert tr["resolution"]["status"] == "UNRESOLVED"
    tr["salience_order"] = list(reversed(tr["salience_order"]))
    assert "SALIENCE_ORDER_NOT_REFERENCE_LABELER_DERIVABLE" in failure_set(row)


def test_missing_anti_collapse_rule_is_rejected():
    row = one_row()
    row["semantic_hyperposition_transition"]["anti_collapse"].remove("NO_MAJORITY_AS_TRUTH")
    failures = failure_set(row)
    assert any(f.startswith("ANTI_COLLAPSE_MISSING:") for f in failures)


def test_branch_order_is_semantic_nuisance_only():
    r0 = B.build_row(B.TRAIN_TEMPLATES[0], "TRAIN", "QUERY_TRUE", B.BRANCH_ORDERS[0], B.CODEBOOK_PERMS[2], B.LAYOUTS[0])
    r1 = B.build_row(B.TRAIN_TEMPLATES[0], "TRAIN", "QUERY_TRUE", B.BRANCH_ORDERS[-1], B.CODEBOOK_PERMS[2], B.LAYOUTS[0])
    assert r0["target"] == r1["target"]
    assert r0["semantic_hyperposition_transition"]["resolution"] == r1["semantic_hyperposition_transition"]["resolution"]
    assert G.adjudicate(r0)["semantic_hyperposition_transition_pass"] is True
    assert G.adjudicate(r1)["semantic_hyperposition_transition_pass"] is True


def test_reference_only_metadata_is_not_training_eligible():
    row = one_row()
    assert row["training_eligible"] is False
    assert "BLOCKED_UNTIL_EXACT_ACCEPTED_ABI_ATOMS" in row["render_status"]
