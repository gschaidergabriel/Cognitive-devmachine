#!/usr/bin/env python3
"""Compatibility exports for the single ClayCode syntax authority.

New admission/evaluation code imports claycode_syntax_v1 directly. This module
remains only so existing regressions and bounded consumers do not create a
second parser implementation while they migrate.
"""
from claycode_syntax_v1 import canonical, extract_calls, call_set, fn_counts

__all__ = ["canonical", "extract_calls", "call_set", "fn_counts"]
