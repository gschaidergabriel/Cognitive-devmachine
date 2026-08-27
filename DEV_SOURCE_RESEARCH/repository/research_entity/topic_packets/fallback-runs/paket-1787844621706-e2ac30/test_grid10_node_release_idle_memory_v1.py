"""Test the release_idle_memory() function from grid10_node_PATCHED.py.

This test verifies that the function:
1. Does not raise exceptions
2. Returns a dict with the expected structure
3. Actually performs memory release operations
"""
import pytest
from grid10_node_PATCHED import release_idle_memory

def test_release_idle_memory_returns_dict():
    """Test that release_idle_memory returns a dict with expected keys."""
    result = release_idle_memory()

    # Verify it's a dict
    assert isinstance(result, dict)

    # Verify required keys exist
    assert "gc_collected" in result
    assert "malloc_trim_called" in result
    assert "malloc_trim_method" in result

    # Verify gc_collected is True
    assert result["gc_collected"] is True

    # Either malloc_trim was called or there was an error
    if result["malloc_trim_called"]:
        assert result["malloc_trim_method"] in ["torch._C._malloc_trim", "ctypes_libc"]
    else:
        assert "malloc_trim_error" in result

def test_release_idle_memory_no_exceptions():
    """Test that release_idle_memory doesn't raise any exceptions."""
    # This should not raise any exceptions
    result = release_idle_memory()
    assert isinstance(result, dict)
