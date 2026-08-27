#!/usr/bin/env python3
"""Successor-dynamic reentry for the GO878 line-identity patch.

The original exact-blob patcher intentionally failed closed after main gained the
historical batch causal-binding repair. This wrapper admits that exact successor blob
without weakening any textual patch invariant.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PATCHER = HERE / "apply_go878_backfill_line_checkpoint.py"
SPEC = importlib.util.spec_from_file_location("go878_backfill_line_checkpoint", PATCHER)
if SPEC is None or SPEC.loader is None:
    raise SystemExit("GO878_LINE_PATCHER_UNRESOLVED")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

mod.EXPECTED_SOURCE_BLOB = "f095ec12ab28aa5df87b1762b2cc19afca592365"
mod.EXPECTED_TEST_BLOB = "702c2e42fe6e4881ef7a08b67f6b8b0b567ac8b4"

if __name__ == "__main__":
    raise SystemExit(mod.main())
