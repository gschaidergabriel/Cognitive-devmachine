#!/usr/bin/env python3
from __future__ import annotations

"""Run the existing matched segmented-vs-full benchmark against V16.

The benchmark logic remains unchanged so V16 stays directly comparable with the provisional
prototype. Only the projection implementation is replaced by the audit-complete V16 class.
"""

import benchmark_semantic_access_pulse_v12 as benchmark
from semantic_access_pulse_v16 import SegmentedPulseProjectionV16


benchmark.SegmentedPulseProjection = SegmentedPulseProjectionV16


if __name__ == "__main__":
    benchmark.main()
