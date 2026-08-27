from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "build" / "install_pinned_xterm.py"
spec = importlib.util.spec_from_file_location("install_pinned_xterm", MODULE_PATH)
assert spec and spec.loader
xterm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(xterm)


def archive(*, name="@xterm/xterm", version="6.0.0", extra=None) -> bytes:
    files = {
        "package/package.json": json.dumps({"name": name, "version": version}).encode(),
        "package/lib/xterm.js": b"console.log('xterm');\n",
        "package/css/xterm.css": b".xterm{}\n",
    }
    if extra:
        files.update(extra)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for path, payload in files.items():
            info = tarfile.TarInfo(path)
            info.size = len(payload)
            info.mode = 0o644
            tf.addfile(info, io.BytesIO(payload))
    return buf.getvalue()


class PinnedXtermSupplyChainTests(unittest.TestCase):
    def test_repository_lock_and_dockerfile_use_digest_pinned_installer(self):
        lock = json.loads((ROOT / "SOURCE_LOCK.json").read_text("utf-8"))
        item = lock["xterm"]
        self.assertEqual(item["package"], "@xterm/xterm")
        self.assertEqual(item["version"], "6.0.0")
        self.assertEqual(len(item["sha512"]), 128)
        self.assertTrue(any("xterm SHA-512 lock" in gate for gate in lock["known_open_supply_chain_gates"]))
        dockerfile = (ROOT / "Dockerfile").read_text("utf-8")
        self.assertIn("install_pinned_xterm.py", dockerfile)
        self.assertNotIn("npm install", dockerfile)
        self.assertNotIn("nodejs npm", dockerfile)
        dockerignore = (ROOT / ".dockerignore").read_text("utf-8")
        self.assertIn("!build/install_pinned_xterm.py", dockerignore)

    def test_archive_resource_bounds_are_explicit(self):
        self.assertEqual(xterm.MAX_ARCHIVE_BYTES, 20 * 1024 * 1024)
        self.assertEqual(xterm.MAX_MEMBERS, 4096)
        self.assertEqual(xterm.MAX_UNPACKED_BYTES, 64 * 1024 * 1024)
        source = MODULE_PATH.read_text("utf-8")
        self.assertIn("response.read(MAX_ARCHIVE_BYTES + 1)", source)
        self.assertIn("len(members) > MAX_MEMBERS", source)
        self.assertIn("unpacked_bytes > MAX_UNPACKED_BYTES", source)

    def test_valid_locked_archive_extracts_required_assets_only(self):
        data = archive(extra={"package/README.md": b"not a runtime asset"})
        xterm.verify_digest(data, hashlib.sha512(data).hexdigest())
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "xterm"
            xterm.install_archive(data, target, "@xterm/xterm", "6.0.0")
            files = sorted(str(path.relative_to(target)) for path in target.rglob("*") if path.is_file())
            self.assertEqual(files, ["css/xterm.css", "lib/xterm.js", "package.json"])
            self.assertEqual(json.loads((target / "package.json").read_text())["version"], "6.0.0")

    def test_package_identity_mismatch_fails_closed(self):
        data = archive(name="@xterm/other")
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(SystemExit, "identity mismatch"):
                xterm.install_archive(data, Path(td) / "xterm", "@xterm/xterm", "6.0.0")

    def test_path_traversal_fails_closed(self):
        data = archive(extra={"package/../escape": b"no"})
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(SystemExit, "unsafe xterm archive path"):
                xterm.install_archive(data, Path(td) / "xterm", "@xterm/xterm", "6.0.0")

    def test_symlink_fails_closed(self):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tf:
            for path, payload in {
                "package/package.json": b'{"name":"@xterm/xterm","version":"6.0.0"}',
                "package/lib/xterm.js": b"x",
                "package/css/xterm.css": b"x",
            }.items():
                info = tarfile.TarInfo(path)
                info.size = len(payload)
                tf.addfile(info, io.BytesIO(payload))
            link = tarfile.TarInfo("package/escape")
            link.type = tarfile.SYMTYPE
            link.linkname = "/etc/passwd"
            tf.addfile(link)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(SystemExit, "unsafe xterm archive member type"):
                xterm.install_archive(buf.getvalue(), Path(td) / "xterm", "@xterm/xterm", "6.0.0")

    def test_digest_mismatch_fails_before_archive_open(self):
        data = archive()
        tampered = bytearray(data)
        tampered[len(tampered) // 2] ^= 0x01
        with self.assertRaisesRegex(SystemExit, "digest mismatch"):
            xterm.verify_digest(bytes(tampered), hashlib.sha512(data).hexdigest())


if __name__ == "__main__":
    unittest.main()
