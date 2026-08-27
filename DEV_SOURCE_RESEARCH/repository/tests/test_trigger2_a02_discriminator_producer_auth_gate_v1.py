from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from tools import trigger2_a02_discriminator_producer_auth_gate_v1 as gate
from tools import trigger2_a02_discriminator_producer_v1 as producer
from tools import trigger2_trusted_hyperposition_pilot_generator_v1 as generator


REPO = Path(__file__).resolve().parents[1]
AUTHORITY_PATH = (
    REPO
    / "research_entity/global/j-space/research/"
      "TRIGGER2_A02_DISCRIMINATOR_PRODUCER_AUTHORITY_V1.json"
)


def _authority():
    return json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))


def _baseline_row():
    authority = _authority()
    policy = authority["policy"]
    bundle = generator.build_subjects(
        generator.CASE_ID,
        generator.default_parameters(),
    )
    receipt = producer.produce(
        world=bundle["formal_world"],
        pre_state=bundle["state_before"],
        event=bundle["event"],
        generation_case_id=generator.CASE_ID,
        policy=policy,
    )
    p = authority["producer"]
    return {
        "generation_case_id_evaluator_only": generator.CASE_ID,
        "formal_task_world_evaluator_only": deepcopy(bundle["formal_world"]),
        "hyperposition_state_before_evaluator_only": deepcopy(bundle["state_before"]),
        "hyperposition_genesis_state_evaluator_only": deepcopy(bundle["genesis_state"]),
        "synthetic_event_history_evaluator_only": [],
        "synthetic_test_event_evaluator_only": deepcopy(bundle["event"]),
        "discriminator_execution_receipts_evaluator_only": [deepcopy(receipt)],
        "discriminator_producer_binding_evaluator_only": {
            "repo_path": p["repo_path"],
            "source_sha256": p["source_sha256"],
            "producer_schema_or_version": p["producer_schema_or_version"],
            "source_lineage": deepcopy(p["source_lineage"]),
            "policy_id": policy["policy_id"],
            "policy_version": policy["policy_version"],
            "policy_jcs_sha256": authority["policy_jcs_sha256"],
            "formal_discriminator_spec_jcs_sha256": policy[
                "formal_discriminator_spec_jcs_sha256"
            ],
        },
    }


def _assert_reject(row):
    result = gate.adjudicate(row)
    assert result["pass"] is False
    assert result["canonical_dataset_admission"] is False
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0
    return result


def test_a02_repository_lineage_resolves_real_commit_path_bytes_and_ancestry():
    p = _authority()["producer"]
    failures, details = gate._verify_repository_lineage(p, p["repo_path"])
    assert failures == []
    assert details["origin_repository"] == gate.EXPECTED_REPOSITORY
    assert details["declared_source_commit_sha"] == p["source_lineage"]["source_commit_sha"]
    assert details["source_commit_path_sha256"] == p["source_sha256"]
    assert details["executed_head_path_sha256"] == p["source_sha256"]
    assert details["source_commit_is_ancestor_of_head"] is True
    assert isinstance(details["executed_head_sha"], str)
    assert len(details["executed_head_sha"]) == 40
    assert isinstance(details["executed_tree_sha"], str)
    assert len(details["executed_tree_sha"]) == 40


def test_a02_repository_lineage_rejects_well_formed_nonexistent_commit():
    p = deepcopy(_authority()["producer"])
    p["source_lineage"]["source_commit_sha"] = "0" * 40
    failures, details = gate._verify_repository_lineage(p, p["repo_path"])
    assert "A02_PRODUCER_SOURCE_LINEAGE_COMMIT_UNRESOLVED" in failures
    assert details["source_commit_is_ancestor_of_head"] is False


def test_a02_repository_lineage_rejects_real_commit_wrong_path_binding():
    p = deepcopy(_authority()["producer"])
    p["source_lineage"]["source_path"] = "tools/trigger2_generation_provenance_gate_v1.py"
    failures, _ = gate._verify_repository_lineage(p, p["repo_path"])
    assert "A02_PRODUCER_SOURCE_LINEAGE_PATH_MISMATCH" in failures
    assert "A02_PRODUCER_SOURCE_LINEAGE_COMMIT_PATH_SHA256_MISMATCH" in failures


def test_a02_baseline_is_authority_derived_and_zero_credit():
    result = gate.adjudicate(_baseline_row())
    assert result["pass"] is True
    assert result["a02_producer_auth_pass"] is True
    assert result["producer_source_verified"] is True
    assert result["producer_source_lineage_verified"] is True
    assert result["policy_digest_verified"] is True
    assert result["producer_invocation_completed"] is True
    assert result["repository_lineage"]["source_commit_is_ancestor_of_head"] is True
    assert result["repository_lineage"]["source_commit_path_sha256"] == _authority()["producer"]["source_sha256"]
    assert result["repository_lineage"]["executed_head_path_sha256"] == _authority()["producer"]["source_sha256"]
    assert result["row_producer_or_policy_fields_authoritative"] is False
    assert result["canonical_dataset_admission"] is False
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0
    assert result["runtime_credit_minted"] == 0
    assert result["jspace_runtime_credit_minted"] == 0
    assert result["hcu_runtime_credit_minted"] == 0
    assert result["entityos_runtime_credit_minted"] == 0
    assert result["canonical_truth_minted"] is False
    assert result["direct_effect_authority_minted"] is False


def test_t2_shpg_a02_fake_executed_rejects():
    row = _baseline_row()
    receipt = row["discriminator_execution_receipts_evaluator_only"][0]
    receipt["executed"] = True
    receipt["execution_receipt_id"] = "invented:receipt"
    result = _assert_reject(row)
    assert "A02_DISCRIMINATOR_RECEIPT_NOT_EXACTLY_AUTHORITY_DERIVED" in result["failures"]


def test_t2_shpg_a02_coherent_receipt_rewrite_rejects():
    row = _baseline_row()
    receipt = row["discriminator_execution_receipts_evaluator_only"][0]
    receipt["execution_receipt_id"] = "t2a02:" + "0" * 64
    receipt["producer_result_jcs_sha256"] = "0" * 64
    result = _assert_reject(row)
    assert "A02_DISCRIMINATOR_RECEIPT_NOT_EXACTLY_AUTHORITY_DERIVED" in result["failures"]


def test_t2_shpg_a02_producer_path_or_sha_swap_rejects():
    row = _baseline_row()
    row["discriminator_producer_binding_evaluator_only"]["repo_path"] = (
        "tools/trigger2_generation_provenance_gate_v1.py"
    )
    row["discriminator_producer_binding_evaluator_only"]["source_sha256"] = "f" * 64
    result = _assert_reject(row)
    assert "A02_ROW_PRODUCER_BINDING_NOT_EXACT_AUTHORITY" in result["failures"]


def test_t2_shpg_a02_source_lineage_swap_rejects():
    row = _baseline_row()
    row["discriminator_producer_binding_evaluator_only"]["source_lineage"][
        "source_commit_sha"
    ] = "0" * 40
    result = _assert_reject(row)
    assert "A02_ROW_PRODUCER_BINDING_NOT_EXACT_AUTHORITY" in result["failures"]


def test_t2_shpg_a02_policy_swap_rejects():
    row = _baseline_row()
    row["discriminator_producer_binding_evaluator_only"]["policy_id"] = "ATTACKER_POLICY"
    row["discriminator_producer_binding_evaluator_only"]["policy_version"] = "999"
    result = _assert_reject(row)
    assert "A02_ROW_PRODUCER_BINDING_NOT_EXACT_AUTHORITY" in result["failures"]


def test_t2_shpg_a02_policy_digest_swap_rejects():
    row = _baseline_row()
    row["discriminator_producer_binding_evaluator_only"]["policy_jcs_sha256"] = "0" * 64
    result = _assert_reject(row)
    assert "A02_ROW_PRODUCER_BINDING_NOT_EXACT_AUTHORITY" in result["failures"]


def test_t2_shpg_a02_prestate_rewrite_rejects_even_if_coverage_could_match():
    row = _baseline_row()
    row["hyperposition_state_before_evaluator_only"]["branches"][0]["v"] = (
        "MUTATED_SEMANTIC_VALUE_WITH_SAME_PREDICTIONS"
    )
    result = _assert_reject(row)
    assert any(
        x.startswith("A02_SUBJECT_NOT_AUTHORITY_RECONSTRUCTED:state_before_jcs_sha256")
        for x in result["failures"]
    )


def test_t2_shpg_a02_world_scoped_event_rewrite_rejects():
    row = _baseline_row()
    row["formal_task_world_evaluator_only"]["world_id"] = "attacker:world"
    result = _assert_reject(row)
    assert "A02_WORLD_SCOPE_MISMATCH" in result["failures"]


def test_t2_shpg_a02_coverage_rewrite_rejects():
    row = _baseline_row()
    receipt = row["discriminator_execution_receipts_evaluator_only"][0]
    receipt["separated_live_pairs"] = receipt["separated_live_pairs"] + 1
    receipt["separates_all_live_pairs"] = not receipt["separates_all_live_pairs"]
    result = _assert_reject(row)
    assert "A02_DISCRIMINATOR_RECEIPT_NOT_EXACTLY_AUTHORITY_DERIVED" in result["failures"]
