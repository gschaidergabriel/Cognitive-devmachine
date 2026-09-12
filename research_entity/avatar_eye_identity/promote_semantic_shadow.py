#!/usr/bin/env python3
"""Fail-closed transactional promoter for the accepted canonical-eye shadow.

This script is intentionally incapable of promoting from prose. It requires two
machine-readable pre-live reports from the exact candidate subject:

* GO_AVATAR_EYE_SHADOW_RUNTIME/v2
* GO_AVATAR_EYE_MATCHED_FROZEN_AB/v1

Both report check maps must be fully true. The currently live buehne.html, the
shadow candidate, and the productive open-eye asset must match their exact
pre-registered hashes. A byte-exact rollback copy is persisted before an atomic
same-filesystem replacement.

Successful installation is only INSTALLED_PENDING_POST_LIVE_GATE. It does not
mint runtime acceptance; a separate live-browser readback is mandatory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from urllib.request import Request, urlopen

EXPECTED_BEFORE_SHA256 = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"
EXPECTED_AFTER_SHA256 = "4fb62046e650f993edb89be24c40262fb8e7202e2c7cda14df7aa0113cfbfb4d"
EXPECTED_OPEN_PLATE_SHA256 = "8ab1a11c6f8a738e34c516bbf65c00e0f48de70c7341bfa970f236e002c94fc9"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path}: expected JSON object")
    return value


def require_all_checks(report: dict, schema: str, name: str) -> None:
    if report.get("schema") != schema:
        raise RuntimeError(f"{name}: schema {report.get('schema')!r} != {schema!r}")
    checks = report.get("checks")
    if not isinstance(checks, dict) or not checks:
        raise RuntimeError(f"{name}: missing non-empty checks map")
    failed = sorted(k for k, v in checks.items() if v is not True)
    if failed:
        raise RuntimeError(f"{name}: failed checks: {failed}")
    if report.get("source_mutation") is not False:
        raise RuntimeError(f"{name}: pre-live report does not prove source_mutation=false")
    if report.get("live_sha256") != EXPECTED_BEFORE_SHA256:
        raise RuntimeError(
            f"{name}: live subject {report.get('live_sha256')} != {EXPECTED_BEFORE_SHA256}"
        )
    if report.get("shadow_sha256") != EXPECTED_AFTER_SHA256:
        raise RuntimeError(
            f"{name}: shadow subject {report.get('shadow_sha256')} != {EXPECTED_AFTER_SHA256}"
        )
    if report.get("open_plate_sha256") != EXPECTED_OPEN_PLATE_SHA256:
        raise RuntimeError(
            f"{name}: open-eye subject {report.get('open_plate_sha256')} != {EXPECTED_OPEN_PLATE_SHA256}"
        )


def http_body_sha(url: str) -> tuple[str, int, str | None]:
    req = Request(url, headers={"Cache-Control": "no-cache", "Pragma": "no-cache"})
    with urlopen(req, timeout=10) as response:
        body = response.read()
        return hashlib.sha256(body).hexdigest(), int(response.status), response.headers.get("Content-Type")


def atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{destination.name}.promote-", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as out:
            with source.open("rb") as inp:
                shutil.copyfileobj(inp, out)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(tmp_name, source.stat().st_mode & 0o777)
        os.replace(tmp_name, destination)
        try:
            dirfd = os.open(destination.parent, os.O_DIRECTORY)
            try:
                os.fsync(dirfd)
            finally:
                os.close(dirfd)
        except (AttributeError, OSError):
            pass
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def promote(args: argparse.Namespace) -> int:
    visual = args.visual_root.resolve()
    live = visual / "buehne.html"
    open_plate = visual / "augen_blink_relief2" / "blink_000.png"
    shadow = args.shadow.resolve()
    runtime_report_path = args.runtime_report.resolve()
    matched_report_path = args.matched_report.resolve()
    evidence = args.evidence_dir.resolve()

    runtime = load_json(runtime_report_path)
    matched = load_json(matched_report_path)
    require_all_checks(runtime, "GO_AVATAR_EYE_SHADOW_RUNTIME/v2", "runtime")
    require_all_checks(matched, "GO_AVATAR_EYE_MATCHED_FROZEN_AB/v1", "matched_ab")

    before_sha = sha256_file(live)
    shadow_sha = sha256_file(shadow)
    open_sha = sha256_file(open_plate)
    if before_sha != EXPECTED_BEFORE_SHA256:
        raise RuntimeError(f"live drift: {before_sha} != {EXPECTED_BEFORE_SHA256}")
    if shadow_sha != EXPECTED_AFTER_SHA256:
        raise RuntimeError(f"shadow drift: {shadow_sha} != {EXPECTED_AFTER_SHA256}")
    if open_sha != EXPECTED_OPEN_PLATE_SHA256:
        raise RuntimeError(f"open-eye drift: {open_sha} != {EXPECTED_OPEN_PLATE_SHA256}")

    if evidence.exists():
        raise RuntimeError(f"evidence directory already exists: {evidence}")
    evidence.mkdir(parents=True)
    rollback = evidence / f"buehne.before.{before_sha}.html"
    shutil.copy2(live, rollback)
    if sha256_file(rollback) != before_sha:
        raise RuntimeError("rollback copy failed byte-exact verification")
    shutil.copy2(runtime_report_path, evidence / "prelive.runtime.json")
    shutil.copy2(matched_report_path, evidence / "prelive.matched_ab.json")
    shutil.copy2(shadow, evidence / f"candidate.{shadow_sha}.html")

    manifest: dict[str, object] = {
        "schema": "GO_AVATAR_EYE_LIVE_PROMOTION/v1",
        "status": "PREPARED",
        "live_path": str(live),
        "before_sha256": before_sha,
        "candidate_sha256": shadow_sha,
        "open_plate_sha256": open_sha,
        "rollback_path": str(rollback),
        "prelive_runtime_report": str(runtime_report_path),
        "prelive_matched_report": str(matched_report_path),
        "verify_url": args.verify_url,
        "post_live_acceptance": False,
    }
    manifest_path = evidence / "promotion.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Final compare immediately before the only mutation.
    if sha256_file(live) != before_sha:
        raise RuntimeError("live subject changed after preparation; refusing promotion")

    atomic_copy(shadow, live)
    after_sha = sha256_file(live)
    if after_sha != shadow_sha:
        atomic_copy(rollback, live)
        raise RuntimeError(f"post-write hash mismatch {after_sha}; rollback attempted")

    http_sha, http_status, content_type = http_body_sha(args.verify_url)
    if http_status != 200 or http_sha != shadow_sha:
        atomic_copy(rollback, live)
        restored = sha256_file(live)
        raise RuntimeError(
            "HTTP readback mismatch after install; rollback executed: "
            f"status={http_status} http_sha={http_sha} restored={restored}"
        )

    manifest.update(
        {
            "status": "INSTALLED_PENDING_POST_LIVE_GATE",
            "after_sha256": after_sha,
            "http_status": http_status,
            "http_sha256": http_sha,
            "http_content_type": content_type,
            "post_live_acceptance": False,
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, sort_keys=True))
    print("EYE_LIVE_INSTALL=INSTALLED_PENDING_POST_LIVE_GATE")
    return 0


def rollback(args: argparse.Namespace) -> int:
    manifest_path = args.rollback_manifest.resolve()
    manifest = load_json(manifest_path)
    if manifest.get("schema") != "GO_AVATAR_EYE_LIVE_PROMOTION/v1":
        raise RuntimeError("rollback manifest schema mismatch")
    live = Path(str(manifest["live_path"])).resolve()
    rollback_path = Path(str(manifest["rollback_path"])).resolve()
    before_sha = str(manifest["before_sha256"])
    candidate_sha = str(manifest["candidate_sha256"])
    current = sha256_file(live)
    if current not in {candidate_sha, before_sha}:
        raise RuntimeError(f"refusing rollback from unknown live subject {current}")
    if current == before_sha:
        print("EYE_LIVE_ROLLBACK=ALREADY_RESTORED")
        return 0
    if sha256_file(rollback_path) != before_sha:
        raise RuntimeError("rollback artifact hash mismatch")
    atomic_copy(rollback_path, live)
    restored = sha256_file(live)
    if restored != before_sha:
        raise RuntimeError(f"rollback verification failed: {restored}")
    manifest["status"] = "ROLLED_BACK"
    manifest["rollback_verified_sha256"] = restored
    manifest["post_live_acceptance"] = False
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, sort_keys=True))
    print("EYE_LIVE_ROLLBACK=PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)

    install = sub.add_parser("install")
    install.add_argument("--visual-root", type=Path, required=True)
    install.add_argument("--shadow", type=Path, required=True)
    install.add_argument("--runtime-report", type=Path, required=True)
    install.add_argument("--matched-report", type=Path, required=True)
    install.add_argument("--evidence-dir", type=Path, required=True)
    install.add_argument("--verify-url", default="http://127.0.0.1:8788/")

    restore = sub.add_parser("rollback")
    restore.add_argument("--rollback-manifest", type=Path, required=True)

    args = ap.parse_args()
    if args.mode == "install":
        return promote(args)
    return rollback(args)


if __name__ == "__main__":
    raise SystemExit(main())
