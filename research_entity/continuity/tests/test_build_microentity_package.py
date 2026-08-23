import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from build_microentity_package import PackageBuildError, build_bytes, write_snapshot


class DeterministicPackageBuilderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "MicroEntity"
        self.root.mkdir()
        (self.root / "hcu").mkdir()
        self.members = ["A.txt", "hcu/B.txt"]
        (self.root / "A.txt").write_bytes(b"alpha\n")
        (self.root / "hcu/B.txt").write_bytes(b"beta\n")
        self.manifest = self.root / "PACKAGE_MANIFEST.json"
        self._write_manifest(self.members)

    def tearDown(self):
        self.tmp.cleanup()

    def _write_manifest(self, members):
        self.manifest.write_text(json.dumps({
            "snapshot": "MICROENTITY_CURRENT.zip",
            "archive_members_required": members,
        }), encoding="utf-8")

    def test_repeated_builds_are_byte_identical(self):
        a = build_bytes(self.root)
        b = build_bytes(self.root)
        self.assertEqual(a.data, b.data)
        self.assertEqual(a.zip_sha256, b.zip_sha256)
        self.assertEqual(a.zip_git_blob_sha1, b.zip_git_blob_sha1)

    def test_archive_is_store_only_exact_order_and_exact_bytes(self):
        result = write_snapshot(self.root)
        target = self.root / "MICROENTITY_CURRENT.zip"
        self.assertEqual(target.read_bytes(), result.data)
        with zipfile.ZipFile(target) as z:
            self.assertEqual(z.namelist(), self.members)
            self.assertIsNone(z.testzip())
            for info, member in zip(z.infolist(), self.members):
                self.assertEqual(info.compress_type, zipfile.ZIP_STORED)
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual(z.read(member), (self.root / member).read_bytes())

    def test_different_python_hash_seed_does_not_change_bytes(self):
        script = (
            "import hashlib,sys; "
            f"sys.path.insert(0,{str(TOOLS)!r}); "
            "from pathlib import Path; "
            "from build_microentity_package import build_bytes; "
            f"print(hashlib.sha256(build_bytes(Path({str(self.root)!r})).data).hexdigest())"
        )
        hashes = []
        for seed in ("1", "987654"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            hashes.append(subprocess.check_output([sys.executable, "-c", script], env=env, text=True).strip())
        self.assertEqual(hashes[0], hashes[1])

    def test_member_change_changes_archive_hash(self):
        before = build_bytes(self.root).zip_sha256
        (self.root / "A.txt").write_bytes(b"changed\n")
        after = build_bytes(self.root).zip_sha256
        self.assertNotEqual(before, after)

    def test_traversal_and_duplicate_manifest_members_fail_closed(self):
        self._write_manifest(["../escape"])
        with self.assertRaisesRegex(PackageBuildError, "MANIFEST_MEMBER_PATH_FORBIDDEN"):
            build_bytes(self.root)
        self._write_manifest(["A.txt", "A.txt"])
        with self.assertRaisesRegex(PackageBuildError, "MANIFEST_DUPLICATE_MEMBER"):
            build_bytes(self.root)

    def test_missing_source_fails_closed(self):
        self._write_manifest(["missing.txt"])
        with self.assertRaisesRegex(PackageBuildError, "MEMBER_SOURCE_REGULAR_FILE_REQUIRED"):
            build_bytes(self.root)


if __name__ == "__main__":
    unittest.main()
