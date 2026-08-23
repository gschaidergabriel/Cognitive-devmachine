import hashlib
import unittest
from dataclasses import replace

from entry_canonicalization_v1 import canonicalize
from jspace_gwt_prototype_v1 import (
    GWTCompetitionRecord,
    JSpaceGWTError,
    JSpaceGWTTransitionTrace,
    TRACE_SCHEMA,
    SELECTOR_SCHEMA,
    trace_material,
    validate_transition_trace,
)
from jspace_vector_control_v1 import ABI_SCHEMA, CODEC_SCHEMA


def _rehash(trace: JSpaceGWTTransitionTrace) -> JSpaceGWTTransitionTrace:
    digest = hashlib.sha256(canonicalize(trace_material(trace))).hexdigest()
    return replace(trace, trace_sha256=digest)


def _valid_trace() -> JSpaceGWTTransitionTrace:
    trace = JSpaceGWTTransitionTrace(
        schema_version=TRACE_SCHEMA,
        trace_id="trace:validator:1",
        generation=91,
        entry_event_sha256="1" * 64,
        entry_admission_sha256="2" * 64,
        route_decision_sha256="3" * 64,
        grid_plan_sha256="4" * 64,
        cell_id="cell-02",
        role="critic",
        jspace_basis_id="basis:test:validator",
        jspace_basis_sha256="5" * 64,
        jspace_input_vector_ref="sha256:" + "6" * 64,
        jspace_input_codec_version=CODEC_SCHEMA,
        jspace_vector_control_abi=ABI_SCHEMA,
        local_workspace_state_ref="entityos:workspace:test:validator",
        gwt_selector_schema=SELECTOR_SCHEMA,
        gwt_selection_sha256="7" * 64,
        gwt_competition_set=(
            GWTCompetitionRecord(
                candidate_id="cand:critic",
                role="critic",
                score=90_000,
                selected=True,
                evidence_ref="evidence:critic",
                evidence_sha256="8" * 64,
            ),
            GWTCompetitionRecord(
                candidate_id="cand:world",
                role="world",
                score=40_000,
                selected=False,
                evidence_ref="evidence:world",
                evidence_sha256="9" * 64,
            ),
        ),
        gwt_winner_ids=("cand:critic",),
        gwt_broadcast_gate=True,
        global_jspace_slice_ref="entityos:jspace:slice:test:validator",
        hyperposition_branch_ids=("branch:a", "branch:b"),
        evidence_class="DETERMINISTIC_CONTROL",
        resource_budget=(("model_tokens", 256), ("wall_ms", 2500)),
        requested_action_class="STRUCTURED_HCU_CANDIDATE",
        expected_structured_model_output={"schema": "HCU_ROLE_OUTPUT/v1"},
        observed_downstream_outcome={"status": "OBSERVED", "accepted": False},
        falsifier_lesion_condition="BASELINE",
        credit_label="NEUTRAL",
        trace_sha256="0" * 64,
    )
    return _rehash(trace)


class JSpaceGWTTraceValidationTests(unittest.TestCase):
    def test_canonical_trace_still_validates(self):
        validate_transition_trace(_valid_trace())

    def test_rehashed_invalid_evidence_class_is_rejected(self):
        poisoned = _rehash(replace(_valid_trace(), evidence_class="SELF_ASSERTED"))
        with self.assertRaisesRegex(JSpaceGWTError, "evidence_class:UNSUPPORTED"):
            validate_transition_trace(poisoned)

    def test_rehashed_noncanonical_resource_budget_is_rejected(self):
        poisoned = _rehash(
            replace(
                _valid_trace(),
                resource_budget=(("model_tokens", 128), ("model_tokens", 256), ("wall_ms", 2500)),
            )
        )
        with self.assertRaisesRegex(JSpaceGWTError, "RESOURCE_BUDGET_CANONICAL_TUPLE_REQUIRED"):
            validate_transition_trace(poisoned)

    def test_rehashed_winner_selection_mismatch_is_rejected(self):
        poisoned = _rehash(replace(_valid_trace(), gwt_winner_ids=("cand:world",)))
        with self.assertRaisesRegex(JSpaceGWTError, "GWT_WINNER_SELECTION_MISMATCH"):
            validate_transition_trace(poisoned)

    def test_rehashed_unknown_lesion_condition_is_rejected(self):
        poisoned = _rehash(replace(_valid_trace(), falsifier_lesion_condition="SELF_REPORT_ONLY"))
        with self.assertRaisesRegex(JSpaceGWTError, "falsifier_lesion_condition:UNSUPPORTED"):
            validate_transition_trace(poisoned)


if __name__ == "__main__":
    unittest.main()
