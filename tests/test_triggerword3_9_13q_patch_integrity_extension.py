from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DELTA = ROOT / "research_entity" / "architecture_archaeology" / "TRIGGERWORD3_9_13Q_PATCH_INTEGRITY_EXTENSION_20260828_GPT56SOL.json"


def load_delta() -> dict:
    return json.loads(DELTA.read_text(encoding="utf-8"))


def test_extension_is_non_authority_and_zero_credit() -> None:
    data = load_delta()
    assert data["status"] == "CURRENT_SOURCE_CURATION_NON_AUTHORITY"
    assert data["patch_integrity_contract"]["status"] == "PROPOSED_SOURCE_CONTRACT_NOT_RUNTIME_PASS"
    assert data["credits"] == {
        "provider_runtime": 0,
        "entityos_whole_runtime": 0,
        "hcu_full_runtime": 0,
        "physical_grid10_runtime": 0,
        "canonical_semantics": 0,
        "jspace_model_runtime": 0,
        "training": 0,
        "whole_product_pass": False,
    }


def test_patch_integrity_contract_closes_source_blind_rewrite_class() -> None:
    contract = load_delta()["patch_integrity_contract"]
    text = "\n".join(
        contract["preconditions"]
        + contract["applicability"]
        + contract["post_apply_integrity"]
        + contract["rollback"]
    )

    required_fragments = (
        "repository commit and tree identity",
        "committed blob identity",
        "full pre-edit SHA-256",
        "declared target-file set == parsed patch target-file set",
        "unified diff",
        "git apply --check",
        "full post-edit SHA-256",
        "outside the declared target set is byte-identical",
        "outside declared patch hunks are unchanged",
        "actual changed-file set == declared target-file set",
        "restore exact pre-edit bytes",
        "rollback hashes equal the bound pre-edit hashes",
    )
    for fragment in required_fragments:
        assert fragment in text

    assert "50 percent shrink heuristic" not in contract["acceptance_rule"]
    assert "FAIL_CLOSED" in contract["acceptance_rule"]


def test_whole_file_replacement_is_explicit_separate_operation() -> None:
    exception = load_delta()["patch_integrity_contract"]["whole_file_replacement_exception"]
    assert "separate explicit operation class" in exception
    assert "must not be inferred from a normal modification request" in exception


def test_trigger3_does_not_fake_root_provider_or_training_progress() -> None:
    boundaries = load_delta()["current_trigger3_no_change_boundaries"]
    assert boundaries["root_readme"] == "NOT_MODIFIED"
    assert "NO_CHANGE_WITH_REASON" in boundaries["root_mass_move"]
    assert boundaries["provider_execution"] == "HARD_OFF; NONE_PERFORMED"
    assert boundaries["together"] == "FORBIDDEN; NONE_PERFORMED"
    assert boundaries["vps_execution"] == "NONE_PERFORMED_BY_THIS_TRIGGER3_DELTA"
    assert boundaries["unusual_experiment"] == "NONE_PERFORMED"
    assert "CREDIT_ZERO" in boundaries["training"]
