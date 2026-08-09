#!/usr/bin/env python3
"""Canonical hardened ten-app runner with full FRANK handoff generation first."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import claycode_base_target_application_suite_v2 as suite
from claycode_target_host_identity import DEFAULT_REGISTRATION

ROOT = Path(__file__).resolve().parents[1]
FULL_FRANK = ROOT / "tools/claycode_full_frank_active_assembly_validation.py"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registration", type=Path, default=DEFAULT_REGISTRATION)
    args = ap.parse_args()

    # Generate the production H2/H3 receipt from the complete frozen H1 ActiveAssembly
    # before the ten-app suite reads FULL_FRANK_HANDOFF. This step itself re-verifies the
    # manually registered Andreas host and remains fail-closed on every differential.
    handoff = subprocess.run(
        [sys.executable, str(FULL_FRANK), "--target", "--registration", str(args.registration)],
        cwd=ROOT,
        check=False,
    )
    if handoff.returncode != 0:
        return handoff.returncode

    # The suite's host verifier reads this module-global. Override only from an explicit
    # CLI path passed by the already identity-verifying canonical target entry point.
    suite.DEFAULT_REGISTRATION = args.registration
    return suite.main()


if __name__ == "__main__":
    raise SystemExit(main())
