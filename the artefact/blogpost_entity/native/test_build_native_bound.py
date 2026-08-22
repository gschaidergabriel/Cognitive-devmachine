"""Compatibility loader for the canonical source-closure falsifier suite.

The test implementation lives only in test_build_native_bound_source_closure.py.
This adapter exists so the exact native 0.7 acceptance workflow can invoke a stable
entry path without duplicating test semantics.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_TARGET = Path(__file__).with_name("test_build_native_bound_source_closure.py")
_SPEC = importlib.util.spec_from_file_location("mini_entity_source_closure_tests", _TARGET)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

SourceClosureTests = _MODULE.SourceClosureTests
