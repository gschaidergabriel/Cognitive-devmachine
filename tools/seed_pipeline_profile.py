#!/usr/bin/env python3
"""Import a runtime profile and optional generic overlays into MiniUnifiedDB.

This is a configuration utility, not an application semantic authority. Overlay keys are
explicitly supplied by the operator; e.g. a state-box JSON can be stored under
`public_state_box` without teaching the pipeline any application name.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--profile", required=True, type=Path)
    ap.add_argument("--overlay", action="append", default=[], metavar="KEY=JSON_FILE")
    ns = ap.parse_args()
    profile = json.loads(ns.profile.read_text(encoding="utf-8"))
    for item in ns.overlay:
        if "=" not in item:
            raise SystemExit("OVERLAY_MUST_BE_KEY=FILE")
        key, path = item.split("=", 1)
        if not key or "." in key:
            raise SystemExit("OVERLAY_KEY_MUST_BE_SINGLE_PROFILE_FIELD")
        profile[key] = json.loads(Path(path).read_text(encoding="utf-8"))
    rt = ProfilePipelineRuntime(root=Path(ns.db).resolve().parent)
    result = rt.apply_profile(ns.db, profile)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
