#!/usr/bin/env python3
"""Generic command-line runner for the DB-resident Clay pipeline v2 reference path."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from clay_profile_pipeline_runtime_v2 import ProfilePipelineRuntimeV2, execute_source


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--entity-db", type=Path, required=True)
    parser.add_argument("--source-db", type=Path, required=True)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--study-surface", type=Path)
    parser.add_argument("--secret-file", default="")
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--apply-profile-only", action="store_true")
    args = parser.parse_args()

    runtime = ProfilePipelineRuntimeV2(root=ROOT, allow_network=args.allow_network)
    if args.profile is not None:
        applied = runtime.apply_profile_file(
            str(args.entity_db),
            args.profile,
            study_surface_path=args.study_surface,
        )
        if not applied.get("ok"):
            print(json.dumps(applied, sort_keys=True), file=sys.stderr)
            return 2
    elif args.study_surface is not None:
        parser.error("--study-surface requires --profile")

    if args.apply_profile_only:
        return 0

    source = args.source.read_text(encoding="utf-8")
    try:
        result, _ = execute_source(
            source,
            "run",
            [str(args.entity_db), str(args.source_db), args.secret_file],
            runtime,
        )
    except Exception as exc:
        print(json.dumps({"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
