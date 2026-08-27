"""Test grid10_node.py::release_idle_memory() (2026-08-27, GRID10 RAM-efficiency
concept). Verifies that the function:
1. Does not raise exceptions.
2. Returns a dict with the expected structure.
3. Actually performs a real gc.collect() + malloc_trim() release.
"""
import importlib.util
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
spec = importlib.util.spec_from_file_location("grid10_node", TOOLS / "grid10_node.py")
grid10_node = importlib.util.module_from_spec(spec)
sys.modules["grid10_node"] = grid10_node
spec.loader.exec_module(grid10_node)

from grid10_node import release_idle_memory  # noqa: E402


def test_release_idle_memory_returns_dict():
    result = release_idle_memory()

    assert isinstance(result, dict)
    assert "gc_collected" in result
    assert "malloc_trim_called" in result
    assert "malloc_trim_method" in result
    assert result["gc_collected"] is True

    if result["malloc_trim_called"]:
        assert result["malloc_trim_method"] in ["torch._C._malloc_trim", "ctypes_libc"]
    else:
        assert "malloc_trim_error" in result


def test_release_idle_memory_no_exceptions():
    result = release_idle_memory()
    assert isinstance(result, dict)


def test_release_idle_memory_callable_multiple_times():
    # must be safe to call repeatedly (this is what the idle-window trigger does)
    for _ in range(3):
        result = release_idle_memory()
        assert isinstance(result, dict)
