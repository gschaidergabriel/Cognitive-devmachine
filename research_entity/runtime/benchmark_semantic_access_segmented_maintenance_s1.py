#!/usr/bin/env python3
from __future__ import annotations

"""Matched segmented-vs-full benchmark bound to collision-free SPM-S1 identity."""

import benchmark_semantic_access_pulse_v12 as benchmark
from semantic_access_segmented_maintenance_s1 import SegmentedPulseMaintenanceS1

benchmark.SegmentedPulseProjection = SegmentedPulseMaintenanceS1

if __name__ == "__main__":
    benchmark.main()
