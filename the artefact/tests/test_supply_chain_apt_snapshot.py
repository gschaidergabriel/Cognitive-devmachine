from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "build" / "configure_pinned_apt.py"


def _load_helper():
    spec = importlib.util.spec_from_file_location("configure_pinned_apt", HELPER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_lock_renders_timestamped_signed_debian_snapshots():
    helper = _load_helper()
    lock = json.loads((ROOT / "SOURCE_LOCK.json").read_text(encoding="utf-8"))
    rendered = helper.render_sources(lock)
    timestamp = lock["debian_apt_snapshot"]["timestamp"]

    assert f"archive/debian/{timestamp}/" in rendered
    assert f"archive/debian-security/{timestamp}/" in rendered
    assert "Suites: trixie trixie-updates" in rendered
    assert "Suites: trixie-security" in rendered
    assert rendered.count("Check-Valid-Until: no") == 2
    assert rendered.count("Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg") == 2
    assert "deb.debian.org" not in rendered


def test_snapshot_timestamp_and_suites_fail_closed():
    helper = _load_helper()
    valid = {
        "debian_apt_snapshot": {
            "timestamp": "20260817T000000Z",
            "suite": "trixie",
            "updates_suite": "trixie-updates",
            "security_suite": "trixie-security",
        }
    }

    bad_timestamp = json.loads(json.dumps(valid))
    bad_timestamp["debian_apt_snapshot"]["timestamp"] = "latest"
    with pytest.raises(ValueError, match="timestamp"):
        helper.render_sources(bad_timestamp)

    bad_suite = json.loads(json.dumps(valid))
    bad_suite["debian_apt_snapshot"]["suite"] = "testing"
    with pytest.raises(ValueError, match="suites"):
        helper.render_sources(bad_suite)


def test_dockerfile_configures_snapshot_before_any_apt_resolution():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    configure = "python /opt/clayverse-build/configure_pinned_apt.py"
    apt_update = "apt-get update"
    apt_install = "apt-get install -y --no-install-recommends ca-certificates tmux"

    assert "COPY SOURCE_LOCK.json /opt/clayverse-build/SOURCE_LOCK.json" in dockerfile
    assert "COPY build/configure_pinned_apt.py /opt/clayverse-build/configure_pinned_apt.py" in dockerfile
    assert dockerfile.index(configure) < dockerfile.index(apt_update) < dockerfile.index(apt_install)
    assert dockerfile.count("apt-get update") == 1


def test_source_lock_no_longer_claims_unpinned_apt_repositories():
    lock = json.loads((ROOT / "SOURCE_LOCK.json").read_text(encoding="utf-8"))
    assert lock["debian_apt_snapshot"]["timestamp"] == "20260817T000000Z"
    gates = lock["known_open_supply_chain_gates"]
    assert all("not yet snapshot/hash pinned" not in gate for gate in gates)
    assert any("exact apt metadata resolution" in gate for gate in gates)
