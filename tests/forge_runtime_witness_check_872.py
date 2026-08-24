#!/usr/bin/env python3
"""Deterministic candidate check used only by the Forge producer runtime witness."""
from pathlib import Path

value = Path("tests/fixtures/forge_runtime_witness_872.txt").read_text(encoding="utf-8").strip()
raise SystemExit(0 if value == "PATCHED" else 1)
