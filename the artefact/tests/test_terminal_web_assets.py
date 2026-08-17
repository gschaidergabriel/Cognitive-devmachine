from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_xterm_is_vendored_into_single_container_image():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "ARG XTERM_SPEC=@xterm/xterm@6.0.0" in dockerfile
    assert 'npm install --global "${CLAUDE_CODE_SPEC}" "${XTERM_SPEC}"' in dockerfile
    assert 'cp -a "$(npm root -g)/@xterm/xterm" /opt/clayverse/vendor/xterm' in dockerfile
    assert "test -f /opt/clayverse/vendor/xterm/lib/xterm.js" in dockerfile
    assert "test -f /opt/clayverse/vendor/xterm/css/xterm.css" in dockerfile


def test_terminal_gateway_uses_only_container_xterm_assets():
    source = (ROOT / "clayverse" / "terminal_gateway.py").read_text(encoding="utf-8")
    assert 'app.mount("/vendor/xterm"' in source
    assert 'href="/vendor/xterm/css/xterm.css"' in source
    assert 'src="/vendor/xterm/lib/xterm.js"' in source
    assert "cdn.jsdelivr.net/npm/@xterm" not in source
