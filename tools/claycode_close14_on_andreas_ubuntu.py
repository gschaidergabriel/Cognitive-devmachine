#!/usr/bin/env python3
"""Compatibility entry point for canonical ClayCode BASE14 target closure.

There is exactly one authoritative executable closure sequence now:
`tools/claycode_run_andreas_target_acceptance.py`. This alias intentionally contains no
second gate/promotion ordering of its own.
"""
from __future__ import annotations

from claycode_run_andreas_target_acceptance import main


if __name__ == "__main__":
    raise SystemExit(main())
