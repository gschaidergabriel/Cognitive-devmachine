#!/usr/bin/env python3
"""CLI wrapper for the FULL_FRANK target finalizer with explicit registration path."""
from __future__ import annotations

import argparse
from pathlib import Path

import claycode_full_frank_target_finalizer as finalizer
from claycode_target_host_identity import DEFAULT_REGISTRATION


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registration", type=Path, default=DEFAULT_REGISTRATION)
    args = ap.parse_args()
    finalizer.DEFAULT_REGISTRATION = args.registration
    return finalizer.main()


if __name__ == "__main__":
    raise SystemExit(main())
