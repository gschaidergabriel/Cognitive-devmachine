from __future__ import annotations

from hashlib import sha256

from tools import trigger2_prompt_content_binding_gate_v1 as gate
from tools import trigger2_trusted_hyperposition_pilot_generator_v1 as generator


def _valid_row() -> dict:
    case_id = generator.CASE_ID
    parameters = generator.default_parameters()
    prompt = generator.render_prompt(case_id, parameters)
    return {
        "prompt": prompt,
        "generation_case_id_evaluator_only": case_id,
        "generation_parameters_evaluator_only": parameters,
        "prompt_binding_evaluator_only": {
            "prompt_sha256": sha256(prompt.encode("utf-8")).hexdigest(),
            "render_source": "trigger2_trusted_hyperposition_pilot_generator_v1.render_prompt",
        },
    }


def test_valid_row_passes():
    result = gate.adjudicate(_valid_row())
    assert result["pass"] is True
    assert result["failures"] == []


def test_missing_prompt_fails_closed():
    row = _valid_row()
    del row["prompt"]
    result = gate.adjudicate(row)
    assert result["pass"] is False
    assert "PROMPT_MISSING_OR_NOT_STRING" in result["failures"]


def test_missing_generation_case_id_fails_closed():
    row = _valid_row()
    del row["generation_case_id_evaluator_only"]
    result = gate.adjudicate(row)
    assert result["pass"] is False
    assert "GENERATION_CASE_ID_EVALUATOR_ONLY_MISSING" in result["failures"]


def test_unknown_case_id_fails_closed():
    row = _valid_row()
    row["generation_case_id_evaluator_only"] = "UNKNOWN_CASE_ID_NOT_IN_AUTHORITY"
    result = gate.adjudicate(row)
    assert result["pass"] is False
    assert any("RENDER_PROMPT_EXCEPTION" in f for f in result["failures"])


def test_mismatched_parameters_fails_closed():
    row = _valid_row()
    row["generation_parameters_evaluator_only"] = {"tampered": True}
    result = gate.adjudicate(row)
    assert result["pass"] is False
    assert any("RENDER_PROMPT_EXCEPTION" in f for f in result["failures"])


def test_wrong_prompt_text_fails_closed():
    # only row['prompt'] is tampered; prompt_binding_evaluator_only still carries the
    # correct hash of the *authorized* prompt, so the binding-claim check itself does not
    # fire here -- the actual-vs-expected prompt comparisons are what catch this.
    row = _valid_row()
    row["prompt"] = "something else entirely"
    result = gate.adjudicate(row)
    assert result["pass"] is False
    assert "PROMPT_DOES_NOT_MATCH_RENDERED_AUTHORITY" in result["failures"]
    assert "PROMPT_SHA256_MISMATCH" in result["failures"]


def test_forged_render_source_fails_closed():
    row = _valid_row()
    row["prompt_binding_evaluator_only"]["render_source"] = "some_other_module.render"
    result = gate.adjudicate(row)
    assert result["pass"] is False
    assert "PROMPT_BINDING_RENDER_SOURCE_MISMATCH" in result["failures"]


def test_zero_credit_boundary():
    result = gate.adjudicate(_valid_row())
    assert result["canonical_dataset_admission"] is False
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0
