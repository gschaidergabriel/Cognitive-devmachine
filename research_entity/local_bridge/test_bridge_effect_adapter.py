#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from bridge_effect_adapter import (
    EffectBodyNonzero,
    EffectClassificationConflict,
    EffectClassificationRequired,
    Verification,
    command_sha256,
    execute_guarded,
)
from host_effect_fence import HostEffectFence, UnknownPriorEffect


def raw(spec: dict) -> bytes:
    return json.dumps(spec, separators=(",", ":"), sort_keys=True).encode()


def h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class BridgeEffectAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="bridge-effect-adapter-")
        self.root = Path(self.tmp.name)
        self.fence = HostEffectFence(self.root / "state", machine_id="test-host")
        self.calls = 0

    def tearDown(self) -> None:
        self.fence.close()
        self.tmp.cleanup()

    def body_ok(self, spec):
        self.calls += 1
        return subprocess.CompletedProcess([spec.get("op", "exec")], 0, b"ok", b"")

    def test_exact_raw_bytes_define_identity(self):
        a = b'{"schema":"CLAY_LOCAL_COMMAND/v1","command_id":"x","op":"read_file"}'
        b = b'{ "schema":"CLAY_LOCAL_COMMAND/v1", "command_id":"x", "op":"read_file" }'
        self.assertNotEqual(command_sha256(a), command_sha256(b))

    def test_legacy_read_file_infers_read_only_without_journal_row(self):
        cmd = raw({"schema":"CLAY_LOCAL_COMMAND/v1","command_id":"read","op":"read_file","path":"/tmp/x"})
        result = execute_guarded(fence=self.fence, raw_command=cmd, holder="chatgpt", body=self.body_ok)
        self.assertEqual(result.outcome, "COMPLETED_AT_NONLIVE_SCOPE")
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.fence.db.execute("select count(*) from effect_attempts").fetchone()[0], 0)

    def test_exec_without_classification_fails_closed_before_body(self):
        cmd = raw({"schema":"CLAY_LOCAL_COMMAND/v1","command_id":"exec","op":"exec","command":"true"})
        with self.assertRaises(EffectClassificationRequired):
            execute_guarded(fence=self.fence, raw_command=cmd, holder="frank", body=self.body_ok)
        self.assertEqual(self.calls, 0)

    def test_exec_cannot_self_declare_read_only(self):
        cmd = raw({"schema":"CLAY_LOCAL_COMMAND/v1","command_id":"liar","op":"exec","effect_class":"READ_ONLY","command":"true"})
        with self.assertRaises(EffectClassificationConflict):
            execute_guarded(fence=self.fence, raw_command=cmd, holder="frank", body=self.body_ok)
        self.assertEqual(self.calls, 0)

    def test_scratch_only_exec_inside_root_runs_without_live_journal(self):
        scratch = self.root / "scratch"; scratch.mkdir()
        cmd = raw({
            "schema":"CLAY_LOCAL_COMMAND/v1","command_id":"scratch","op":"exec",
            "effect_class":"SCRATCH_ONLY","scratch_root":str(scratch),
            "touched_paths":[str(scratch / "out.txt")],"command":"echo ok"
        })
        result = execute_guarded(fence=self.fence, raw_command=cmd, holder="chatgpt", body=self.body_ok)
        self.assertEqual(result.outcome, "COMPLETED_AT_NONLIVE_SCOPE")
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.fence.db.execute("select count(*) from effect_attempts").fetchone()[0], 0)

    def test_live_body_return_without_verifier_remains_unverified_and_blocks_next(self):
        cmd1 = raw({"schema":"CLAY_LOCAL_COMMAND/v1","command_id":"live1","op":"exec","effect_class":"LIVE_MUTATION","command":"touch x"})
        r1 = execute_guarded(fence=self.fence, raw_command=cmd1, holder="chatgpt", body=self.body_ok)
        self.assertEqual(r1.outcome, "BODY_RETURNED_UNVERIFIED")
        status = self.fence.db.execute("select status from effect_attempts where command_id='live1'").fetchone()[0]
        self.assertEqual(status, "BODY_RETURNED_UNVERIFIED")
        cmd2 = raw({"schema":"CLAY_LOCAL_COMMAND/v1","command_id":"live2","op":"exec","effect_class":"LIVE_MUTATION","command":"touch y"})
        with self.assertRaises(UnknownPriorEffect):
            execute_guarded(fence=self.fence, raw_command=cmd2, holder="frank", body=self.body_ok)
        self.assertEqual(self.calls, 1)

    def test_independent_verifier_promotes_and_exact_replay_suppresses_body(self):
        cmd = raw({"schema":"CLAY_LOCAL_COMMAND/v1","command_id":"verified","op":"exec","effect_class":"LIVE_MUTATION","command":"touch x"})
        def verify(spec, result):
            self.assertEqual(result.returncode, 0)
            return Verification(h(b"independent filesystem readback"), "independent readback")
        r1 = execute_guarded(fence=self.fence, raw_command=cmd, holder="chatgpt", body=self.body_ok, verifier=verify)
        self.assertEqual(r1.outcome, "VERIFIED_SUCCEEDED")
        self.assertEqual(self.calls, 1)
        r2 = execute_guarded(fence=self.fence, raw_command=cmd, holder="frank", body=self.body_ok, verifier=verify)
        self.assertEqual(r2.outcome, "DUPLICATE_SUPPRESSED_VERIFIED")
        self.assertEqual(self.calls, 1)

    def test_nonzero_live_body_becomes_unknown(self):
        cmd = raw({"schema":"CLAY_LOCAL_COMMAND/v1","command_id":"bad","op":"exec","effect_class":"SYSTEM_MUTATION","command":"false"})
        def body_bad(spec):
            self.calls += 1
            return subprocess.CompletedProcess(["false"], 7, b"", b"bad")
        with self.assertRaises(EffectBodyNonzero):
            execute_guarded(fence=self.fence, raw_command=cmd, holder="frank", body=body_bad)
        status = self.fence.db.execute("select status from effect_attempts where command_id='bad'").fetchone()[0]
        self.assertEqual(status, "UNKNOWN")

    def test_subject_precondition_checked_before_live_body(self):
        subject = self.root / "live.txt"; subject.write_bytes(b"current")
        cmd = raw({
            "schema":"CLAY_LOCAL_COMMAND/v1","command_id":"drift","op":"exec",
            "effect_class":"LIVE_MUTATION","command":"touch x",
            "subject_preconditions":[{"path":str(subject),"sha256":h(b"stale")}]
        })
        with self.assertRaises(Exception):
            execute_guarded(fence=self.fence, raw_command=cmd, holder="chatgpt", body=self.body_ok)
        self.assertEqual(self.calls, 0)


if __name__ == "__main__":
    unittest.main()
