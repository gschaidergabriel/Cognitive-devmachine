from __future__ import annotations

import json
import re
from pathlib import Path

LOCK_PATH = Path("/opt/clayverse-build/SOURCE_LOCK.json")
SOURCES_PATH = Path("/etc/apt/sources.list.d/debian.sources")
LEGACY_SOURCES_PATH = Path("/etc/apt/sources.list")
_TIMESTAMP_RE = re.compile(r"^[0-9]{8}T[0-9]{6}Z$")


def render_sources(lock: dict) -> str:
    snapshot = lock.get("debian_apt_snapshot")
    if not isinstance(snapshot, dict):
        raise ValueError("SOURCE_LOCK missing debian_apt_snapshot")

    timestamp = snapshot.get("timestamp")
    if not isinstance(timestamp, str) or not _TIMESTAMP_RE.fullmatch(timestamp):
        raise ValueError("invalid Debian snapshot timestamp")

    suite = snapshot.get("suite")
    updates_suite = snapshot.get("updates_suite")
    security_suite = snapshot.get("security_suite")
    if (suite, updates_suite, security_suite) != ("trixie", "trixie-updates", "trixie-security"):
        raise ValueError("unexpected Debian snapshot suites")

    return (
        "Types: deb\n"
        f"URIs: http://snapshot.debian.org/archive/debian/{timestamp}/\n"
        f"Suites: {suite} {updates_suite}\n"
        "Components: main\n"
        "Check-Valid-Until: no\n"
        "Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg\n"
        "\n"
        "Types: deb\n"
        f"URIs: http://snapshot.debian.org/archive/debian-security/{timestamp}/\n"
        f"Suites: {security_suite}\n"
        "Components: main\n"
        "Check-Valid-Until: no\n"
        "Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg\n"
    )


def main() -> None:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    rendered = render_sources(lock)
    if not Path("/usr/share/keyrings/debian-archive-keyring.gpg").is_file():
        raise SystemExit("Debian archive keyring missing from pinned base image")
    SOURCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    SOURCES_PATH.write_text(rendered, encoding="utf-8")
    LEGACY_SOURCES_PATH.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
