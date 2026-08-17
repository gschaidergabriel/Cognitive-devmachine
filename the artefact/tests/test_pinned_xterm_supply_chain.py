from __future__ import annotations

import base64
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest


ARTEFACT = Path(__file__).resolve().parents[1]
HELPER = ARTEFACT / "build" / "install_pinned_xterm.py"
spec = importlib.util.spec_from_file_location("install_pinned_xterm", HELPER)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

EXPECTED_XTERM_SRI = "sha512-TQwDdQGtwwDt+2cgKDLn0IRaSxYu1tSUjgKarSDkUM0ZNiSRXFpjxEsvc/Zgc5kq5omJ+V0a8/kIM2WD3sMOYg=="


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

    def test_source_lock_binds_expected_xterm_archive(self) -> None:
        lock = json.loads((ARTEFACT / "SOURCE_LOCK.json").read_text(encoding="utf-8"))
        xterm = lock["xterm_web"]
        self.assertEqual(xterm["package"], "@xterm/xterm")
        self.assertEqual(xterm["version"], "6.0.0")
        self.assertEqual(xterm["integrity"], EXPECTED_XTERM_SRI)
        self.assertEqual(set(xterm["required_assets"]), set(module.REQUIRED_ASSETS))

    def test_dockerfile_uses_pinned_helper_without_node_or_npm(self) -> None:
        dockerfile = (ARTEFACT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("install_pinned_xterm.py", dockerfile)
        self.assertIn("python /opt/clayverse-build/install_pinned_xterm.py", dockerfile)
        self.assertNotIn("npm install", dockerfile)
        self.assertNotIn("nodejs", dockerfile)
        self.assertNotIn("ARG XTERM_SPEC", dockerfile)


if __name__ == "__main__":
    unittest.main()
