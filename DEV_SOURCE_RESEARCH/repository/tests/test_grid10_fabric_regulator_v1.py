"""Regression tests for Fabric.get_regulator()/set_regulator() (2026-08-27, GRID10
cybernetic-cognition-architecture experiment, Part 7 -- adapted onto the REAL fabric
API, not the concept doc's imagined Grid10Fabric/get_regulator-with-no-CAS pseudocode).
"""
import importlib.util
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
spec = importlib.util.spec_from_file_location("grid10_fabric", TOOLS / "grid10_fabric.py")
grid10_fabric = importlib.util.module_from_spec(spec)
sys.modules["grid10_fabric"] = grid10_fabric
spec.loader.exec_module(grid10_fabric)

from grid10_fabric import Fabric, FabricError  # noqa: E402


def _fabric(tmp_path):
    return Fabric(tmp_path / "s1.sqlite")


def test_get_unset_regulator_no_default_returns_none(tmp_path):
    f = _fabric(tmp_path)
    assert f.get_regulator("temperature") is None


def test_get_unset_regulator_with_default(tmp_path):
    f = _fabric(tmp_path)
    r = f.get_regulator("temperature", default=0.85)
    assert r["value_real"] == 0.85
    assert r["version"] == 0


def test_set_then_get(tmp_path):
    f = _fabric(tmp_path)
    f.set_regulator("temperature", 0.9, writer="meta-eval-1")
    r = f.get_regulator("temperature")
    assert r["value_real"] == 0.9
    assert r["version"] == 1
    assert r["writer"] == "meta-eval-1"


def test_cas_success_then_stale_failure(tmp_path):
    f = _fabric(tmp_path)
    f.set_regulator("temperature", 0.9, writer="meta-eval-1")  # version -> 1
    f.set_regulator("temperature", 0.95, writer="meta-eval-1", expected_version=1)  # version -> 2

    with __import__("pytest").raises(FabricError):
        f.set_regulator("temperature", 1.0, writer="meta-eval-2", expected_version=1)  # stale

    r = f.get_regulator("temperature")
    assert r["value_real"] == 0.95
    assert r["version"] == 2


def test_independent_regulators(tmp_path):
    f = _fabric(tmp_path)
    f.set_regulator("temperature", 0.9, writer="meta-eval-1")
    f.set_regulator("top_p", 0.8, writer="meta-eval-2")

    assert f.get_regulator("temperature")["value_real"] == 0.9
    assert f.get_regulator("top_p")["value_real"] == 0.8

    f.set_regulator("temperature", 0.95, writer="meta-eval-1", expected_version=1)
    assert f.get_regulator("top_p")["value_real"] == 0.8
    assert f.get_regulator("top_p")["version"] == 1
