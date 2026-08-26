from __future__ import annotations

from copy import deepcopy

import pytest

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


@pytest.mark.xfail(
    strict=True,
    reason=(
        "KNOWN P0 GAP (found 2026-08-26, DB_MATCH production assembler build): none "
        "of the 5 wired v4 per-row gates (generation/A02/epistemic/tokenizer-ABI/replay) "
        "bind or verify the actual model_visible content -- 'prompt' is not covered by "
        "generation_receipt_evaluator_only, the A02 discriminator binding, the digest "
        "registry, or the replay proof. A row's candidate_pre_admission_pass is entirely "
        "about *_evaluator_only provenance/formal-world fields; the literal text a model "
        "would actually be trained on can be swapped after assembly with zero detection. "
        "Must be closed (e.g. prompt content hashed into generation_receipt_evaluator_only "
        "or a new prompt-binding gate) before any real admission, not just before scaling."
    ),
)
def test_tampered_prompt_after_generation_receipt_fails_closed():
    row = assembler.assemble_db_match_row()
    row["prompt"] = "UNAUTHORIZED PROMPT SWAP"
    result = v4.adjudicate(row)
    assert result["pass"] is False
