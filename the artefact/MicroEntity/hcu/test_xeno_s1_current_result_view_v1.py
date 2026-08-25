import unittest
from unittest.mock import patch

from xeno_shared_state_boot_v1 import CoordinatorLease
from xeno_s1_current_result_view_v1 import (
    CurrentResultViewError,
    list_current_result_candidates,
)


def lease():
    return CoordinatorLease(
        "GRID_COORDINATOR_LEASE/v1",
        "a" * 64,
        "c-b",
        ("results",),
        7,
        "b" * 64,
        "XENO_COORDINATOR_POLICY/v1",
        "c" * 64,
    )


def row(result_id, epoch, digest):
    return {
        "result_id": result_id,
        "schema": "NODE_RESULT/v1",
        "node_id": "n1",
        "task_id": "t1",
        "state_epoch": epoch,
        "state_digest": digest,
        "payload_ref": f"mem://{result_id}",
        "payload_sha256": "d" * 64,
        "ingested_by": "c-b",
    }


class CurrentResultViewTests(unittest.TestCase):
    @patch("xeno_s1_current_result_view_v1.list_ingested_results")
    def test_excludes_historical_epoch_and_digest_rows(self, mocked):
        current = lease()
        mocked.return_value = [
            row("current", current.state_epoch, current.state_digest),
            row("old-epoch", current.state_epoch - 1, current.state_digest),
            row("old-digest", current.state_epoch, "e" * 64),
        ]
        observed = list_current_result_candidates(
            object(),
            current,
            coordinator_node_id="c-b",
            expected_authority_binding_sha256="c" * 64,
        )
        self.assertEqual(["current"], [item["result_id"] for item in observed])

    @patch("xeno_s1_current_result_view_v1.list_ingested_results")
    def test_empty_current_epoch_is_valid_empty_view(self, mocked):
        current = lease()
        mocked.return_value = [row("old", 6, "f" * 64)]
        observed = list_current_result_candidates(
            object(),
            current,
            coordinator_node_id="c-b",
            expected_authority_binding_sha256="c" * 64,
        )
        self.assertEqual([], observed)

    @patch("xeno_s1_current_result_view_v1.list_ingested_results")
    def test_malformed_persisted_row_fails_closed(self, mocked):
        mocked.return_value = [{"result_id": "broken"}]
        with self.assertRaisesRegex(CurrentResultViewError, "RESULT_ROW_MISSING_FIELDS"):
            list_current_result_candidates(
                object(),
                lease(),
                coordinator_node_id="c-b",
                expected_authority_binding_sha256="c" * 64,
            )

    @patch("xeno_s1_current_result_view_v1.list_ingested_results")
    def test_underlying_lease_gate_is_not_bypassed(self, mocked):
        mocked.side_effect = RuntimeError("STALE_COORDINATOR_LEASE")
        with self.assertRaisesRegex(RuntimeError, "STALE_COORDINATOR_LEASE"):
            list_current_result_candidates(
                object(),
                lease(),
                coordinator_node_id="c-b",
                expected_authority_binding_sha256="c" * 64,
            )
        mocked.assert_called_once()


if __name__ == "__main__":
    unittest.main()
