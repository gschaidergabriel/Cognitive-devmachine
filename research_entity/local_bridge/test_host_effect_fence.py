#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from host_effect_fence import (
    CommandIdentityConflict,
    EffectClass,
    EffectFenceError,
    HostEffectFence,
    PathHashPrecondition,
    ScratchBoundaryError,
    SubjectDrift,
    UnknownPriorEffect,
)


def h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class HostEffectFenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="host-effect-fence-test-")
        self.root = Path(self.tmp.name)
        self.fence = HostEffectFence(self.root / "state", machine_id="test-host")

    def tearDown(self) -> None:
        self.fence.close()
        self.tmp.cleanup()

    def test_read_only_does_not_create_effect_attempt(self) -> None:
        subject = self.root / "subject.txt"
        subject.write_bytes(b"stable")
        with self.fence.effect(
            command_id="ro-1",
            command_sha256=h(b"ro-command"),
            effect_class=EffectClass.READ_ONLY,
            holder="chatgpt",
            preconditions=[PathHashPrecondition(subject, h(b"stable"))],
        ) as ticket:
            self.assertEqual(ticket.generation, 0)
            self.assertFalse(ticket.duplicate_suppressed)
        count = self.fence.db.execute("SELECT COUNT(*) FROM effect_attempts").fetchone()[0]
        self.assertEqual(count, 0)

    def test_subject_drift_fails_before_live_effect(self) -> None:
        subject = self.root / "live.txt"
        subject.write_bytes(b"new")
        with self.assertRaises(SubjectDrift):
            with self.fence.effect(
                command_id="live-drift",
                command_sha256=h(b"cmd"),
                effect_class=EffectClass.LIVE_MUTATION,
                holder="frank",
                preconditions=[PathHashPrecondition(subject, h(b"old"))],
            ):
                self.fail("effect body must not run")
        count = self.fence.db.execute("SELECT COUNT(*) FROM effect_attempts").fetchone()[0]
        self.assertEqual(count, 0)

    def test_scratch_escape_fails_closed(self) -> None:
        scratch = self.root / "scratch"
        scratch.mkdir()
        outside = self.root / "live.txt"
        with self.assertRaises(ScratchBoundaryError):
            with self.fence.effect(
                command_id="scratch-escape",
                command_sha256=h(b"cmd"),
                effect_class=EffectClass.SCRATCH_ONLY,
                holder="chatgpt",
                scratch_root=scratch,
                touched_paths=[outside],
            ):
                self.fail("effect body must not run")

    def test_body_return_is_not_success_and_blocks_next_effect(self) -> None:
        cid = "live-1"
        digest = h(b"live-command")
        with self.fence.effect(
            command_id=cid,
            command_sha256=digest,
            effect_class=EffectClass.LIVE_MUTATION,
            holder="chatgpt",
        ) as ticket:
            self.assertFalse(ticket.duplicate_suppressed)
        status = self.fence.db.execute(
            "SELECT status FROM effect_attempts WHERE command_id=?", (cid,)
        ).fetchone()[0]
        self.assertEqual(status, "BODY_RETURNED_UNVERIFIED")

        with self.assertRaises(UnknownPriorEffect):
            with self.fence.effect(
                command_id="live-2",
                command_sha256=h(b"other"),
                effect_class=EffectClass.LIVE_MUTATION,
                holder="frank",
            ):
                self.fail("second live effect must be fenced")

    def test_independent_verification_enables_exact_replay_suppression(self) -> None:
        cid = "live-verified"
        digest = h(b"command")
        with self.fence.effect(
            command_id=cid,
            command_sha256=digest,
            effect_class=EffectClass.LIVE_MUTATION,
            holder="chatgpt",
        ):
            pass
        outcome = h(b"independent readback receipt")
        self.fence.verify_success(
            cid,
            digest,
            outcome_sha256=outcome,
            note="readback hash bound by independent verifier",
        )
        row = self.fence.db.execute(
            "SELECT status,outcome_sha256 FROM effect_attempts WHERE command_id=?", (cid,)
        ).fetchone()
        self.assertEqual(row["status"], "VERIFIED_SUCCEEDED")
        self.assertEqual(row["outcome_sha256"], outcome)

        body_ran = False
        with self.fence.effect(
            command_id=cid,
            command_sha256=digest,
            effect_class=EffectClass.LIVE_MUTATION,
            holder="frank",
        ) as ticket:
            self.assertTrue(ticket.duplicate_suppressed)
            if not ticket.duplicate_suppressed:
                body_ran = True
        self.assertFalse(body_ran)

    def test_same_command_id_changed_bytes_conflicts_even_after_verified_success(self) -> None:
        cid = "immutable-id"
        d1 = h(b"v1")
        with self.fence.effect(
            command_id=cid,
            command_sha256=d1,
            effect_class=EffectClass.SYSTEM_MUTATION,
            holder="frank",
        ):
            pass
        self.fence.verify_success(cid, d1, outcome_sha256=h(b"readback"), note="verified")
        with self.assertRaises(CommandIdentityConflict):
            with self.fence.effect(
                command_id=cid,
                command_sha256=h(b"v2"),
                effect_class=EffectClass.SYSTEM_MUTATION,
                holder="chatgpt",
            ):
                self.fail("identity conflict must not execute")

    def test_effect_exception_becomes_unknown_and_blocks_replay(self) -> None:
        cid = "crash-window"
        digest = h(b"effect")
        with self.assertRaisesRegex(RuntimeError, "simulated"):
            with self.fence.effect(
                command_id=cid,
                command_sha256=digest,
                effect_class=EffectClass.LIVE_MUTATION,
                holder="chatgpt",
            ):
                raise RuntimeError("simulated external ambiguity")
        status = self.fence.db.execute(
            "SELECT status FROM effect_attempts WHERE command_id=?", (cid,)
        ).fetchone()[0]
        self.assertEqual(status, "UNKNOWN")
        with self.assertRaises(UnknownPriorEffect):
            with self.fence.effect(
                command_id=cid,
                command_sha256=digest,
                effect_class=EffectClass.LIVE_MUTATION,
                holder="chatgpt",
            ):
                self.fail("unknown effect must not replay")

    def test_reconcile_requires_explicit_note_and_then_allows_retry(self) -> None:
        cid = "unknown-reconcile"
        digest = h(b"effect")
        try:
            with self.fence.effect(
                command_id=cid,
                command_sha256=digest,
                effect_class=EffectClass.LIVE_MUTATION,
                holder="frank",
            ):
                raise OSError("ambiguous")
        except OSError:
            pass
        with self.assertRaises(ValueError):
            self.fence.reconcile_safe(cid, note="")
        self.fence.reconcile_safe(cid, note="independent filesystem readback proves original bytes")
        ran = False
        with self.fence.effect(
            command_id=cid,
            command_sha256=digest,
            effect_class=EffectClass.LIVE_MUTATION,
            holder="frank",
        ):
            ran = True
        self.assertTrue(ran)

    def test_verify_requires_unverified_body_state(self) -> None:
        with self.assertRaises(KeyError):
            self.fence.verify_success(
                "missing", h(b"cmd"), outcome_sha256=h(b"out"), note="no row"
            )


if __name__ == "__main__":
    unittest.main()
