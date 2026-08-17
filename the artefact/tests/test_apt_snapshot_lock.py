import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "build" / "install_pinned_apt.py"
spec = importlib.util.spec_from_file_location("install_pinned_apt", HELPER_PATH)
install_pinned_apt = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(install_pinned_apt)


def _load_lock():
    return json.loads((ROOT / "SOURCE_LOCK.json").read_text(encoding="utf-8"))


def _write_lock(tmp_path: Path, lock: dict) -> Path:
    path = tmp_path / "SOURCE_LOCK.json"
    path.write_text(json.dumps(lock), encoding="utf-8")
    return path


def test_debian_apt_lock_renders_only_fixed_snapshot_sources():
    apt = install_pinned_apt.load_and_validate(ROOT / "SOURCE_LOCK.json")
    rendered = install_pinned_apt.render_sources(apt)

    assert "http://snapshot.debian.org/archive/debian/20260817T000000Z/" in rendered
    assert "http://snapshot.debian.org/archive/debian-security/20260817T000000Z/" in rendered
    assert "Suites: trixie" in rendered
    assert "Suites: trixie-security" in rendered
    assert rendered.count("Check-Valid-Until: no") == 2
    assert "deb.debian.org" not in rendered
    assert "security.debian.org" not in rendered


def test_debian_apt_lock_rejects_mutable_mirror_substitution(tmp_path):
    lock = _load_lock()
    lock["debian_apt"]["archives"][0]["uri"] = "http://deb.debian.org/debian"
    with pytest.raises(ValueError, match="exact Debian snapshot"):
        install_pinned_apt.load_and_validate(_write_lock(tmp_path, lock))


def test_debian_apt_lock_rejects_snapshot_uri_mismatch(tmp_path):
    lock = _load_lock()
    lock["debian_apt"]["archives"][0]["uri"] = (
        "http://snapshot.debian.org/archive/debian/20260816T000000Z/"
    )
    with pytest.raises(ValueError, match="exact Debian snapshot"):
        install_pinned_apt.load_and_validate(_write_lock(tmp_path, lock))


def test_debian_apt_lock_rejects_package_set_or_signing_drift(tmp_path):
    lock = _load_lock()
    lock["debian_apt"]["packages"].append("curl")
    with pytest.raises(ValueError, match="package set drift"):
        install_pinned_apt.load_and_validate(_write_lock(tmp_path, lock))

    lock = _load_lock()
    lock["debian_apt"]["archives"][1]["signed_by"] = "/tmp/other.gpg"
    with pytest.raises(ValueError, match="signing keyring drift"):
        install_pinned_apt.load_and_validate(_write_lock(tmp_path, lock))


def test_dockerfile_removes_inherited_sources_before_apt_resolution():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "rm -f /etc/apt/sources.list" in dockerfile
    assert "install_pinned_apt.py --write-sources" in dockerfile
    assert "install_pinned_apt.py --print-packages" in dockerfile
    assert dockerfile.index("COPY SOURCE_LOCK.json") < dockerfile.index("apt-get update")
