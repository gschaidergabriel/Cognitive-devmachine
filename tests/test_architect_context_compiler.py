import json
from pathlib import Path

from tools.architect_context_compiler import compile_context


def _write_state(path: Path, **overrides) -> None:
    state = {
        "architect_id": "federated-development-architect",
        "generation": 6,
        "federation_mode": "SEPARATE_STATE_SHARED_DIRECTION",
        "active_project_binding_id": "frankenstein-2.0",
        "active_owner_intent_epoch_id": "epoch-current",
        "active_owner_direction_summary": "keep runtime evidence ahead of stale aggregates",
        "current_focus": "runtime-first",
        "active_goal_ids": ["goal-a"],
        "primary_frontier_workpackage_ids": ["F2-WP-002", "F2-WP-510"],
        "observed_parallel_component_work": ["F2-WP-1102"],
        "current_blockers": ["aggregate projection lags granular evidence"],
        "current_uncertainty": ["runner health unknown"],
        "authority_resolution": {"admitted_supervisor_authority": "8.78"},
        "aggregate_projection": {"authority": "CACHE_ONLY_NOT_TRUTH_AUTHORITY"},
        "runtime_transport": {"target_environment": "clay-direct-dev"},
        "evidence_precedence": "granular evidence > aggregate projections",
        "current_processing_mode": "ARCHITECT_RUNTIME_FIRST_SYNTHESIS_ROUTING",
        "current_context_budget_policy": "delta only",
        "next_exact_actions": ["run discriminator"],
        "last_ingested_heads": {
            "frankenstein_2_main": "old-f2",
            "research_entity_main": "same-research",
        },
    }
    state.update(overrides)
    path.write_text(json.dumps(state), encoding="utf-8")


def test_compiler_preserves_owner_project_frontier_and_blockers(tmp_path):
    state_path = tmp_path / "ARCHITECT_STATE.json"
    _write_state(state_path)

    capsule = compile_context(
        tmp_path / "missing.sqlite",
        state_path,
        12,
        {"frankenstein_2_main": "new-f2", "research_entity_main": "same-research"},
    )

    assert capsule["active_project_binding_id"] == "frankenstein-2.0"
    assert capsule["active_owner_intent_epoch_id"] == "epoch-current"
    assert capsule["active_owner_direction_summary"] == "keep runtime evidence ahead of stale aggregates"
    assert capsule["active_workpackage_ids"] == ["F2-WP-002", "F2-WP-510"]
    assert capsule["primary_frontier_workpackage_ids"] == ["F2-WP-002", "F2-WP-510"]
    assert capsule["observed_parallel_component_work"] == ["F2-WP-1102"]
    assert capsule["current_blockers"] == ["aggregate projection lags granular evidence"]
    assert capsule["current_uncertainty"] == ["runner health unknown"]
    assert capsule["authority_resolution"]["admitted_supervisor_authority"] == "8.78"
    assert capsule["aggregate_projection"]["authority"] == "CACHE_ONLY_NOT_TRUTH_AUTHORITY"
    assert capsule["runtime_transport"]["target_environment"] == "clay-direct-dev"
    assert capsule["evidence_precedence"] == "granular evidence > aggregate projections"


def test_head_delta_is_fail_visible_for_changed_unchanged_and_unknown_heads(tmp_path):
    state_path = tmp_path / "ARCHITECT_STATE.json"
    _write_state(state_path)

    capsule = compile_context(
        tmp_path / "missing.sqlite",
        state_path,
        12,
        {
            "frankenstein_2_main": "new-f2",
            "research_entity_main": "same-research",
            "new_project_main": "first-observation",
        },
    )

    changed = capsule["head_deltas"]["frankenstein_2_main"]
    unchanged = capsule["head_deltas"]["research_entity_main"]
    unknown = capsule["head_deltas"]["new_project_main"]

    assert changed == {
        "previous": "old-f2",
        "current": "new-f2",
        "previous_known": True,
        "changed": True,
    }
    assert unchanged == {
        "previous": "same-research",
        "current": "same-research",
        "previous_known": True,
        "changed": False,
    }
    assert unknown == {
        "previous": None,
        "current": "first-observation",
        "previous_known": False,
        "changed": True,
    }


def test_explicit_active_workpackages_outrank_primary_frontier_fallback(tmp_path):
    state_path = tmp_path / "ARCHITECT_STATE.json"
    _write_state(
        state_path,
        active_workpackage_ids=["F2-WP-explicit"],
        primary_frontier_workpackage_ids=["F2-WP-fallback"],
    )

    capsule = compile_context(tmp_path / "missing.sqlite", state_path, 12, {})

    assert capsule["active_workpackage_ids"] == ["F2-WP-explicit"]
    assert capsule["primary_frontier_workpackage_ids"] == ["F2-WP-fallback"]
