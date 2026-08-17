"""Compatibility export for the single canonical method-kind registry.

All Stage-B implementation now lives in method_memory.py + method_stageb.py. This module
exists only so the retained Stage-A MicroClay code can import METHOD_KINDS without keeping
a second method-retrieval implementation.
"""
from .method_memory import METHOD_KINDS

__all__ = ["METHOD_KINDS"]
