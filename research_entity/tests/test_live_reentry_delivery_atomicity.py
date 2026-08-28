from __future__ import annotations

import unittest

from research_entity.coordination.live_reentry_delivery_atomicity import (
    CLAIMED,
    DELIVERED_ACK_PENDING,
    PENDING,
    UNKNOWN_DELIVERY,
    DeliveryState,
    DeliveryStateError,
    authorize_delivery,
    claim,
    finalize_delivery,
    mark_unknown,
    recovery_decision,
    route_id,
)


class LiveReentryDeliveryAtomicityTests(unittest.TestCase):
    def _route(self) -> str:
        return route_id(
            run_id="run-1",
            receiver="github:pull/611",
            message_kind="MATERIAL_DELTA_PLUS_COUNTER_CHALLENGE",
            decision="ADOPT",
            payload_digest="a" * 64,
        )

    def test_route_id_is_deterministic_and_scope_sensitive(self) -> None:
        first = self._route()
        self.assertEqual(first, self._route())
        self.assertEqual(len(first), 64)
        self.assertNotEqual(
            first,
            route_id(
                run_id="run-1",
                receiver="github:pull/602",
                message_kind="MATERIAL_DELTA_PLUS_COUNTER_CHALLENGE",
                decision="ADOPT",
                payload_digest="a" * 64,
            ),
        )
        with self.assertRaises(DeliveryStateError):
            route_id(
                run_id="",
                receiver="github:pull/611",
                message_kind="MATERIAL_DELTA",
                decision="ADOPT",
                payload_digest="a" * 64,
            )

    def test_only_one_worker_can_claim_same_manifest_version(self) -> None:
        pending = DeliveryState(route_id=self._route())
        self.assertEqual(pending.status, PENDING)

        worker_a = claim(pending, expected_version=0, claim_id="worker-a")
        self.assertEqual(worker_a.status, CLAIMED)
        self.assertTrue(authorize_delivery(worker_a, claim_id="worker-a"))
        self.assertFalse(authorize_delivery(worker_a, claim_id="worker-b"))

        with self.assertRaises(DeliveryStateError):
            claim(worker_a, expected_version=0, claim_id="worker-b")
        with self.assertRaises(DeliveryStateError):
            claim(worker_a, expected_version=worker_a.version, claim_id="worker-b")

    def test_finalize_requires_owner_exact_marker_and_positive_comment(self) -> None:
        route = self._route()
        claimed = claim(DeliveryState(route_id=route), expected_version=0, claim_id="worker-a")

        with self.assertRaises(DeliveryStateError):
            finalize_delivery(
                claimed,
                claim_id="worker-b",
                comment_id=1,
                marker_route_id=route,
            )
        with self.assertRaises(DeliveryStateError):
            finalize_delivery(
                claimed,
                claim_id="worker-a",
                comment_id=1,
                marker_route_id="0" * 64,
            )
        with self.assertRaises(DeliveryStateError):
            finalize_delivery(
                claimed,
                claim_id="worker-a",
                comment_id=0,
                marker_route_id=route,
            )

        delivered = finalize_delivery(
            claimed,
            claim_id="worker-a",
            comment_id=5314946954,
            marker_route_id=route,
        )
        self.assertEqual(delivered.status, DELIVERED_ACK_PENDING)
        self.assertEqual(delivered.comment_id, 5314946954)
        self.assertEqual(recovery_decision(
            delivered,
            claim_expired=True,
            exact_marker_comment_id=None,
            target_scan_available=True,
        ), "NO_RETRY")

    def test_uncertain_delivery_recovery_never_blindly_retries(self) -> None:
        route = self._route()
        claimed = claim(DeliveryState(route_id=route), expected_version=0, claim_id="worker-a")
        unknown = mark_unknown(claimed, claim_id="worker-a")
        self.assertEqual(unknown.status, UNKNOWN_DELIVERY)

        self.assertEqual(
            recovery_decision(
                unknown,
                claim_expired=True,
                exact_marker_comment_id=5314946954,
                target_scan_available=True,
            ),
            "FINALIZE_EXISTING_DELIVERY",
        )
        finalized = finalize_delivery(
            unknown,
            claim_id="worker-a",
            comment_id=5314946954,
            marker_route_id=route,
        )
        self.assertEqual(finalized.status, DELIVERED_ACK_PENDING)

        self.assertEqual(
            recovery_decision(
                unknown,
                claim_expired=True,
                exact_marker_comment_id=None,
                target_scan_available=False,
            ),
            "KEEP_UNKNOWN",
        )
        self.assertEqual(
            recovery_decision(
                unknown,
                claim_expired=False,
                exact_marker_comment_id=None,
                target_scan_available=True,
            ),
            "WAIT_FOR_ACTIVE_CLAIM",
        )
        self.assertEqual(
            recovery_decision(
                unknown,
                claim_expired=True,
                exact_marker_comment_id=None,
                target_scan_available=True,
            ),
            "RECLAIM_BY_NEW_CAS",
        )

    def test_wrong_worker_cannot_mark_unknown(self) -> None:
        claimed = claim(
            DeliveryState(route_id=self._route()),
            expected_version=0,
            claim_id="worker-a",
        )
        with self.assertRaises(DeliveryStateError):
            mark_unknown(claimed, claim_id="worker-b")


if __name__ == "__main__":
    unittest.main()
