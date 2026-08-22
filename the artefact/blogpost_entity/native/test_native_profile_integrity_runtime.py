#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shlex
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path


NATIVE = Path(__file__).resolve().parent
SOURCE = NATIVE / "mini_entity.c"


def run(argv: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if check and proc.returncode != 0:
        raise AssertionError(f"command failed rc={proc.returncode}: {shlex.join(argv)}\n{proc.stderr}")
    return proc


class NativeProfileIntegrityRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._build_tmp = tempfile.TemporaryDirectory(prefix="mini-entity-profile-integrity-build-")
        cls.binary = Path(cls._build_tmp.name) / "mini_entity.clay"
        pkg = run(["pkg-config", "--cflags", "--libs", "sqlite3", "libcurl", "json-c"], check=True)
        flags = shlex.split(pkg.stdout)
        run(
            [
                "gcc",
                "-O2",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-Wno-deprecated-declarations",
                "-o",
                str(cls.binary),
                str(SOURCE),
                *flags,
            ],
            check=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._build_tmp.cleanup()

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="mini-entity-profile-integrity-runtime-")
        root = Path(self._tmp.name)
        self.db = root / "entity.db"
        self.preset = root / "profile.json"
        profile = {
            "schema": "clay-pipeline-profile/v2",
            "profile_id": "integrity_probe",
            "identity": {"task": "neutral test", "language": "en"},
            "personality": {"system_prompt": "Use supplied evidence only."},
            "inference": {"kind": "api", "endpoint": "https://example.invalid", "model": "none"},
        }
        self.profile_bytes = (json.dumps(profile, sort_keys=True, separators=(",", ":")) + "\n").encode()
        self.preset.write_bytes(self.profile_bytes)
        run([str(self.binary), "init", str(self.db)], check=True)
        run([str(self.binary), "preset-apply", str(self.db), str(self.preset)], check=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_valid_profile_hash_is_accepted(self) -> None:
        proc = run([str(self.binary), "status", str(self.db)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["profile_present"])
        with sqlite3.connect(self.db) as db:
            stored = db.execute(
                "SELECT profile_sha256 FROM profiles WHERE profile_id='integrity_probe'"
            ).fetchone()[0]
        self.assertEqual(stored, hashlib.sha256(self.profile_bytes).hexdigest())

    def test_profile_json_drift_fails_closed_without_state_change(self) -> None:
        drifted = b'{"profile_id":"integrity_probe","identity":{"task":"silently drifted"}}\n'
        with sqlite3.connect(self.db) as db:
            before = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()[0]
            db.execute(
                "UPDATE profiles SET profile_json=? WHERE profile_id='integrity_probe'",
                (drifted.decode(),),
            )
            db.commit()

        proc = run([str(self.binary), "status", str(self.db)])
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("PROFILE_HASH_MISMATCH", proc.stderr)
        with sqlite3.connect(self.db) as db:
            after = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()[0]
        self.assertEqual(before, after)

    def test_malformed_profile_hash_metadata_fails_closed(self) -> None:
        with sqlite3.connect(self.db) as db:
            db.execute(
                "UPDATE profiles SET profile_sha256=? WHERE profile_id='integrity_probe'",
                ("0" * 63,),
            )
            db.commit()

        proc = run([str(self.binary), "status", str(self.db)])
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("PROFILE_HASH_METADATA_INVALID", proc.stderr)


if __name__ == "__main__":
    unittest.main()
