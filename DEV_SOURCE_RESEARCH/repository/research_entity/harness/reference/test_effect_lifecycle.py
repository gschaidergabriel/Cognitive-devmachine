import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from effect_authority import (
    AuthoritySource,
    ConfirmationReceipt,
    EffectAuthorityGate,
    EffectClass,
    EffectDecision,
    EffectRequest,
)
from effect_lifecycle import (
    EffectLifecycleStore,
    LifecycleState,
    RecoveryClass,
)

NOW = datetime(2026, 8, 10, 13, 31, tzinfo=timezone.utc)


def user_req(**kw):
    base = dict(actor=AuthoritySource.AUTHENTICATED_USER, authenticated=True, action="a", target="r")
    base.update(kw)
    return EffectRequest(**base)


def receipt_for(req, nonce="n", *, expiry=None, request_hash=None):
    return ConfirmationReceipt(
        request_hash=request_hash or req.request_hash(),
        actor=AuthoritySource.AUTHENTICATED_USER,
        effect_class=req.effect_class,
        exact_target=req.target,
        exact_action=req.action,
        impact_summary="test impact",
        confirmed_at=NOW,
        expiry=expiry,
        nonce=nonce,
    )


class GateRegressionTests(unittest.TestCase):
    def test_existing_core_matrix(self):
        gate = EffectAuthorityGate()
        cases = [
            (user_req(effect_class=EffectClass.READ_ONLY), EffectDecision.ALLOW),
            (user_req(effect_class=EffectClass.REVERSIBLE_WRITE, scoped_capability=True, rollback_available=True), EffectDecision.ALLOW),
            (user_req(effect_class=EffectClass.EXTERNAL_COMMUNICATION, destination_resolved=True, payload_bound_to_user_intent=True), EffectDecision.ALLOW),
            (user_req(effect_class=EffectClass.PRIVILEGED_CHANGE), EffectDecision.REQUIRE_CONFIRMATION),
            (user_req(effect_class=EffectClass.UNKNOWN_EFFECT), EffectDecision.DEGRADE_TO_PROPOSAL),
            (user_req(effect_class=EffectClass.DESTRUCTIVE, destructive_kind="DELETE_DATA", explicit_target=False), EffectDecision.DENY),
        ]
        for req, expected in cases:
            self.assertEqual(gate.evaluate(req).decision, expected)

    def test_pure_validate_does_not_consume_nonce(self):
        gate = EffectAuthorityGate()
        req = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE)
        rcpt = receipt_for(req, "pure", expiry=NOW + timedelta(minutes=5))
        self.assertEqual(gate.validate_confirmation(req, rcpt, now=NOW).decision, EffectDecision.ALLOW)
        self.assertEqual(gate.validate_confirmation(req, rcpt, now=NOW).decision, EffectDecision.ALLOW)
        self.assertNotIn("pure", gate.used_confirmation_nonces)

    def test_apply_still_one_shot_in_memory(self):
        gate = EffectAuthorityGate()
        req = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE)
        rcpt = receipt_for(req, "local", expiry=NOW + timedelta(minutes=5))
        self.assertEqual(gate.apply_confirmation(req, rcpt, now=NOW).decision, EffectDecision.ALLOW)
        self.assertEqual(gate.apply_confirmation(req, rcpt, now=NOW).decision, EffectDecision.DENY)

    def test_receipt_hash_changes_on_material_receipt_mutation(self):
        req = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE)
        a = receipt_for(req, "x", expiry=NOW + timedelta(minutes=5))
        b = ConfirmationReceipt(**{**a.__dict__, "impact_summary": "different"})
        self.assertNotEqual(a.receipt_hash(), b.receipt_hash())

    def test_exact_expiry_boundary_is_rejected(self):
        gate = EffectAuthorityGate()
        req = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE)
        rcpt = receipt_for(req, "expiry-edge", expiry=NOW)
        self.assertEqual(gate.validate_confirmation(req, rcpt, now=NOW).decision, EffectDecision.DENY)

    def test_future_dated_confirmation_is_rejected(self):
        gate = EffectAuthorityGate()
        req = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE)
        rcpt = ConfirmationReceipt(
            request_hash=req.request_hash(),
            actor=AuthoritySource.AUTHENTICATED_USER,
            effect_class=req.effect_class,
            exact_target=req.target,
            exact_action=req.action,
            impact_summary="impact",
            confirmed_at=NOW + timedelta(seconds=1),
            expiry=NOW + timedelta(minutes=5),
            nonce="future",
        )
        self.assertEqual(gate.validate_confirmation(req, rcpt, now=NOW).decision, EffectDecision.DENY)

    def test_expiry_before_confirmation_is_rejected(self):
        gate = EffectAuthorityGate()
        req = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE)
        rcpt = ConfirmationReceipt(
            request_hash=req.request_hash(),
            actor=AuthoritySource.AUTHENTICATED_USER,
            effect_class=req.effect_class,
            exact_target=req.target,
            exact_action=req.action,
            impact_summary="impact",
            confirmed_at=NOW,
            expiry=NOW - timedelta(seconds=1),
            nonce="bad-order",
        )
        self.assertEqual(gate.validate_confirmation(req, rcpt, now=NOW).decision, EffectDecision.DENY)

    def test_empty_nonce_rejected(self):
        gate = EffectAuthorityGate()
        req = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE)
        rcpt = receipt_for(req, "", expiry=NOW + timedelta(minutes=5))
        self.assertEqual(gate.validate_confirmation(req, rcpt, now=NOW).decision, EffectDecision.DENY)

    def test_empty_impact_summary_rejected(self):
        gate = EffectAuthorityGate()
        req = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE)
        rcpt = ConfirmationReceipt(
            request_hash=req.request_hash(),
            actor=AuthoritySource.AUTHENTICATED_USER,
            effect_class=req.effect_class,
            exact_target=req.target,
            exact_action=req.action,
            impact_summary=" ",
            confirmed_at=NOW,
            expiry=NOW + timedelta(minutes=5),
            nonce="impact",
        )
        self.assertEqual(gate.validate_confirmation(req, rcpt, now=NOW).decision, EffectDecision.DENY)

    def test_naive_timestamp_rejected_not_exception(self):
        gate = EffectAuthorityGate()
        req = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE)
        rcpt = ConfirmationReceipt(
            request_hash=req.request_hash(),
            actor=AuthoritySource.AUTHENTICATED_USER,
            effect_class=req.effect_class,
            exact_target=req.target,
            exact_action=req.action,
            impact_summary="impact",
            confirmed_at=datetime(2026, 8, 10, 13, 31),
            expiry=None,
            nonce="naive",
        )
        self.assertEqual(gate.validate_confirmation(req, rcpt, now=NOW).decision, EffectDecision.DENY)

    def test_non_authoritative_signal_mutation_does_not_change_request_hash(self):
        req = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE)
        mutated = EffectRequest(**{
            **req.__dict__,
            "translator_claims_authority": True,
            "model_confidence": 1.0,
            "gwt_ignition": True,
            "claygraph_salience": 1.0,
        })
        self.assertEqual(req.request_hash(), mutated.request_hash())


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "effects.sqlite3")
        self.store = EffectLifecycleStore(self.db)
        self.priv = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE, action="rotate-key", target="svc")
        self.rcpt = receipt_for(self.priv, "nonce-1", expiry=NOW + timedelta(minutes=5))

    def tearDown(self):
        self.tmp.cleanup()

    def test_confirmed_reservation_consumes_nonce_atomically(self):
        r = self.store.reserve_confirmed(self.priv, self.rcpt, now=NOW)
        self.assertTrue(r.admitted)
        self.assertEqual(r.state, LifecycleState.RESERVED)
        self.assertEqual(self.store.confirmation_count(), 1)
        self.assertEqual(self.store.event_count(r.effect_id), 1)

    def test_durable_replay_rejected_after_restart(self):
        first = self.store.reserve_confirmed(self.priv, self.rcpt, now=NOW)
        restarted = EffectLifecycleStore(self.db)
        second = restarted.reserve_confirmed(self.priv, self.rcpt, now=NOW)
        self.assertTrue(first.admitted)
        self.assertFalse(second.admitted)
        self.assertIn("replay", second.reason)

    def test_fault_after_confirmation_insert_rolls_back_both_tables(self):
        with self.assertRaises(RuntimeError):
            self.store.reserve_confirmed(
                self.priv, self.rcpt, now=NOW, fault_after_confirmation_insert=True
            )
        self.assertEqual(self.store.confirmation_count(), 0)
        eid = self.store.effect_id_for_confirmed(self.priv, self.rcpt)
        self.assertIsNone(self.store.effect_row(eid))
        self.assertEqual(self.store.integrity_check(), "ok")

    def test_stale_confirmation_never_reaches_store(self):
        stale = receipt_for(self.priv, "stale", expiry=NOW - timedelta(seconds=1))
        r = self.store.reserve_confirmed(self.priv, stale, now=NOW)
        self.assertFalse(r.admitted)
        self.assertEqual(self.store.confirmation_count(), 0)

    def test_mismatch_never_reaches_store(self):
        bad = receipt_for(self.priv, "bad", expiry=NOW + timedelta(minutes=5), request_hash="bad")
        r = self.store.reserve_confirmed(self.priv, bad, now=NOW)
        self.assertFalse(r.admitted)
        self.assertEqual(self.store.confirmation_count(), 0)

    def test_policy_mutation_invalidates_preexisting_confirmation(self):
        req = user_req(
            effect_class=EffectClass.DESTRUCTIVE,
            destructive_kind="DELETE_DATA",
            action="delete",
            target="file",
            explicit_target=True,
            impact_preview=True,
            backup_state_known=True,
        )
        rcpt = receipt_for(req, "mut", expiry=NOW + timedelta(minutes=5))
        mutated = user_req(
            effect_class=EffectClass.DESTRUCTIVE,
            destructive_kind="DELETE_DATA",
            action="delete",
            target="file",
            explicit_target=True,
            impact_preview=True,
            backup_state_known=True,
            no_backup_disclosed=True,
        )
        r = self.store.reserve_confirmed(mutated, rcpt, now=NOW)
        self.assertFalse(r.admitted)
        self.assertEqual(self.store.confirmation_count(), 0)

    def test_concurrent_same_nonce_exactly_one_reservation(self):
        def work(_):
            return self.store.reserve_confirmed(self.priv, self.rcpt, now=NOW)
        with ThreadPoolExecutor(max_workers=12) as ex:
            results = list(ex.map(work, range(24)))
        self.assertEqual(sum(r.admitted for r in results), 1)
        self.assertEqual(self.store.confirmation_count(), 1)

    def test_duplicate_idempotency_key_blocked_even_with_fresh_confirmation(self):
        a = self.store.reserve_confirmed(
            self.priv, self.rcpt, now=NOW, idempotency_key="downstream-42", external_idempotent=True
        )
        req2 = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE, action="rotate-key", target="svc")
        rcpt2 = receipt_for(req2, "nonce-2", expiry=NOW + timedelta(minutes=5))
        b = self.store.reserve_confirmed(
            req2, rcpt2, now=NOW, idempotency_key="downstream-42", external_idempotent=True
        )
        self.assertTrue(a.admitted)
        self.assertFalse(b.admitted)
        self.assertIn("idempotency", b.reason)
        self.assertEqual(self.store.confirmation_count(), 1)

    def test_reserved_crash_restart_is_safe_to_start(self):
        r = self.store.reserve_confirmed(self.priv, self.rcpt, now=NOW)
        restarted = EffectLifecycleStore(self.db)
        self.assertEqual(restarted.recovery_class(r.effect_id), RecoveryClass.SAFE_TO_START)

    def test_committing_non_idempotent_crash_requires_reconciliation(self):
        r = self.store.reserve_confirmed(self.priv, self.rcpt, now=NOW)
        self.store.begin_attempt(r.effect_id, attempt_id="a1", now=NOW)
        restarted = EffectLifecycleStore(self.db)
        self.assertEqual(restarted.recovery_class(r.effect_id), RecoveryClass.RECONCILE_REQUIRED)

    def test_committing_idempotent_crash_can_retry_same_key(self):
        r = self.store.reserve_confirmed(
            self.priv, self.rcpt, now=NOW, idempotency_key="idem-1", external_idempotent=True
        )
        self.store.begin_attempt(r.effect_id, attempt_id="a1", now=NOW)
        restarted = EffectLifecycleStore(self.db)
        self.assertEqual(
            restarted.recovery_class(r.effect_id),
            RecoveryClass.SAFE_TO_RETRY_SAME_IDEMPOTENCY_KEY,
        )

    def test_same_attempt_idempotent_local_retry_is_noop(self):
        r = self.store.reserve_confirmed(self.priv, self.rcpt, now=NOW)
        first = self.store.begin_attempt(r.effect_id, attempt_id="a1", now=NOW)
        second = self.store.begin_attempt(r.effect_id, attempt_id="a1", now=NOW)
        self.assertTrue(first.changed)
        self.assertFalse(second.changed)
        self.assertEqual(second.state, LifecycleState.COMMITTING)

    def test_different_second_attempt_not_started_from_committing(self):
        r = self.store.reserve_confirmed(self.priv, self.rcpt, now=NOW)
        self.store.begin_attempt(r.effect_id, attempt_id="a1", now=NOW)
        second = self.store.begin_attempt(r.effect_id, attempt_id="a2", now=NOW)
        self.assertFalse(second.changed)
        self.assertEqual(second.state, LifecycleState.COMMITTING)

    def test_unverified_outcome_requires_reconciliation(self):
        r = self.store.reserve_confirmed(self.priv, self.rcpt, now=NOW)
        self.store.begin_attempt(r.effect_id, attempt_id="a1", now=NOW)
        out = self.store.record_outcome(
            r.effect_id, success=True, verified=False, outcome={"provider": "timeout"}, now=NOW
        )
        self.assertEqual(out.state, LifecycleState.OUTCOME_UNKNOWN)
        self.assertEqual(self.store.recovery_class(r.effect_id), RecoveryClass.RECONCILE_REQUIRED)

    def test_unverified_outcome_idempotent_can_retry(self):
        r = self.store.reserve_confirmed(
            self.priv, self.rcpt, now=NOW, idempotency_key="idem-2", external_idempotent=True
        )
        self.store.begin_attempt(r.effect_id, attempt_id="a1", now=NOW)
        self.store.record_outcome(
            r.effect_id, success=False, verified=False, outcome={"provider": "connection_lost"}, now=NOW
        )
        self.assertEqual(
            self.store.recovery_class(r.effect_id),
            RecoveryClass.SAFE_TO_RETRY_SAME_IDEMPOTENCY_KEY,
        )

    def test_verified_success_requires_reentry(self):
        r = self.store.reserve_confirmed(self.priv, self.rcpt, now=NOW)
        self.store.begin_attempt(r.effect_id, attempt_id="a1", now=NOW)
        out = self.store.record_outcome(
            r.effect_id, success=True, verified=True, outcome={"status": "ok"}, now=NOW
        )
        self.assertEqual(out.state, LifecycleState.OUTCOME_SUCCEEDED)
        self.assertEqual(self.store.recovery_class(r.effect_id), RecoveryClass.REENTRY_PENDING)

    def test_verified_failure_also_requires_reentry(self):
        r = self.store.reserve_confirmed(self.priv, self.rcpt, now=NOW)
        self.store.begin_attempt(r.effect_id, attempt_id="a1", now=NOW)
        out = self.store.record_outcome(
            r.effect_id, success=False, verified=True, outcome={"status": "rejected"}, now=NOW
        )
        self.assertEqual(out.state, LifecycleState.OUTCOME_FAILED)
        self.assertEqual(self.store.recovery_class(r.effect_id), RecoveryClass.REENTRY_PENDING)

    def test_reentry_rejects_unknown_outcome(self):
        r = self.store.reserve_confirmed(self.priv, self.rcpt, now=NOW)
        self.store.begin_attempt(r.effect_id, attempt_id="a1", now=NOW)
        self.store.record_outcome(
            r.effect_id, success=True, verified=False, outcome={"status": "maybe"}, now=NOW
        )
        re = self.store.record_reentry(r.effect_id, reentry={"delta": "x"}, now=NOW)
        self.assertFalse(re.changed)
        self.assertEqual(re.state, LifecycleState.OUTCOME_UNKNOWN)

    def test_verified_outcome_reentry_completes(self):
        r = self.store.reserve_confirmed(self.priv, self.rcpt, now=NOW)
        self.store.begin_attempt(r.effect_id, attempt_id="a1", now=NOW)
        self.store.record_outcome(
            r.effect_id, success=True, verified=True, outcome={"status": "ok"}, now=NOW
        )
        re = self.store.record_reentry(r.effect_id, reentry={"outcome": "bound", "causal": "effect"}, now=NOW)
        self.assertTrue(re.changed)
        self.assertEqual(re.state, LifecycleState.REENTERED)
        self.assertEqual(self.store.recovery_class(r.effect_id), RecoveryClass.COMPLETE)
        self.assertEqual(self.store.event_count(r.effect_id), 4)

    def test_direct_allow_read_can_reserve_without_confirmation(self):
        req = user_req(effect_class=EffectClass.READ_ONLY, action="read", target="public")
        r = self.store.reserve_allowed(req, reservation_key="r1", now=NOW)
        self.assertTrue(r.admitted)
        self.assertEqual(self.store.confirmation_count(), 0)

    def test_non_allowed_cannot_use_direct_reservation_path(self):
        req = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE, action="admin", target="svc")
        r = self.store.reserve_allowed(req, reservation_key="r1", now=NOW)
        self.assertFalse(r.admitted)
        self.assertIsNone(r.effect_id)

    def test_integrity_check_after_full_lifecycle(self):
        r = self.store.reserve_confirmed(self.priv, self.rcpt, now=NOW)
        self.store.begin_attempt(r.effect_id, attempt_id="a1", now=NOW)
        self.store.record_outcome(r.effect_id, success=True, verified=True, outcome={"x": 1}, now=NOW)
        self.store.record_reentry(r.effect_id, reentry={"y": 2}, now=NOW)
        self.assertEqual(self.store.integrity_check(), "ok")

    def test_multiple_fresh_confirmations_can_reserve_distinct_effects(self):
        for i in range(20):
            req = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE, action=f"a{i}", target=f"r{i}")
            rcpt = receipt_for(req, f"n{i}", expiry=NOW + timedelta(minutes=5))
            r = self.store.reserve_confirmed(req, rcpt, now=NOW)
            self.assertTrue(r.admitted)
        self.assertEqual(self.store.confirmation_count(), 20)
        self.assertEqual(self.store.integrity_check(), "ok")

    def test_trace_hash_and_state_chain_verifies(self):
        r = self.store.reserve_confirmed(self.priv, self.rcpt, now=NOW)
        self.store.begin_attempt(r.effect_id, attempt_id="a1", now=NOW)
        self.store.record_outcome(r.effect_id, success=True, verified=True, outcome={"status": "ok"}, now=NOW)
        self.store.record_reentry(r.effect_id, reentry={"delta": "done"}, now=NOW)
        self.assertEqual(self.store.verify_effect_trace(r.effect_id), (True, "ok"))

    def test_trace_payload_tamper_detected_even_when_sqlite_integrity_ok(self):
        r = self.store.reserve_confirmed(self.priv, self.rcpt, now=NOW)
        import sqlite3
        conn = sqlite3.connect(self.db)
        conn.execute("UPDATE effect_events SET payload_json='{\"tampered\":true}' WHERE effect_id=?", (r.effect_id,))
        conn.commit()
        conn.close()
        self.assertEqual(self.store.integrity_check(), "ok")
        ok, reason = self.store.verify_effect_trace(r.effect_id)
        self.assertFalse(ok)
        self.assertEqual(reason, "event hash mismatch")

    def test_effect_row_state_tamper_detected(self):
        r = self.store.reserve_confirmed(self.priv, self.rcpt, now=NOW)
        import sqlite3
        conn = sqlite3.connect(self.db)
        conn.execute("UPDATE effects SET state=? WHERE effect_id=?", (LifecycleState.OUTCOME_SUCCEEDED.value, r.effect_id))
        conn.commit()
        conn.close()
        ok, reason = self.store.verify_effect_trace(r.effect_id)
        self.assertFalse(ok)
        self.assertIn("disagrees", reason)

    def test_500_policy_field_mutations_reject_old_confirmation(self):
        base = user_req(
            effect_class=EffectClass.DESTRUCTIVE,
            destructive_kind="DELETE_DATA",
            action="delete",
            target="file",
            explicit_target=True,
            impact_preview=True,
            backup_state_known=True,
        )
        rcpt = receipt_for(base, "fuzz-base", expiry=NOW + timedelta(minutes=5))
        for i in range(500):
            if i % 5 == 0:
                mutated = EffectRequest(**{**base.__dict__, "target": f"file-{i}"})
            elif i % 5 == 1:
                mutated = EffectRequest(**{**base.__dict__, "action": f"delete-{i}"})
            elif i % 5 == 2:
                mutated = EffectRequest(**{**base.__dict__, "backup_state_known": False, "no_backup_disclosed": True})
            elif i % 5 == 3:
                mutated = EffectRequest(**{**base.__dict__, "scoped_capability": True})
            else:
                mutated = EffectRequest(**{**base.__dict__, "exact_scope": True})
            self.assertNotEqual(base.request_hash(), mutated.request_hash())
            self.assertFalse(self.store.reserve_confirmed(mutated, rcpt, now=NOW).admitted)
        self.assertEqual(self.store.confirmation_count(), 0)

    @unittest.skipUnless(hasattr(os, "fork"), "Linux/fork interprocess lock test")
    def test_interprocess_same_confirmation_exactly_one(self):
        import multiprocessing as mp
        ctx = mp.get_context("fork")
        q = ctx.Queue()
        db = self.db
        req = self.priv
        rcpt = self.rcpt

        def worker():
            s = EffectLifecycleStore(db)
            x = s.reserve_confirmed(req, rcpt, now=NOW)
            q.put(bool(x.admitted))

        procs = [ctx.Process(target=worker) for _ in range(8)]
        for p in procs:
            p.start()
        for p in procs:
            p.join(10)
            self.assertEqual(p.exitcode, 0)
        outcomes = [q.get(timeout=2) for _ in procs]
        self.assertEqual(sum(outcomes), 1)
        self.assertEqual(self.store.confirmation_count(), 1)
        self.assertEqual(self.store.integrity_check(), "ok")

    @unittest.skipUnless(hasattr(os, "fork"), "Linux/fork crash test")
    def test_real_process_death_mid_transaction_leaves_no_partial_authority(self):
        import sqlite3
        effect_id = "crash-uncommitted-effect"
        pid = os.fork()
        if pid == 0:
            conn = sqlite3.connect(self.db, isolation_level=None)
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """INSERT INTO effects(
                    effect_id,request_hash,effect_class,target,action,state,
                    confirmation_nonce,confirmation_receipt_hash,external_idempotent,reserved_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (
                    effect_id,
                    self.priv.request_hash(),
                    self.priv.effect_class.value,
                    self.priv.target,
                    self.priv.action,
                    LifecycleState.RESERVED.value,
                    "crash-nonce",
                    "crash-receipt-hash",
                    0,
                    NOW.isoformat(),
                ),
            )
            conn.execute(
                """INSERT INTO confirmation_consumptions(nonce,request_hash,receipt_hash,effect_id,consumed_at)
                   VALUES(?,?,?,?,?)""",
                ("crash-nonce", self.priv.request_hash(), "crash-receipt-hash", effect_id, NOW.isoformat()),
            )
            os._exit(17)
        waited, status = os.waitpid(pid, 0)
        self.assertEqual(waited, pid)
        self.assertTrue(os.WIFEXITED(status))
        self.assertEqual(os.WEXITSTATUS(status), 17)
        restarted = EffectLifecycleStore(self.db)
        self.assertIsNone(restarted.effect_row(effect_id))
        self.assertEqual(restarted.confirmation_count(), 0)
        self.assertEqual(restarted.integrity_check(), "ok")


if __name__ == "__main__":
    unittest.main(verbosity=2)
