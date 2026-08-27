#!/usr/bin/env python3
"""Run the Ubuntu desktop target proof against the same explicit host registration.

The underlying validator remains the authority on desktop semantics. This wrapper only
binds its module-global registration path to the registration already verified by the
canonical BASE14 entry point.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import claycode_ubuntu_desktop_target_validation as desktop
from claycode_target_host_identity import DEFAULT_REGISTRATION


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registration", type=Path, default=DEFAULT_REGISTRATION)
    args = ap.parse_args()
    desktop.DEFAULT_REGISTRATION = args.registration
    return desktop.main()


if __name__ == "__main__":
    raise SystemExit(main())
