#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path


NATIVE = Path(__file__).resolve().parent
SOURCE = NATIVE / "mini_entity.c"
BUILDER = NATIVE / "build_native_bound.py"


def run(argv: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise AssertionError(
            f"command failed rc={proc.returncode}: {' '.join(argv)}\n"
            f"stdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc


class NativeProfileIntegrityRuntimeTests(unittest.TestCase):
    """Exact-source profile-digest consistency fence and its explicit boundary."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._build_tmp = tempfile.TemporaryDirectory(
            prefix="mini-entity-profile-integrity-build-"
        )
        build_root = Path(cls._build_tmp.name)
        cls.binary = build_root / "mini_entity.clay"
        cls.receipt = build_root / "build_receipt.json"
        run(
            [
                "python3",
                str(BUILDER),
                "--source",
                str(SOURCE),
                "--output",
                str(cls.binary),
                "--receipt",
                str(cls.receipt),
                "--version-label",
                "mini-entity/0.7.0-dev1",
                "--source-date-epoch",
                "1787371200",
                "--repeat",
                "1",
            ],
            check=True,
        )
        cls.binary.chmod(0o755)
        receipt = json.loads(cls.receipt.read_text(encoding="utf-8"))
        assert receipt["schema"] == "mini-entity-native-build-provenance/v2"
        assert receipt["build_definition"]["source_identity_sha256"] == receipt["build_definition"]["source_closure"]["sha256"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls._build_tmp.cleanup()

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(
            prefix="mini-entity-profile-integrity-runtime-"
        )
        root = Path(self._tmp.name)
        self.db = root / "entity.db"
        self.preset = root / "profile.json"
        profile = {
            "profile_id": "integrity_probe",
            "identity": {"task": "neutral integrity probe", "language": "en"},
            "personality": {"system_prompt": "Use supplied evidence only."},
            "inference": {
                "kind": "api",
                "endpoint": "https://example.invalid",
                "model": "none",
            },
        }
        self.profile_text = json.dumps(
            profile, sort_keys=True, separators=(",", ":")
        ) + "\n"
        self.preset.write_text(self.profile_text, encoding="utf-8")
        run([str(self.binary), "init", str(self.db)], check=True)
        run(
            [str(self.binary), "preset-apply", str(self.db), str(self.preset)],
            check=True,
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _generation(self) -> int:
        with sqlite3.connect(self.db) as db:
            return int(
                db.execute(
                    "SELECT generation FROM entity_state WHERE id=1"
                ).fetchone()[0]
            )

    def test_valid_profile_hash_is_accepted(self) -> None:
        proc = run([str(self.binary), "status", str(self.db)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["profile_present"])
        self.assertEqual(payload["native_semantic_admission"], "NATIVE_SIMPLE_PROFILE_ADMITTED")
        with sqlite3.connect(self.db) as db:
            stored = db.execute(
                "SELECT profile_sha256 FROM profiles WHERE profile_id='integrity_probe'"
            ).fetchone()[0]
        self.assertEqual(
            stored,
            hashlib.sha256(self.profile_text.encode("utf-8")).hexdigest(),
        )

    def test_same_length_profile_drift_fails_closed_without_state_change(self) -> None:
        before = self._generation()
        drifted = self.profile_text.replace("neutral integrity probe", "neutral integrity probE")
        self.assertEqual(len(drifted), len(self.profile_text))
        self.assertNotEqual(drifted, self.profile_text)
        with sqlite3.connect(self.db) as db:
            db.execute(
                "UPDATE profiles SET profile_json=? WHERE profile_id='integrity_probe'",
                (drifted,),
            )
            db.commit()

        proc = run([str(self.binary), "status", str(self.db)])
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("PROFILE_HASH_MISMATCH", proc.stderr)
        self.assertEqual(before, self._generation())

    def test_malformed_profile_hash_metadata_fails_closed(self) -> None:
        before = self._generation()
        with sqlite3.connect(self.db) as db:
            db.execute(
                "UPDATE profiles SET profile_sha256=? WHERE profile_id='integrity_probe'",
                ("0" * 63,),
            )
            db.commit()

        proc = run([str(self.binary), "status", str(self.db)])
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("PROFILE_HASH_METADATA_INVALID", proc.stderr)
        self.assertEqual(before, self._generation())

    def test_coherent_profile_and_digest_rewrite_is_not_authentication(self) -> None:
        """One bounded unusual experiment: prove the fence is consistency, not trust-root auth."""
        before = self._generation()
        rewritten = self.profile_text.replace("neutral integrity probe", "neutral integrity probE")
        rewritten_hash = hashlib.sha256(rewritten.encode("utf-8")).hexdigest()
        with sqlite3.connect(self.db) as db:
            db.execute(
                "UPDATE profiles SET profile_json=?, profile_sha256=? "
                "WHERE profile_id='integrity_probe'",
                (rewritten, rewritten_hash),
            )
            db.commit()

        proc = run([str(self.binary), "status", str(self.db)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["native_semantic_admission"], "NATIVE_SIMPLE_PROFILE_ADMITTED")
        self.assertEqual(before, self._generation())


if __name__ == "__main__":
    unittest.main()
