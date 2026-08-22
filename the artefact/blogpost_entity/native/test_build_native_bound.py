"""Stable native 0.7 acceptance test entry.

Source-closure semantics remain owned by test_build_native_bound_source_closure.py.
Runtime guard semantics remain owned by test_native_runtime_guards.py. This adapter
only exposes both suites to the existing canonical exact-repro workflow.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load(filename: str, module_name: str):
    target = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, target)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_closure = _load("test_build_native_bound_source_closure.py", "mini_entity_source_closure_tests")
_runtime = _load("test_native_runtime_guards.py", "mini_entity_runtime_guard_tests")

SourceClosureTests = _closure.SourceClosureTests
NativeRuntimeGuardTests = _runtime.NativeRuntimeGuardTests
