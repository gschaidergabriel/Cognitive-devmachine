from __future__ import annotations

import unittest

from tools.zero_entityos_reentry_evidence_gate_v1 import (
    ReentryEvidenceError,
    normalize_reentry_evidence,
)


def reentry():
    return {
        "schema": "WORKSPACE_REENTRY/v1",
        "source_result_id": "res-1",
        "source_process_id": "ZECP14",
        "causal_event_id": "ce-1",
        "from_workspace_epoch": 4,
        "to_workspace_epoch": 5,
        "reentry_payload_ref": "fixture:return",
        "reentry_digest": "digest-1",
        "observed_downstream_change": "TRUE",
    }


def measurement(change="TRUE"):
    return {
        "schema": "WORKSPACE_REENTRY_CAUSAL_MEASUREMENT/v1",
        "measurement_id": "m-1",
        "source_result_id": "res-1",
        "causal_event_id": "ce-1",
        "reentry_digest": "digest-1",
        "intervention_id": "i-1",
        "matched_control_id": "c-1",
        "metric_id": "task-delta-v1",
        "baseline_value": 0.2,
        "intervention_value": 0.5,
        "observed_downstream_change": change,
        "off_target_result": "PASS",
        "observation_surface": "EXPOSED_WORKSPACE_INTERFACE",
    }


class GateTests(unittest.TestCase):
    def test_stubbed_true_is_downgraded(self):
        got = normalize_reentry_evidence(
            reentry(), source_metadata={"stubbed": True, "runtime_credit": 0}
        )
        self.assertEqual("UNKNOWN", got["observed_downstream_change"])
        self.assertEqual(0, got["causal_credit"])
        self.assertEqual(0, got["global_jspace_causal_credit"])

    def test_synthetic_fixture_true_is_downgraded(self):
        got = normalize_reentry_evidence(
            reentry(),
            source_metadata={
                "synthetic_fixture_return": True,
                "runtime_credit": "SYNTHETIC_REFERENCE_FIXTURE_ONLY",
            },
        )
        self.assertEqual("UNKNOWN", got["observed_downstream_change"])
        self.assertEqual("PACKET_BINDING_ONLY", got["credit_scope"])

    def test_unmeasured_non_synthetic_true_is_downgraded(self):
        got = normalize_reentry_evidence(
            reentry(), source_metadata={"runtime_credit": "OBSERVED_INTERFACE"}
        )
        self.assertEqual("UNKNOWN", got["observed_downstream_change"])
        self.assertEqual(0, got["causal_credit"])

    def test_valid_matched_measurement_scopes_credit_to_observable_reentry(self):
        got = normalize_reentry_evidence(
            reentry(),
            source_metadata={"runtime_credit": "OBSERVED_INTERFACE"},
            measurement=measurement("TRUE"),
        )
        self.assertEqual("TRUE", got["observed_downstream_change"])
        self.assertEqual(1, got["causal_credit"])
        self.assertEqual("OBSERVABLE_WORKSPACE_REENTRY_ONLY", got["credit_scope"])
        self.assertEqual(0, got["global_jspace_causal_credit"])

    def test_unknown_measurement_stays_zero_credit(self):
        got = normalize_reentry_evidence(
            reentry(),
            source_metadata={"runtime_credit": "OBSERVED_INTERFACE"},
            measurement=measurement("UNKNOWN"),
        )
        self.assertEqual("UNKNOWN", got["observed_downstream_change"])
        self.assertEqual(0, got["causal_credit"])

    def test_mismatched_causal_identity_rejected(self):
        bad = measurement()
        bad["causal_event_id"] = "other"
        with self.assertRaisesRegex(
            ReentryEvidenceError, "MEASUREMENT_CAUSAL_EVENT_MISMATCH"
        ):
            normalize_reentry_evidence(
                reentry(),
                source_metadata={"runtime_credit": "OBSERVED_INTERFACE"},
                measurement=bad,
            )

    def test_missing_matched_control_rejected(self):
        bad = measurement()
        bad["matched_control_id"] = ""
        with self.assertRaisesRegex(ReentryEvidenceError, "MATCHED_CONTROL_ID_REQUIRED"):
            normalize_reentry_evidence(
                reentry(),
                source_metadata={"runtime_credit": "OBSERVED_INTERFACE"},
                measurement=bad,
            )


if __name__ == "__main__":
    unittest.main()
