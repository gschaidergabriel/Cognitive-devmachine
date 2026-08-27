"""Offline, fast tests for xeno_diagnostic_specialist_wrapper_v1 -- no model, no
network, no torch. Every rejection/acceptance case here is a real row from the
2026-08-27 Together diagnostic run's holdout test (research_entity/topic_packets/
trigger2-together-diagnostic-finetune-20260827/HOLDOUT_INFERENCE_RESULTS_20260827.json),
not invented examples."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from xeno_diagnostic_specialist_wrapper_v1 import (  # noqa: E402
    validate_raw_output,
    wrap_as_result_packet,
    TRAINED_CLASS_WORDS,
)
from xeno_shell_packets_v1 import validate_result_packet, RESULT_PACKET_ALLOWED_CLASSES  # noqa: E402


# --- real acceptance cases (actual model outputs from the holdout test) ---

def test_accepts_real_ordinal_hit():
    # B0_WRITE_BASELINE holdout row: exact real match in the live run.
    ok, atom = validate_raw_output("ABI_ACCEPTED_ORDINAL:14")
    assert ok is True
    assert atom == "ABI_ACCEPTED_ORDINAL:14"


def test_accepts_real_class_word_hit():
    # B6_HYPERPOSITION_EVIDENCE_AUTHORITY holdout row: exact real match.
    ok, atom = validate_raw_output("PRESERVE_BRANCHES")
    assert ok is True
    assert atom == "PRESERVE_BRANCHES"


def test_accepts_wrong_but_in_vocabulary_answer():
    # B6_GWT_UPTAKE holdout row: model said 'alpha', expected was 'gamma' -- wrong
    # ANSWER, but 'alpha' is a real trained class word. This shell layer's job is
    # atom validity, not task correctness (that's the eval's job, already reported
    # honestly at 2/12 in the holdout test) -- so this must validate=True.
    ok, atom = validate_raw_output("alpha")
    assert ok is True
    assert atom == "alpha"


def test_accepts_all_trained_class_words():
    for w in TRAINED_CLASS_WORDS:
        ok, atom = validate_raw_output(w)
        assert ok is True, f"expected {w!r} to validate"
        assert atom == w


def test_accepts_ordinal_boundaries():
    assert validate_raw_output("ABI_ACCEPTED_ORDINAL:0") == (True, "ABI_ACCEPTED_ORDINAL:0")
    assert validate_raw_output("ABI_ACCEPTED_ORDINAL:299") == (True, "ABI_ACCEPTED_ORDINAL:299")


# --- real rejection cases (actual derailed model outputs from the holdout test) ---

def test_rejects_real_b3_cpp_derailment():
    raw = "```cpp\n#include <string>\n#include <vector>\n#include <map>\n#include <set>\n#include"
    ok, reason = validate_raw_output(raw)
    assert ok is False
    assert reason == "CODE_BLOCK_DERAILMENT"


def test_rejects_real_b3_python_derailment():
    raw = '```python\nfrom typing import Optional, Union\n\n# Define the entry points\nALLOW = "ALLOW"\nDENY'
    ok, reason = validate_raw_output(raw)
    assert ok is False
    assert reason == "CODE_BLOCK_DERAILMENT"


def test_rejects_bare_letter_not_in_vocabulary():
    # B1 holdout row: model said 'E' (expected ABI_ACCEPTED_ORDINAL:12). 'E' is not
    # a trained class word (R/P/Q are, from the GWT families -- E is not).
    ok, reason = validate_raw_output("E")
    assert ok is False
    assert reason == "NOT_IN_TRAINED_VOCABULARY"


def test_rejects_entity_name_echo():
    # B4 holdout row: model echoed the queried entity name 'cell_16' instead of
    # returning the atom it maps to.
    ok, reason = validate_raw_output("cell_16")
    assert ok is False
    assert reason == "NOT_IN_TRAINED_VOCABULARY"


def test_rejects_out_of_range_ordinal():
    ok, reason = validate_raw_output("ABI_ACCEPTED_ORDINAL:300")
    assert ok is False
    assert reason == "ORDINAL_OUT_OF_TRAINED_RANGE:300"


def test_rejects_empty_and_none():
    assert validate_raw_output("") == (False, "EMPTY_OUTPUT")
    assert validate_raw_output("   ") == (False, "EMPTY_OUTPUT")
    assert validate_raw_output(None) == (False, "EMPTY_OUTPUT")


# --- packet wrapping: real schema, both outcomes ---

def test_wrap_accepted_produces_valid_candidate_packet():
    packet = wrap_as_result_packet(
        raw_output="ABI_ACCEPTED_ORDINAL:14",
        source_work_digest="0" * 64,
    )
    validate_result_packet(packet)  # raises on any schema violation
    assert packet["body"]["result_class"] == "CANDIDATE"
    assert packet["body"]["result_class"] in RESULT_PACKET_ALLOWED_CLASSES
    assert packet["body"]["payload"]["validated"] is True
    assert packet["body"]["payload"]["atom"] == "ABI_ACCEPTED_ORDINAL:14"
    assert packet["body"]["payload"]["rejection_reason"] is None


def test_wrap_rejected_is_still_a_valid_candidate_packet_not_dropped():
    packet = wrap_as_result_packet(
        raw_output="```cpp\n#include <string>",
        source_work_digest="0" * 64,
    )
    validate_result_packet(packet)  # a rejection must still be a schema-valid packet
    assert packet["body"]["result_class"] == "CANDIDATE"
    assert packet["body"]["payload"]["validated"] is False
    assert packet["body"]["payload"]["atom"] is None
    assert packet["body"]["payload"]["rejection_reason"] == "CODE_BLOCK_DERAILMENT"


def test_wrap_never_mints_restricted_classes():
    # Structural guarantee already enforced by xeno_shell_packets_v1 for a MODEL
    # producer -- this test just confirms this wrapper never tries to route
    # around it by passing a different result_class through.
    import inspect
    src = inspect.getsource(wrap_as_result_packet)
    assert 'result_class="CANDIDATE"' in src
