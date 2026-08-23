import json
import tempfile
import unittest
from pathlib import Path

import rebuild_snapshot as rs

class SnapshotTests(unittest.TestCase):
    def fixture(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "a.txt").write_text("alpha\n", encoding="utf-8")
        (root / "sub").mkdir()
        (root / "sub/b.txt").write_text("beta\n", encoding="utf-8")
        manifest = {
            "package": "MicroEntity",
            "archive_members_required": ["a.txt", "sub/b.txt"],
        }
        (root / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
        return td, root

    def test_deterministic_and_verified(self):
        td, root = self.fixture()
        self.addCleanup(td.cleanup)
        one = rs.rebuild(root, root / "one.zip", None, "h", "t")
        two = rs.rebuild(root, root / "two.zip", None, "h", "t")
        self.assertEqual((root / "one.zip").read_bytes(), (root / "two.zip").read_bytes())
        self.assertEqual(one["archive_sha256"], two["archive_sha256"])
        self.assertEqual(one["member_count"], 2)

    def test_member_order_is_manifest_order(self):
        td, root = self.fixture()
        self.addCleanup(td.cleanup)
        receipt = rs.rebuild(root, root / "x.zip", None, None, None)
        self.assertEqual([m["name"] for m in receipt["members"]], ["a.txt", "sub/b.txt"])

    def test_unusual_traversal_poison_fails_closed(self):
        td, root = self.fixture()
        self.addCleanup(td.cleanup)
        manifest = json.loads((root / "PACKAGE_MANIFEST.json").read_text())
        manifest["archive_members_required"].append("../escape.txt")
        (root / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(rs.SnapshotError, "UNSAFE_MEMBER_PATH"):
            rs.rebuild(root, root / "poison.zip", None, None, None)

if __name__ == "__main__":
    unittest.main()
