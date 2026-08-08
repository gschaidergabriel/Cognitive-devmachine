import copy
import json
import unittest

from frank_harness.state_ledger import (
    DomainMutation,
    EventChainError,
    InvalidTransitionError,
    ProvenanceRef,
    ReplayMismatchError,
    StaleEpochError,
    StateLedger,
    canonical_json,
    semantic_hash,
)


class CanonicalTests(unittest.TestCase):
    def test_mapping_order_does_not_change_identity(self):
        a = {"z": 1, "a": {"b": 2, "a": 1}}
        b = {"a": {"a": 1, "b": 2}, "z": 1}
        self.assertEqual(canonical_json(a), canonical_json(b))
        self.assertEqual(semantic_hash(a), semantic_hash(b))

    def test_set_order_is_canonical(self):
        self.assertEqual(semantic_hash({"x": {3, 1, 2}}), semantic_hash({"x": {2, 3, 1}}))

    def test_nan_rejected(self):
        with self.assertRaises(InvalidTransitionError):
            semantic_hash({"x": float("nan")})


class LedgerTests(unittest.TestCase):
    def test_event_apply_epochs_hash_and_provenance(self):
        ledger = StateLedger()
        p = ProvenanceRef("user:1", "trusted_user", source_epoch=4)
        ev = ledger.apply(
            "goal.create",
            [DomainMutation("goals", "replace", {"active": ["g1"]}, 0, (p,))],
            metadata={"turn": 1},
        )
        self.assertEqual(ev.seq, 1)
        self.assertEqual(ledger.read("goals").epoch, 1)
        self.assertEqual(ledger.read("goals").provenance[0].source_id, "user:1")
        self.assertEqual(ev.result_state_hash, ledger.state_hash)
        ledger.verify_chain()

    def test_stale_epoch_fails_closed_without_partial_commit(self):
        ledger = StateLedger()
        ledger.apply("x.init", [DomainMutation("x", "replace", {"v": 1}, 0)])
        before = ledger.snapshot()
        with self.assertRaises(StaleEpochError):
            ledger.apply("x.stale", [DomainMutation("x", "merge", {"v": 2}, 0)])
        after = ledger.snapshot()
        self.assertEqual(before.state_hash, after.state_hash)
        self.assertEqual(before.last_event_hash, after.last_event_hash)

    def test_multi_domain_event_is_atomic(self):
        ledger = StateLedger()
        ledger.apply(
            "turn.commit",
            [
                DomainMutation("workspace", "replace", {"winner": "c7"}, 0),
                DomainMutation("goals", "replace", {"active": ["g7"]}, 0),
            ],
        )
        self.assertEqual(ledger.read("workspace").epoch, 1)
        self.assertEqual(ledger.read("goals").epoch, 1)
        self.assertEqual(len(ledger.events), 1)

    def test_duplicate_domain_in_event_rejected(self):
        ledger = StateLedger()
        with self.assertRaises(InvalidTransitionError):
            ledger.apply(
                "bad",
                [
                    DomainMutation("x", "replace", 1, 0),
                    DomainMutation("x", "replace", 2, 0),
                ],
            )

    def test_merge_append_extend_delete(self):
        ledger = StateLedger()
        ledger.apply("obj", [DomainMutation("obj", "replace", {"a": {"b": 1}, "c": 2}, 0)])
        ledger.apply("obj.merge", [DomainMutation("obj", "merge", {"a": {"d": 3}}, 1)])
        self.assertEqual(ledger.read("obj").value, {"a": {"b": 1, "d": 3}, "c": 2})
        ledger.apply("obj.del", [DomainMutation("obj", "delete_path", ["a", "b"], 2)])
        self.assertEqual(ledger.read("obj").value, {"a": {"d": 3}, "c": 2})
        ledger.apply("list", [DomainMutation("list", "replace", [1], 0)])
        ledger.apply("list.append", [DomainMutation("list", "append", 2, 1)])
        ledger.apply("list.extend", [DomainMutation("list", "extend", [3, 4], 2)])
        self.assertEqual(ledger.read("list").value, [1, 2, 3, 4])

    def test_export_replay_exact(self):
        ledger = StateLedger()
        for i in range(5):
            epoch = ledger.domain_epoch("ticks")
            ledger.apply(
                "tick",
                [DomainMutation("ticks", "replace", {"n": i + 1}, epoch)],
                metadata={"i": i},
            )
        exported = ledger.export_log()
        clone = StateLedger.replay(json.loads(json.dumps(exported)))
        self.assertEqual(clone.state_hash, ledger.state_hash)
        self.assertEqual(clone.last_event_hash, ledger.last_event_hash)
        self.assertEqual(clone.export_log(), exported)

    def test_tampered_payload_detected(self):
        ledger = StateLedger()
        ledger.apply("x", [DomainMutation("x", "replace", {"safe": True}, 0)])
        bad = copy.deepcopy(ledger.export_log())
        bad["events"][0]["mutations"][0]["payload"]["safe"] = False
        with self.assertRaises((ReplayMismatchError, EventChainError)):
            StateLedger.replay(bad)

    def test_tampered_chain_detected(self):
        ledger = StateLedger()
        ledger.apply("x", [DomainMutation("x", "replace", 1, 0)])
        ledger.apply("y", [DomainMutation("y", "replace", 2, 0)])
        bad = copy.deepcopy(ledger.export_log())
        bad["events"][1]["previous_event_hash"] = "f" * 64
        with self.assertRaises(EventChainError):
            StateLedger.replay(bad)

    def test_nondeterminism_receipt_is_part_of_event_identity(self):
        a = StateLedger()
        b = StateLedger()
        e1 = a.apply(
            "sensor",
            [DomainMutation("body", "replace", {"cpu": 0.2}, 0)],
            nondeterminism_receipts=[{"source": "sensor", "sample_id": 1}],
        )
        e2 = b.apply(
            "sensor",
            [DomainMutation("body", "replace", {"cpu": 0.2}, 0)],
            nondeterminism_receipts=[{"source": "sensor", "sample_id": 2}],
        )
        self.assertEqual(e1.result_state_hash, e2.result_state_hash)
        self.assertNotEqual(e1.event_hash, e2.event_hash)


if __name__ == "__main__":
    unittest.main()
