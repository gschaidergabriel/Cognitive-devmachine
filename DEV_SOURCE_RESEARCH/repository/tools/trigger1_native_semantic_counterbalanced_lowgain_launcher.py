#!/usr/bin/env python3
"""Calibration-only successor launcher for the semantic counterbalanced native-cvec test.

The prior run did not open holdout. This launcher changes only the declared calibration
search domain to lower gains while preserving the exact semantic derivation, calibration
families, counterbalancing, native runtime, six controls and still-unseen holdout.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from tools import trigger1_local_qwen06_native_semantic_counterbalanced_execute as experiment

LAYER_CANDIDATES = (14, 20)
GAIN_GRID = (0.25, 0.5, 1.0, 2.0, 4.0)


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output_dir_from_argv() -> Path | None:
    try:
        idx = sys.argv.index("--output-dir")
        return Path(sys.argv[idx + 1])
    except (ValueError, IndexError):
        return None


def main() -> int:
    experiment.LAYER_CANDIDATES = LAYER_CANDIDATES
    experiment.GAIN_GRID = GAIN_GRID
    out = output_dir_from_argv()
    rc = experiment.main()
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema": "CLAY_SEMANTIC_COUNTERBALANCED_CALIBRATION_OVERRIDE/v1",
            "launcher_sha256": sha_file(Path(__file__)),
            "base_executor_sha256": sha_file(Path(experiment.__file__)),
            "layer_candidates": list(LAYER_CANDIDATES),
            "gain_grid": list(GAIN_GRID),
            "changed_scope": "CALIBRATION_SEARCH_DOMAIN_ONLY",
            "holdout_definition_modified": False,
            "semantic_derivation_modified": False,
            "metric_definition_modified": False,
            "control_family_modified": False,
        }
        (out / "calibration_override_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
