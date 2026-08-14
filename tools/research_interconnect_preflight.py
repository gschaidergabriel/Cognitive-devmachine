#!/usr/bin/env python3
"""Compatibility entrypoint for the current Frank-v0.1 research interconnect preflight.

The implementation moved to research_interconnect_preflight_v2.py when registry schema 3.0
introduced distinct Frank-v0.1 operational trigger kinds.  Keep this historical path stable
because trigger protocols and external jobs invoke it directly.
"""
from research_interconnect_preflight_v2 import *  # noqa: F401,F403
from research_interconnect_preflight_v2 import main


if __name__ == "__main__":
    main()
