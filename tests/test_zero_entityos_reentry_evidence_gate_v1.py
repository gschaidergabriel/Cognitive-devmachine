from __future__ import annotations

import unittest

from tools.run_zero_entityos_variable_grid_fixture_v1 import (
    WorkIdentity,
    claude_reentry_fixture,
)
from tools.zero_entityos_reentry_evidence_gate_v1 import (
    ReentryEvidenceError,
    normalize_reentry_evidence,
)
from tools.zero_entityos_variable_grid_fixture_v1 import (
    RuntimeConfig,
    VariableGridFixture,
)


def reentry(change="TRUE"):
    return {
        "schema": "WORKSPACE_REENTRY/v1",
        "source_result_id": "res-1",
        "source_process_id": "ZECP14",
        "causal_event_id": "ce-1",
        "from_workspace_epoch": 4,
        "to_workspace_epoch": 5,
        "reentry_payload_ref": "fixture:return",
        "reentry_digest": "digest-1",
        "observed_downstream_change": change,
    }


class GateTests(unittest.TestCase):
    def test_stubbed_true_is_downgraded_to_none(self):
        got = normalize_reentry_evidence(
            reentry(), source_metadata={"stubbed": True, "runtime_credit": 0}
        )
        self.assertEqual("TRUE", got["raw_observed_downstream_change"])
        self.assertEqual("UNKNOWN", got["observed_downstream_change"])
        self.assertEqual("NONE", got["causal_credit"])
        self.assertEqual(0, got["global_jspace_causal_credit"])
        self.assertEqual("PACKET_BINDING_ONLY", got["credit_scope"])

    def test_synthetic_fixture_true_is_downgraded_to_none(self):
        got = normalize_reentry_evidence(
            reentry(),
            source_metadata={
                "synthetic_fixture_return": True,
                "runtime_credit": "SYNTHETIC_REFERENCE_FIXTURE_ONLY",
            },
        )
        self.assertEqual("UNKNOWN", got["observed_downstream_change"])
        self.assertEqual("NONE", got["causal_credit"])
        self.assertEqual("GLOBAL_WORKSPACE_REENTRY_RECEIPT_CONTRACT/v1", got["positive_promotion_contract"])

    def test_unmeasured_non_synthetic_true_is_still_none(self):
        got = normalize_reentry_evidence(
            reentry(), source_metadata={"runtime_credit": "OBSERVED_INTERFACE_UNMEASURED"}
        )
        self.assertEqual("UNKNOWN", got["observed_downstream_change"])
        self.assertEqual("NONE", got["causal_credit"])
        self.assertEqual("REENTRY_PRESENT_UNMEASURED", got["credit_scope"])

    def test_false_and_unknown_are_preserved_as_raw_but_not_promoted(self):
        for change in ("FALSE", "UNKNOWN"):
            got = normalize_reentry_evidence(
                reentry(change), source_metadata={"runtime_credit": "OBSERVED_INTERFACE_UNMEASURED"}
            )
            self.assertEqual(change, got["raw_observed_downstream_change"])
            self.assertEqual("UNKNOWN", got["observed_downstream_change"])
            self.assertEqual("NONE", got["causal_credit"])

    def test_bad_reentry_schema_fails_closed(self):
        bad = reentry()
        bad["schema"] = "OTHER/v1"
        with self.assertRaisesRegex(ReentryEvidenceError, "REENTRY_SCHEMA_MISMATCH"):
            normalize_reentry_evidence(bad)

    def test_current_class_fixture_stub_is_downgraded(self):
        census = {
            "schema": "ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS/v1",
            "processes": [
                {
                    "id": "ZECP14",
                    "implementation_class": "EXTERNAL_STRONG_MODEL_BRIDGE",
                }
            ],
        }
        abi = {"schema": "COGNITIVE_PROCESS_ABI/v1"}
        rt = VariableGridFixture(census, abi, RuntimeConfig(requested_n=1, available_n=1))
        try:
            admission = rt.admit_task({"task": "reentry-gate-integration"})
            raw = rt.stub_claude_roundtrip(
                admission, "work-integration-1", 7, ["db:fixture:state"]
            )
            self.assertEqual("TRUE", raw["reentry"]["observed_downstream_change"])
            got = normalize_reentry_evidence(
                raw["reentry"], source_metadata=raw["result"]
            )
            self.assertEqual("UNKNOWN", got["observed_downstream_change"])
            self.assertEqual("NONE", got["causal_credit"])
            self.assertEqual(0, got["global_jspace_causal_credit"])
        finally:
            rt.close()

    def test_current_runner_synthetic_fixture_is_downgraded(self):
        work = WorkIdentity(
            causal_event_id="fixture-event-001",
            admission_id="fixture-admission-001",
            generation=1,
            work_id="fixture-work-001",
            process_id="ZECP06",
        )
        raw = claude_reentry_fixture(work, {"candidate": "A"})
        self.assertEqual("TRUE", raw["reentry"]["observed_downstream_change"])
        got = normalize_reentry_evidence(
            raw["reentry"], source_metadata=raw["return"]
        )
        self.assertEqual("UNKNOWN", got["observed_downstream_change"])
        self.assertEqual("NONE", got["causal_credit"])
        self.assertEqual(0, got["global_jspace_causal_credit"])


if __name__ == "__main__":
    unittest.main()
