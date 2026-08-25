from __future__ import annotations

from copy import deepcopy

from tools import trigger2_discriminator_producer_auth_v1 as auth
from tools import trigger2_trusted_hyperposition_pilot_generator_v1 as generator


def _upstream_generation_pass():
    case = auth._authority()["allowed_cases"][generator.CASE_ID]
    return {
        "schema": auth.EXPECTED_UPSTREAM_GENERATION_SCHEMA,
        "pass": True,
        "generation_provenance_pass": True,
        "failures": [],
        "reconstructed_subject_hashes": {
            "formal_world_jcs_sha256": case["formal_world_sha256"],
            "state_before_jcs_sha256": case["state_before_sha256"],
            "event_jcs_sha256": case["event_sha256"],
        },
        "expected_generation_receipt": {
            "schema": "UNIT_TEST_GENERATION_RECEIPT",
            "generation_case_id": generator.CASE_ID,
            "world_id": case["world_id"],
            "event_id": case["event_id"],
        },
    }


def _row():
    bundle = generator.build_subjects(generator.CASE_ID, generator.default_parameters())
    return {
        "generation_case_id_evaluator_only": generator.CASE_ID,
        "formal_task_world_evaluator_only": deepcopy(bundle["formal_world"]),
        "hyperposition_state_before_evaluator_only": deepcopy(bundle["state_before"]),
        "hyperposition_genesis_state_evaluator_only": deepcopy(bundle["genesis_state"]),
        "synthetic_event_history_evaluator_only": deepcopy(bundle["event_history"]),
        "synthetic_test_event_evaluator_only": deepcopy(bundle["event"]),
        "discriminator_execution_receipts_evaluator_only": [],
    }


def _derive(row):
    result, sanitized = auth.authenticate_and_sanitize(row, _upstream_generation_pass())
    assert result["pass"], result
    assert sanitized is not None
    return result, sanitized


def _claim(row, receipt):
    row["discriminator_execution_receipts_evaluator_only"] = [receipt]
    return auth.authenticate_and_sanitize(row, _upstream_generation_pass())


def _coherent_reid(receipt):
    receipt["execution_receipt_id"] = "t2disc:" + auth._digest(receipt["producer"])
    return receipt


def test_A02_happy_path_derives_receipt_from_repository_authority_and_execution():
    row = _row()
    result, sanitized = _derive(row)
    receipt = result["reconstructed_discriminator_receipt"]
    authority = auth._authority()

    assert receipt["admissible"] is True
    assert receipt["executed"] is True
    assert receipt["synthetic_execution"] is True
    assert receipt["execution_scope"] == "DETERMINISTIC_EVALUATOR_ONLY"
    assert receipt["producer"]["producer_repo_path"] == auth.EXPECTED_REPO_PATH
    assert receipt["producer"]["producer_source_sha256"] == authority["producer"]["source_sha256"]
    assert receipt["producer"]["producer_source_commit_sha"] == authority["producer"]["source_commit_sha"]
    assert receipt["producer"]["policy_sha256"] == authority["allowed_cases"][generator.CASE_ID]["policy_sha256"]
    assert sanitized["discriminator_execution_receipts_evaluator_only"] == [receipt]
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0
    assert result["runtime_credit_minted"] == 0
    assert result["canonical_truth_minted"] is False
    assert result["direct_effect_authority_minted"] is False


def test_T2_SHPG_A02_FAKE_EXECUTED_rejected():
    row = _row()
    result, _ = _derive(row)
    forged = deepcopy(result["reconstructed_discriminator_receipt"])
    forged["executed"] = True
    forged["execution_receipt_id"] = "attacker:asserted-executed"

    result2, sanitized2 = _claim(row, forged)
    assert not result2["pass"]
    assert sanitized2 is None
    assert "ROW_CARRIED_DISCRIMINATOR_RECEIPT_DIFFERS_FROM_AUTHENTICATED_PRODUCER_OUTPUT" in result2["failures"]


def test_T2_SHPG_A02_COHERENT_RECEIPT_REWRITE_rejected():
    row = _row()
    result, _ = _derive(row)
    forged = deepcopy(result["reconstructed_discriminator_receipt"])
    forged["producer"]["ordering_result_sha256"] = "1" * 64
    _coherent_reid(forged)

    result2, sanitized2 = _claim(row, forged)
    assert not result2["pass"]
    assert sanitized2 is None
    assert "ROW_CARRIED_DISCRIMINATOR_RECEIPT_DIFFERS_FROM_AUTHENTICATED_PRODUCER_OUTPUT" in result2["failures"]


def test_T2_SHPG_A02_PRODUCER_PATH_OR_SHA_SWAP_rejected():
    row = _row()
    result, _ = _derive(row)
    forged = deepcopy(result["reconstructed_discriminator_receipt"])
    forged["producer"]["producer_repo_path"] = "tools/attacker_equivalent_producer.py"
    forged["producer"]["producer_source_sha256"] = "0" * 64
    _coherent_reid(forged)

    result2, sanitized2 = _claim(row, forged)
    assert not result2["pass"]
    assert sanitized2 is None
    assert "ROW_CARRIED_DISCRIMINATOR_RECEIPT_DIFFERS_FROM_AUTHENTICATED_PRODUCER_OUTPUT" in result2["failures"]


def test_T2_SHPG_A02_POLICY_SWAP_rejected():
    row = _row()
    result, _ = _derive(row)
    forged = deepcopy(result["reconstructed_discriminator_receipt"])
    forged["producer"]["policy_sha256"] = "2" * 64
    forged["producer"]["formal_discriminator_spec_sha256"] = "3" * 64
    _coherent_reid(forged)

    result2, sanitized2 = _claim(row, forged)
    assert not result2["pass"]
    assert sanitized2 is None
    assert "ROW_CARRIED_DISCRIMINATOR_RECEIPT_DIFFERS_FROM_AUTHENTICATED_PRODUCER_OUTPUT" in result2["failures"]


def test_T2_SHPG_A02_PRESTATE_REWRITE_same_coverage_rejected():
    row = _row()
    row["hyperposition_state_before_evaluator_only"]["query_id"] = "attacker:same-branches"
    row["hyperposition_genesis_state_evaluator_only"] = deepcopy(
        row["hyperposition_state_before_evaluator_only"]
    )
    result, sanitized = auth.authenticate_and_sanitize(row, _upstream_generation_pass())

    assert not result["pass"]
    assert sanitized is None
    assert "DISCRIMINATOR_PRESTATE_AUTHORITY_DIGEST_MISMATCH" in result["failures"]


def test_T2_SHPG_A02_WORLD_SCOPED_EVENT_REWRITE_rejected():
    row = _row()
    row["formal_task_world_evaluator_only"]["world_id"] = "attacker:other-world"
    result, sanitized = auth.authenticate_and_sanitize(row, _upstream_generation_pass())

    assert not result["pass"]
    assert sanitized is None
    assert (
        "DISCRIMINATOR_WORLD_ID_AUTHORITY_MISMATCH" in result["failures"]
        or "DISCRIMINATOR_FORMAL_WORLD_AUTHORITY_DIGEST_MISMATCH" in result["failures"]
    )


def test_T2_SHPG_A02_COVERAGE_REWRITE_rejected():
    row = _row()
    result, _ = _derive(row)
    forged = deepcopy(result["reconstructed_discriminator_receipt"])
    forged["separated_live_pairs"] = forged["separated_live_pairs"] + 1
    forged["separates_all_live_pairs"] = True
    _coherent_reid(forged)

    result2, sanitized2 = _claim(row, forged)
    assert not result2["pass"]
    assert sanitized2 is None
    assert "ROW_CARRIED_DISCRIMINATOR_RECEIPT_DIFFERS_FROM_AUTHENTICATED_PRODUCER_OUTPUT" in result2["failures"]


def test_A02_admissibility_is_derived_from_pinned_formal_spec_not_row_boolean():
    row = _row()
    row["formal_task_world_evaluator_only"]["tests"]["db_probe"]["risk_rank"] = 99
    result, sanitized = auth.authenticate_and_sanitize(row, _upstream_generation_pass())

    assert not result["pass"]
    assert sanitized is None
    assert "FORMAL_DISCRIMINATOR_SPEC_MISMATCH" in result["failures"]


def test_A02_repository_authority_source_hash_is_fail_closed(monkeypatch):
    row = _row()
    original = auth._authority

    def mutated_authority():
        value = deepcopy(original())
        value["producer"]["source_sha256"] = "0" * 64
        return value

    monkeypatch.setattr(auth, "_authority", mutated_authority)
    result, sanitized = auth.authenticate_and_sanitize(row, _upstream_generation_pass())

    assert not result["pass"]
    assert sanitized is None
    assert "DISCRIMINATOR_PRODUCER_SOURCE_SHA256_AUTHORITY_MISMATCH" in result["failures"]


def test_A02_nonempty_history_fails_closed_in_bounded_v1():
    row = _row()
    row["synthetic_event_history_evaluator_only"] = [
        deepcopy(row["synthetic_test_event_evaluator_only"])
    ]
    result, sanitized = auth.authenticate_and_sanitize(row, _upstream_generation_pass())

    assert not result["pass"]
    assert sanitized is None
    assert "DISCRIMINATOR_PRODUCER_V1_REQUIRES_EMPTY_HISTORY" in result["failures"]


def test_A02_requires_upstream_generation_provenance_pass():
    row = _row()
    result, sanitized = auth.authenticate_and_sanitize(
        row,
        {
            "schema": auth.EXPECTED_UPSTREAM_GENERATION_SCHEMA,
            "pass": False,
            "generation_provenance_pass": False,
        },
    )

    assert not result["pass"]
    assert sanitized is None
    assert "UPSTREAM_GENERATION_PROVENANCE_PASS_REQUIRED" in result["failures"]
