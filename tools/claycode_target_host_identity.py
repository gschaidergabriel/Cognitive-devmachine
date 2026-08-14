#!/usr/bin/env python3
"""Register/verify the owner-fixed Andreas Ubuntu developer-system identity locally.

The registration file is intentionally outside the repository by default. It binds the
trusted manual registration step to Linux machine-id plus stable host/runtime facts.
Repository/CI cannot manufacture a matching target receipt unless it executes on the
registered machine or someone deliberately copies the local trust anchor; that trust
anchor is therefore operational evidence, not a cryptographic hardware attestation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TARGET_HOST = "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"
DEFAULT_REGISTRATION = Path.home() / ".config" / "claycode" / "andreas_target_registration.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def command_text(argv: list[str]) -> str:
    try:
        return subprocess.run(argv, text=True, capture_output=True, timeout=5, check=False).stdout.strip()
    except Exception:
        return ""


def os_release() -> dict[str, str]:
    p = Path("/etc/os-release")
    out: dict[str, str] = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k] = v.strip().strip('"')
    return out


def fingerprint() -> dict:
    machine_id_path = Path("/etc/machine-id")
    machine_id = machine_id_path.read_text(encoding="utf-8").strip() if machine_id_path.exists() else ""
    cc = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang") or ""
    release = os_release()
    core = {
        "target_host": TARGET_HOST,
        "system": platform.system(),
        "architecture": platform.machine(),
        "hostname": socket.gethostname(),
        "os_id": release.get("ID"),
        "os_version_id": release.get("VERSION_ID"),
        "machine_id_sha256": sha(machine_id.encode()) if machine_id else None,
        "uname": command_text(["uname", "-a"]),
        "python_version": platform.python_version(),
        "c_compiler_path": cc,
        "c_compiler_version": command_text([cc, "--version"]).splitlines()[0] if cc else "",
    }
    core["fingerprint_sha256"] = sha(json.dumps(core, sort_keys=True, separators=(",", ":")).encode())
    return core


def validate_platform(fp: dict) -> list[str]:
    errors = []
    if fp.get("system") != "Linux": errors.append("NOT_LINUX")
    if str(fp.get("os_id", "")).lower() != "ubuntu": errors.append("NOT_UBUNTU")
    if not fp.get("machine_id_sha256"): errors.append("MACHINE_ID_MISSING")
    if not fp.get("c_compiler_version"): errors.append("C_COMPILER_MISSING")
    return errors


def register(path: Path, acknowledge: str) -> int:
    if acknowledge != TARGET_HOST:
        raise SystemExit(f"registration requires --acknowledge {TARGET_HOST}")
    fp = fingerprint()
    errors = validate_platform(fp)
    if errors:
        print(json.dumps({"registered": False, "errors": errors, "fingerprint": fp}, indent=2))
        return 2
    payload = {
        "schema_version": "1.0",
        "trust_anchor": "OWNER_MANUAL_TARGET_REGISTRATION",
        "target_host": TARGET_HOST,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "fingerprint": fp,
        "warning": "Keep this file local to the target machine. Copying it elsewhere weakens host-identity evidence.",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    print(json.dumps({"registered": True, "path": str(path), "fingerprint_sha256": fp["fingerprint_sha256"]}, indent=2))
    return 0


def verify(path: Path) -> tuple[bool, dict]:
    current = fingerprint()
    errors = validate_platform(current)
    if not path.exists():
        errors.append("LOCAL_TARGET_REGISTRATION_MISSING")
        return False, {"target_host": TARGET_HOST, "errors": errors, "current": current}
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"LOCAL_TARGET_REGISTRATION_INVALID:{type(exc).__name__}")
        return False, {"target_host": TARGET_HOST, "errors": errors, "current": current}
    if saved.get("target_host") != TARGET_HOST:
        errors.append("REGISTRATION_TARGET_ID_MISMATCH")
    registered = saved.get("fingerprint") or {}
    stable_keys = ["system", "architecture", "hostname", "os_id", "machine_id_sha256"]
    drift = {k: {"registered": registered.get(k), "current": current.get(k)} for k in stable_keys if registered.get(k) != current.get(k)}
    if drift:
        errors.append("TARGET_FINGERPRINT_DRIFT")
    payload = {
        "target_host": TARGET_HOST,
        "verified": not errors,
        "errors": errors,
        "registration_path": str(path),
        "registered_fingerprint_sha256": registered.get("fingerprint_sha256"),
        "current_fingerprint_sha256": current.get("fingerprint_sha256"),
        "stable_drift": drift,
        "host_fingerprint": {
            "uname": current.get("uname"),
            "architecture": current.get("architecture"),
            "python_version": current.get("python_version"),
            "c_compiler_version": current.get("c_compiler_version"),
            "machine_id_sha256": current.get("machine_id_sha256"),
            "os_id": current.get("os_id"),
            "os_version_id": current.get("os_version_id"),
            "hostname": current.get("hostname"),
        },
        "attestation_strength": "OWNER_LOCAL_REGISTRATION_PLUS_MACHINE_ID_FINGERPRINT_NOT_HARDWARE_ATTESTATION",
    }
    return not errors, payload


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("register")
    r.add_argument("--registration", type=Path, default=DEFAULT_REGISTRATION)
    r.add_argument("--acknowledge", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--registration", type=Path, default=DEFAULT_REGISTRATION)
    v.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.cmd == "register":
        return register(args.registration, args.acknowledge)
    ok, payload = verify(args.registration)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) if args.json else ("TARGET_HOST_VERIFIED" if ok else "TARGET_HOST_NOT_VERIFIED:" + ",".join(payload["errors"])))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
