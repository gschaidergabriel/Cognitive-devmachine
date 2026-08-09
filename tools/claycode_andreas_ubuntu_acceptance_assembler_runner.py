#!/usr/bin/env python3
"""Run the strict target assembler against the same explicit host registration."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import claycode_andreas_ubuntu_acceptance_assembler as assembler
from claycode_target_host_identity import DEFAULT_REGISTRATION

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ROOT / "tools/claycode_target_host_identity.py"


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

    assembler.host_identity = host_identity
    return assembler.main()


if __name__ == "__main__":
    raise SystemExit(main())
