import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "build" / "write_pinned_debian_sources.py"
LOCK_PATH = ROOT / "SOURCE_LOCK.json"
DOCKERFILE_PATH = ROOT / "Dockerfile"


def _load_helper():
    spec = importlib.util.spec_from_file_location("clayverse_debian_snapshot", HELPER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repository_lock_renders_only_fixed_snapshot_sources():
    helper = _load_helper()
    apt = helper.load_lock(LOCK_PATH)
    rendered = helper.render(apt)
    snapshot = apt["snapshot_id"]

    assert snapshot == "20260817T000000Z"
    assert rendered.count(f"/{snapshot}/") == 2
    assert rendered.count("https://snapshot.debian.org/archive/") == 2
    assert rendered.count("Check-Valid-Until: no") == 2
    assert "deb.debian.org" not in rendered
    assert "security.debian.org" not in rendered


def test_snapshot_uri_drift_fails_closed(tmp_path):
    helper = _load_helper()
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    lock["debian_apt"]["archives"][0]["uri"] = "https://deb.debian.org/debian"
    bad = tmp_path / "SOURCE_LOCK.json"
    bad.write_text(json.dumps(lock), encoding="utf-8")

    with pytest.raises(SystemExit, match="snapshot URI is not bound"):
        helper.load_lock(bad)


def test_dockerfile_removes_moving_sources_before_apt_update():
    source = DOCKERFILE_PATH.read_text(encoding="utf-8")
    write_pos = source.index("write_pinned_debian_sources.py")
    delete_pos = source.index("find /etc/apt/sources.list.d")
    update_pos = source.index("apt-get update")
    install_pos = source.index("apt-get install -y --no-install-recommends ca-certificates tmux")

    assert write_pos < delete_pos < update_pos < install_pos
    assert "! -name clayverse-snapshot.sources -delete" in source
    assert "rm -f /etc/apt/sources.list" in source
    assert "https://snapshot.debian.org" not in source
