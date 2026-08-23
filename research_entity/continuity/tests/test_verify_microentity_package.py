import json
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from verify_microentity_package import PackageVerificationError, make_receipt, verify_package


class PackageVerifierTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "MicroEntity"
        self.root.mkdir()
        (self.root / "hcu").mkdir()
        self.members = ["A.txt", "hcu/B.txt"]
        (self.root / "A.txt").write_bytes(b"alpha\n")
        (self.root / "hcu/B.txt").write_bytes(b"beta\n")
        (self.root / "PACKAGE_MANIFEST.json").write_text(
            json.dumps({"snapshot": "MICROENTITY_CURRENT.zip", "archive_members_required": self.members}),
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, *, names=None, mutate=None):
        names = self.members if names is None else names
        target = self.root / "MICROENTITY_CURRENT.zip"
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for name in names:
                data = (self.root / name).read_bytes()
                if mutate and name in mutate:
                    data = mutate[name]
                z.writestr(name, data)
        return target

    def test_exact_order_and_source_bytes_pass(self):
        self.build()
        result = verify_package(self.root)
        self.assertEqual(result.members, tuple(self.members))
        self.assertEqual(len(result.zip_sha256), 64)
        self.assertEqual(len(result.zip_git_blob_sha1), 40)

    def test_truncated_zip_fails_closed(self):
        target = self.build()
        data = target.read_bytes()
        target.write_bytes(data[:-13])
        with self.assertRaisesRegex(PackageVerificationError, "ZIP_BAD_OR_TRUNCATED"):
            verify_package(self.root)

    def test_missing_member_fails_closed(self):
        self.build(names=["A.txt"])
        with self.assertRaisesRegex(PackageVerificationError, "ZIP_MEMBER_SET_OR_ORDER_MISMATCH"):
            verify_package(self.root)

    def test_member_order_mismatch_fails_closed(self):
        self.build(names=list(reversed(self.members)))
        with self.assertRaisesRegex(PackageVerificationError, "ZIP_MEMBER_SET_OR_ORDER_MISMATCH"):
            verify_package(self.root)

    def test_stale_member_bytes_fail_closed(self):
        self.build(mutate={"A.txt": b"stale\n"})
        with self.assertRaisesRegex(PackageVerificationError, "ZIP_MEMBER_BYTES_MISMATCH:A.txt"):
            verify_package(self.root)

    def test_duplicate_member_fails_closed(self):
        target = self.root / "MICROENTITY_CURRENT.zip"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(target, "w") as z:
                z.writestr("A.txt", b"alpha\n")
                z.writestr("A.txt", b"alpha\n")
                z.writestr("hcu/B.txt", b"beta\n")
        with self.assertRaisesRegex(PackageVerificationError, "ZIP_DUPLICATE_MEMBER"):
            verify_package(self.root)

    def test_manifest_traversal_fails_closed(self):
        (self.root / "PACKAGE_MANIFEST.json").write_text(
            json.dumps({"snapshot": "MICROENTITY_CURRENT.zip", "archive_members_required": ["../escape"]}),
            encoding="utf-8",
        )
        self.build(names=[])
        with self.assertRaisesRegex(PackageVerificationError, "MANIFEST_MEMBER_PATH_FORBIDDEN"):
            verify_package(self.root)

    def test_receipt_requires_exact_git_identity_and_mints_no_runtime_credit(self):
        self.build()
        result = verify_package(self.root)
        receipt = make_receipt(result, source_commit="a" * 40, source_tree="b" * 40, package_path="the artefact/MicroEntity")
        self.assertEqual(receipt["schema"], "PACKAGE_ARTIFACT_RECEIPT/v1")
        self.assertEqual(receipt["runtime_credit"], 0)
        with self.assertRaisesRegex(PackageVerificationError, "SOURCE_COMMIT_GIT_SHA1_REQUIRED"):
            make_receipt(result, source_commit="bad", source_tree="b" * 40, package_path="x")


if __name__ == "__main__":
    unittest.main()
