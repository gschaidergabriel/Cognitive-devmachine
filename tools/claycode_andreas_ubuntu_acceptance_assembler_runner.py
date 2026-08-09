#!/usr/bin/env python3
"""Run the strict target assembler against one explicit registered host identity.

In addition to the base assembler, this wrapper makes the real Ubuntu mapped-window
APP-05 receipt a hard prerequisite and binds its hash into the emitted strict target
receipt.  A kernel-FD/headless proxy cannot therefore satisfy the final GUI acceptance by
itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import claycode_andreas_ubuntu_acceptance_assembler as assembler
from claycode_target_host_identity import DEFAULT_REGISTRATION

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ROOT / "tools/claycode_target_host_identity.py"
DESKTOP = ROOT / "research_entity/claycode/target/APP05_UBUNTU_DESKTOP.json"
STRICT = ROOT / "research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_ACCEPTANCE_STRICT.json"
TARGET = "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def desktop_ok() -> tuple[bool, dict]:
    if not DESKTOP.exists():
        return False, {"error": "REAL_UBUNTU_DESKTOP_RECEIPT_MISSING"}
    try:
        d = json.loads(DESKTOP.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, {"error": "REAL_UBUNTU_DESKTOP_RECEIPT_INVALID", "detail": type(exc).__name__}
    observed = d.get("observed") if isinstance(d.get("observed"), dict) else {}
    ok = (
        d.get("target_host") == TARGET
        and d.get("application") == "GUI_INTERACTIVE"
        and d.get("pass") is True
        and d.get("counts_as_target_acceptance") is True
        and d.get("authority_boundary_preserved") is True
        and observed.get("io_mode") == "TK_REAL_DESKTOP_EVENT_LOOP"
        and observed.get("window_was_mapped") is True
        and (d.get("negative_or_failure_path") or {}).get("forbidden_event_rejected") is True
    )
    return ok, d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registration", type=Path, default=DEFAULT_REGISTRATION)
    args = ap.parse_args()

    def host_identity():
        cp = subprocess.run(
            [sys.executable, str(IDENTITY), "verify", "--registration", str(args.registration), "--json"],
            cwd=ROOT, text=True, capture_output=True, timeout=15, check=False,
        )
        try:
            data = json.loads(cp.stdout)
        except Exception:
            data = {
                "verified": False,
                "errors": ["HOST_IDENTITY_OUTPUT_INVALID"],
                "stdout_tail": cp.stdout[-1000:],
                "stderr_tail": cp.stderr[-1000:],
            }
        return cp.returncode == 0 and data.get("verified") is True, data

    desktop_pass, desktop = desktop_ok()
    if not desktop_pass:
        if STRICT.exists():
            STRICT.unlink()
        print(json.dumps({"overall_pass": False, "error": "REAL_UBUNTU_DESKTOP_NOT_ACCEPTED", "desktop": desktop}, ensure_ascii=False))
        return 2

    assembler.host_identity = host_identity
    rc = assembler.main()
    if rc != 0 or not STRICT.exists():
        return rc or 2

    strict = json.loads(STRICT.read_text(encoding="utf-8"))
    if strict.get("overall_pass") is not True:
        return 2
    applications = strict.get("applications") if isinstance(strict.get("applications"), dict) else {}
    gui = applications.get("GUI_INTERACTIVE") if isinstance(applications.get("GUI_INTERACTIVE"), dict) else None
    if gui is None:
        STRICT.unlink(missing_ok=True)
        print(json.dumps({"overall_pass": False, "error": "STRICT_GUI_APPLICATION_MISSING"}))
        return 2

    desktop_hash = sha(DESKTOP)
    gui["real_ubuntu_desktop"] = {
        "pass": True,
        "receipt_path": str(DESKTOP.relative_to(ROOT)),
        "receipt_sha256": desktop_hash,
        "io_mode": (desktop.get("observed") or {}).get("io_mode"),
        "window_was_mapped": (desktop.get("observed") or {}).get("window_was_mapped"),
    }
    strict["desktop_gui_target_pass"] = True
    strict["desktop_gui_receipt_path"] = str(DESKTOP.relative_to(ROOT))
    strict["desktop_gui_receipt_sha256"] = desktop_hash
    strict["overall_pass"] = True
    STRICT.write_text(json.dumps(strict, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"overall_pass": True, "desktop_gui_target_pass": True, "receipt": str(STRICT.relative_to(ROOT)), "desktop_sha256": desktop_hash}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
