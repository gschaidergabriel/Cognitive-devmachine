from __future__ import annotations

from copy import deepcopy

from tools import trigger2_db_match_row_assembler_v1 as assembler
from tools import trigger2_hyperposition_state_history_generation_bound_gate_v4 as v4


def test_assembled_row_passes_full_v4_chain():
    row = assembler.assemble_db_match_row()
    result = v4.adjudicate(row)
    assert result["failures"] == []
    assert result["pass"] is True
    assert result["candidate_pre_admission_pass"] is True


def test_assembled_row_mints_zero_credit():
    row = assembler.assemble_db_match_row()
    result = v4.adjudicate(row)
    assert result["canonical_dataset_admission"] is False
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0
    assert result["canonical_truth_minted"] is False
    assert result["direct_effect_authority_minted"] is False


def test_exact_replay_of_accepted_row_is_plus_zero():
    row = assembler.assemble_db_match_row()
    first = v4.adjudicate(row)
    second = v4.adjudicate(row)
    assert first["pass"] == second["pass"] == True
    assert first["failures"] == second["failures"] == []
    # re-adjudicating a candidate is a pure evaluation with no persisted
    # ledger/dataset write in this composer -- credit fields must stay
    # identically zero on every replay, never double-counted.
    for key in (
        "accepted_dataset_tokens_minted",
        "training_credit_minted",
        "canonical_dataset_admission",
    ):
        assert first[key] == second[key]


def test_two_independent_assemblies_are_structurally_identical():
    row_a = assembler.assemble_db_match_row()
    row_b = assembler.assemble_db_match_row()
    assert row_a == row_b


def test_missing_tokenizer_atoms_fails_closed():
    row = assembler.assemble_db_match_row()
    del row["tokenizer_atoms_used"]
    result = v4.adjudicate(row)
    assert result["pass"] is False
    assert any("TOKENIZER_ABI" in f for f in result["failures"])


def test_forged_discriminator_producer_binding_fails_closed():
    row = assembler.assemble_db_match_row()
    row["discriminator_producer_binding_evaluator_only"]["source_sha256"] = "0" * 64
    result = v4.adjudicate(row)
    assert result["pass"] is False
    assert any("A02" in f for f in result["failures"])


def test_forged_event_digest_registry_fails_closed():
    row = assembler.assemble_db_match_row()
    event_id = row["synthetic_test_event_evaluator_only"]["event_id"]
    row["event_digest_registry_evaluator_only"]["events"][event_id] = "f" * 64
    result = v4.adjudicate(row)
    assert result["pass"] is False


def test_forged_v3_reference_target_fails_closed():
    row = assembler.assemble_db_match_row()
    row["v3_reference_target_evaluator_only"]["state_after"] = None
    result = v4.adjudicate(row)
    assert result["pass"] is False


def test_nonempty_history_transplant_fails_closed_under_a02():
    # HIST_CHAIN-style transplant onto a DB_MATCH-authorized row body: the
    # A02 gate is scoped to empty-history cases in the current authority
    # (supervisor 8.89 P1_A02_NONEMPTY_HISTORY_DECISION); confirms the
    # scoping is actually enforced, not just documented.
    row = assembler.assemble_db_match_row()
    row["synthetic_event_history_evaluator_only"] = [
        deepcopy(row["synthetic_test_event_evaluator_only"])
    ]
    result = v4.adjudicate(row)
    assert result["pass"] is False


def test_tampered_prompt_after_generation_receipt_fails_closed():
    # Was a tracked strict-xfail P0 gap (found 2026-08-26): none of the previously wired
    # 5 gates bound row['prompt']. Closed by tools/trigger2_prompt_content_binding_gate_v1.py,
    # wired as the v4 composer's 6th and final per-row check.
    row = assembler.assemble_db_match_row()
    row["prompt"] = "UNAUTHORIZED PROMPT SWAP"
    result = v4.adjudicate(row)
    assert result["pass"] is False
    assert any("PROMPT_CONTENT_BINDING" in f for f in result["failures"])


def test_forged_prompt_binding_sha256_without_touching_prompt_fails_closed():
    row = assembler.assemble_db_match_row()
    row["prompt_binding_evaluator_only"]["prompt_sha256"] = "0" * 64
    result = v4.adjudicate(row)
    assert result["pass"] is False
    assert any("PROMPT_CONTENT_BINDING" in f for f in result["failures"])


def test_missing_prompt_binding_evaluator_only_fails_closed():
    row = assembler.assemble_db_match_row()
    del row["prompt_binding_evaluator_only"]
    result = v4.adjudicate(row)
    assert result["pass"] is False
    assert any("PROMPT_CONTENT_BINDING" in f for f in result["failures"])
