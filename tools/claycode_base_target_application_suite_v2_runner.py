#!/usr/bin/env python3
"""CLI wrapper for the hardened target application suite with explicit registration path."""
from __future__ import annotations

import argparse
from pathlib import Path

import claycode_base_target_application_suite_v2 as suite
from claycode_target_host_identity import DEFAULT_REGISTRATION


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registration", type=Path, default=DEFAULT_REGISTRATION)
    args = ap.parse_args()
    # The suite's host verifier reads this module-global. Override only from an explicit
    # CLI path passed by the already identity-verifying canonical target entry point.
    suite.DEFAULT_REGISTRATION = args.registration
    return suite.main()


if __name__ == "__main__":
    raise SystemExit(main())
