#!/usr/bin/env python3
"""Render ClayVerse's fail-closed Debian snapshot APT source contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

LOCK_SCHEMA = "ClayVerseSourceLock/v1"
APT_SCHEMA = "ClayVerseDebianSnapshot/v1"
SNAPSHOT_RE = re.compile(r"^\d{8}T\d{6}Z$")
PACKAGE_RE = re.compile(r"^[a-z0-9][a-z0-9+.-]*$")
EXPECTED_PACKAGES = ("ca-certificates", "tmux")
EXPECTED_ARCHIVES = {
    "debian": "trixie",
    "debian-security": "trixie-security",
}
EXPECTED_SIGNED_BY = "/usr/share/keyrings/debian-archive-keyring.gpg"
EXPECTED_HOST = "snapshot.debian.org"


def _fail(message: str) -> ValueError:
    return ValueError(f"invalid debian_apt source lock: {message}")


def load_and_validate(lock_path: Path) -> dict:
    raw = json.loads(lock_path.read_text(encoding="utf-8"))
    if raw.get("schema") != LOCK_SCHEMA:
        raise _fail("wrong top-level schema")

    apt = raw.get("debian_apt")
    if not isinstance(apt, dict) or apt.get("schema") != APT_SCHEMA:
        raise _fail("missing/wrong debian_apt schema")

    allowed = {
        "schema",
        "snapshot",
        "archives",
        "packages",
        "integrity",
        "mutable_mirror_fallback",
    }
    if set(apt) != allowed:
        raise _fail("unexpected debian_apt fields")

    snapshot = apt.get("snapshot")
    if not isinstance(snapshot, str) or not SNAPSHOT_RE.fullmatch(snapshot):
        raise _fail("snapshot must be YYYYMMDDThhmmssZ")

    if apt.get("integrity") != "DEBIAN_SIGNED_RELEASE_TO_PACKAGES_TO_DEB_HASH_CHAIN":
        raise _fail("unexpected integrity contract")
    if apt.get("mutable_mirror_fallback") is not False:
        raise _fail("mutable mirror fallback must be false")

    packages = apt.get("packages")
    if packages != list(EXPECTED_PACKAGES):
        raise _fail("package set drift")
    if any(not PACKAGE_RE.fullmatch(pkg) for pkg in packages):
        raise _fail("invalid package name")

    archives = apt.get("archives")
    if not isinstance(archives, list) or len(archives) != len(EXPECTED_ARCHIVES):
        raise _fail("archive set drift")

    seen = set()
    for entry in archives:
        if not isinstance(entry, dict):
            raise _fail("archive entry must be object")
        expected_fields = {
            "archive", "uri", "suite", "components", "signed_by", "check_valid_until"
        }
        if set(entry) != expected_fields:
            raise _fail("unexpected archive fields")

        archive = entry.get("archive")
        if archive not in EXPECTED_ARCHIVES or archive in seen:
            raise _fail("unknown/duplicate archive")
        seen.add(archive)

        if entry.get("suite") != EXPECTED_ARCHIVES[archive]:
            raise _fail("suite drift")
        if entry.get("components") != ["main"]:
            raise _fail("components drift")
        if entry.get("signed_by") != EXPECTED_SIGNED_BY:
            raise _fail("signing keyring drift")
        if entry.get("check_valid_until") is not False:
            raise _fail("snapshot Valid-Until must be disabled per-source")

        uri = entry.get("uri")
        if not isinstance(uri, str):
            raise _fail("uri must be string")
        parsed = urlparse(uri)
        expected_path = f"/archive/{archive}/{snapshot}/"
        if (
            parsed.scheme != "https"
            or parsed.hostname != EXPECTED_HOST
            or parsed.port is not None
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.path != expected_path
        ):
            raise _fail("archive uri must be the exact HTTPS Debian snapshot path")

    if seen != set(EXPECTED_ARCHIVES):
        raise _fail("missing archive")
    return apt


def render_sources(apt: dict) -> str:
    stanzas = []
    for entry in apt["archives"]:
        stanzas.append(
            "\n".join(
                [
                    "Types: deb",
                    f"URIs: {entry['uri']}",
                    f"Suites: {entry['suite']}",
                    f"Components: {' '.join(entry['components'])}",
                    f"Signed-By: {entry['signed_by']}",
                    "Check-Valid-Until: no",
                ]
            )
        )
    return "\n\n".join(stanzas) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lock",
        default="/opt/clayverse-build/SOURCE_LOCK.json",
        type=Path,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write-sources", type=Path)
    group.add_argument("--print-packages", action="store_true")
    args = parser.parse_args()

    apt = load_and_validate(args.lock)
    if args.write_sources is not None:
        args.write_sources.parent.mkdir(parents=True, exist_ok=True)
        args.write_sources.write_text(render_sources(apt), encoding="utf-8")
    else:
        print(" ".join(apt["packages"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())