import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_xterm_is_digest_locked_and_vendored_without_node_or_npm():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    lock = json.loads((ROOT / "SOURCE_LOCK.json").read_text(encoding="utf-8"))["xterm"]
    assert lock["package"] == "@xterm/xterm"
    assert lock["version"] == "6.0.0"
    assert len(lock["sha512"]) == 128
    assert "install_pinned_xterm.py" in dockerfile
    assert "npm install" not in dockerfile
    assert "nodejs" not in dockerfile
    assert "test -f /opt/clayverse/vendor/xterm/lib/xterm.js" in dockerfile
    assert "test -f /opt/clayverse/vendor/xterm/css/xterm.css" in dockerfile


def test_terminal_gateway_uses_only_container_xterm_assets():
    source = (ROOT / "clayverse" / "terminal_gateway.py").read_text(encoding="utf-8")
    assert 'app.mount("/vendor/xterm"' in source
    assert 'href="/vendor/xterm/css/xterm.css"' in source
    assert 'src="/vendor/xterm/lib/xterm.js"' in source
    assert "cdn.jsdelivr.net/npm/@xterm" not in source
