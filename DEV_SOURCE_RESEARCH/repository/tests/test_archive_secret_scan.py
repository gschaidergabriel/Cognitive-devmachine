from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("archive_secret_scan", ROOT / "tools" / "archive_secret_scan.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def test_detects_without_echoing_secret():
    fake = "API_KEY='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'\nfoo gsk_1234567890abcdefghijklmnop\n"
    findings = mod.scan_text(fake, "synthetic.txt")
    assert findings
    serialized = repr(findings)
    assert "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" not in serialized
    assert "gsk_1234567890abcdefghijklmnop" not in serialized
    assert all("fingerprint" in f and "match_length" in f for f in findings)


def test_clean_text_is_clean():
    assert mod.scan_text("no credentials here\n", "clean.txt") == []
