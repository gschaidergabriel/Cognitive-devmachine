from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "trigger2_synthetic_relation_deriver_v1.py"
SPEC = importlib.util.spec_from_file_location("trigger2_synthetic_relation_deriver_v1", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
DERIVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DERIVER)


def branch(bid: str, prediction: str, *, context: str = "APPLIES") -> dict:
    return {
        "branch_id": bid,
        "v": f"hypothesis:{bid}",
        "K": context,
        "E_plus": [],
        "E_minus": [],
        "F": [],
        "T": "episode",
        "A": {"source": "synthetic:test"},
        "sigma": "LIVE_UNRESOLVED",
        "projection_visibility": "VISIBLE",
        "predictions": {"disc:1": prediction},
    }


def state(*, admissible: bool = True, exact: bool = True) -> dict:
    return {
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": [branch("b0", "YES"), branch("b1", "NO")],
        "discriminator_catalog": {
            "disc:1": {
                "test_id": "disc:1",
                "admissible": admissible,
                "exact_outcome_discriminator": exact,
            }
        },
    }


def observation(
    *,
    event_id: str = "ev:1",
    ancestry: str = "anc:1",
    group: str = "grp:1",
    observed: str = "YES",
) -> dict:
    return {
        "evidence_event_id": event_id,
        "correlation_ancestry_id": ancestry,
        "independence_group": group,
        "provenance": {"fixture": "unit"},
        "test_id": "disc:1",
        "observed_outcome": observed,
    }


def test_derives_support_and_falsification_without_relation_input() -> None:
    result = DERIVER.derive(state(), observation())
    assert result["relations"] == {"b0": "SUPPORTS", "b1": "FALSIFIES"}
    assert result["state_after"]["branches"][0]["E_plus"][0]["relation"] == "SUPPORTS"
    assert result["state_after"]["branches"][1]["F"][0]["relation"] == "FALSIFIES"
    assert result["derivation_receipt"]["self_asserted_label"] is False


def test_rejects_caller_supplied_relation_or_winner() -> None:
    obs = observation()
    obs["relation"] = "SUPPORTS"
    with pytest.raises(ValueError, match="caller-supplied"):
        DERIVER.derive(state(), obs)
    obs = observation()
    obs["winner_branch_id"] = "b0"
    with pytest.raises(ValueError, match="caller-supplied"):
        DERIVER.derive(state(), obs)


def test_exact_admissible_discriminator_derives_unique_resolution() -> None:
    result = DERIVER.derive(state(), observation())
    assert result["resolution"] == {"status": "RESOLVED", "resolved_branch_id": "b0"}
    evaluation = result["discriminator_evaluation"]
    assert evaluation["admissible"] is True
    assert evaluation["separation_derived"] is True
    assert evaluation["self_asserted_winner"] is False
    assert evaluation["winner_branch_id"] == "b0"
    assert result["derivation_receipt"]["kind"] == "VERIFIED_DISCRIMINATOR_OUTCOME"


def test_inadmissible_discriminator_never_resolves() -> None:
    result = DERIVER.derive(state(admissible=False), observation())
    assert result["resolution"]["status"] == "UNRESOLVED"
    assert result["discriminator_evaluation"] is None


def test_soft_counterevidence_does_not_resolve() -> None:
    result = DERIVER.derive(state(exact=False), observation())
    assert result["relations"] == {"b0": "SUPPORTS", "b1": "COUNTERS"}
    assert result["resolution"]["status"] == "UNRESOLVED"


def test_unknown_branch_prediction_blocks_resolution() -> None:
    s = state()
    s["branches"][1]["predictions"]["disc:1"] = "UNKNOWN"
    result = DERIVER.derive(s, observation())
    assert result["relations"]["b1"] == "UNKNOWN_RELATION"
    assert result["resolution"]["status"] == "UNRESOLVED"


def test_unknown_context_branch_blocks_resolution() -> None:
    s = state()
    s["branches"].append(branch("b2", "NO", context="UNKNOWN"))
    result = DERIVER.derive(s, observation())
    assert result["resolution"]["status"] == "UNRESOLVED"


def test_same_dependence_group_different_event_gets_no_independent_credit() -> None:
    first = DERIVER.derive(state(), observation(event_id="ev:1", ancestry="anc:1", group="grp:1"))
    second_state = first["state_after"]
    second = DERIVER.derive(
        second_state,
        observation(event_id="ev:2", ancestry="anc:2", group="grp:1"),
    )
    assert second["independent_credit"] is False
    new_record = second["state_after"]["branches"][0]["E_plus"][-1]
    assert new_record["independent_credit"] is False


def test_same_ancestry_different_group_gets_no_independent_credit() -> None:
    first = DERIVER.derive(state(), observation(event_id="ev:1", ancestry="anc:1", group="grp:1"))
    second = DERIVER.derive(
        first["state_after"],
        observation(event_id="ev:2", ancestry="anc:1", group="grp:2"),
    )
    assert second["independent_credit"] is False


def test_exact_replay_is_idempotent() -> None:
    first = DERIVER.derive(state(), observation())
    replay = DERIVER.derive(first["state_after"], observation())
    assert replay["status"] == "EXACT_REPLAY_IDEMPOTENT"
    assert replay["state_after"] == first["state_after"]


def test_same_event_id_with_mutated_payload_fails_closed() -> None:
    first = DERIVER.derive(state(), observation())
    mutated = observation(observed="NO")
    with pytest.raises(ValueError, match="mutated immutable payload"):
        DERIVER.derive(first["state_after"], mutated)


def test_branch_birth_is_not_admitted() -> None:
    obs = observation()
    obs["new_branch_payload"] = branch("b2", "YES")
    obs["branch_creation_warranted"] = True
    with pytest.raises(ValueError, match="branch birth is not admitted"):
        DERIVER.derive(state(), obs)


def test_full_tuple_is_fail_closed_required() -> None:
    s = state()
    del s["branches"][0]["A"]
    with pytest.raises(ValueError, match="branch missing mandatory field: A"):
        DERIVER.derive(s, observation())


def test_existing_event_without_digest_is_rejected() -> None:
    s = state()
    s["branches"][0]["E_plus"].append(
        {
            "evidence_event_id": "ev:old",
            "correlation_ancestry_id": "anc:old",
            "independence_group": "grp:old",
            "relation": "SUPPORTS",
        }
    )
    with pytest.raises(ValueError, match="lacks immutable event_digest"):
        DERIVER.derive(s, observation())
