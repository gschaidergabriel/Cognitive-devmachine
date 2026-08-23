import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "ucf_causal_validator", ROOT / "tools" / "validate_unified_cognitive_fabric_receipt_v1.py"
)
ucf = importlib.util.module_from_spec(VALIDATOR_SPEC)
assert VALIDATOR_SPEC.loader is not None
VALIDATOR_SPEC.loader.exec_module(ucf)

FIXTURE_SPEC = importlib.util.spec_from_file_location(
    "ucf_fixture", ROOT / "tests" / "test_unified_cognitive_fabric_receipt_v1.py"
)
fixture = importlib.util.module_from_spec(FIXTURE_SPEC)
assert FIXTURE_SPEC.loader is not None
FIXTURE_SPEC.loader.exec_module(fixture)


def redigest(receipt):
    receipt["receipt_envelope_digest"] = "0" * 64
    receipt["receipt_envelope_digest"] = ucf.canonical_digest(receipt)
    return receipt


def claude_executed_receipt():
    receipt = fixture.valid_receipt()
    receipt["inference"].update(
        engine_class="claude_code",
        executed=True,
        jspace_mode="COMPILED_EXTERNAL",
        local_activation_access=False,
        external_hidden_state_claimed=False,
        adapter_version="claude-code-adapter/v1",
    )
    receipt["execution"].update(lane_cost_class="FREE", lane_admitted=True, network_touch_count=1)
    return redigest(receipt)


def test_executed_compiled_external_requires_jspace_observation():
    receipt = claude_executed_receipt()
    receipt["workspace"]["jspace_observation_refs"] = []
    redigest(receipt)
    with pytest.raises(ucf.ReceiptError, match="EXECUTED_NONPLAIN_JSPACE_REQUIRES_OBSERVATION"):
        ucf.validate(receipt)


def test_executed_cognitive_cycle_requires_one_gwt_winner():
    receipt = claude_executed_receipt()
    receipt["workspace"]["gwt_winners"] = []
    redigest(receipt)
    with pytest.raises(ucf.ReceiptError, match="EXECUTED_COGNITIVE_CYCLE_REQUIRES_GWT_WINNER"):
        ucf.validate(receipt)


def test_blocked_nonexecuted_receipt_may_carry_no_causal_claim():
    receipt = claude_executed_receipt()
    receipt["workspace"]["jspace_observation_refs"] = []
    receipt["workspace"]["gwt_winners"] = []
    receipt["inference"].update(executed=False, candidate_result_digest=None, epistemic_status="NOT_APPLICABLE")
    receipt["authority"].update(validation_decision="BLOCKED", canonical_write_committed=False)
    receipt["execution"]["lane_admitted"] = False
    redigest(receipt)
    assert ucf.validate(receipt)["ok"] is True


def test_plain_compatibility_may_omit_jspace_observation_but_not_gwt_winner():
    receipt = fixture.valid_receipt()
    receipt["workspace"]["jspace_observation_refs"] = []
    receipt["inference"].update(
        engine_class="adaptive_backend",
        jspace_mode="PLAIN_COMPATIBILITY",
        local_activation_access=False,
        external_hidden_state_claimed=False,
        adapter_version="adaptive-backend/v1",
    )
    redigest(receipt)
    assert ucf.validate(receipt)["ok"] is True


def test_jspace_observation_refs_are_typed_and_unique():
    receipt = claude_executed_receipt()
    receipt["workspace"]["jspace_observation_refs"] = ["j:layer:12", "j:layer:12"]
    redigest(receipt)
    with pytest.raises(ucf.ReceiptError, match="JSPACE_OBSERVATION_REF_DUPLICATE"):
        ucf.validate(receipt)

    receipt = claude_executed_receipt()
    receipt["workspace"]["jspace_observation_refs"] = [""]
    redigest(receipt)
    with pytest.raises(ucf.ReceiptError, match="JSPACE_OBSERVATION_REF_INVALID"):
        ucf.validate(receipt)
