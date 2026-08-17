from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load() -> tuple[dict, str]:
    lock = json.loads((ROOT / "SOURCE_LOCK.json").read_text(encoding="utf-8"))
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    return lock, dockerfile


def test_debian_apt_lock_is_explicit_and_bounded() -> None:
    lock, _ = _load()
    apt = lock["debian_apt"]
    assert apt["archive"] == "debian"
    assert re.fullmatch(r"[0-9]{8}T[0-9]{6}Z", apt["snapshot"])
    assert apt["uri_template"] == "https://snapshot.debian.org/archive/debian/{snapshot}/"
    assert apt["suite"] == "trixie"
    assert apt["components"] == ["main"]
    assert apt["check_valid_until"] is False
    assert apt["signed_by"] == "/usr/share/keyrings/debian-archive-keyring.gpg"
    assert apt["integrity"] == "TLS_PLUS_APT_SIGNED_RELEASE_INDEX_AND_PACKAGE_HASH_CHAIN"
    assert apt["packages"] == {
        "ca-certificates": "20250419",
        "tmux": "3.5a-3",
    }


def test_dockerfile_replaces_mutable_mirrors_and_consumes_lock() -> None:
    _, dockerfile = _load()
    copy_pos = dockerfile.index("COPY SOURCE_LOCK.json /opt/clayverse-build/SOURCE_LOCK.json")
    apt_pos = dockerfile.index("apt-get update")
    assert copy_pos < apt_pos
    assert "deb.debian.org" not in dockerfile
    assert "https://snapshot.debian.org/archive/debian/${SNAPSHOT}/" in dockerfile
    assert "rm -f /etc/apt/sources.list /etc/apt/sources.list.d/*" in dockerfile
    assert "test -s /etc/ssl/certs/ca-certificates.crt" in dockerfile
    assert "test -r /usr/share/keyrings/debian-archive-keyring.gpg" in dockerfile
    assert "Check-Valid-Until: no" in dockerfile
    assert "Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg" in dockerfile
    assert '"ca-certificates=${CA_CERTIFICATES_VERSION}"' in dockerfile
    assert '"tmux=${TMUX_VERSION}"' in dockerfile
    assert "dpkg-query -W -f='${Version}' ca-certificates" in dockerfile
    assert "dpkg-query -W -f='${Version}' tmux" in dockerfile


def test_source_lock_no_longer_claims_mutable_apt_as_unrepaired() -> None:
    lock, _ = _load()
    gates = lock["known_open_supply_chain_gates"]
    assert not any("not yet snapshot/hash pinned" in gate for gate in gates)
    assert any("authorized isolated OCI build" in gate for gate in gates)
