from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SNAPSHOT_RE = re.compile(r"^[0-9]{8}T[0-9]{6}Z$")
EXPECTED = (
    ("debian", ("trixie", "trixie-updates")),
    ("debian-security", ("trixie-security",)),
)


def load_lock(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "ClayVerseSourceLock/v1":
        raise SystemExit("invalid SOURCE_LOCK schema")
    apt = data.get("debian_apt")
    if not isinstance(apt, dict):
        raise SystemExit("missing debian_apt lock")
    snapshot = apt.get("snapshot_id")
    if not isinstance(snapshot, str) or not SNAPSHOT_RE.fullmatch(snapshot):
        raise SystemExit("invalid Debian snapshot_id")
    if apt.get("signed_by") != "/usr/share/keyrings/debian-archive-keyring.gpg":
        raise SystemExit("unexpected Debian keyring")
    if apt.get("check_valid_until") is not False:
        raise SystemExit("snapshot Check-Valid-Until must be false")
    if apt.get("packages") != ["ca-certificates", "tmux"]:
        raise SystemExit("unexpected baseline apt package set")
    archives = apt.get("archives")
    if not isinstance(archives, list) or len(archives) != len(EXPECTED):
        raise SystemExit("unexpected Debian archive set")
    for row, (name, suites) in zip(archives, EXPECTED, strict=True):
        if not isinstance(row, dict) or row.get("name") != name:
            raise SystemExit("unexpected Debian archive identity")
        expected_uri = f"https://snapshot.debian.org/archive/{name}/{snapshot}/"
        if row.get("uri") != expected_uri:
            raise SystemExit("snapshot URI is not bound to snapshot_id")
        if row.get("suites") != list(suites) or row.get("components") != ["main"]:
            raise SystemExit("unexpected Debian suite/components")
    return apt


def render(apt: dict) -> str:
    stanzas: list[str] = []
    for row in apt["archives"]:
        stanzas.append(
            "\n".join(
                [
                    "Types: deb",
                    f"URIs: {row['uri']}",
                    f"Suites: {' '.join(row['suites'])}",
                    f"Components: {' '.join(row['components'])}",
                    f"Signed-By: {apt['signed_by']}",
                    "Check-Valid-Until: no",
                ]
            )
        )
    return "\n\n".join(stanzas) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    apt = load_lock(args.lock)
    text = render(apt)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
