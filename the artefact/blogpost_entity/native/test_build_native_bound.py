"""Stable native 0.7 regression entry for the exact-repro workflow.

Source-closure semantics remain owned by test_build_native_bound_source_closure.py.
Local-runner environment isolation is exercised by test_native_local_env_isolation.py.
Profile-v2 admission debt is bound by test_native_v2_parity_contract.py.
This adapter exposes all three suites through one canonical workflow entry without
creating a second runtime or acceptance path.
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


_closure = _load(
    "test_build_native_bound_source_closure.py",
    "mini_entity_source_closure_tests",
)
_env = _load(
    "test_native_local_env_isolation.py",
    "mini_entity_local_env_isolation_tests",
)
_v2_parity = _load(
    "test_native_v2_parity_contract.py",
    "mini_entity_v2_parity_contract_tests",
)

SourceClosureTests = _closure.SourceClosureTests
NativeLocalEnvIsolationTests = _env.NativeLocalEnvIsolationTests
NativeProfileV2ParityContractTests = _v2_parity.NativeProfileV2ParityContractTests
