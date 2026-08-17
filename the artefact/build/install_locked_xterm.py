#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import subprocess
import tempfile

LOCK_SCHEMA = "ClayVerseSourceLock/v1"


class XtermLockError(RuntimeError):
    pass


def load_xterm_lock(path: Path) -> tuple[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise XtermLockError(f"cannot read source lock: {exc}") from exc
    if data.get("schema") != LOCK_SCHEMA:
        raise XtermLockError("unexpected source lock schema")
    entry = data.get("xterm")
    if not isinstance(entry, dict):
        raise XtermLockError("missing xterm source lock")
    package = entry.get("package")
    version = entry.get("version")
    integrity = entry.get("tarball_integrity")
    if package != "@xterm/xterm" or not isinstance(version, str) or not version:
        raise XtermLockError("invalid xterm package/version lock")
    if not isinstance(integrity, str) or not integrity.startswith("sha512-"):
        raise XtermLockError("invalid xterm sha512 integrity lock")
    try:
        digest = base64.b64decode(integrity.removeprefix("sha512-"), validate=True)
    except ValueError as exc:
        raise XtermLockError("invalid xterm integrity base64") from exc
    if len(digest) != hashlib.sha512().digest_size:
        raise XtermLockError("invalid xterm sha512 digest length")
    return f"{package}@{version}", integrity


def sri_sha512(path: Path) -> str:
    digest = hashlib.sha512()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha512-" + base64.b64encode(digest.digest()).decode("ascii")


def verify_archive(path: Path, expected_integrity: str) -> None:
    actual_integrity = sri_sha512(path)
    if not hmac.compare_digest(actual_integrity, expected_integrity):
        raise XtermLockError(
            "xterm tarball integrity mismatch: "
            f"expected {expected_integrity}, got {actual_integrity}"
        )


def _pack_xterm(spec: str, destination: Path) -> Path:
    proc = subprocess.run(
        [
            "npm",
            "pack",
            "--json",
            "--ignore-scripts",
            "--pack-destination",
            str(destination),
            spec,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise XtermLockError("npm pack returned invalid JSON") from exc
    if not isinstance(payload, list) or len(payload) != 1 or not isinstance(payload[0], dict):
        raise XtermLockError("npm pack returned unexpected result cardinality")
    filename = payload[0].get("filename")
    if not isinstance(filename, str) or not filename or Path(filename).name != filename:
        raise XtermLockError("npm pack returned unsafe filename")
    archive = (destination / filename).resolve()
    if archive.parent != destination.resolve() or not archive.is_file():
        raise XtermLockError("npm pack archive missing or escaped destination")
    return archive


def install(lock_path: Path) -> None:
    spec, expected_integrity = load_xterm_lock(lock_path)
    with tempfile.TemporaryDirectory(prefix="clayverse-xterm-") as tmp:
        archive = _pack_xterm(spec, Path(tmp))
        verify_archive(archive, expected_integrity)
        env = os.environ.copy()
        env.setdefault("npm_config_audit", "false")
        env.setdefault("npm_config_fund", "false")
        subprocess.run(
            ["npm", "install", "--global", "--ignore-scripts", str(archive)],
            check=True,
            env=env,
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lock",
        type=Path,
        default=Path("/opt/clayverse-build/SOURCE_LOCK.json"),
    )
    parser.add_argument("--verify-archive", type=Path)
    args = parser.parse_args()
    spec, expected_integrity = load_xterm_lock(args.lock)
    if args.verify_archive is not None:
        verify_archive(args.verify_archive, expected_integrity)
        print(
            json.dumps(
                {"spec": spec, "integrity": expected_integrity, "verified": True},
                sort_keys=True,
            )
        )
        return 0
    install(args.lock)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
