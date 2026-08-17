from __future__ import annotations

import base64
import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest


HELPER = Path(__file__).resolve().parents[1] / "build" / "install_pinned_xterm.py"
spec = importlib.util.spec_from_file_location("install_pinned_xterm", HELPER)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def make_tar(entries: list[tuple[str, bytes]]) -> bytes:
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        for name, data in entries:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(data))
    return output.getvalue()


def sri(blob: bytes) -> str:
    return "sha512-" + base64.b64encode(hashlib.sha512(blob).digest()).decode("ascii")


class PinnedXtermSupplyChainTests(unittest.TestCase):
    def test_verified_archive_installs_only_required_assets(self) -> None:
        blob = make_tar([
            ("package/lib/xterm.js", b"window.Terminal = function () {};\n"),
            ("package/css/xterm.css", b".xterm { display: block; }\n"),
            ("package/README.md", b"ignored\n"),
        ])
        module._verify_archive(blob, sri(blob))
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "xterm"
            module._extract_required_assets(blob, destination)
            self.assertEqual((destination / "lib/xterm.js").read_bytes(), b"window.Terminal = function () {};\n")
            self.assertEqual((destination / "css/xterm.css").read_bytes(), b".xterm { display: block; }\n")
            self.assertFalse((destination / "README.md").exists())

    def test_digest_mismatch_fails_closed(self) -> None:
        blob = make_tar([
            ("package/lib/xterm.js", b"a"),
            ("package/css/xterm.css", b"b"),
        ])
        with self.assertRaisesRegex(ValueError, "sha512 mismatch"):
            module._verify_archive(blob + b"tamper", sri(blob))

    def test_missing_required_asset_fails_closed(self) -> None:
        blob = make_tar([("package/lib/xterm.js", b"a")])
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "missing required assets"):
                module._extract_required_assets(blob, Path(tmp))

    def test_duplicate_required_asset_fails_closed(self) -> None:
        blob = make_tar([
            ("package/lib/xterm.js", b"a"),
            ("package/lib/xterm.js", b"b"),
            ("package/css/xterm.css", b"c"),
        ])
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "duplicate required"):
                module._extract_required_assets(blob, Path(tmp))

    def test_path_traversal_member_fails_closed(self) -> None:
        blob = make_tar([
            ("package/lib/xterm.js", b"a"),
            ("package/css/xterm.css", b"b"),
            ("package/../../escape", b"owned"),
        ])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "unsafe xterm archive member"):
                module._extract_required_assets(blob, root / "xterm")
            self.assertFalse((root / "escape").exists())


if __name__ == "__main__":
    unittest.main()
