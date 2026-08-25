from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tools" / "trigger2_hyperposition_reference_labelers_v1.py"
SPEC = importlib.util.spec_from_file_location("trigger2_hp_labelers", PATH)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


def branch(bid, value):
    return {
        "schema": MOD.BRANCH_SCHEMA,
        "branch_id": bid,
        "v_semantic_value": value,
        "K_context_predicate": "ctx=test",
        "E_plus": [],
        "E_minus": [],
        "F_falsifier": f"falsify:{bid}",
        "T_validity_scope": "synthetic_test",
        "A_origin_provenance": "pytest",
        "sigma_epistemic_status": "HYPOTHESIS",
        "projection_visibility": "VISIBLE",
        "validity": "LIVE",
    }


def base_branches():
    return [branch("b0", "TRUE"), branch("b1", "FALSE"), branch("b2", "UNKNOWN")]


def obs(**kw):
    x = {
        "evidence_id": "e1",
        "provenance_ancestry_id": "p1",
        "independence_group": "g1",
        "evidence_kind": "NONDISCRIMINATING_OBSERVATION",
        "supports": ["b0"],
        "contradicts": ["b1"],
        "falsifies": [],
        "discriminator_id": None,
        "resolution_authorized": False,
        "synthetic_world": True,
    }
    x.update(kw)
    return x


def test_selftest_passes():
    r = MOD.selftest()
    assert r["pass"] is True
    assert r["training_credit"] == 0


def test_nondiscriminating_update_preserves_live_branches():
    u = MOD.U_update(base_branches(), obs())
    assert [b["validity"] for b in u["branches"]] == ["LIVE", "LIVE", "LIVE"]
    r = MOD.D_resolve(u["branches"], obs())
    assert r["status"] == "UNRESOLVED"


def test_exact_synthetic_discriminator_can_resolve_task_world_only():
    o = obs(
        evidence_id="e2",
        evidence_kind="EXACT_SYNTHETIC_PROOF",
        supports=["b0"],
        contradicts=[],
        falsifies=["b1", "b2"],
        discriminator_id="d1",
        resolution_authorized=True,
    )
    u = MOD.U_update(base_branches(), o)
    r = MOD.D_resolve(u["branches"], o)
    assert r["status"] == "RESOLVED_WITHIN_SYNTHETIC_WORLD"
    assert r["resolved_branch"] == "b0"
    assert r["canonical_truth_allowed"] is False
    assert r["direct_effect_authority"] is False


def test_replay_is_idempotent_for_same_evidence_identity():
    o = obs()
    first = MOD.U_update(base_branches(), o)
    second = MOD.U_update(first["branches"], o)
    assert second["audit"]["added_support"] == []
    assert second["audit"]["added_counterevidence"] == []
    assert len(second["audit"]["duplicate_ignored"]) == 2


def test_majority_or_recurrence_cannot_resolve():
    o = obs(
        evidence_kind="RECURRENCE_OR_MAJORITY",
        falsifies=["b1", "b2"],
        discriminator_id=None,
        resolution_authorized=False,
    )
    u = MOD.U_update(base_branches(), o)
    r = MOD.D_resolve(u["branches"], o)
    assert r["status"] == "UNRESOLVED"


def test_discriminator_ranking_prefers_pair_coverage_before_cost():
    ranked = MOD.U_d_test_order(
        base_branches(),
        [
            {
                "discriminator_id": "cheap_partial",
                "separates_pairs": [["b0", "b1"]],
                "cost_rank": 0,
                "independence_group": "ga",
            },
            {
                "discriminator_id": "full",
                "separates_pairs": [["b0", "b1"], ["b0", "b2"], ["b1", "b2"]],
                "cost_rank": 3,
                "independence_group": "gb",
            },
        ],
    )
    assert ranked["ranking"][0]["discriminator_id"] == "full"
    assert ranked["probability_interpretation_forbidden"] is True


def test_salience_is_never_truth_or_probability():
    r = MOD.f_salience_rank(
        [
            {"item_id": "x", "context_match": True, "task_relevance_rank": 2, "novelty": True},
            {"item_id": "y", "context_match": False, "task_relevance_rank": 0, "novelty": False},
        ]
    )
    assert r["salience_is_truth"] is False
    assert r["salience_is_probability"] is False


def test_duplicate_branch_ids_fail_closed():
    b = base_branches()
    b[1]["branch_id"] = "b0"
    try:
        MOD.validate_branch_set(b)
    except MOD.LabelerError:
        return
    raise AssertionError("duplicate branch ids must fail closed")
